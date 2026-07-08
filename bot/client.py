import hashlib
import hmac
import logging
import time
from urllib.parse import urlencode

import requests

logger = logging.getLogger("trading_bot.client")


class BinanceAPIError(Exception):
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self.payload = payload
        super().__init__(f"Binance API error [{status_code}]: {payload}")


class BinanceFuturesClient:
    def __init__(self, api_key, api_secret, base_url="https://testnet.binancefuture.com", timeout=10):
        if not api_key or not api_secret:
            raise ValueError(
                "API key and secret must be set (BINANCE_API_KEY / BINANCE_API_SECRET env vars)."
            )
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        self.session = requests.Session()
        self.session.headers.update({"X-MBX-APIKEY": self.api_key})

    def _sign(self, params: dict) -> dict:
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"), query_string.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        params["signature"] = signature
        return params

    def _request(self, method: str, path: str, params: dict = None, signed: bool = False) -> dict:
        url = f"{self.base_url}{path}"
        params = dict(params) if params else {}

        if signed:
            params["timestamp"] = int(time.time() * 1000)
            params.setdefault("recvWindow", 5000)
            params = self._sign(params)

        # Never log the signature or api key.
        safe_params = {k: v for k, v in params.items() if k != "signature"}
        logger.info("REQUEST %s %s | params=%s", method, path, safe_params)

        try:
            response = self.session.request(method, url, params=params, timeout=self.timeout)
        except requests.exceptions.RequestException as exc:
            logger.error("NETWORK ERROR %s %s | %s", method, path, exc)
            raise

        try:
            data = response.json()
        except ValueError:
            data = {"raw_text": response.text}

        if response.status_code >= 400:
            logger.error(
                "RESPONSE %s %s | status=%s body=%s", method, path, response.status_code, data
            )
            raise BinanceAPIError(response.status_code, data)

        logger.info(
            "RESPONSE %s %s | status=%s body=%s", method, path, response.status_code, data
        )
        return data

    # --- Public endpoints -------------------------------------------------

    def ping(self) -> dict:
        return self._request("GET", "/fapi/v1/ping")

    def get_server_time(self) -> dict:
        return self._request("GET", "/fapi/v1/time")

    def get_symbol_price(self, symbol: str) -> dict:
        return self._request("GET", "/fapi/v1/ticker/price", {"symbol": symbol})

    # --- Signed (trading) endpoints ----------------------------------------

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: float = None,
        time_in_force: str = None,
        stop_price: float = None,
        reduce_only: bool = None,
    ) -> dict:
        params = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
        }
        if time_in_force:
            params["timeInForce"] = time_in_force
        if price is not None:
            params["price"] = price
        if stop_price is not None:
            params["stopPrice"] = stop_price
        if reduce_only is not None:
            params["reduceOnly"] = reduce_only

        return self._request("POST", "/fapi/v1/order", params, signed=True)

    def get_order(self, symbol: str, order_id: int) -> dict:
        return self._request(
            "GET", "/fapi/v1/order", {"symbol": symbol, "orderId": order_id}, signed=True
        )

    def cancel_order(self, symbol: str, order_id: int) -> dict:
        return self._request(
            "DELETE", "/fapi/v1/order", {"symbol": symbol, "orderId": order_id}, signed=True
        )
