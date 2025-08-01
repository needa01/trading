from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    fullname = models.CharField(max_length=255, null=True, blank=True) 
    username = models.CharField(max_length=255, unique=True, blank=False, null=False)
    title = models.TextField(null=True, blank=True)
    email = models.EmailField(unique=True) 
    created_at = models.DateTimeField(auto_now_add=True,blank=False,null=False)



class Currency(models.Model):
    name = models.CharField(max_length=50)
    symbol = models.CharField(max_length=10, unique=True)
    is_crypto = models.BooleanField(default=True)
    active = models.BooleanField(default=True)
    
class Balances(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    currency =models.ForeignKey(Currency, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('user', 'currency')
        
class WalletTransaction(models.Model):
    class TransactionType(models.TextChoices):
        DEPOSIT = 'deposit'
        WITHDRAWAL = 'withdrawal'

    class TransactionStatus(models.TextChoices):
        PENDING = 'pending'
        COMPLETED = 'completed'
        FAILED = 'failed'

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='wallet_transactions')
    type = models.CharField(max_length=10, choices=TransactionType.choices)
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    status = models.CharField(max_length=10, choices=TransactionStatus.choices, default='pending')
    source = models.TextField(null=True, blank=True)
    destination = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

# --- 5. Orders ---
class Order(models.Model):
    class OrderType(models.TextChoices):
        BUY = 'buy'
        SELL = 'sell'

    class ExecutionType(models.TextChoices):
        LIMIT = 'limit'
        MARKET = 'market'

    class OrderStatus(models.TextChoices):
        PENDING = 'pending'
        PARTIAL = 'partial'
        EXECUTED = 'executed'
        CANCELLED = 'cancelled'

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='orders')
    type = models.CharField(max_length=10, choices=OrderType.choices)
    execution_type = models.CharField(max_length=10, choices=ExecutionType.choices, default='limit')
    base_currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='base_orders')
    quote_currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='quote_orders')
    price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    quantity = models.DecimalField(max_digits=20, decimal_places=8)
    remaining_quantity = models.DecimalField(max_digits=20, decimal_places=8)
    locked_funds = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    status = models.CharField(max_length=10, choices=OrderStatus.choices, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

# --- 6. Trades ---
class Trade(models.Model):
    buy_order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, related_name='buy_trades')
    sell_order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, related_name='sell_trades')
    buyer = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='buy_trades')
    seller = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='sell_trades')
    base_currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='base_trades')
    quote_currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='quote_trades')
    price = models.DecimalField(max_digits=20, decimal_places=8)
    quantity = models.DecimalField(max_digits=20, decimal_places=8)
    fee_buyer = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    fee_seller = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    traded_at = models.DateTimeField(auto_now_add=True)

# --- 7. Last Traded Price (LTP) ---
class LastTradedPrice(models.Model):
    base_currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='ltp_base')
    quote_currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='ltp_quote')
    price = models.DecimalField(max_digits=20, decimal_places=8)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('base_currency', 'quote_currency')

# --- 8. Charges ---
class Charge(models.Model):
    base_currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='charges_base')
    quote_currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='charges_quote')
    maker_fee = models.DecimalField(max_digits=5, decimal_places=4)
    taker_fee = models.DecimalField(max_digits=5, decimal_places=4)
    active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('base_currency', 'quote_currency')
