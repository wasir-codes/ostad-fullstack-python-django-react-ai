"""
This file talks to an external AI API (OpenRouter) to analyze a job
description and pull out 5 things: summary, required skills, required
experience, important technologies, and interview prep suggestions.

Kept in its own file instead of stuffed into views.py because it's a
distinct chunk of logic (build a prompt, call an API, parse text back out)
that doesn't need to know anything about Django requests/responses - it
just takes a string in and returns a dict out. Easier to reason about and
easier to test by hand in the shell if needed.
"""

import json
import requests
from django.conf import settings

OPENROUTER_URL = 'https://openrouter.ai/api/v1/chat/completions'

# telling the AI exactly what shape to reply in (a JSON object with these 5
# keys) makes the response predictable to parse. this is basically the whole
# trick to getting structured data out of a model that normally just writes
# paragraphs.
SYSTEM_PROMPT = (
    "You are an assistant that analyzes job descriptions for a job application "
    "tracker app. Given a job description, respond with ONLY a JSON object "
    "(no markdown, no code fences, no extra text) with exactly these keys: "
    "summary, required_skills, required_experience, important_technologies, "
    "interview_prep. Each value should be a short, plain-text paragraph or "
    "bullet-style list written as a single string."
)

# openrouter's free models share a pool with everyone else using them, so one
# can get rate-limited (HTTP 429) at random times that have nothing to do
# with our own usage. If the model set in .env fails, we retry once with this
# backup before giving up - keeps the feature working without needing a paid
# key. Kept as a plain constant instead of another .env setting since this is
# just a safety net, not something that needs configuring per-deployment.
BACKUP_MODEL = 'nvidia/nemotron-3-nano-30b-a3b:free'


def _call_openrouter(job_description, model):
    """
    Makes one request to OpenRouter with a specific model. Returns
    (result, error) same as analyze_job_description - kept as its own
    function so analyze_job_description can call it twice (primary model,
    then backup model) without repeating all this code.
    """
    headers = {
        'Authorization': f'Bearer {settings.OPENROUTER_API_KEY}',
        'Content-Type': 'application/json',
    }

    # this is the same request "shape" the OpenAI API uses - a list of
    # messages with roles. system = instructions for the model, user = the
    # actual thing we want it to work on
    payload = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': job_description},
        ],
    }

    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()  # raises an exception if we got a 4xx/5xx back
    except requests.exceptions.RequestException as e:
        return None, f'Could not reach the AI API ({e})'

    data = response.json()

    try:
        raw_text = data['choices'][0]['message']['content']
    except (KeyError, IndexError):
        return None, 'AI response was missing the expected content.'

    # some models wrap JSON in ```json ... ``` code fences even when told not
    # to - strip that off before trying to parse it
    raw_text = raw_text.strip()
    if raw_text.startswith('```'):
        raw_text = raw_text.strip('`')
        if raw_text.startswith('json'):
            raw_text = raw_text[4:]
        raw_text = raw_text.strip()

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        return None, 'Could not parse the AI response as JSON. Try again.'

    # build the result with .get() and a fallback string for every field -
    # if the model forgot a key, we still show something instead of a
    # KeyError crashing the whole view
    result = {
        'summary': parsed.get('summary', 'Not provided.'),
        'required_skills': parsed.get('required_skills', 'Not provided.'),
        'required_experience': parsed.get('required_experience', 'Not provided.'),
        'important_technologies': parsed.get('important_technologies', 'Not provided.'),
        'interview_prep': parsed.get('interview_prep', 'Not provided.'),
    }
    return result, None


def analyze_job_description(job_description):
    """
    Sends the job description to the AI model and returns (result, error).

    - result: a dict with the 5 fields, or None if something went wrong
    - error: a short string explaining what went wrong, or None if it worked

    Returning a tuple like this instead of raising an exception means the
    view can just check "did error come back?" without a try/except of its
    own for every possible failure.

    Tries the model set in .env (OPENROUTER_MODEL) first. If that fails for
    any reason, tries BACKUP_MODEL once before giving up - free models can
    get temporarily rate-limited by OpenRouter's shared pool at random times,
    unrelated to anything this app is doing.
    """
    if not settings.OPENROUTER_API_KEY:
        return None, 'No OPENROUTER_API_KEY set in .env'

    result, error = _call_openrouter(job_description, settings.OPENROUTER_MODEL)
    if result is not None:
        return result, None

    # first attempt failed - try the backup model, but only if it's actually
    # different from what we just tried (no point retrying the same thing)
    if settings.OPENROUTER_MODEL != BACKUP_MODEL:
        backup_result, backup_error = _call_openrouter(job_description, BACKUP_MODEL)
        if backup_result is not None:
            return backup_result, None
        error = f'{error} (backup model also failed: {backup_error})'

    return None, error
