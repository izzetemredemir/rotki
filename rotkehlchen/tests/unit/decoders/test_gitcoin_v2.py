import pytest

from rotkehlchen.accounting.structures.balance import Balance
from rotkehlchen.assets.asset import Asset
from rotkehlchen.chain.evm.decoding.constants import CPT_GAS, CPT_GITCOIN
from rotkehlchen.constants.assets import A_ARB, A_DAI, A_ETH, A_POLYGON_POS_MATIC
from rotkehlchen.fval import FVal
from rotkehlchen.history.events.structures.evm_event import EvmEvent
from rotkehlchen.history.events.structures.types import HistoryEventSubType, HistoryEventType
from rotkehlchen.tests.utils.ethereum import get_decoded_events_of_transaction
from rotkehlchen.types import Location, TimestampMS, deserialize_evm_tx_hash


@pytest.mark.vcr(filter_query_parameters=['apikey'])
@pytest.mark.parametrize('optimism_accounts', [['0x9531C059098e3d194fF87FebB587aB07B30B1306']])
def test_optimism_donation_received(optimism_inquirer, optimism_accounts):
    tx_hash = deserialize_evm_tx_hash('0x08685669305ee26060a5a78ae70065aec76d9e62a35f0837c291fb1232f33601')  # noqa: E501
    events, _ = get_decoded_events_of_transaction(
        evm_inquirer=optimism_inquirer,
        tx_hash=tx_hash,
    )
    user_address, timestamp, amount_str = optimism_accounts[0], TimestampMS(1692176477000), '0.00122'  # noqa: E501
    expected_events = [EvmEvent(
        tx_hash=tx_hash,
        sequence_index=0,
        timestamp=timestamp,
        location=Location.OPTIMISM,
        event_type=HistoryEventType.RECEIVE,
        event_subtype=HistoryEventSubType.DONATE,
        asset=A_ETH,
        balance=Balance(amount=FVal(amount_str)),
        location_label=user_address,
        notes=f'Receive a gitcoin donation of {amount_str} ETH from 0xf0C2007aD05a8d66e98be932C698c232292eC8eA',  # noqa: E501
        counterparty=CPT_GITCOIN,
        address='0x99906Ea77C139000681254966b397a98E4bFdE21',
    )]
    assert events == expected_events


@pytest.mark.vcr(filter_query_parameters=['apikey'])
@pytest.mark.parametrize('ethereum_accounts', [['0x9531C059098e3d194fF87FebB587aB07B30B1306']])
def test_ethereum_donation_received(ethereum_inquirer, ethereum_accounts):
    tx_hash = deserialize_evm_tx_hash('0x71fc406467f342f5801560a326aa29ac424381daf17cc04b5573960425ba605b')  # noqa: E501
    events, _ = get_decoded_events_of_transaction(evm_inquirer=ethereum_inquirer, tx_hash=tx_hash)
    amount_str = '0.001'
    expected_events = [EvmEvent(
        tx_hash=tx_hash,
        sequence_index=0,
        timestamp=TimestampMS(1683655379000),
        location=Location.ETHEREUM,
        event_type=HistoryEventType.RECEIVE,
        event_subtype=HistoryEventSubType.DONATE,
        asset=A_ETH,
        balance=Balance(amount=FVal(amount_str)),
        location_label=ethereum_accounts[0],
        notes=f'Receive a gitcoin donation of {amount_str} ETH from 0xc191a29203a83eec8e846c26340f828C68835715',  # noqa: E501
        counterparty=CPT_GITCOIN,
        address='0xDA2F26B30e8f5aa9cbE9c5B7Ed58E1cA81D0EbF2',
    )]
    assert events == expected_events


