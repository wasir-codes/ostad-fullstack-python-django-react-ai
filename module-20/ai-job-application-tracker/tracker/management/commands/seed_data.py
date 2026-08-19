from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from tracker.models import Category, Tag, JobApplication, Interview


class Command(BaseCommand):
    help = 'Creates a demo user with a few sample job applications and interviews, for screenshots.'

    def handle(self, *args, **options):
        # get_or_create so running this command twice doesn't create duplicate
        # demo users - it just reuses the existing one
        user, created = User.objects.get_or_create(username='demo_user')
        if created:
            user.set_password('demo12345')
            user.save()
            self.stdout.write('Created demo_user (password: demo12345)')
        else:
            self.stdout.write('demo_user already exists, reusing it')

        # a few categories and tags to attach to the sample applications
        backend, _ = Category.objects.get_or_create(name='Backend')
        frontend, _ = Category.objects.get_or_create(name='Frontend')
        data, _ = Category.objects.get_or_create(name='Data')

        django_tag, _ = Tag.objects.get_or_create(name='Django')
        remote_tag, _ = Tag.objects.get_or_create(name='Remote')
        startup_tag, _ = Tag.objects.get_or_create(name='Startup')

        today = timezone.now().date()

        sample_applications = [
            {
                'job_title': 'Junior Django Developer',
                'company_name': 'Nimbus Softworks',
                'job_description': (
                    'We are looking for a Junior Django Developer to join our backend team. '
                    'You will build REST APIs, work with PostgreSQL, and collaborate with the '
                    'frontend team. Required: Python, Django, basic SQL. Nice to have: Docker, '
                    'AWS, React. 0-1 years experience is fine, we mentor junior engineers.'
                ),
                'location': 'Remote',
                'salary': '40k-55k BDT',
                'job_url': 'https://example.com/jobs/1',
                'application_date': today - timedelta(days=10),
                'status': JobApplication.APPLIED,
                'category': backend,
                'tags': [django_tag, remote_tag],
            },
            {
                'job_title': 'Frontend Engineer',
                'company_name': 'Bright Path Labs',
                'job_description': (
                    'Bright Path Labs is hiring a Frontend Engineer to work on our React '
                    'dashboard product. You should be comfortable with JavaScript, React, and '
                    'CSS. Experience with TypeScript is a plus. 1-2 years of experience preferred.'
                ),
                'location': 'Dhaka',
                'salary': '50k-70k BDT',
                'job_url': 'https://example.com/jobs/2',
                'application_date': today - timedelta(days=5),
                'status': JobApplication.SCREENING,
                'category': frontend,
                'tags': [startup_tag],
            },
            {
                'job_title': 'Data Analyst Intern',
                'company_name': 'Northlake Analytics',
                'job_description': (
                    'Internship role for a Data Analyst. You will write SQL queries, build '
                    'dashboards, and help clean datasets. Python and Excel experience helpful. '
                    'No prior professional experience required - this is an entry-level internship.'
                ),
                'location': 'Khulna',
                'salary': '15k BDT',
                'job_url': 'https://example.com/jobs/3',
                'application_date': today - timedelta(days=2),
                'status': JobApplication.WISHLIST,
                'category': data,
                'tags': [],
            },
            {
                'job_title': 'Backend Engineer (Python)',
                'company_name': 'Ferrous Systems BD',
                'job_description': (
                    'Backend Engineer role working on a Django + DRF API serving a mobile app. '
                    'Required: Django, DRF, PostgreSQL, Git. Bonus: Celery, Redis, CI/CD. '
                    '2+ years experience preferred but open to strong junior candidates.'
                ),
                'location': 'Remote',
                'salary': '60k-90k BDT',
                'job_url': 'https://example.com/jobs/4',
                'application_date': today - timedelta(days=15),
                'status': JobApplication.INTERVIEW,
                'category': backend,
                'tags': [django_tag, remote_tag],
            },
        ]

        for entry in sample_applications:
            tags = entry.pop('tags')
            application, created = JobApplication.objects.get_or_create(
                user=user,
                job_title=entry['job_title'],
                company_name=entry['company_name'],
                defaults=entry,
            )
            if tags:
                application.tags.set(tags)  # .set() replaces the whole tag list in one go
            if created:
                self.stdout.write(f'  + {application}')

        # give the "Interview" status application an upcoming interview,
        # so the dashboard's "Upcoming Interviews" section has something to show
        interview_app = JobApplication.objects.get(user=user, company_name='Ferrous Systems BD')
        Interview.objects.get_or_create(
            application=interview_app,
            interview_type='TECHNICAL',
            defaults={
                'interview_datetime': timezone.now() + timedelta(days=3, hours=2),
                'meeting_link': 'https://meet.example.com/ferrous-tech-round',
                'notes': 'Focus on Django ORM and REST API design questions.',
            },
        )

        self.stdout.write(self.style.SUCCESS('Seed data ready. Log in as demo_user / demo12345'))
