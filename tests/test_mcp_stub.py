from gemini_mantle_agent.mcp_stub import (
    CANNED_BLOCK_HEIGHT,
    CHAIN_ID,
    DEPOSIT_TX_HASH,
    WMNT_ADDRESS,
    get_block_height_response,
    get_protocol_tvl_response,
    get_transaction_response,
    list_top_protocols_response,
    query_contract_response,
)


def test_block_height_pinned():
    payload = get_block_height_response()
    assert payload["chain"] == CHAIN_ID == "mantle-mainnet"
    assert payload["block_height"] == CANNED_BLOCK_HEIGHT == 90215643
    assert payload["timestamp"].endswith("Z")


def test_protocol_tvl_agni_finance_verbatim():
    payload = get_protocol_tvl_response("Agni Finance")
    assert payload["protocol"] == "Agni Finance"
    # TVL number must be exactly the canned figure — agent will quote it.
    assert payload["tvl_usd"] == 12_847_193.42
    assert payload["tvl_eth_equiv"] == 4172.05
    assert payload["block_height"] == CANNED_BLOCK_HEIGHT
    assert payload["source"] == "defillama-shape"


def test_protocol_tvl_fusionx_verbatim():
    payload = get_protocol_tvl_response("FusionX")
    assert payload["tvl_usd"] == 7_209_344.18
    assert payload["block_height"] == CANNED_BLOCK_HEIGHT


def test_protocol_tvl_unknown_returns_error_with_known_list():
    payload = get_protocol_tvl_response("NotAProtocol")
    assert "error" in payload
    assert "Agni Finance" in payload["known_protocols"]
    assert "FusionX" in payload["known_protocols"]


def test_query_contract_wmnt_total_supply():
    payload = query_contract_response(WMNT_ADDRESS, "totalSupply()")
    assert payload["address"] == "0x4200000000000000000000000000000000000006"
    assert payload["method"] == "totalSupply()"
    assert payload["result_hex"].startswith("0x")
    assert payload["result_decimal"] == "267982104928374950000000"
    assert payload["decimals"] == 18
    assert "MNT" in payload["human"]
    assert payload["block_height"] == CANNED_BLOCK_HEIGHT


def test_query_contract_unknown_returns_error():
    payload = query_contract_response("0xdeadbeef", "foo()")
    assert "error" in payload
    assert any(
        c["address"] == WMNT_ADDRESS for c in payload["known_calls"]
    )


def test_get_transaction_canned_deposit():
    payload = get_transaction_response(DEPOSIT_TX_HASH)
    assert payload["hash"] == DEPOSIT_TX_HASH
    assert payload["to"] == WMNT_ADDRESS
    assert payload["status"] == 1
    assert payload["method_signature"] == "deposit()"
    assert payload["mnt_value"] == 0.5
    assert payload["block_number"] == 90215600


def test_get_transaction_unknown_returns_error():
    payload = get_transaction_response("0x00")
    assert "error" in payload
    assert DEPOSIT_TX_HASH in payload["known_hashes"]


def test_list_top_protocols_dex():
    payload = list_top_protocols_response("DEX", limit=5)
    assert payload["category"] == "DEX"
    assert payload["block_height"] == CANNED_BLOCK_HEIGHT
    names = [p["name"] for p in payload["protocols"]]
    assert "Agni Finance" in names
    # Shares within category should add up to ~100.
    total_share = sum(p["share_pct"] for p in payload["protocols"])
    assert abs(total_share - 100.0) < 0.5


def test_list_top_protocols_unknown_category():
    payload = list_top_protocols_response("NotACategory")
    assert "error" in payload
    assert "DEX" in payload["known_categories"]


def test_mantle_story_chain_is_consistent():
    """The agent's killer move: walk get_protocol_tvl → get_block_height
    → query_contract → get_transaction and have every block_height and
    address line up across tools.

    This is what makes the agent's CONFIDENCE high: the chain agrees.
    """
    tvl = get_protocol_tvl_response("Agni Finance")
    block = get_block_height_response()
    contract = query_contract_response(WMNT_ADDRESS, "totalSupply()")
    tx = get_transaction_response(DEPOSIT_TX_HASH)
    top = list_top_protocols_response("DEX", limit=5)

    # 1) Same block height across every tool that returned one.
    assert (
        tvl["block_height"]
        == block["block_height"]
        == contract["block_height"]
        == top["block_height"]
        == 90215643
    )

    # 2) "Agni Finance" appears in both list_top_protocols and get_protocol_tvl.
    assert tvl["protocol"] == "Agni Finance"
    names = [p["name"] for p in top["protocols"]]
    assert "Agni Finance" in names

    # 3) WMNT address appears in both query_contract and get_transaction.to.
    assert contract["address"] == WMNT_ADDRESS
    assert tx["to"] == WMNT_ADDRESS

    # 4) The tx hash is consistent byte-for-byte.
    assert (
        tx["hash"]
        == "0xa9b3c1ee78d2f04e7c8c1c4d5e2f1234567890abcdef1234567890abcdef1234"
    )
