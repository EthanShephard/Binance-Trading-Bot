import logging

from .client import BinanceAPIError

logger = logging.getLogger("trading_bot.orders")


class OrderManager:
    def __init__(self, client):
        self.client = client

    def place_order(self, symbol, side, order_type, quantity, price=None, stop_price=None):
        logger.info(
            "Preparing order | symbol=%s side=%s type=%s qty=%s price=%s stop_price=%s",
            symbol, side, order_type, quantity, price, stop_price,
        )

        api_order_type = order_type
        kwargs = {}

        if order_type == "LIMIT":
            kwargs["time_in_force"] = "GTC"
            kwargs["price"] = price
        elif order_type == "STOP_LIMIT":
            # Binance futures has no literal "STOP_LIMIT" type; a stop order
            # with both stopPrice and price behaves as stop-limit.
            api_order_type = "STOP"
            kwargs["time_in_force"] = "GTC"
            kwargs["price"] = price
            kwargs["stop_price"] = stop_price
        # MARKET needs no extra params.

        try:
            response = self.client.place_order(
                symbol=symbol,
                side=side,
                order_type=api_order_type,
                quantity=quantity,
                **kwargs,
            )
        except BinanceAPIError as exc:
            logger.error("Order rejected by API: %s", exc)
            raise
        except Exception:
            logger.exception("Unexpected error while placing order")
            raise

        logger.info(
            "Order accepted | orderId=%s status=%s executedQty=%s",
            response.get("orderId"), response.get("status"), response.get("executedQty"),
        )
        return response
