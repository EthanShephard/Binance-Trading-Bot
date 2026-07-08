import re

VALID_SIDES = {"BUY", "SELL"}
VALID_TYPES = {"MARKET", "LIMIT", "STOP_LIMIT"}

# Loose futures symbol pattern, e.g. BTCUSDT, ETHUSDT, 1000SHIBUSDT
SYMBOL_RE = re.compile(r"^[A-Z0-9]{5,20}$")


class ValidationError(Exception):
    """Raised for any bad user input, before an API call is ever made."""


def validate_symbol(symbol: str) -> str:
    symbol = (symbol or "").strip().upper()
    if not SYMBOL_RE.match(symbol):
        raise ValidationError(f"Invalid symbol: {symbol!r}. Expected e.g. 'BTCUSDT'.")
    return symbol


def validate_side(side: str) -> str:
    side = (side or "").strip().upper()
    if side not in VALID_SIDES:
        raise ValidationError(f"Invalid side: {side!r}. Must be one of {sorted(VALID_SIDES)}.")
    return side


def validate_order_type(order_type: str) -> str:
    order_type = (order_type or "").strip().upper()
    if order_type not in VALID_TYPES:
        raise ValidationError(
            f"Invalid order type: {order_type!r}. Must be one of {sorted(VALID_TYPES)}."
        )
    return order_type


def validate_quantity(quantity) -> float:
    try:
        quantity = float(quantity)
    except (TypeError, ValueError):
        raise ValidationError(f"Quantity must be a number, got {quantity!r}.")
    if quantity <= 0:
        raise ValidationError("Quantity must be greater than 0.")
    return quantity


def validate_price(price, required: bool):
    if price is None or price == "":
        if required:
            raise ValidationError("Price is required for LIMIT / STOP_LIMIT orders.")
        return None
    try:
        price = float(price)
    except (TypeError, ValueError):
        raise ValidationError(f"Price must be a number, got {price!r}.")
    if price <= 0:
        raise ValidationError("Price must be greater than 0.")
    return price


def validate_stop_price(stop_price, required: bool):
    if stop_price is None or stop_price == "":
        if required:
            raise ValidationError("Stop price is required for STOP_LIMIT orders.")
        return None
    try:
        stop_price = float(stop_price)
    except (TypeError, ValueError):
        raise ValidationError(f"Stop price must be a number, got {stop_price!r}.")
    if stop_price <= 0:
        raise ValidationError("Stop price must be greater than 0.")
    return stop_price
