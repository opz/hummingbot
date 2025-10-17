from typing import Optional

from hummingbot.connector.exchange.coinbase_wrapped import coinbase_wrapped_constants as constants
from hummingbot.connector.time_synchronizer import TimeSynchronizer
from hummingbot.core.api_throttler.async_throttler import AsyncThrottler
from hummingbot.core.web_assistant.auth import AuthBase
from hummingbot.core.web_assistant.web_assistants_factory import WebAssistantsFactory


def rest_url(path_url: str, domain: str = constants.DEFAULT_DOMAIN) -> str:
    if path_url.startswith("http"):
        return path_url
    if not path_url.startswith("/"):
        path_url = f"/{path_url}"
    return constants.REST_URL.format(domain=domain) + path_url


def build_api_factory(
    throttler: Optional[AsyncThrottler] = None,
    time_synchronizer: Optional[TimeSynchronizer] = None,
    domain: str = constants.DEFAULT_DOMAIN,
    auth: Optional[AuthBase] = None,
) -> WebAssistantsFactory:
    throttler = throttler or AsyncThrottler(constants.RATE_LIMITS)
    time_synchronizer = time_synchronizer or TimeSynchronizer()
    return WebAssistantsFactory(
        throttler=throttler,
        auth=auth,
    )
