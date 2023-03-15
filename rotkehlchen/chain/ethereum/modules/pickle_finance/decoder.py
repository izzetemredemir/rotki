from typing import TYPE_CHECKING, Callable

from rotkehlchen.accounting.structures.types import HistoryEventSubType, HistoryEventType
from rotkehlchen.assets.asset import EvmToken
from rotkehlchen.chain.ethereum.utils import asset_normalized_value
from rotkehlchen.chain.evm.constants import ZERO_ADDRESS
from rotkehlchen.chain.evm.decoding.interfaces import DecoderInterface
from rotkehlchen.chain.evm.decoding.structures import ActionItem
from rotkehlchen.chain.evm.structures import EvmTxReceiptLog
from rotkehlchen.constants.resolver import ethaddress_to_identifier
from rotkehlchen.globaldb.handler import GlobalDBHandler
from rotkehlchen.types import PICKLE_JAR_PROTOCOL, EvmTransaction
from rotkehlchen.utils.misc import hex_or_bytes_to_address, hex_or_bytes_to_int

from .constants import CPT_PICKLE

if TYPE_CHECKING:
    from rotkehlchen.accounting.structures.evm_event import EvmEvent
    from rotkehlchen.chain.ethereum.node_inquirer import EthereumInquirer
    from rotkehlchen.chain.evm.decoding.base import BaseDecoderTools
    from rotkehlchen.user_messages import MessagesAggregator


class PickleFinanceDecoder(DecoderInterface):

    def __init__(
            self,
            ethereum_inquirer: 'EthereumInquirer',
            base_tools: 'BaseDecoderTools',
            msg_aggregator: 'MessagesAggregator',
    ) -> None:
        super().__init__(
            evm_inquirer=ethereum_inquirer,
            base_tools=base_tools,
            msg_aggregator=msg_aggregator,
        )
        jars = GlobalDBHandler().get_evm_tokens(
            chain_id=ethereum_inquirer.chain_id,
            protocol=PICKLE_JAR_PROTOCOL,
        )
        self.pickle_contracts = {jar.evm_address for jar in jars}

    def _maybe_enrich_pickle_transfers(
            self,
            token: EvmToken,  # pylint: disable=unused-argument
            tx_log: EvmTxReceiptLog,
            transaction: EvmTransaction,
            event: 'EvmEvent',
            action_items: list[ActionItem],  # pylint: disable=unused-argument
            all_logs: list[EvmTxReceiptLog],  # pylint: disable=unused-argument
    ) -> bool:
        """
        Enrich tranfer transactions to address for jar deposits and withdrawals
        May raise:
        - UnknownAsset
        - WrongAssetType
        """
        crypto_asset = event.asset.resolve_to_crypto_asset()
        if not (
            hex_or_bytes_to_address(tx_log.topics[2]) in self.pickle_contracts or
            hex_or_bytes_to_address(tx_log.topics[1]) in self.pickle_contracts or
            tx_log.address in self.pickle_contracts
        ):
            return False

        if (  # Deposit give asset
            event.event_type == HistoryEventType.SPEND and
            event.event_subtype == HistoryEventSubType.NONE and
            event.location_label == transaction.from_address and
            hex_or_bytes_to_address(tx_log.topics[2]) in self.pickle_contracts
        ):
            if EvmToken(ethaddress_to_identifier(tx_log.address)) != event.asset:
                return True
            amount_raw = hex_or_bytes_to_int(tx_log.data)
            amount = asset_normalized_value(
                amount=amount_raw,
                asset=event.asset.resolve_to_crypto_asset(),
            )
            if event.balance.amount == amount:
                event.event_type = HistoryEventType.DEPOSIT
                event.event_subtype = HistoryEventSubType.DEPOSIT_ASSET
                event.counterparty = CPT_PICKLE
                event.notes = f'Deposit {event.balance.amount} {crypto_asset.symbol} in pickle contract'  # noqa: E501
        elif (  # Deposit receive wrapped
            event.event_type == HistoryEventType.RECEIVE and
            event.event_subtype == HistoryEventSubType.NONE and
            tx_log.address in self.pickle_contracts
        ):
            amount_raw = hex_or_bytes_to_int(tx_log.data)
            amount = asset_normalized_value(
                amount=amount_raw,
                asset=event.asset.resolve_to_crypto_asset(),
            )
            if event.balance.amount == amount:
                event.event_type = HistoryEventType.RECEIVE
                event.event_subtype = HistoryEventSubType.RECEIVE_WRAPPED
                event.counterparty = CPT_PICKLE
                event.notes = f'Receive {event.balance.amount} {crypto_asset.symbol} after depositing in pickle contract'  # noqa: E501
        elif (  # Withdraw send wrapped
            event.event_type == HistoryEventType.SPEND and
            event.event_subtype == HistoryEventSubType.NONE and
            event.location_label == transaction.from_address and
            hex_or_bytes_to_address(tx_log.topics[2]) == ZERO_ADDRESS and
            hex_or_bytes_to_address(tx_log.topics[1]) in transaction.from_address
        ):
            if event.asset != EvmToken(ethaddress_to_identifier(tx_log.address)):
                return True
            amount_raw = hex_or_bytes_to_int(tx_log.data)
            amount = asset_normalized_value(
                amount=amount_raw,
                asset=event.asset.resolve_to_crypto_asset(),
            )
            if event.balance.amount == amount:
                event.event_type = HistoryEventType.SPEND
                event.event_subtype = HistoryEventSubType.RETURN_WRAPPED
                event.counterparty = CPT_PICKLE
                event.notes = f'Return {event.balance.amount} {crypto_asset.symbol} to the pickle contract'  # noqa: E501
        elif (  # Withdraw receive asset
            event.event_type == HistoryEventType.RECEIVE and
            event.event_subtype == HistoryEventSubType.NONE and
            event.location_label == transaction.from_address and
            hex_or_bytes_to_address(tx_log.topics[2]) == transaction.from_address and
            hex_or_bytes_to_address(tx_log.topics[1]) in self.pickle_contracts
        ):
            if event.asset != EvmToken(ethaddress_to_identifier(tx_log.address)):
                return True
            amount_raw = hex_or_bytes_to_int(tx_log.data)
            amount = asset_normalized_value(
                amount=amount_raw,
                asset=event.asset.resolve_to_crypto_asset(),
            )
            if event.balance.amount == amount:
                event.event_type = HistoryEventType.WITHDRAWAL
                event.event_subtype = HistoryEventSubType.REMOVE_ASSET
                event.counterparty = CPT_PICKLE
                event.notes = f'Unstake {event.balance.amount} {crypto_asset.symbol} from the pickle contract'  # noqa: E501

        return True

    # -- DecoderInterface methods

    def enricher_rules(self) -> list[Callable]:
        return [
            self._maybe_enrich_pickle_transfers,
        ]

    def counterparties(self) -> list[str]:
        return [CPT_PICKLE]
