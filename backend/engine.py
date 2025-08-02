from .models import Order, Trade, Balance, LastTradedPrice, Charge
from django.db import transaction
from decimal import Decimal
from django.utils import timezone

@transaction.atomic
def match_orders():
    # Match BUY orders with SELL orders
    buy_orders = Order.objects.filter(type='BUY', status__in=['PENDING', 'PARTIAL']).order_by('-price', 'created_at')
    sell_orders = Order.objects.filter(type='SELL', status__in=['PENDING', 'PARTIAL']).order_by('price', 'created_at')

    for buy in buy_orders:
        for sell in sell_orders:
            if buy.base_currency != sell.base_currency or buy.quote_currency != sell.quote_currency:
                continue

            if buy.price < sell.price:
                continue  # Price mismatch

            match_qty = min(buy.remaining_quantity, sell.remaining_quantity)
            if match_qty <= 0:
                continue

            trade_price = sell.price
            total_trade_value = trade_price * match_qty

            # Fetch charges
            try:
                charge = Charge.objects.get(base_currency=buy.base_currency, quote_currency=buy.quote_currency, active=True)
                maker_fee = charge.maker_fee / 100  # convert to decimal percent
                taker_fee = charge.taker_fee / 100
            except Charge.DoesNotExist:
                maker_fee = taker_fee = Decimal(0)

            # Assume SELL is maker, BUY is taker
            fee_seller = trade_price * match_qty * maker_fee
            fee_buyer = trade_price * match_qty * taker_fee

            # Update balances
            _update_balance(sell.user, sell.base_currency, -match_qty)  # seller gives BTC
            _update_balance(sell.user, sell.quote_currency, total_trade_value - fee_seller)  # seller gets INR

            _update_balance(buy.user, buy.base_currency, match_qty)  # buyer receives BTC
            _update_balance(buy.user, buy.quote_currency, -(total_trade_value + fee_buyer))  # buyer pays INR

            # Update remaining quantities
            buy.remaining_quantity -= match_qty
            sell.remaining_quantity -= match_qty

            buy.status = 'PARTIAL' if buy.remaining_quantity > 0 else 'FILLED'
            sell.status = 'PARTIAL' if sell.remaining_quantity > 0 else 'FILLED'

            buy.save(update_fields=['remaining_quantity', 'status'])
            sell.save(update_fields=['remaining_quantity', 'status'])

            # Create Trade
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
    from .models import Balance
    obj, created = Balance.objects.get_or_create(user=user, currency=currency)
    obj.amount += Decimal(amount)
    obj.save(update_fields=['amount'])