@pytest.mark.vcr(filter_query_parameters=['apikey'])
@pytest.mark.parametrize('ethereum_accounts', [[
    '0x1B274eaCc333F4a904D72b576B55A108532aB379',
    # also track a grantee to see we handle donating to self fine
    '0xB352bB4E2A4f27683435f153A259f1B207218b1b',
]])
def test_ethereum_make_donation(ethereum_inquirer, ethereum_accounts):
    tx_hash = deserialize_evm_tx_hash('0xd8d55b66f19a6dbf260d171fbb0c4c146f00c90919f1215cf691d7f0684771c6')  # noqa: E501
    events, _ = get_decoded_events_of_transaction(evm_inquirer=ethereum_inquirer, tx_hash=tx_hash)
    user_address, tracked_grant, timestamp, amount_str, gas_str = ethereum_accounts[0], ethereum_accounts[1], TimestampMS(1683676595000), '0.0006', '0.011086829409239852'  # noqa: E501
    expected_events = [EvmEvent(
        tx_hash=tx_hash,
        sequence_index=0,
        timestamp=timestamp,
        location=Location.ETHEREUM,
        event_type=HistoryEventType.SPEND,
        event_subtype=HistoryEventSubType.FEE,
        asset=A_ETH,
        balance=Balance(amount=FVal(gas_str)),
        location_label=user_address,
        notes=f'Burn {gas_str} ETH for gas',
        counterparty=CPT_GAS,
    ), EvmEvent(
        tx_hash=tx_hash,
        sequence_index=1,
        timestamp=timestamp,
        location=Location.ETHEREUM,
        event_type=HistoryEventType.TRANSFER,
        event_subtype=HistoryEventSubType.DONATE,
        asset=A_ETH,
        balance=Balance(amount=FVal(amount_str)),
        location_label=user_address,
        notes=f'Transfer a gitcoin donation of {amount_str} ETH to {tracked_grant}',
        counterparty=CPT_GITCOIN,
        address=tracked_grant,
    )]

    expected_events += [EvmEvent(
        tx_hash=tx_hash,
        sequence_index=idx,
        timestamp=timestamp,
        location=Location.ETHEREUM,
        event_type=HistoryEventType.SPEND,
        event_subtype=HistoryEventSubType.DONATE,
        asset=A_ETH,
        balance=Balance(amount=FVal(amount_str)),
        location_label=user_address,
        notes=f'Make a gitcoin donation of {amount_str} ETH to {grant_address}',
        counterparty=CPT_GITCOIN,
        address=grant_address,
    ) for idx, grant_address in [
        (2, '0x713Bc00D1df5C452F172C317D39eFf71B771C163'),
        (107, '0xDEcf6615152AC768BFB688c4eF882e35DeBE08ac'),
        (109, '0x187089b65520D2208aB93FB471C4970c29eAf929'),
        (111, '0xb7081Fd06E7039D198D10A8b72B824e60C1B1E16'),
    ]]
    assert events == expected_events


@pytest.mark.vcr(filter_query_parameters=['apikey'])
@pytest.mark.parametrize('optimism_accounts', [['0x9531C059098e3d194fF87FebB587aB07B30B1306']])
def test_optimism_create_project(optimism_inquirer, optimism_accounts):
    tx_hash = deserialize_evm_tx_hash('0xe59f04c693e91f1659bd8bc718c993158efeb9af02c9c6337f039c44d8a822f6')  # noqa: E501
    events, _ = get_decoded_events_of_transaction(evm_inquirer=optimism_inquirer, tx_hash=tx_hash)
    user_address, timestamp, gas_str = optimism_accounts[0], TimestampMS(1691697693000), '0.000085459641651569'  # noqa: E501
    expected_events = [EvmEvent(
        tx_hash=tx_hash,
        sequence_index=0,
        timestamp=timestamp,
        location=Location.OPTIMISM,
        event_type=HistoryEventType.SPEND,
        event_subtype=HistoryEventSubType.FEE,
        asset=A_ETH,
        balance=Balance(amount=FVal(gas_str)),
        location_label=user_address,
        notes=f'Burn {gas_str} ETH for gas',
        counterparty=CPT_GAS,
    ), EvmEvent(
        tx_hash=tx_hash,
        sequence_index=65,
        timestamp=timestamp,
        location=Location.OPTIMISM,
        event_type=HistoryEventType.INFORMATIONAL,
        event_subtype=HistoryEventSubType.CREATE,
        asset=A_ETH,
        balance=Balance(),
        location_label=user_address,
        notes=f'Create gitcoin project with id 779 and owner {user_address}',
        counterparty=CPT_GITCOIN,
        address='0x8e1bD5Da87C14dd8e08F7ecc2aBf9D1d558ea174',
    ), EvmEvent(
        tx_hash=tx_hash,
        sequence_index=66,
        timestamp=timestamp,
        location=Location.OPTIMISM,
        event_type=HistoryEventType.INFORMATIONAL,
        event_subtype=HistoryEventSubType.UPDATE,
        asset=A_ETH,
        balance=Balance(),
        location_label=user_address,
        notes='Update gitcoin project with id 779',
        counterparty=CPT_GITCOIN,
        address='0x8e1bD5Da87C14dd8e08F7ecc2aBf9D1d558ea174',
    )]
    assert events == expected_events


