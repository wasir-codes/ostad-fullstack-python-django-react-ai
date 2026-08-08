from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from bank.models import BankAccount, Transaction
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone


class Command(BaseCommand):
    """
    Quick command to create a demo user + account + some transactions
    so there's data to take screenshots of.

    Run with: python manage.py seed_data
    """
    help = 'Seeds the database with one sample user, account, and transactions'

    def handle(self, *args, **kwargs):
        # delete old demo user first so this command can be run more than once
        User.objects.filter(username='demo_user').delete()

        user = User.objects.create_user(username='demo_user', password='DemoPass123')
        account = BankAccount.objects.create(
            user=user,
            account_holder_name='Demo User',
            account_number='ACC1000123',
            balance=Decimal('0.00'),
        )

        # a mix of deposits and withdrawals, roughly one per day going backwards
        sample_transactions = [
            ('DEPOSIT', Decimal('1000.00')),
            ('DEPOSIT', Decimal('500.00')),
            ('WITHDRAWAL', Decimal('200.00')),
            ('DEPOSIT', Decimal('750.00')),
            ('WITHDRAWAL', Decimal('300.00')),
            ('DEPOSIT', Decimal('150.00')),
            ('WITHDRAWAL', Decimal('100.00')),
            ('DEPOSIT', Decimal('400.00')),
        ]

        balance = Decimal('0.00')
        days_ago = len(sample_transactions)
        for txn_type, amount in sample_transactions:
            if txn_type == 'DEPOSIT':
                balance += amount
            else:
                balance -= amount

            txn = Transaction.objects.create(
                account=account,
                transaction_type=txn_type,
                amount=amount,
                balance_after=balance,
            )
            # backdate the timestamp a bit so the history page looks realistic
            # (auto_now_add sets it automatically, so we update it after creation)
            txn.timestamp = timezone.now() - timedelta(days=days_ago)
            txn.save()
            days_ago -= 1

        account.balance = balance
        account.save()

        self.stdout.write(self.style.SUCCESS(
            f'Seeded demo_user (password: DemoPass123) with account {account.account_number}, '
            f'balance BDT {account.balance}, and {len(sample_transactions)} transactions.'
        ))
