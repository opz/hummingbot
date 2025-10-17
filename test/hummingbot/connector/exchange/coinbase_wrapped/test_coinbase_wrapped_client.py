import asyncio
import unittest
from test.isolated_asyncio_wrapper_test_case import IsolatedAsyncioWrapperTestCase
from unittest.mock import AsyncMock, patch

from hummingbot.connector.exchange.coinbase_wrapped.coinbase_wrapped_client import CoinbaseWrappedClient


class CoinbaseWrappedClientTests(IsolatedAsyncioWrapperTestCase):

    def setUp(self) -> None:
        self.api_key = "test_api_key"
        self.api_secret = "test_api_secret"
        self.client = CoinbaseWrappedClient(self.api_key, self.api_secret)

    @patch("hummingbot.connector.exchange.coinbase_wrapped.coinbase_wrapped_client.rest_url", return_value="https://api.test")
    async def test_get_conversion_rate(self, mock_rest_url):
        mock_rest_assistant = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "pricing": [
                {"base_asset": "ETH", "wrapped_asset": "cbETH", "rate": "0.985"}
            ]
        })
        mock_response.text = AsyncMock(return_value="")
        mock_rest_assistant.execute_request_and_get_response.return_value = mock_response

        self.client._api_factory.get_rest_assistant = AsyncMock(return_value=mock_rest_assistant)

        rate = await self.client.get_conversion_rate("ETH", "cbETH")

        self.assertEqual(rate, 0.985)

    @patch("hummingbot.connector.exchange.coinbase_wrapped.coinbase_wrapped_client.rest_url", return_value="https://api.test")
    async def test_stake_wrap_returns_response(self, mock_rest_url):
        conversion_id = "conv-123"
        mock_rest_assistant = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "conversion_id": conversion_id
        })
        mock_response.text = AsyncMock(return_value="")
        mock_rest_assistant.execute_request_and_get_response.return_value = mock_response

        self.client._api_factory.get_rest_assistant = AsyncMock(return_value=mock_rest_assistant)
        self.client._wait_for_completion = AsyncMock(return_value={"status": "completed"})

        response = await self.client.stake_wrap("ETH", "cbETH", "1", wait=True)

        self.assertEqual(response["conversion_id"], conversion_id)
        self.assertEqual(response["final_status"], {"status": "completed"})

    @patch("hummingbot.connector.exchange.coinbase_wrapped.coinbase_wrapped_client.rest_url", return_value="https://api.test")
    async def test_get_stake_wrap_status(self, mock_rest_url):
        mock_rest_assistant = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "status": "pending"
        })
        mock_response.text = AsyncMock(return_value="")
        mock_rest_assistant.execute_request_and_get_response.return_value = mock_response

        self.client._api_factory.get_rest_assistant = AsyncMock(return_value=mock_rest_assistant)

        status = await self.client.get_stake_wrap_status("conv-123")

        self.assertEqual(status["status"], "pending")

    async def test_wait_for_completion_times_out(self):
        self.client.get_stake_wrap_status = AsyncMock(return_value={"status": "pending"})
        with self.assertRaises(asyncio.TimeoutError):
            await self.client._wait_for_completion("conv-123", poll_interval=0, timeout=0.01)

    @patch("hummingbot.connector.exchange.coinbase_wrapped.coinbase_wrapped_client.rest_url", return_value="https://api.test")
    async def test_rest_call_retries_on_server_error(self, mock_rest_url):
        mock_rest_assistant = AsyncMock()
        error_response = AsyncMock()
        error_response.status = 500
        error_response.json = AsyncMock(return_value={"error": "server error"})
        error_response.text = AsyncMock(return_value="server error")
        success_response = AsyncMock()
        success_response.status = 200
        success_response.json = AsyncMock(return_value={"pricing": []})
        success_response.text = AsyncMock(return_value="")
        mock_rest_assistant.execute_request_and_get_response.side_effect = [error_response, success_response]

        self.client._api_factory.get_rest_assistant = AsyncMock(return_value=mock_rest_assistant)

        response = await self.client._rest_call("/endpoint")

        self.assertEqual(response, {"pricing": []})
        self.assertEqual(mock_rest_assistant.execute_request_and_get_response.call_count, 2)

    async def test_rest_call_raises_on_non_retryable_error(self):
        mock_rest_assistant = AsyncMock()
        error_response = AsyncMock()
        error_response.status = 400
        error_response.json = AsyncMock(return_value={"error": "bad request"})
        error_response.text = AsyncMock(return_value="bad request")
        mock_rest_assistant.execute_request_and_get_response.return_value = error_response

        self.client._api_factory.get_rest_assistant = AsyncMock(return_value=mock_rest_assistant)

        with self.assertRaises(IOError):
            await self.client._rest_call("/endpoint")

    async def test_rest_call_handles_non_dict_payload(self):
        mock_rest_assistant = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(side_effect=ValueError("not json"))
        mock_response.text = AsyncMock(return_value="raw text")
        mock_rest_assistant.execute_request_and_get_response.return_value = mock_response

        self.client._api_factory.get_rest_assistant = AsyncMock(return_value=mock_rest_assistant)

        response = await self.client._rest_call("/endpoint")

        self.assertEqual(response, {"data": "raw text"})

    async def test_get_conversion_rate_when_not_found(self):
        mock_rest_assistant = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"pricing": []})
        mock_response.text = AsyncMock(return_value="")
        mock_rest_assistant.execute_request_and_get_response.return_value = mock_response

        self.client._api_factory.get_rest_assistant = AsyncMock(return_value=mock_rest_assistant)

        rate = await self.client.get_conversion_rate("ETH", "cbETH")

        self.assertIsNone(rate)


if __name__ == "__main__":
    unittest.main()
