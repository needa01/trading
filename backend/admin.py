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
    list_display = ('id', 'user', 'type', 'base_currency', 'quote_currency', 'price', 'quantity', 'remaining_quantity', 'status')
    exclude = ('user',)  # ✅ Hide user field from the form

    def save_model(self, request, obj, form, change):
        if not change or not obj.user_id:
            obj.user = request.user  # ✅ Assign current user
        obj.save()
        
        
    # 1. Restrict queryset based on user role
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return Order.objects.none()  # superusers see nothing
        return qs.filter(user=request.user)

    # 2. Auto-assign the current user and hide user field in form
    def save_model(self, request, obj, form, change):
        if not change or not obj.user_id:
            obj.user = request.user
        obj.save()

    # 3. Prevent users from seeing or editing `user` field
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not request.user.is_superuser:
            if 'user' in form.base_fields:
                form.base_fields['user'].disabled = True
        return form

    # 4. Hide fields from form that should be auto-handled
    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        readonly += ['locked_funds', 'remaining_quantity']
        return readonly

    # 5. Control add/change/delete permissions
    def has_change_permission(self, request, obj=None):
        return obj is None or obj.user == request.user

    def has_delete_permission(self, request, obj=None):
        return obj is None or obj.user == request.user

    def has_add_permission(self, request):
        return request.user.is_staff and not request.user.is_superuser

    # 6. Optional: Limit trading to specific base/quote pairs
    # def formfield_for_foreignkey(self, db_field, request, **kwargs):
    #     if db_field.name == "base_currency":
    #         kwargs["queryset"] = Currency.objects.filter(symbol__in=["BTC", "ETH"])
    #     if db_field.name == "quote_currency":
    #         kwargs["queryset"] = Currency.objects.filter(symbol__in=["INR", "USDT"])
    #     return super().formfield_for_foreignkey(db_field, request, **kwargs)

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