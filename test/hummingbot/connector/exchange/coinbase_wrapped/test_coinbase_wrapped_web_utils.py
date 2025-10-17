import unittest
from test.isolated_asyncio_wrapper_test_case import IsolatedAsyncioWrapperTestCase
from unittest.mock import patch

from hummingbot.connector.exchange.coinbase_wrapped import coinbase_wrapped_constants as constants
from hummingbot.connector.exchange.coinbase_wrapped.coinbase_wrapped_web_utils import build_api_factory, rest_url
from hummingbot.core.api_throttler.async_throttler import AsyncThrottler
from hummingbot.core.web_assistant.web_assistants_factory import WebAssistantsFactory


class CoinbaseWrappedWebUtilsTests(IsolatedAsyncioWrapperTestCase):

    def test_rest_url_with_relative_path(self):
        result = rest_url("/exchange/assets/wrapped/pricing")
        expected = constants.REST_URL.format(domain=constants.DEFAULT_DOMAIN) + "/exchange/assets/wrapped/pricing"
        self.assertEqual(result, expected)

    def test_rest_url_with_absolute_url(self):
        url = "https://api.coinbase.com/api/v3/custom"
        result = rest_url(url)
        self.assertEqual(result, url)

    @patch("hummingbot.connector.exchange.coinbase_wrapped.coinbase_wrapped_web_utils.TimeSynchronizer")
    @patch("hummingbot.connector.exchange.coinbase_wrapped.coinbase_wrapped_web_utils.AsyncThrottler", autospec=True)
    @patch.object(WebAssistantsFactory, "__init__", return_value=None)
    def test_build_api_factory_defaults(self, mock_factory_init, mock_throttler, mock_time_sync):
        throttler_instance = mock_throttler.return_value

        factory = build_api_factory()

        mock_throttler.assert_called_once_with(constants.RATE_LIMITS)
        mock_time_sync.assert_called_once()
        mock_factory_init.assert_called_once_with(throttler=throttler_instance, auth=None)
        self.assertIsInstance(factory, WebAssistantsFactory)

    def test_build_api_factory_with_provided_instances(self):
        throttler = AsyncThrottler(constants.RATE_LIMITS)
        factory = build_api_factory(throttler=throttler)
        self.assertIsInstance(factory, WebAssistantsFactory)
        self.assertIs(factory.throttler, throttler)


if __name__ == "__main__":
    unittest.main()
