"""Unit tests for the stub Mantle MCP response builders.

These tests use only the Python standard library (``unittest``) and
exercise the pure ``*_response`` helpers in
:mod:`gemini_mantle_agent.mcp_stub`. They do NOT require the ``mcp``
package, because the response builders are deliberately decoupled from
the MCP server framework.

Run with::

    python3 -m unittest discover -s tests
"""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src")
)

from gemini_mantle_agent.mcp_stub import (  # noqa: E402
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


class BlockHeightTests(unittest.TestCase):
    def test_block_height_pinned(self):
        payload = get_block_height_response()
        self.assertEqual(payload["chain"], CHAIN_ID)
        self.assertEqual(CHAIN_ID, "mantle-mainnet")
        self.assertEqual(payload["block_height"], CANNED_BLOCK_HEIGHT)
        self.assertEqual(CANNED_BLOCK_HEIGHT, 90215643)
        self.assertTrue(payload["timestamp"].endswith("Z"))


class ProtocolTvlTests(unittest.TestCase):
    def test_agni_finance_verbatim(self):
        payload = get_protocol_tvl_response("Agni Finance")
        self.assertEqual(payload["protocol"], "Agni Finance")
        # TVL number must be exactly the canned figure — agent quotes it.
        self.assertEqual(payload["tvl_usd"], 12_847_193.42)
        self.assertEqual(payload["tvl_eth_equiv"], 4172.05)
        self.assertEqual(payload["block_height"], CANNED_BLOCK_HEIGHT)
        self.assertEqual(payload["source"], "defillama-shape")

    def test_fusionx_verbatim(self):
        payload = get_protocol_tvl_response("FusionX")
        self.assertEqual(payload["tvl_usd"], 7_209_344.18)
        self.assertEqual(payload["block_height"], CANNED_BLOCK_HEIGHT)

    def test_unknown_returns_error_with_known_list(self):
        payload = get_protocol_tvl_response("NotAProtocol")
        self.assertIn("error", payload)
        self.assertIn("Agni Finance", payload["known_protocols"])
        self.assertIn("FusionX", payload["known_protocols"])

    def test_returns_a_copy_not_the_canned_dict(self):
        # The agent must not be able to mutate the canned chain state.
        first = get_protocol_tvl_response("Agni Finance")
        first["tvl_usd"] = 0.0
        second = get_protocol_tvl_response("Agni Finance")
        self.assertEqual(second["tvl_usd"], 12_847_193.42)


class QueryContractTests(unittest.TestCase):
    def test_wmnt_total_supply(self):
        payload = query_contract_response(WMNT_ADDRESS, "totalSupply()")
        self.assertEqual(
            payload["address"],
            "0x4200000000000000000000000000000000000006",
        )
        self.assertEqual(payload["method"], "totalSupply()")
        self.assertTrue(payload["result_hex"].startswith("0x"))
        self.assertEqual(
            payload["result_decimal"], "267982104928374950000000"
        )
        self.assertEqual(payload["decimals"], 18)
        self.assertIn("MNT", payload["human"])
        self.assertEqual(payload["block_height"], CANNED_BLOCK_HEIGHT)

    def test_unknown_returns_error(self):
        payload = query_contract_response("0xdeadbeef", "foo()")
        self.assertIn("error", payload)
        self.assertTrue(
            any(c["address"] == WMNT_ADDRESS for c in payload["known_calls"])
        )


class GetTransactionTests(unittest.TestCase):
    def test_canned_deposit(self):
        payload = get_transaction_response(DEPOSIT_TX_HASH)
        self.assertEqual(payload["hash"], DEPOSIT_TX_HASH)
        self.assertEqual(payload["to"], WMNT_ADDRESS)
        self.assertEqual(payload["status"], 1)
        self.assertEqual(payload["method_signature"], "deposit()")
        self.assertEqual(payload["mnt_value"], 0.5)
        self.assertEqual(payload["block_number"], 90215600)

    def test_unknown_returns_error(self):
        payload = get_transaction_response("0x00")
        self.assertIn("error", payload)
        self.assertIn(DEPOSIT_TX_HASH, payload["known_hashes"])


class ListTopProtocolsTests(unittest.TestCase):
    def test_dex(self):
        payload = list_top_protocols_response("DEX", limit=5)
        self.assertEqual(payload["category"], "DEX")
        self.assertEqual(payload["block_height"], CANNED_BLOCK_HEIGHT)
        names = [p["name"] for p in payload["protocols"]]
        self.assertIn("Agni Finance", names)
        # Shares within category should add up to ~100.
        total_share = sum(p["share_pct"] for p in payload["protocols"])
        self.assertLess(abs(total_share - 100.0), 0.5)

    def test_limit_is_respected(self):
        payload = list_top_protocols_response("DEX", limit=1)
        self.assertEqual(payload["result_count"], 1)
        self.assertEqual(len(payload["protocols"]), 1)
        self.assertEqual(payload["protocols"][0]["name"], "Agni Finance")

    def test_limit_floor_is_one(self):
        # A non-positive limit must not return an empty (or negative-slice)
        # list — the floor is one protocol.
        payload = list_top_protocols_response("DEX", limit=0)
        self.assertGreaterEqual(payload["result_count"], 1)

    def test_unknown_category(self):
        payload = list_top_protocols_response("NotACategory")
        self.assertIn("error", payload)
        self.assertIn("DEX", payload["known_categories"])


class StoryChainConsistencyTests(unittest.TestCase):
    """The agent's killer move: walk get_protocol_tvl → get_block_height
    → query_contract → get_transaction and have every block_height and
    address line up across tools. This is what justifies CONFIDENCE: high.
    """

    def test_story_chain_is_consistent(self):
        tvl = get_protocol_tvl_response("Agni Finance")
        block = get_block_height_response()
        contract = query_contract_response(WMNT_ADDRESS, "totalSupply()")
        tx = get_transaction_response(DEPOSIT_TX_HASH)
        top = list_top_protocols_response("DEX", limit=5)

        # 1) Same block height across every tool that returned one.
        self.assertEqual(tvl["block_height"], 90215643)
        self.assertEqual(block["block_height"], 90215643)
        self.assertEqual(contract["block_height"], 90215643)
        self.assertEqual(top["block_height"], 90215643)

        # 2) Agni Finance in both list_top_protocols and get_protocol_tvl.
        self.assertEqual(tvl["protocol"], "Agni Finance")
        names = [p["name"] for p in top["protocols"]]
        self.assertIn("Agni Finance", names)

        # 3) WMNT address in both query_contract and get_transaction.to.
        self.assertEqual(contract["address"], WMNT_ADDRESS)
        self.assertEqual(tx["to"], WMNT_ADDRESS)

        # 4) The tx hash is consistent byte-for-byte.
        self.assertEqual(
            tx["hash"],
            "0xa9b3c1ee78d2f04e7c8c1c4d5e2f1234567890abcdef1234567890abcdef1234",
        )


if __name__ == "__main__":
    unittest.main()
