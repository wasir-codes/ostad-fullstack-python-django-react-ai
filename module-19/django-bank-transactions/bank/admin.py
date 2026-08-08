from django.contrib import admin
from .models import BankAccount, Transaction

# registering these so I can poke around the data in /admin while testing
admin.site.register(BankAccount)
admin.site.register(Transaction)
