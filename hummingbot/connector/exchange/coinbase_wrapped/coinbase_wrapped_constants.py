from dataclasses import dataclass

from hummingbot.core.api_throttler.data_types import RateLimit


EXCHANGE_NAME = "Coinbase Wrapped"

DEFAULT_DOMAIN = "com"

HBOT_ORDER_ID_PREFIX = "CBWRP-"
MAX_ORDER_ID_LEN = 32

HBOT_BROKER_ID = "Hummingbot"

BASE_URL = "https://api.coinbase.{domain}"
REST_URL = "https://api.coinbase.{domain}/api/v3"

USER_AGENT = "hummingbot-coinbase-wrapped/0.1.0"

# Coinbase Wrapped endpoints
# Reference: https://docs.cdp.coinbase.com/exchange/reference/exchangerestapi_getassetswrappedpricing
CONVERSION_RATE_EP = "/exchange/assets/wrapped/pricing"
STAKE_WRAP_EP = "/brokerage/wrapped-assets/convert"
STAKE_STATUS_EP = "/brokerage/wrapped-assets/conversions/{conversion_id}"

# Basic rate limit (~1 rps)
RATE_LIMIT_ID = "coinbase_wrapped_rest"
RATE_LIMITS = [RateLimit(limit_id=RATE_LIMIT_ID, limit=1, time_interval=1)]