@pytest.mark.vcr(filter_query_parameters=['apikey'])
@pytest.mark.parametrize('ethereum_accounts', [['0x9531C059098e3d194fF87FebB587aB07B30B1306']])
def test_ethereum_project_apply(ethereum_inquirer, ethereum_accounts):
    tx_hash = deserialize_evm_tx_hash('0x3e4639d97be450c6d32ce77a146898780b75781caaf004d3c40bae083dec07c7')  # noqa: E501
    events, _ = get_decoded_events_of_transaction(evm_inquirer=ethereum_inquirer, tx_hash=tx_hash)
    user_address, timestamp, gas_str = ethereum_accounts[0], TimestampMS(1673472803000), '0.000645250895735256'  # noqa: E501
    expected_events = [EvmEvent(
        tx_hash=tx_hash,
        sequence_index=0,
        timestamp=timestamp,
        location=Location.ETHEREUM,
        event_type=HistoryEventType.SPEND,
        event_subtype=HistoryEventSubType.FEE,
        asset=A_ETH,
        balance=Balance(amount=FVal(gas_str)),
        location_label=user_address,
        notes=f'Burn {gas_str} ETH for gas',
        counterparty=CPT_GAS,
    ), EvmEvent(
        tx_hash=tx_hash,
        sequence_index=413,
        timestamp=timestamp,
        location=Location.ETHEREUM,
        event_type=HistoryEventType.INFORMATIONAL,
        event_subtype=HistoryEventSubType.APPLY,
        asset=A_ETH,
        balance=Balance(),
        location_label=user_address,
        notes='Apply to gitcoin round with project application id 0x755e5c4d042c1245555075b699e774c2ed0f0f1499460201fc936a0595e91683',  # noqa: E501
        counterparty=CPT_GITCOIN,
        address='0xe575282b376E3c9886779A841A2510F1Dd8C2CE4',
    )]
    assert events == expected_events


@pytest.mark.vcr(filter_query_parameters=['apikey'])
@pytest.mark.parametrize('ethereum_accounts', [['0x9531C059098e3d194fF87FebB587aB07B30B1306']])
def test_ethereum_project_update(ethereum_inquirer, ethereum_accounts):
    tx_hash = deserialize_evm_tx_hash('0xfe00fa198eb5395e1d809e017c6b416e882b0aef16e82bf00cd60ce5576bb122')  # noqa: E501
    events, _ = get_decoded_events_of_transaction(evm_inquirer=ethereum_inquirer, tx_hash=tx_hash)
    user_address, timestamp, gas_str = ethereum_accounts[0], TimestampMS(1681330523000), '0.001464795019471285'  # noqa: E501
    expected_events = [EvmEvent(
        tx_hash=tx_hash,
        sequence_index=0,
        timestamp=timestamp,
        location=Location.ETHEREUM,
        event_type=HistoryEventType.SPEND,
        event_subtype=HistoryEventSubType.FEE,
        asset=A_ETH,
        balance=Balance(amount=FVal(gas_str)),
        location_label=user_address,
        notes=f'Burn {gas_str} ETH for gas',
        counterparty=CPT_GAS,
    ), EvmEvent(
        tx_hash=tx_hash,
        sequence_index=192,
        timestamp=timestamp,
        location=Location.ETHEREUM,
        event_type=HistoryEventType.INFORMATIONAL,
        event_subtype=HistoryEventSubType.UPDATE,
        asset=A_ETH,
        balance=Balance(),
        location_label=user_address,
        notes='Update gitcoin project with id 128',
        counterparty=CPT_GITCOIN,
        address='0x03506eD3f57892C85DB20C36846e9c808aFe9ef4',
    )]
    assert events == expected_events


