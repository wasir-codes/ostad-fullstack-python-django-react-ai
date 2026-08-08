from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import BankAccount


class RegisterForm(UserCreationForm):
    # just using Django's built in form, added email since the default one
    # only asks for username + password
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        # loop through the fields and add bootstrap styling to all of them
        # instead of setting widgets one by one
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({'class': 'form-control'})


class BankAccountForm(forms.ModelForm):
    class Meta:
        model = BankAccount
        fields = ['account_holder_name', 'account_number', 'balance']
        widgets = {
            'account_holder_name': forms.TextInput(attrs={'class': 'form-control'}),
            'account_number': forms.TextInput(attrs={'class': 'form-control'}),
            # spelling out BDT here instead of the symbol - reads clearer in a form label
            'balance': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Starting balance (BDT)'}),
        }


class DepositForm(forms.Form):
    amount = forms.DecimalField(max_digits=12, decimal_places=2, min_value=0.01,
                                 widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Amount to deposit (BDT)'}))


class WithdrawForm(forms.Form):
    amount = forms.DecimalField(max_digits=12, decimal_places=2, min_value=0.01,
                                 widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Amount to withdraw (BDT)'}))
