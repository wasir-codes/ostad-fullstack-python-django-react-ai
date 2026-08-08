from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count
from django.core.paginator import Paginator
from datetime import datetime

from .forms import RegisterForm, BankAccountForm, DepositForm, WithdrawForm
from .models import BankAccount, Transaction


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # log them in right away, no need to make them log in twice
            messages.success(request, 'Account created! Now set up your bank account below.')
            return redirect('create_account')
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = RegisterForm()
    return render(request, 'bank/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'bank/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def create_account(request):
    # if this user already has an account, don't let them make a second one
    if BankAccount.objects.filter(user=request.user).exists():
        return redirect('dashboard')

    if request.method == 'POST':
        form = BankAccountForm(request.POST)
        if form.is_valid():
            account = form.save(commit=False)
            account.user = request.user
            account.save()
            messages.success(request, 'Bank account created successfully.')
            return redirect('dashboard')
    else:
        form = BankAccountForm()
    return render(request, 'bank/create_account.html', {'form': form})


@login_required
def dashboard(request):
    # every logged in user only ever sees their own account - filtered by request.user
    account = BankAccount.objects.filter(user=request.user).first()
    if not account:
        return redirect('create_account')

    # aggregate totals using the ORM instead of looping over transactions in python
    deposits = account.transactions.filter(transaction_type=Transaction.DEPOSIT).aggregate(total=Sum('amount'))
    withdrawals = account.transactions.filter(transaction_type=Transaction.WITHDRAWAL).aggregate(total=Sum('amount'))
    total_transactions = account.transactions.aggregate(count=Count('id'))

    context = {
        'account': account,
        'total_deposits': deposits['total'] or 0,
        'total_withdrawals': withdrawals['total'] or 0,
        'total_transactions': total_transactions['count'] or 0,
    }
    return render(request, 'bank/dashboard.html', context)


@login_required
def deposit_view(request):
    account = get_object_or_404(BankAccount, user=request.user)

    if request.method == 'POST':
        form = DepositForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            account.balance += amount
            account.save()

            Transaction.objects.create(
                account=account,
                transaction_type=Transaction.DEPOSIT,
                amount=amount,
                balance_after=account.balance,
            )
            messages.success(request, f'Deposited ৳{amount} successfully. New balance: ৳{account.balance}')
            return redirect('dashboard')
    else:
        form = DepositForm()
    return render(request, 'bank/deposit.html', {'form': form, 'account': account})


@login_required
def withdraw_view(request):
    account = get_object_or_404(BankAccount, user=request.user)

    if request.method == 'POST':
        form = WithdrawForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']

            # prevent overdraft - can't take out more money than what's in the account
            if amount > account.balance:
                messages.error(request, 'Insufficient balance for this withdrawal.')
            else:
                account.balance -= amount
                account.save()

                Transaction.objects.create(
                    account=account,
                    transaction_type=Transaction.WITHDRAWAL,
                    amount=amount,
                    balance_after=account.balance,
                )
                messages.success(request, f'Withdrew ৳{amount} successfully. New balance: ৳{account.balance}')
                return redirect('dashboard')
    else:
        form = WithdrawForm()
    return render(request, 'bank/withdraw.html', {'form': form, 'account': account})


@login_required
def transaction_history(request):
    account = get_object_or_404(BankAccount, user=request.user)
    transactions = account.transactions.all()  # already ordered newest first via Meta.ordering

    # search by type (deposit/withdrawal) - dropdown on the template
    type_filter = request.GET.get('type', '')
    if type_filter:
        transactions = transactions.filter(transaction_type=type_filter)

    # filter by a specific date, e.g. 21/05/2026 typed into a text box (dd/mm/yyyy,
    # matches the format used everywhere else on this page)
    date_filter = request.GET.get('date', '')
    if date_filter:
        # make sure it's actually a real dd/mm/yyyy date before filtering with it -
        # otherwise a bad value would crash the page, and Django's timestamp__date
        # lookup expects an actual date object, not a dd/mm/yyyy string
        try:
            parsed_date = datetime.strptime(date_filter, '%d/%m/%Y').date()
            transactions = transactions.filter(timestamp__date=parsed_date)
        except ValueError:
            messages.error(request, 'Please enter the date as dd/mm/yyyy.')

    # paginate so the page doesn't get huge with lots of transactions
    paginator = Paginator(transactions, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'type_filter': type_filter,
        'date_filter': date_filter,
    }
    return render(request, 'bank/transaction_history.html', context)