@pytest.mark.vcr(filter_query_parameters=['apikey'])
@pytest.mark.parametrize('optimism_accounts', [['0xd034Fd34eaEe5eC2c413C51936109E12873f4DA5']])
def test_optimism_many_donations_different_strategies(optimism_inquirer, optimism_accounts):
    tx_hash = deserialize_evm_tx_hash('0x5d85b436f5f177de6019baa9ecebae285e0def4924546307fac40556bece4cd7')  # noqa: E501
    events, _ = get_decoded_events_of_transaction(evm_inquirer=optimism_inquirer, tx_hash=tx_hash)
    user_address, timestamp, gas_str = optimism_accounts[0], TimestampMS(1692300843000), '0.004506208027331091'  # noqa: E501
    op_dai = Asset('eip155:10/erc20:0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1')
    assert events[0:2] == [EvmEvent(
        tx_hash=tx_hash,
        sequence_index=0,
        timestamp=timestamp,
        location=Location.OPTIMISM,
        event_type=HistoryEventType.SPEND,
        event_subtype=HistoryEventSubType.FEE,
        asset=A_ETH,
        balance=Balance(amount=FVal(gas_str)),
        location_label=user_address,
        notes=f'Burn {gas_str} ETH for gas',
        counterparty=CPT_GAS,
    ), EvmEvent(
        tx_hash=tx_hash,
        sequence_index=50,
        timestamp=timestamp,
        location=Location.OPTIMISM,
        event_type=HistoryEventType.INFORMATIONAL,
        event_subtype=HistoryEventSubType.APPROVE,
        asset=op_dai,
        balance=Balance(FVal('147.7')),
        location_label=user_address,
        notes=f'Set DAI spending approval of {user_address} by 0x15fa08599EB017F89c1712d0Fe76138899FdB9db to 147.7',  # noqa: E501
        address='0x15fa08599EB017F89c1712d0Fe76138899FdB9db',
    )]

    assert len(events) == 121  # 119 donations plus the 2 events above
    for event in events[2:]:
        assert event.location == Location.OPTIMISM
        assert event.event_type == HistoryEventType.SPEND
        assert event.event_subtype == HistoryEventSubType.DONATE
        assert event.asset == op_dai
        assert FVal(1) <= event.balance.amount <= FVal(5)
        assert event.location_label == user_address
        assert event.notes.startswith('Make a gitcoin donation')
        assert event.counterparty == CPT_GITCOIN


@pytest.mark.vcr(filter_query_parameters=['apikey'])
@pytest.mark.parametrize('optimism_accounts', [['0x9531C059098e3d194fF87FebB587aB07B30B1306']])
def test_optimism_grant_payout(optimism_inquirer, optimism_accounts):
    tx_hash = deserialize_evm_tx_hash('0x84110136c94ceb71c72afb27ccb517eb33f77a8a419d125101644e2c43294815')  # noqa: E501
    events, _ = get_decoded_events_of_transaction(evm_inquirer=optimism_inquirer, tx_hash=tx_hash)
    amount_str = '1228.529999999999934464'
    expected_events = [EvmEvent(
        tx_hash=tx_hash,
        sequence_index=73,
        timestamp=TimestampMS(1696942367000),
        location=Location.OPTIMISM,
        event_type=HistoryEventType.RECEIVE,
        event_subtype=HistoryEventSubType.DONATE,
        asset=Asset('eip155:10/erc20:0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1'),  # DAI
        balance=Balance(amount=FVal(amount_str)),
        location_label=optimism_accounts[0],
        notes=f'Receive matching payout of {amount_str} DAI for a gitcoin round',
        counterparty=CPT_GITCOIN,
        address='0xEb33BB3705135e99F7975cDC931648942cB2A96f',
    )]
    assert events == expected_events


@pytest.mark.vcr(filter_query_parameters=['apikey'])
@pytest.mark.parametrize('ethereum_accounts', [['0x9531C059098e3d194fF87FebB587aB07B30B1306']])
def test_ethereum_grant_payout(ethereum_inquirer, ethereum_accounts):
    tx_hash = deserialize_evm_tx_hash('0x66ff5be7841f05cc9cb53fd0307460690f91203c52490f5bbfdeabe8462be50b')  # noqa: E501
    events, _ = get_decoded_events_of_transaction(evm_inquirer=ethereum_inquirer, tx_hash=tx_hash)
    amount_str = '20000'
    expected_events = [EvmEvent(
        tx_hash=tx_hash,
        sequence_index=313,
        timestamp=TimestampMS(1689038123000),
        location=Location.ETHEREUM,
        event_type=HistoryEventType.RECEIVE,
        event_subtype=HistoryEventSubType.DONATE,
        asset=A_DAI,
        balance=Balance(amount=FVal(amount_str)),
        location_label=ethereum_accounts[0],
        notes=f'Receive matching payout of {amount_str} DAI for a gitcoin round',
        counterparty=CPT_GITCOIN,
        address='0xebaF311F318b5426815727101fB82f0Af3525d7b',
    )]
    assert events == expected_events


