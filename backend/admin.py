from django.contrib import admin

admin.site.site_header = "CoinDCX Admin"
admin.site.site_title = "Crypto Trading Platform"
admin.site.index_title = "Welcome to CoinDCX Admin Panel"

# Register your models here.
from .models import (
    CustomUser, Currency, Balance, WalletTransaction,
    Order, Trade, LastTradedPrice, Charge
)

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'username', 'is_active', 'is_staff')
    search_fields = ('email', 'username')
    
    def has_module_permission(self, request):
        return request.user.is_superuser

@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'name', 'is_crypto', 'active')
    search_fields = ('symbol', 'name')
    
    def has_module_permission(self, request):
        return request.user.is_superuser
    
@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'type', 'currency', 'amount', 'status', 'created_at')
    list_filter = ('type', 'status', 'currency')
    search_fields = ('user__email',)
    def has_module_permission(self, request):
        return request.user.is_staff
    
@admin.register(Balance)
class BalanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'currency', 'amount')
    list_filter = ('currency',)
    search_fields = ('user__email',)



@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'type', 'execution_type', 'base_currency', 'quote_currency',
        'price', 'quantity', 'remaining_quantity', 'status', 'created_at'
    )
    list_filter = ('type', 'execution_type', 'status', 'base_currency')
    search_fields = ('user__email',)

@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = (
        'buyer', 'seller', 'base_currency', 'quote_currency',
        'price', 'quantity', 'traded_at'
    )
    search_fields = ('buyer__email', 'seller__email')
    list_filter = ('base_currency', 'quote_currency')

@admin.register(LastTradedPrice)
class LastTradedPriceAdmin(admin.ModelAdmin):
    list_display = ('base_currency', 'quote_currency', 'price', 'updated_at')

@admin.register(Charge)
class ChargeAdmin(admin.ModelAdmin):
    list_display = ('base_currency', 'quote_currency', 'maker_fee', 'taker_fee', 'active')
