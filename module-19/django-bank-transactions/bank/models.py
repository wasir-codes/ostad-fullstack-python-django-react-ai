from django.db import models
from django.contrib.auth.models import User


class BankAccount(models.Model):
    """
    One user has exactly one bank account (that's all this assignment asks for).
    We use OneToOneField so Django enforces that at the database level.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    account_holder_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=20, unique=True)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.account_holder_name} - {self.account_number}"


class Transaction(models.Model):
    """
    Every deposit/withdrawal made against an account gets a row here.
    Storing balance_after means we don't have to recalculate history later.
    """
    DEPOSIT = 'DEPOSIT'
    WITHDRAWAL = 'WITHDRAWAL'
    TRANSACTION_TYPES = [
        (DEPOSIT, 'Deposit'),
        (WITHDRAWAL, 'Withdrawal'),
    ]

    account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        # newest transactions first by default
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.transaction_type} of {self.amount} on {self.account.account_number}"