@pytest.mark.vcr(filter_query_parameters=['apikey'])
@pytest.mark.parametrize('polygon_pos_accounts', [['0x9531C059098e3d194fF87FebB587aB07B30B1306']])
def test_polygon_donation_matic_received(polygon_pos_inquirer, polygon_pos_accounts):
    tx_hash = deserialize_evm_tx_hash('0x32837e03ac3e9066f09c1ee0807c533aa1bef5e3119b98dcacdd1ca631bc7ca6')  # noqa: E501
    events, _ = get_decoded_events_of_transaction(
        evm_inquirer=polygon_pos_inquirer,
        tx_hash=tx_hash,
    )
    user_address, timestamp, amount_str = polygon_pos_accounts[0], TimestampMS(1700595622000), '4'
    expected_events = [EvmEvent(
        tx_hash=tx_hash,
        sequence_index=0,
        timestamp=timestamp,
        location=Location.POLYGON_POS,
        event_type=HistoryEventType.RECEIVE,
        event_subtype=HistoryEventSubType.DONATE,
        asset=A_POLYGON_POS_MATIC,
        balance=Balance(amount=FVal(amount_str)),
        location_label=user_address,
        notes=f'Receive a gitcoin donation of {amount_str} POL from 0x6017B1d17f4D7547dC4aac88fbD0AA1826e7e6CE',  # noqa: E501
        counterparty=CPT_GITCOIN,
        address='0x03e50B688beB7c0E5e90F51188D0fa38c9152f9d',
    )]
    assert events == expected_events


@pytest.mark.vcr(filter_query_parameters=['apikey'])
@pytest.mark.parametrize('polygon_pos_accounts', [['0x9531C059098e3d194fF87FebB587aB07B30B1306']])
def test_polygon_donation_token_received(polygon_pos_inquirer, polygon_pos_accounts):
    tx_hash = deserialize_evm_tx_hash('0x17601356467af0cfcf3a62f93879b504695b8690545b2b8669da5ec0f3a2a91b')  # noqa: E501
    events, _ = get_decoded_events_of_transaction(
        evm_inquirer=polygon_pos_inquirer,
        tx_hash=tx_hash,
    )
    user_address, timestamp, amount_str = polygon_pos_accounts[0], TimestampMS(1700593336000), '1.5'  # noqa: E501
    expected_events = [EvmEvent(
        tx_hash=tx_hash,
        sequence_index=236,
        timestamp=timestamp,
        location=Location.POLYGON_POS,
        event_type=HistoryEventType.RECEIVE,
        event_subtype=HistoryEventSubType.DONATE,
        asset=Asset('eip155:137/erc20:0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359'),
        balance=Balance(amount=FVal(amount_str)),
        location_label=user_address,
        notes=f'Receive a gitcoin donation of {amount_str} USDC from 0x3d1f546F05834423Acc7e4CA1169ae320cee9AF0',  # noqa: E501
        counterparty=CPT_GITCOIN,
        address='0xe04d9e9CcDf65EB1Db51E56C04beE4c8582edB73',
    )]
    assert events == expected_events


