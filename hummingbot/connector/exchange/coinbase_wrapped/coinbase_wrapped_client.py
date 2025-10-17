import asyncio
import logging
from typing import Any, Dict, Optional

from hummingbot.connector.exchange.coinbase_wrapped import coinbase_wrapped_constants as constants
from hummingbot.connector.exchange.coinbase_wrapped.coinbase_wrapped_auth import CoinbaseWrappedAuth
from hummingbot.connector.exchange.coinbase_wrapped.coinbase_wrapped_web_utils import build_api_factory, rest_url
from hummingbot.connector.time_synchronizer import TimeSynchronizer
from hummingbot.core.api_throttler.async_throttler import AsyncThrottler
from hummingbot.core.utils.async_retry import async_retry
from hummingbot.core.web_assistant.connections.data_types import RESTMethod

logger = logging.getLogger(__name__)


class CoinbaseWrappedClient:
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        domain: str = constants.DEFAULT_DOMAIN,
        throttler: Optional[AsyncThrottler] = None,
    ):
        self._domain = domain
        self._time_synchronizer = TimeSynchronizer()
        self._auth = CoinbaseWrappedAuth(api_key, api_secret, self._time_synchronizer)
        self._throttler = throttler or AsyncThrottler(constants.RATE_LIMITS)
        self._api_factory = build_api_factory(
            throttler=self._throttler,
            time_synchronizer=self._time_synchronizer,
            domain=domain,
            auth=self._auth,
        )

    @property
    def domain(self) -> str:
        return self._domain

    @async_retry(retry_count=3, retry_interval=2.0, exception_types=[IOError])
    async def _rest_call(
        self,
        endpoint: str,
        method: RESTMethod = RESTMethod.GET,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        is_auth_required: bool = True,
    ) -> Dict[str, Any]:
        rest_assistant = await self._api_factory.get_rest_assistant()
        url = rest_url(endpoint, domain=self._domain)
        headers = {"User-Agent": constants.USER_AGENT}
        response = await rest_assistant.execute_request_and_get_response(
            url=url,
            throttler_limit_id=constants.RATE_LIMIT_ID,
            params=params,
            data=data,
            method=method,
            is_auth_required=is_auth_required,
            headers=headers,
            return_err=True,
        )

        status = response.status
        try:
            payload = await response.json()
        except Exception:
            payload = {"text": await response.text()}

        if status == 429 or status >= 500:
            logger.warning("Coinbase Wrapped API throttled or errored with status %s. Retrying...", status)
            raise IOError(f"Retryable HTTP error {status}: {payload}")

        if status >= 400:
            raise IOError(f"HTTP error {status}: {payload}")

        if isinstance(payload, dict):
            return payload

        return {"data": payload}

    async def get_conversion_rate(self, base_asset: str, wrapped_asset: str) -> Optional[float]:
        params = {"base_asset": base_asset, "wrapped_asset": wrapped_asset}
        result = await self._rest_call(constants.CONVERSION_RATE_EP, params=params, is_auth_required=True)
        pricing = result.get("pricing", [])
        for entry in pricing:
            if entry.get("base_asset") == base_asset and entry.get("wrapped_asset") == wrapped_asset:
                return float(entry.get("rate"))
        return None

    async def stake_wrap(
        self,
        base_asset: str,
        wrapped_asset: str,
        amount: str,
        wait: bool = True,
    ) -> Dict[str, Any]:
        payload = {
            "base_asset": base_asset,
            "wrapped_asset": wrapped_asset,
            "amount": amount,
        }
        response = await self._rest_call(
            constants.STAKE_WRAP_EP,
            method=RESTMethod.POST,
            data=payload,
            is_auth_required=True,
        )
        conversion_id = response.get("conversion_id")
        if wait and conversion_id is not None:
            final_status = await self._wait_for_completion(conversion_id)
            response["final_status"] = final_status
        return response

    async def get_stake_wrap_status(self, conversion_id: str) -> Dict[str, Any]:
        endpoint = constants.STAKE_STATUS_EP.format(conversion_id=conversion_id)
        return await self._rest_call(endpoint, is_auth_required=True)

    async def _wait_for_completion(self, conversion_id: str, poll_interval: float = 2.0, timeout: float = 60.0):
        start = asyncio.get_event_loop().time()
        while True:
            status = await self.get_stake_wrap_status(conversion_id)
            state = status.get("status")
            if state in {"completed", "failed", "cancelled"}:
                return status
            if asyncio.get_event_loop().time() - start > timeout:
                raise asyncio.TimeoutError(f"Conversion {conversion_id} did not complete within timeout")
            await asyncio.sleep(poll_interval)
