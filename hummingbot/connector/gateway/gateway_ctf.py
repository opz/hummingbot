import asyncio
from decimal import Decimal
from typing import Optional

from hummingbot.connector.gateway.gateway_base import GatewayBase
from hummingbot.core.data_type.common import TradeType


class GatewayCtf(GatewayBase):
    def get_order_size_quantum(self, trading_pair: str, order_size: Decimal) -> Decimal:
        """Override, always 6 decimals for Polymarket"""
        return Decimal("1e-6")

    async def split_position(self, conditionId: str, trading_pairs: list[str], amount: int, negRisk: bool) -> str:
        gateway_instance = self._get_gateway_instance()

        order_ids = {}
        for trading_pair in trading_pairs:
            order_id = self.create_market_order_id(TradeType.BUY, trading_pair)
            order_ids[trading_pair] = order_id

        try:
            tx = await gateway_instance.api_request(
                "post",
                f"connectors/{self.connector_name}/split-position",
                {
                    "walletAddress": self.address,
                    "conditionId": conditionId,
                    "amount": amount,
                    "negRisk": negRisk
                }
            )

            signature: Optional[str] = tx.get("signature")
            if signature is not None and signature != "":
                # Only start tracking orders after we successfully get a transaction hash
                order_amount = amount * Decimal("1e-6")
                for trading_pair in trading_pairs:
                    quantized_amount = self.quantize_order_amount(trading_pair, order_amount)
                    # Don't track til there is a signature to avoid SQL error from missing exchange_order_id
                    self.start_tracking_order(
                        order_id=order_ids[trading_pair],
                        exchange_order_id=signature,
                        trading_pair=trading_pair,
                        trade_type=TradeType.BUY,
                        price=Decimal("0.5"),
                        amount=quantized_amount
                    )

                    self.update_order_from_hash(order_ids[trading_pair], trading_pair, signature, tx)

                return signature
            else:
                raise ValueError("No transaction hash returned from gateway")
        except asyncio.CancelledError:
            raise
        except Exception as e:
            # Handle failure for all orders that were created
            for trading_pair in trading_pairs:
                self._handle_operation_failure(order_ids[trading_pair], trading_pair, "submitting split position", e)