@pytest.mark.vcr(filter_query_parameters=['apikey'])
@pytest.mark.parametrize('polygon_pos_accounts', [['0x9531C059098e3d194fF87FebB587aB07B30B1306']])
def test_polygon_apply_to_round(polygon_pos_inquirer, polygon_pos_accounts):
    tx_hash = deserialize_evm_tx_hash('0x51c1909ce9268f453d4b7136b0fecb72d8da567f406c37014dd8ad8ed05c9a1f')  # noqa: E501
    events, _ = get_decoded_events_of_transaction(
        evm_inquirer=polygon_pos_inquirer,
        tx_hash=tx_hash,
    )
    user_address, timestamp, gas_str = polygon_pos_accounts[0], TimestampMS(1699442294000), '0.05638388497968273'  # noqa: E501
    expected_events = [EvmEvent(
        tx_hash=tx_hash,
        sequence_index=0,
        timestamp=timestamp,
        location=Location.POLYGON_POS,
        event_type=HistoryEventType.SPEND,
        event_subtype=HistoryEventSubType.FEE,
        asset=A_POLYGON_POS_MATIC,
        balance=Balance(amount=FVal(gas_str)),
        location_label=user_address,
        notes=f'Burn {gas_str} POL for gas',
        counterparty=CPT_GAS,
    ), EvmEvent(
        tx_hash=tx_hash,
        sequence_index=1047,
        timestamp=timestamp,
        location=Location.POLYGON_POS,
        event_type=HistoryEventType.INFORMATIONAL,
        event_subtype=HistoryEventSubType.APPLY,
        asset=A_ETH,
        balance=Balance(),
        location_label=user_address,
        notes='Apply to gitcoin round with project application id 0xbb5864fabd76bd8a9d620dd2cfd089a0507135e6e57d12487d4ffd74a4939538',  # noqa: E501
        counterparty=CPT_GITCOIN,
        address='0xa1D52F9b5339792651861329A046dD912761E9A9',
    )]
    assert events == expected_events


@pytest.mark.vcr(filter_query_parameters=['apikey'])
@pytest.mark.parametrize('ethereum_accounts', [['0x9531C059098e3d194fF87FebB587aB07B30B1306']])
def test_ethereum_voted_without_application_index(ethereum_inquirer, ethereum_accounts):
    """Test that voted events missing the application index are properly seen as donations"""
    tx_hash = deserialize_evm_tx_hash('0xdcb6d2282b34a3cb7637ac65d8b7f1d0e8f2bc149379767f0b6f9ba2afa8a359')  # noqa: E501
    events, _ = get_decoded_events_of_transaction(
        evm_inquirer=ethereum_inquirer,
        tx_hash=tx_hash,
    )
    user_address, timestamp, amount = ethereum_accounts[0], TimestampMS(1673960015000), '0.0035'
    expected_events = [EvmEvent(
        tx_hash=tx_hash,
        sequence_index=0,
        timestamp=timestamp,
        location=Location.ETHEREUM,
        event_type=HistoryEventType.RECEIVE,
        event_subtype=HistoryEventSubType.DONATE,
        asset=A_ETH,
        balance=Balance(amount=FVal(amount)),
        location_label=user_address,
        notes=f'Receive a gitcoin donation of {amount} ETH from 0xcD9a4e7C2ad6AAae7Ac25c2139d71739d9Fa2284',  # noqa: E501
        counterparty=CPT_GITCOIN,
        address='0x8fBEa07446DdF4518b1a7BA2B4f11Bd140a8DF41',
    )]
    assert events == expected_events


@pytest.mark.vcr(filter_query_parameters=['apikey'])
@pytest.mark.parametrize('arbitrum_one_accounts', [['0x9531C059098e3d194fF87FebB587aB07B30B1306']])
def test_allocated_receive_token(arbitrum_one_inquirer, arbitrum_one_accounts):
    tx_hash = deserialize_evm_tx_hash('0x0388c141d93924d4737c4c52956469ecdb2c0a8dd9b3802317994c027d0a38af')  # noqa: E501
    events, _ = get_decoded_events_of_transaction(
        evm_inquirer=arbitrum_one_inquirer,
        tx_hash=tx_hash,
    )
    user_address, timestamp, amount = arbitrum_one_accounts[0], TimestampMS(1729693571000), '1.77'
    expected_events = [EvmEvent(
        tx_hash=tx_hash,
        sequence_index=81,
        timestamp=timestamp,
        location=Location.ARBITRUM_ONE,
        event_type=HistoryEventType.RECEIVE,
        event_subtype=HistoryEventSubType.DONATE,
        asset=A_ARB,
        balance=Balance(amount=FVal(amount)),
        location_label=user_address,
        notes=f'Receive a gitcoin donation of {amount} ARB from 0x830862F98399520f351273B12FD3C622a226bDfE',  # noqa: E501
        counterparty=CPT_GITCOIN,
        address='0x8e1bD5Da87C14dd8e08F7ecc2aBf9D1d558ea174',
    )]
    assert events == expected_events


