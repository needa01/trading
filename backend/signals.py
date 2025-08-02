from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from decimal import Decimal

from .models import Order, Balance, Trade, Charge, LastTradedPrice
from django.db import transaction


@receiver(post_save, sender=Order)
def handle_order_creation(sender, instance, created, **kwargs):
    if created:
        lock_funds(instance)
        match_orders()


def lock_funds(order):
    """Lock funds when an order is created."""
    if order.type == 'BUY':
        total_cost = order.price * order.quantity
        _lock_user_balance(order.user, order.quote_currency, total_cost)
        order.locked_funds = total_cost
    elif order.type == 'SELL':
        _lock_user_balance(order.user, order.base_currency, order.quantity)
        order.locked_funds = order.quantity

    order.save(update_fields=['locked_funds'])


def _lock_user_balance(user, currency, amount):
    """Lock funds from user balance."""
    balance, _ = Balance.objects.get_or_create(user=user, currency=currency)
    if balance.amount < amount:
        raise Exception("Insufficient balance to place order.")
    balance.amount -= amount
    balance.save(update_fields=['amount'])


@transaction.atomic
def match_orders():
    buy_orders = Order.objects.select_for_update().filter(type='BUY', status__in=['PENDING', 'PARTIAL']).order_by('-price', 'created_at')
    sell_orders = Order.objects.select_for_update().filter(type='SELL', status__in=['PENDING', 'PARTIAL']).order_by('price', 'created_at')

    for buy in buy_orders:
        for sell in sell_orders:
            if (
                buy.base_currency != sell.base_currency or
                buy.quote_currency != sell.quote_currency or
                buy.price < sell.price or
                buy.remaining_quantity <= 0 or
                sell.remaining_quantity <= 0
            ):
                continue

            match_qty = min(buy.remaining_quantity, sell.remaining_quantity)
            trade_price = sell.price
            total_trade_value = trade_price * match_qty

            # Charges
            maker_fee = taker_fee = Decimal(0)
            try:
                charge = Charge.objects.get(base_currency=buy.base_currency, quote_currency=buy.quote_currency, active=True)
                maker_fee = charge.maker_fee / 100
                taker_fee = charge.taker_fee / 100
            except Charge.DoesNotExist:
                pass

            fee_seller = total_trade_value * maker_fee
            fee_buyer = total_trade_value * taker_fee

            # Update balances
            _update_balance(sell.user, sell.quote_currency, total_trade_value - fee_seller)  # Seller gets quote
            _update_balance(buy.user, buy.base_currency, match_qty)  # Buyer gets base

            # Deduct locked funds
            buy.locked_funds -= (total_trade_value + fee_buyer)
            sell.locked_funds -= match_qty
            buy.save(update_fields=['locked_funds'])
            sell.save(update_fields=['locked_funds'])

            # Update orders
            buy.remaining_quantity -= match_qty
            sell.remaining_quantity -= match_qty

            buy.status = 'PARTIAL' if buy.remaining_quantity > 0 else 'FILLED'
            sell.status = 'PARTIAL' if sell.remaining_quantity > 0 else 'FILLED'

            buy.save(update_fields=['remaining_quantity', 'status'])
            sell.save(update_fields=['remaining_quantity', 'status'])

            # Record trade
            Trade.objects.create(
                buy_order=buy,
                sell_order=sell,
                buyer=buy.user,
                seller=sell.user,
                base_currency=buy.base_currency,
                quote_currency=buy.quote_currency,
                price=trade_price,
                quantity=match_qty,
                fee_buyer=fee_buyer,
                fee_seller=fee_seller,
                traded_at=timezone.now()
            )

            # Update LTP
            LastTradedPrice.objects.update_or_create(
                base_currency=buy.base_currency,
                quote_currency=buy.quote_currency,
                defaults={'price': trade_price, 'updated_at': timezone.now()}
            )

            if buy.remaining_quantity == 0:
                break  # move to next buy order


def _update_balance(user, currency, amount):
    balance, _ = Balance.objects.get_or_create(user=user, currency=currency)
    balance.amount += amount
    balance.save(update_fields=['amount'])


# Optional — Call this if you want to cancel an order manually
def release_locked_funds(order):
    if order.locked_funds > 0:
        if order.type == 'BUY':
            _update_balance(order.user, order.quote_currency, order.locked_funds)
        elif order.type == 'SELL':
            _update_balance(order.user, order.base_currency, order.locked_funds)
        order.locked_funds = Decimal(0)
        order.status = 'CANCELLED'
        order.save(update_fields=['locked_funds', 'status'])
