import asyncio
from typing import Optional

from hummingbot.connector.gateway.gateway_base import GatewayBase


class GatewayCtf(GatewayBase):
    async def split_position(self, conditionId: str, amount: int, negRisk: bool) -> str:
        gateway_instance = self._get_gateway_instance()

        try:
            tx = await gateway_instance.api_request(
                "post",
                f"/connectors/{self.connector_name}/split-position",
                {
                    "conditionId": conditionId,
                    "amount": amount,
                    "negRisk": negRisk
                }
            )

            signature: Optional[str] = tx.get("signature")
            if signature is not None and signature != "":
                return signature
            else:
                raise ValueError("No transaction hash returned from gateway")
        except asyncio.CancelledError:
            raise
        except Exception:
            raise
