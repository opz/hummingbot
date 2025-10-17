import hmac
import json
import logging
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from hummingbot.connector.exchange.coinbase_wrapped import coinbase_wrapped_constants as constants
from hummingbot.connector.time_synchronizer import TimeSynchronizer
from hummingbot.core.web_assistant.auth import AuthBase
from hummingbot.core.web_assistant.connections.data_types import RESTMethod, RESTRequest, WSRequest
from hummingbot.logger import HummingbotLogger


class CoinbaseWrappedAuth(AuthBase):
    """Simple HMAC auth for Coinbase Exchange REST endpoints."""

    _logger: Optional[HummingbotLogger] = None

    def __init__(self, api_key: str, api_secret: str, time_provider: TimeSynchronizer):
        self._api_key = api_key
        self._api_secret = api_secret
        self._time_provider = time_provider

    @classmethod
    def logger(cls) -> HummingbotLogger:
        if cls._logger is None:
            cls._logger = logging.getLogger(HummingbotLogger.logger_name_for_class(cls))
        return cls._logger

    async def rest_authenticate(self, request: RESTRequest) -> RESTRequest:
        timestamp = str(int(self._time_provider.time()))
        payload_str = ""
        if request.method in {RESTMethod.POST, RESTMethod.PUT} and request.data is not None:
            payload_str = request.data if isinstance(request.data, str) else json.dumps(request.data)

        parsed_url = urlparse(request.url or "")
        request_path = parsed_url.path or ""
        if parsed_url.query:
            request_path = f"{request_path}?{parsed_url.query}"

        message = f"{timestamp}{request.method.value}{request_path}{payload_str}"
        signature = hmac.new(self._api_secret.encode("utf-8"), message.encode("utf-8"), digestmod="sha256").hexdigest()

        headers: Dict[str, Any] = dict(request.headers or {})
        headers.update({
            "CB-ACCESS-KEY": self._api_key,
            "CB-ACCESS-SIGN": signature,
            "CB-ACCESS-TIMESTAMP": timestamp,
            "User-Agent": constants.USER_AGENT,
        })
        request.headers = headers
        if payload_str and isinstance(request.data, dict):
            request.data = payload_str
        return request

    async def ws_authenticate(self, request: WSRequest) -> WSRequest:
        return request
