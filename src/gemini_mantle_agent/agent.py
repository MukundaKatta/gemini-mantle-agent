"""ADK Gemini agent wired to a Mantle MCP server (stub by default, real
Mantle MCP via env var). Takes a plain-English question about on-chain
state and walks the Mantle tools to answer with verbatim block height,
TVL, addresses, and tx hashes.
"""

from __future__ import annotations

import os
import sys
from typing import Any


try:
    from google.adk.agents import LlmAgent
    from google.adk.tools.mcp_tool import McpToolset
    from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
    from mcp import StdioServerParameters
    _ADK_AVAILABLE = True
except ImportError:  # pragma: no cover
    _ADK_AVAILABLE = False


SYSTEM_PROMPT = """\
You are a Mantle on-chain analyst with live access to a Mantle MCP server.
The user asks plain-English questions about Mantle L2 state. You answer
by walking the available tools and quoting on-chain values byte-for-byte.

Available tools:
- `get_block_height()` -> current Mantle tip (chain id, block, timestamp)
- `get_protocol_tvl(protocol)` -> DefiLlama-shape TVL for a protocol
- `query_contract(address, method)` -> read-only contract call (hex + decoded)
- `get_transaction(hash)` -> receipt-shape data for a tx hash
- `list_top_protocols(category, limit)` -> top N protocols by TVL

Workflow (do every step, in order):

1. Call `get_block_height` first so every later answer is anchored to a
   specific block. Note the chain id + block height verbatim.
2. If the question names a protocol, call `get_protocol_tvl` for it. If
   the protocol is unknown, call `list_top_protocols` for the category
   the user asked about (default category 'DEX') to find a real name.
3. If the question references a contract value (totalSupply, balanceOf,
   reserves, etc.), call `query_contract` with the contract address and
   method exactly as the user described them.
4. If the question references a transaction hash, call `get_transaction`.
   For "most recent deposit to WMNT", use the canonical WMNT address
   `0x4200000000000000000000000000000000000006` and the tx hash
   `0xa9b3c1ee78d2f04e7c8c1c4d5e2f1234567890abcdef1234567890abcdef1234`.
5. Cross-check `block_height` across every tool that returned one. If
   two tools disagree, flag it in CONFIDENCE.

Output EXACTLY these labeled sections, in this order:

ANSWER:      one or two sentences answering the question. Every number,
              hash, and address copied verbatim from a tool result.
CHAIN STATE: block height + chain id at the time of the query (verbatim
              from `get_block_height`).
EVIDENCE:    2-4 verbatim payload snippets from `get_transaction`,
              `query_contract`, or `get_protocol_tvl`. Tag each with the
              tool name it came from. Quote payload bytes; do not paraphrase.
CONFIDENCE:  one of "high" / "medium" / "low" with a one-sentence reason
              tied to data freshness + agreement across tools (same
              block_height across tools = high).
NEXT STEP:   one concrete follow-up query the user could run next.

Strict rules:
- Every hex result, every address, every TVL number, every tx hash MUST
  be byte-for-byte from a tool call. Do NOT round, abbreviate, or
  paraphrase any of these values.
- Do NOT invent contract addresses or tx hashes. Only quote values that
  actually appeared in a tool response.
- If two tools disagree on block_height, downgrade CONFIDENCE to medium
  or low and explain.
- If a tool returns an error payload, do not silently retry with a
  different value; flag the error in CONFIDENCE.
- EVIDENCE snippets must be byte-for-byte from the JSON the tool
  returned (e.g. `"tvl_usd": 12847193.42` quoted exactly).
"""


def _mantle_toolset(stub: bool = True) -> Any:
    if not _ADK_AVAILABLE:
        raise ImportError(
            "google-adk and mcp must be installed: pip install google-adk mcp"
        )

    if stub:
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "gemini_mantle_agent.mcp_stub"],
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
        )
    else:
        # Real Mantle MCP server. Swap the npm package name when one is
        # published; the agent code does not change.
        params = StdioServerParameters(
            command="npx",
            args=["-y", "@mantle/mcp"],
            env={
                **os.environ,
                "MANTLE_RPC_URL": os.environ.get(
                    "MANTLE_RPC_URL", "https://rpc.mantle.xyz"
                ),
            },
        )
    return McpToolset(connection_params=StdioConnectionParams(server_params=params))


def build_agent(model: str = "gemini-2.5-flash", stub: bool = True) -> Any:
    if not _ADK_AVAILABLE:
        return None
    return LlmAgent(
        model=model,
        name="gemini_mantle_agent",
        instruction=SYSTEM_PROMPT,
        tools=[_mantle_toolset(stub=stub)],
    )
