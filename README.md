# gemini-mantle-agent

[![CI](https://github.com/MukundaKatta/gemini-mantle-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/MukundaKatta/gemini-mantle-agent/actions/workflows/ci.yml)

An on-chain analyst agent built on **Google Cloud Agent Builder (ADK)**,
**Gemini 2.5**, and a **Mantle MCP server**. Submission for the
**DoraHacks Mantle Turing Test 2026** (deadline 2026-06-15).

**License:** Apache 2.0
**Author:** Mukunda Katta, independent.

## What it does

You ask a plain-English question about Mantle L2 chain state — "what's
TVL on Agni Finance right now and the most recent deposit to the WMNT
contract?" — and the agent walks a Mantle MCP server (stub by default,
real Mantle RPC swap-in) to answer with a five-section labeled report:

```
ANSWER:      one or two sentences, every number/hash/address copied verbatim.
CHAIN STATE: block height + chain id at query time (verbatim).
EVIDENCE:    2-4 verbatim payload snippets, each tagged with the tool name.
CONFIDENCE:  high / medium / low, grounded in agreement across tools.
NEXT STEP:   one concrete follow-up the user could run.
```

Strict rule: every TVL number, contract address, hex result, and tx
hash MUST be byte-for-byte from a tool call. The agent never
paraphrases on-chain values. If two tools disagree on `block_height`,
the answer is downgraded in CONFIDENCE.

## Tool surface

The agent uses a Mantle MCP tool surface. A stub MCP server ships in
the repo with a canned story chain (`block_height = 90215643`,
WMNT canonical at `0x4200...0006`, Agni Finance TVL = $12,847,193.42).
The real-Mantle-MCP swap is one env-var change away.

- `get_block_height()` — current Mantle tip (chain id + block + timestamp)
- `get_protocol_tvl(protocol)` — DefiLlama-shape TVL for a Mantle protocol
- `query_contract(address, method)` — read-only contract call (hex + decoded)
- `get_transaction(hash)` — receipt-shape data (from / to / gas / status)
- `list_top_protocols(category, limit)` — top N protocols by TVL on Mantle

## Architecture

```
┌──────────────────────┐    ┌───────────────────────┐   ┌────────────────────────────┐
│ Streamlit dashboard  │──▶ │  ADK LlmAgent          │──▶│  Mantle MCP server          │
│ on Cloud Run         │    │  Gemini 2.5 on Vertex  │   │  (stub for demos,           │
│                      │    │  AI                    │   │   real Mantle RPC via       │
│ "What's TVL on ..."  │    │                        │   │   MANTLE_RPC_URL)           │
└──────────────────────┘    └───────────────────────┘   └────────────────────────────┘
```

## Try it locally

```bash
git clone https://github.com/MukundaKatta/gemini-mantle-agent
cd gemini-mantle-agent
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

gcloud auth application-default login
export GOOGLE_CLOUD_PROJECT=your-project
export GOOGLE_GENAI_USE_VERTEXAI=true
export GOOGLE_CLOUD_LOCATION=us-central1

PYTHONPATH=src streamlit run app/dashboard.py
```

## Try it against a real Mantle MCP

```bash
export MANTLE_RPC_URL="https://rpc.mantle.xyz"
```

Untick "Use stub Mantle MCP" in the sidebar. The agent then spawns
the real `@mantle/mcp` server via `npx`. (When that npm package
publishes — until then, the stub is the canonical demo path.)

## Tests

The test suite uses only the Python standard library (`unittest`) and
needs **no third-party packages installed** — the canned-chain-state
response builders are deliberately decoupled from the `mcp` and
`google-adk` runtime dependencies, so the core logic can be unit-tested
anywhere:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

(`pytest` also discovers and runs the same `tests/` directory if you
prefer it.)

The suite pins the story-chain contract: every tool that returns a
`block_height` agrees on `90215643`, Agni Finance shows up in both
`list_top_protocols` and `get_protocol_tvl`, the WMNT address
`0x4200000000000000000000000000000000000006` appears in both
`query_contract` and `get_transaction.to`, and the deposit tx hash
matches byte-for-byte. It also covers the error paths (unknown protocol
/ contract / tx / category), the `limit` floor on `list_top_protocols`,
the defensive copy on `get_protocol_tvl`, and the documented
offline-fallback contracts of `build_agent` and `ask` when `google-adk`
is not installed.

## Using the stub chain state directly

The pure response builders are importable on their own, without `mcp` or
`google-adk`, which makes them easy to reuse in tests, notebooks, or your
own harness:

```python
from gemini_mantle_agent.mcp_stub import (
    get_block_height_response,
    get_protocol_tvl_response,
    list_top_protocols_response,
)

get_block_height_response()
# {'chain': 'mantle-mainnet', 'block_height': 90215643,
#  'timestamp': '2026-05-20T18:00:00Z'}

get_protocol_tvl_response("Agni Finance")["tvl_usd"]
# 12847193.42

[p["name"] for p in list_top_protocols_response("DEX")["protocols"]]
# ['Agni Finance', 'FusionX', 'Merchant Moe']
```

To run the full stub as an MCP server over stdio (this path does require
the `mcp` package):

```bash
PYTHONPATH=src python3 -m gemini_mantle_agent.mcp_stub
```

## License

Apache 2.0. Mukunda Katta, independent.
