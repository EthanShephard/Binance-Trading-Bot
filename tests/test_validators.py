import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from bot.validators import (
    ValidationError,
    validate_order_type,
    validate_price,
    validate_quantity,
    validate_side,
    validate_stop_price,
    validate_symbol,
)


def test_validate_symbol_ok():
    assert validate_symbol("btcusdt") == "BTCUSDT"


def test_validate_symbol_bad():
    with pytest.raises(ValidationError):
        validate_symbol("BTC")


def test_validate_side_ok():
    assert validate_side("buy") == "BUY"


def test_validate_side_bad():
    with pytest.raises(ValidationError):
        validate_side("HOLD")


def test_validate_order_type_ok():
    assert validate_order_type("limit") == "LIMIT"


def test_validate_order_type_bad():
    with pytest.raises(ValidationError):
        validate_order_type("ICEBERG")


def test_validate_quantity_ok():
    assert validate_quantity("0.5") == 0.5


def test_validate_quantity_zero_fails():
    with pytest.raises(ValidationError):
        validate_quantity("0")


def test_validate_price_required_missing():
    with pytest.raises(ValidationError):
        validate_price(None, required=True)


def test_validate_price_not_required_missing():
    assert validate_price(None, required=False) is None


def test_validate_stop_price_required_missing():
    with pytest.raises(ValidationError):
        validate_stop_price(None, required=True)
