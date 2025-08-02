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
    
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'type', 'price', 'quantity', 'remaining_quantity', 'status')
    def get_queryset(self, request):
        if request.user.is_superuser:
            return Order.objects.none()  # superuser sees nothing
        return super().get_queryset(request).filter(user=request.user)
    def has_change_permission(self, request, obj=None):
        return obj is None or obj.user == request.user
    def has_delete_permission(self, request, obj=None):
        return obj is None or obj.user == request.user
    def has_add_permission(self, request):
        return request.user.is_staff and not request.user.is_superuser

admin.site.register(Order, OrderAdmin)

# ---------------- Trade Admin ----------------
class TradeAdmin(admin.ModelAdmin):
    list_display = ('id', 'buyer', 'seller', 'base_currency', 'quote_currency', 'price', 'quantity', 'traded_at')
    def get_queryset(self, request):
        if request.user.is_superuser:
            return Trade.objects.none()
        return Trade.objects.filter(buyer=request.user) | Trade.objects.filter(seller=request.user)
    def has_module_permission(self, request):
        return not request.user.is_superuser
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False

admin.site.register(Trade, TradeAdmin)

# ---------------- LTP Admin ----------------
class LTPAdmin(admin.ModelAdmin):
    list_display = ('id', 'base_currency', 'quote_currency', 'price', 'updated_at')
    def has_module_permission(self, request):
        return not request.user.is_superuser
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False

admin.site.register(LastTradedPrice, LTPAdmin)

# ---------------- Charges Admin ----------------
class ChargesAdmin(admin.ModelAdmin):
    list_display = ('base_currency', 'quote_currency', 'maker_fee', 'taker_fee')
    def get_queryset(self, request):
        return Charge.objects.none() if request.user.is_superuser else super().get_queryset(request)
    def has_module_permission(self, request):
        return not request.user.is_superuser
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False

admin.site.register(Charge, ChargesAdmin)

# ---------------- Balance Admin ----------------
class BalanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'currency', 'amount')
    def get_queryset(self, request):
        return Balance.objects.filter(user=request.user) if not request.user.is_superuser else Balance.objects.none()
    def has_module_permission(self, request):
        return not request.user.is_superuser
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False

admin.site.register(Balance, BalanceAdmin)