@pytest.mark.vcr(filter_query_parameters=['apikey'])
@pytest.mark.parametrize('arbitrum_one_accounts', [['0x514e84986C09Ca52661eeE5EC8a3E6b645c54388']])
def test_allocated_donate_token(arbitrum_one_inquirer, arbitrum_one_accounts):
    tx_hash = deserialize_evm_tx_hash('0x9509a7be197f1926a480f0c02251c5b1f7d4fc4334a77c991efb61f55c243e5f')  # noqa: E501
    events, _ = get_decoded_events_of_transaction(
        evm_inquirer=arbitrum_one_inquirer,
        tx_hash=tx_hash,
    )
    user_address, timestamp, gas, amount, approve = arbitrum_one_accounts[0], TimestampMS(1729720900000), '0.00000367783', '2', '4'  # noqa: E501
    expected_events = [EvmEvent(
        tx_hash=tx_hash,
        sequence_index=0,
        timestamp=timestamp,
        location=Location.ARBITRUM_ONE,
        event_type=HistoryEventType.SPEND,
        event_subtype=HistoryEventSubType.FEE,
        asset=A_ETH,
        balance=Balance(amount=FVal(gas)),
        location_label=user_address,
        notes=f'Burn {gas} ETH for gas',
        counterparty=CPT_GAS,
    ), EvmEvent(
        tx_hash=tx_hash,
        sequence_index=1,
        timestamp=timestamp,
        location=Location.ARBITRUM_ONE,
        event_type=HistoryEventType.INFORMATIONAL,
        event_subtype=HistoryEventSubType.APPROVE,
        asset=A_ARB,
        balance=Balance(FVal(approve)),
        location_label=user_address,
        notes=f'Set ARB spending approval of {user_address} by 0x8e1bD5Da87C14dd8e08F7ecc2aBf9D1d558ea174 to {approve}',  # noqa: E501
        address='0x8e1bD5Da87C14dd8e08F7ecc2aBf9D1d558ea174',
    ), EvmEvent(
        tx_hash=tx_hash,
        sequence_index=2,
        timestamp=timestamp,
        location=Location.ARBITRUM_ONE,
        event_type=HistoryEventType.INFORMATIONAL,
        event_subtype=HistoryEventSubType.APPROVE,
        asset=A_ARB,
        balance=Balance(),
        location_label=user_address,
        notes=f'Revoke ARB spending approval of {user_address} by 0x8e1bD5Da87C14dd8e08F7ecc2aBf9D1d558ea174',  # noqa: E501
        address='0x8e1bD5Da87C14dd8e08F7ecc2aBf9D1d558ea174',
    ), EvmEvent(
        tx_hash=tx_hash,
        sequence_index=3,
        timestamp=timestamp,
        location=Location.ARBITRUM_ONE,
        event_type=HistoryEventType.SPEND,
        event_subtype=HistoryEventSubType.DONATE,
        asset=A_ARB,
        balance=Balance(FVal(amount)),
        location_label=user_address,
        notes=f'Make a gitcoin donation of {amount} ARB to 0xb9ecee9a0e273d8A1857F3B8EeA30e5dD3cb6335',  # noqa: E501
        counterparty=CPT_GITCOIN,
        address='0xb9ecee9a0e273d8A1857F3B8EeA30e5dD3cb6335',
    ), EvmEvent(
        tx_hash=tx_hash,
        sequence_index=9,
        timestamp=timestamp,
        location=Location.ARBITRUM_ONE,
        event_type=HistoryEventType.SPEND,
        event_subtype=HistoryEventSubType.DONATE,
        asset=A_ARB,
        balance=Balance(FVal(amount)),
        location_label=user_address,
        notes=f'Make a gitcoin donation of {amount} ARB to 0xE6D7b9Fb31B93E542f57c7B6bfa0a5a48EfC9D0f',  # noqa: E501
        counterparty=CPT_GITCOIN,
        address='0xE6D7b9Fb31B93E542f57c7B6bfa0a5a48EfC9D0f',
    )]
    assert events == expected_events


