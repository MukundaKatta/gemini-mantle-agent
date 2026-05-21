"""Stub Mantle MCP server.

Mirrors a Mantle on-chain MCP tool surface:
  - `get_block_height`     — current tip on Mantle L2 (block + timestamp)
  - `get_protocol_tvl`     — DefiLlama-shape TVL for a protocol on Mantle
  - `query_contract`       — read-only contract call (e.g. WMNT totalSupply)
  - `get_transaction`      — receipt-shape data for a tx hash
  - `list_top_protocols`   — top N protocols by TVL in a category (DEX, etc.)

Returns canned, realistic responses so judges can reproduce the demo
without provisioning a Mantle RPC. Real Mantle MCP swap is one env-var
change away — the agent code is unchanged.

Run with: python -m gemini_mantle_agent.mcp_stub

Submission: DoraHacks Mantle Turing Test Hackathon
            (deadline 2026-06-15)
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent


NOW = datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Canned Mantle chain state
# ---------------------------------------------------------------------------

# All canned tools agree on this block height. That gives the agent a
# clean "agreement across tools" signal it can cite in CONFIDENCE.
CANNED_BLOCK_HEIGHT = 90215643
CANNED_BLOCK_TIMESTAMP = "2026-05-20T18:00:00Z"
CHAIN_ID = "mantle-mainnet"

# Canonical WMNT contract address on Mantle.
WMNT_ADDRESS = "0x4200000000000000000000000000000000000006"

# The "most recent deposit" tx hash the story-chain walks to.
DEPOSIT_TX_HASH = (
    "0xa9b3c1ee78d2f04e7c8c1c4d5e2f1234567890abcdef1234567890abcdef1234"
)


_PROTOCOL_TVL: dict[str, dict[str, Any]] = {
    "Agni Finance": {
        "protocol": "Agni Finance",
        "tvl_usd": 12_847_193.42,
        "tvl_eth_equiv": 4172.05,
        "block_height": CANNED_BLOCK_HEIGHT,
        "source": "defillama-shape",
    },
    "FusionX": {
        "protocol": "FusionX",
        "tvl_usd": 7_209_344.18,
        "tvl_eth_equiv": 2341.91,
        "block_height": CANNED_BLOCK_HEIGHT,
        "source": "defillama-shape",
    },
    "Merchant Moe": {
        "protocol": "Merchant Moe",
        "tvl_usd": 4_512_807.65,
        "tvl_eth_equiv": 1466.17,
        "block_height": CANNED_BLOCK_HEIGHT,
        "source": "defillama-shape",
    },
}


_CONTRACT_CALLS: dict[tuple[str, str], dict[str, Any]] = {
    (WMNT_ADDRESS, "totalSupply()"): {
        "address": WMNT_ADDRESS,
        "method": "totalSupply()",
        "result_hex": "0x000000000000000000000000000000000000000000003812c6921e1a8de4f000",
        "result_decimal": "267982104928374950000000",
        "decimals": 18,
        "human": "267982.10 MNT",
        "block_height": CANNED_BLOCK_HEIGHT,
    },
}


_TRANSACTIONS: dict[str, dict[str, Any]] = {
    DEPOSIT_TX_HASH: {
        "hash": DEPOSIT_TX_HASH,
        "block_number": 90215600,
        "from": "0x1f9090aaE28b8a3dCeaDf281B0F12828e676c326",
        "to": WMNT_ADDRESS,
        "value_wei": 0,
        "gas_used": 47832,
        "status": 1,
        "method_signature": "deposit()",
        "mnt_value": 0.5,
    },
}


# Top-protocols rankings by category. Shares sum to 100% within category.
_TOP_PROTOCOLS: dict[str, list[dict[str, Any]]] = {
    "DEX": [
        {"name": "Agni Finance",  "tvl_usd": 12_847_193.42, "share_pct": 52.3},
        {"name": "FusionX",        "tvl_usd": 7_209_344.18,  "share_pct": 29.3},
        {"name": "Merchant Moe",   "tvl_usd": 4_512_807.65,  "share_pct": 18.4},
    ],
}


# ---------------------------------------------------------------------------
# Response builders
# ---------------------------------------------------------------------------


def get_block_height_response() -> dict[str, Any]:
    return {
        "chain":        CHAIN_ID,
        "block_height": CANNED_BLOCK_HEIGHT,
        "timestamp":    CANNED_BLOCK_TIMESTAMP,
    }


def get_protocol_tvl_response(protocol: str) -> dict[str, Any]:
    rec = _PROTOCOL_TVL.get(protocol)
    if rec is None:
        return {
            "error": f"unknown protocol {protocol!r}",
            "known_protocols": sorted(_PROTOCOL_TVL.keys()),
        }
    # Return a shallow copy so the agent can't mutate the canned data.
    return dict(rec)


def query_contract_response(address: str, method: str) -> dict[str, Any]:
    rec = _CONTRACT_CALLS.get((address, method))
    if rec is None:
        return {
            "error": (
                f"no canned response for contract call "
                f"address={address!r} method={method!r}"
            ),
            "known_calls": [
                {"address": a, "method": m} for (a, m) in _CONTRACT_CALLS
            ],
        }
    return dict(rec)


def get_transaction_response(tx_hash: str) -> dict[str, Any]:
    rec = _TRANSACTIONS.get(tx_hash)
    if rec is None:
        return {
            "error": f"no canned transaction for hash {tx_hash!r}",
            "known_hashes": sorted(_TRANSACTIONS.keys()),
        }
    return dict(rec)


def list_top_protocols_response(
    category: str, limit: int = 5
) -> dict[str, Any]:
    rows = _TOP_PROTOCOLS.get(category)
    if rows is None:
        return {
            "error": f"unknown category {category!r}",
            "known_categories": sorted(_TOP_PROTOCOLS.keys()),
        }
    limited = rows[: max(1, int(limit))]
    return {
        "category":    category,
        "limit":       int(limit),
        "block_height": CANNED_BLOCK_HEIGHT,
        "protocols":   limited,
        "result_count": len(limited),
    }


# ---------------------------------------------------------------------------
# MCP server wiring
# ---------------------------------------------------------------------------


def _make_server() -> Server:
    server = Server("mantle-mcp-stub")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="get_block_height",
                description=(
                    "Return the current tip of Mantle mainnet. Returns "
                    "chain id, block height (integer), and the block "
                    "timestamp in ISO 8601 UTC."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            Tool(
                name="get_protocol_tvl",
                description=(
                    "Return TVL for a named DeFi protocol on Mantle "
                    "(DefiLlama-shape). Returns tvl_usd, tvl_eth_equiv, "
                    "and the block_height the figure was sampled at."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "protocol": {"type": "string"},
                    },
                    "required": ["protocol"],
                },
            ),
            Tool(
                name="query_contract",
                description=(
                    "Read-only call on a Mantle contract. Returns the "
                    "raw hex result, a decimal decoding, the decimals "
                    "field, and a human-readable string. Use this for "
                    "totalSupply, balanceOf, etc."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "address": {"type": "string"},
                        "method":  {"type": "string"},
                    },
                    "required": ["address", "method"],
                },
            ),
            Tool(
                name="get_transaction",
                description=(
                    "Fetch receipt-shape data for a transaction on Mantle: "
                    "hash, block_number, from, to, value_wei, gas_used, "
                    "status, decoded method signature, and the human MNT value."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "hash": {"type": "string"},
                    },
                    "required": ["hash"],
                },
            ),
            Tool(
                name="list_top_protocols",
                description=(
                    "Return the top N protocols on Mantle in a category "
                    "(e.g. 'DEX'). Returns name, tvl_usd, and share_pct "
                    "of category TVL for each row."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "category": {"type": "string"},
                        "limit":    {"type": "integer", "default": 5},
                    },
                    "required": ["category"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(
        name: str, arguments: dict[str, Any]
    ) -> list[TextContent]:
        a = arguments or {}
        if name == "get_block_height":
            payload = get_block_height_response()
        elif name == "get_protocol_tvl":
            payload = get_protocol_tvl_response(a.get("protocol", ""))
        elif name == "query_contract":
            payload = query_contract_response(
                a.get("address", ""), a.get("method", "")
            )
        elif name == "get_transaction":
            payload = get_transaction_response(a.get("hash", ""))
        elif name == "list_top_protocols":
            payload = list_top_protocols_response(
                a.get("category", ""), a.get("limit", 5)
            )
        else:
            payload = {"error": f"unknown tool {name!r}"}
        return [
            TextContent(
                type="text",
                text=json.dumps(payload, indent=2, default=str),
            )
        ]

    return server


async def _main() -> None:
    server = _make_server()
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


def main() -> None:
    asyncio.run(_main())


if __name__ == "__main__":
    main()
