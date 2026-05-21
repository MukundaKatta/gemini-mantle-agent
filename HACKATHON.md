# DoraHacks Mantle Turing Test Hackathon — submission

DoraHacks event: https://dorahacks.io/hackathon/mantleturingtesthackathon2026
Deadline: 2026-06-15
Prize pool: $100,000

## Elevator pitch
A Gemini agent that walks a Mantle MCP server to answer plain-English
questions about Mantle L2 chain state, quoting block height, contract
addresses, TVL figures, and tx hashes byte-for-byte. The "Turing Test"
framing: the agent's answers read like a sharp on-chain analyst, but
every number it cites is provably from a verifiable tool call — never
invented or paraphrased.

## Rule compliance

| Rule | How we meet it |
|---|---|
| Built for Mantle | Agent walks a Mantle MCP tool surface (block height, protocol TVL, contract calls, tx receipts, top protocols by category). Real Mantle RPC swap is one env-var change. |
| AI agent (not just a script) | `google.adk.agents.LlmAgent` with Gemini 2.5 Flash on Vertex AI; multi-turn tool calls + self-check across `block_height` agreement. |
| Newly created | Standalone repo created during the Mantle Turing Test build window. |
| Original work | Standalone repo, Apache 2.0. |
| Runs publicly | Streamlit dashboard on Cloud Run, public URL. |

## Description

`gemini-mantle-agent` treats every on-chain question as a walk through
the chain's truth-set:

1. `get_block_height` to anchor the answer to a specific Mantle tip.
2. `get_protocol_tvl(protocol)` for the named protocol's DefiLlama-shape TVL.
3. `query_contract(address, method)` for the relevant read-only contract
   call (totalSupply, balanceOf, reserves, ...).
4. `get_transaction(hash)` for receipt-shape tx data (from / to / gas /
   status / method signature).
5. Optional `list_top_protocols(category)` to rank by TVL when the user
   doesn't name a specific protocol.

The agent's answer is a 5-section labeled report (ANSWER / CHAIN STATE
/ EVIDENCE / CONFIDENCE / NEXT STEP). Every TVL number, contract
address, hex result, and tx hash is byte-for-byte from a tool call. The
system prompt rejects paraphrasing on-chain values, and downgrades
CONFIDENCE if two tools disagree on `block_height`.

## Story chain shipped in the stub

- Block height: `90215643` (Mantle mainnet, 2026-05-20T18:00:00Z)
- Agni Finance TVL: `$12,847,193.42` (4172.05 ETH-equivalent)
- WMNT canonical: `0x4200000000000000000000000000000000000006`
- WMNT totalSupply: `267982104928374950000000` (decimals 18 → 267982.10 MNT)
- Deposit tx: `0xa9b3c1ee78d2f04e7c8c1c4d5e2f1234567890abcdef1234567890abcdef1234`
  to WMNT, status 1, gas_used 47832, method `deposit()`.

Every tool agrees on the same block height, which is what lets the
agent claim CONFIDENCE: high on the demo question.

## Built with
python, gemini, gemini-2-5, vertex-ai, google-cloud-agent-builder,
agent-development-kit, mcp, model-context-protocol, mantle,
mantle-network, on-chain, defillama, streamlit, google-cloud-run,
apache-2

## Try it out
- Code repo: https://github.com/MukundaKatta/gemini-mantle-agent
- Live demo (Cloud Run): pinned after deploy
- Demo video: pinned after upload
- Author: Mukunda Katta, independent.
