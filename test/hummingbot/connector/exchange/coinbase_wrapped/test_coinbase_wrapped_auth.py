import hmac
import unittest
from test.isolated_asyncio_wrapper_test_case import IsolatedAsyncioWrapperTestCase
from unittest.mock import AsyncMock, MagicMock

from hummingbot.connector.exchange.coinbase_wrapped import coinbase_wrapped_constants as constants
from hummingbot.connector.exchange.coinbase_wrapped.coinbase_wrapped_auth import CoinbaseWrappedAuth
from hummingbot.core.web_assistant.connections.data_types import RESTMethod, RESTRequest


class CoinbaseWrappedAuthTests(IsolatedAsyncioWrapperTestCase):

    def setUp(self):
        self.api_key = "test-api-key"
        self.api_secret = "test-secret"
        self.time_synchronizer_mock = AsyncMock()
        self.time_synchronizer_mock.time = MagicMock(return_value=1234567890)
        self.auth = CoinbaseWrappedAuth(self.api_key, self.api_secret, self.time_synchronizer_mock)

    async def test_rest_authenticate_adds_expected_headers_and_signature(self):
        request = RESTRequest(
            method=RESTMethod.POST,
            url="https://api.coinbase.com/api/v3/exchange/assets/wrapped/pricing",
            data={"foo": "bar"},
            headers={},
            is_auth_required=True,
        )

        configured_request = await self.auth.rest_authenticate(request)

        expected_message = "1234567890POST/api/v3/exchange/assets/wrapped/pricing{\"foo\": \"bar\"}"
        expected_signature = hmac.new(
            self.api_secret.encode("utf-8"),
            expected_message.encode("utf-8"),
            digestmod="sha256",
        ).hexdigest()

        self.assertEqual(configured_request.headers["CB-ACCESS-KEY"], self.api_key)
        self.assertEqual(configured_request.headers["CB-ACCESS-SIGN"], expected_signature)
        self.assertEqual(configured_request.headers["CB-ACCESS-TIMESTAMP"], "1234567890")
        self.assertEqual(configured_request.headers["User-Agent"], constants.USER_AGENT)

    async def test_rest_authenticate_handles_query_params(self):
        request = RESTRequest(
            method=RESTMethod.GET,
            url="https://api.coinbase.com/api/v3/exchange/assets/wrapped/pricing?base=ETH&wrapped=cbETH",
            headers={},
            is_auth_required=True,
        )

        configured_request = await self.auth.rest_authenticate(request)

        expected_message = "1234567890GET/api/v3/exchange/assets/wrapped/pricing?base=ETH&wrapped=cbETH"
        expected_signature = hmac.new(
            self.api_secret.encode("utf-8"),
            expected_message.encode("utf-8"),
            digestmod="sha256",
        ).hexdigest()

        self.assertEqual(configured_request.headers["CB-ACCESS-SIGN"], expected_signature)


if __name__ == "__main__":
    unittest.main()