@pytest.mark.vcr(filter_query_parameters=['apikey'])
@pytest.mark.parametrize('arbitrum_one_accounts', [['0x173a7942Ac9989d8A2203051bF22E673BcDa6e9D']])
def test_allocated_donate_eth(arbitrum_one_inquirer, arbitrum_one_accounts):
    tx_hash = deserialize_evm_tx_hash('0x92450a269e9dc36bb78e3c631104eec0e9e190f5672e666bcd6397f310617849')  # noqa: E501
    events, _ = get_decoded_events_of_transaction(
        evm_inquirer=arbitrum_one_inquirer,
        tx_hash=tx_hash,
    )
    user_address, timestamp, gas, amount = arbitrum_one_accounts[0], TimestampMS(1729747404000), '0.00000219175', '0.001'  # noqa: E501
    expected_events = [EvmEvent(
        tx_hash=tx_hash,
        sequence_index=0,
        timestamp=timestamp,
        location=Location.ARBITRUM_ONE,
        event_type=HistoryEventType.SPEND,
        event_subtype=HistoryEventSubType.FEE,
        asset=A_ETH,
        balance=Balance(amount=FVal(gas)),
        location_label=user_address,
        notes=f'Burn {gas} ETH for gas',
        counterparty=CPT_GAS,
    ), EvmEvent(
        tx_hash=tx_hash,
        sequence_index=1,
        timestamp=timestamp,
        location=Location.ARBITRUM_ONE,
        event_type=HistoryEventType.SPEND,
        event_subtype=HistoryEventSubType.DONATE,
        asset=A_ETH,
        balance=Balance(FVal(amount)),
        location_label=user_address,
        notes=f'Make a gitcoin donation of {amount} ETH to 0x698386C93513d6D0C58f296633A7A3e529bd4026',  # noqa: E501
        counterparty=CPT_GITCOIN,
        address='0x698386C93513d6D0C58f296633A7A3e529bd4026',
    ), EvmEvent(
        tx_hash=tx_hash,
        sequence_index=10,
        timestamp=timestamp,
        location=Location.ARBITRUM_ONE,
        event_type=HistoryEventType.SPEND,
        event_subtype=HistoryEventSubType.DONATE,
        asset=A_ETH,
        balance=Balance(FVal(amount)),
        location_label=user_address,
        notes=f'Make a gitcoin donation of {amount} ETH to 0xfcBf17200C64E860F6639aa12B525015d115F863',  # noqa: E501
        counterparty=CPT_GITCOIN,
        address='0xfcBf17200C64E860F6639aa12B525015d115F863',
    )]
    assert events == expected_events


@pytest.mark.vcr(filter_query_parameters=['apikey'])
@pytest.mark.parametrize('arbitrum_one_accounts', [['0x9531C059098e3d194fF87FebB587aB07B30B1306']])
def test_registered(arbitrum_one_inquirer, arbitrum_one_accounts):
    tx_hash = deserialize_evm_tx_hash('0x75d7138bc9f43954d64120d29be217274e08a6e27a7f3634e5dbc6f1f466e372')  # noqa: E501
    events, _ = get_decoded_events_of_transaction(
        evm_inquirer=arbitrum_one_inquirer,
        tx_hash=tx_hash,
    )
    user_address, timestamp, gas, recipient_id = arbitrum_one_accounts[0], TimestampMS(1727784046000), '0.0000047042', '0x73B00B94762f800A244B6a84617Adbf07b9520a8'  # noqa: E501
    expected_events = [EvmEvent(
        tx_hash=tx_hash,
        sequence_index=0,
        timestamp=timestamp,
        location=Location.ARBITRUM_ONE,
        event_type=HistoryEventType.SPEND,
        event_subtype=HistoryEventSubType.FEE,
        asset=A_ETH,
        balance=Balance(amount=FVal(gas)),
        location_label=user_address,
        notes=f'Burn {gas} ETH for gas',
        counterparty=CPT_GAS,
    ), EvmEvent(
        tx_hash=tx_hash,
        sequence_index=1,
        timestamp=timestamp,
        location=Location.ARBITRUM_ONE,
        event_type=HistoryEventType.INFORMATIONAL,
        event_subtype=HistoryEventSubType.APPLY,
        asset=A_ETH,
        balance=Balance(),
        location_label=user_address,
        notes=f'Register for a gitcoin round with recipient id {recipient_id}',
        counterparty=CPT_GITCOIN,
        extra_data={'recipient_id': recipient_id},
    )]
    assert events == expected_events
