#!/usr/bin/env python3
import argparse
import logging
import os
import sys

from bot.client import BinanceAPIError, BinanceFuturesClient
from bot.logging_config import setup_logging
from bot.orders import OrderManager
from bot.validators import (
    ValidationError,
    validate_order_type,
    validate_price,
    validate_quantity,
    validate_side,
    validate_stop_price,
    validate_symbol,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Place MARKET / LIMIT / STOP_LIMIT orders on Binance Futures Testnet (USDT-M)."
    )
    parser.add_argument("--symbol", required=True, help="Trading pair, e.g. BTCUSDT")
    parser.add_argument("--side", required=True, help="BUY or SELL")
    parser.add_argument(
        "--type", dest="order_type", required=True, help="MARKET, LIMIT, or STOP_LIMIT"
    )
    parser.add_argument("--quantity", required=True, help="Order quantity")
    parser.add_argument("--price", required=False, help="Required for LIMIT / STOP_LIMIT")
    parser.add_argument(
        "--stop-price", dest="stop_price", required=False, help="Required for STOP_LIMIT"
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("BINANCE_BASE_URL", "https://testnet.binancefuture.com"),
        help="API base URL (defaults to Futures Testnet)",
    )
    return parser


def main(argv=None) -> int:
    logger = setup_logging()
    parser = build_parser()
    args = parser.parse_args(argv)

    # --- Validate input before touching the network at all -----------------
    try:
        symbol = validate_symbol(args.symbol)
        side = validate_side(args.side)
        order_type = validate_order_type(args.order_type)
        quantity = validate_quantity(args.quantity)
        price = validate_price(args.price, required=order_type in ("LIMIT", "STOP_LIMIT"))
        stop_price = validate_stop_price(args.stop_price, required=order_type == "STOP_LIMIT")
    except ValidationError as exc:
        print(f"[INPUT ERROR] {exc}")
        logger.error("Input validation failed: %s", exc)
        return 1

    print("Order request summary:")
    print(f"  Symbol     : {symbol}")
    print(f"  Side       : {side}")
    print(f"  Type       : {order_type}")
    print(f"  Quantity   : {quantity}")
    if price is not None:
        print(f"  Price      : {price}")
    if stop_price is not None:
        print(f"  Stop Price : {stop_price}")

    # --- Build client --------------------------------------------------------
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")

    try:
        client = BinanceFuturesClient(api_key, api_secret, base_url=args.base_url)
    except ValueError as exc:
        print(f"[CONFIG ERROR] {exc}")
        logger.error("Client configuration error: %s", exc)
        return 1

    order_manager = OrderManager(client)

    # --- Place order -----------------------------------------------------------
    try:
        response = order_manager.place_order(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
        )
    except BinanceAPIError as exc:
        print(f"[API ERROR] {exc}")
        return 1
    except Exception as exc:  # network errors, timeouts, etc.
        print(f"[UNEXPECTED ERROR] {exc}")
        return 1

    print("\nOrder response:")
    print(f"  orderId     : {response.get('orderId')}")
    print(f"  status      : {response.get('status')}")
    print(f"  executedQty : {response.get('executedQty')}")
    print(f"  avgPrice    : {response.get('avgPrice')}")
    print("\n✅ Order placed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
