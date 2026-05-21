"""gemini-mantle-agent dashboard."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gemini_mantle_agent.runner import ask  # noqa: E402


st.set_page_config(
    page_title="gemini-mantle-agent",
    layout="wide",
    page_icon=":link:",
)
st.title("gemini-mantle-agent")
st.caption(
    "On-chain analyst on Google Cloud Agent Builder (ADK) + Gemini 2.5, "
    "wired to a Mantle MCP server. Cites block height, addresses, TVL, "
    "and tx hashes byte-for-byte. Submission for the DoraHacks Mantle "
    "Turing Test 2026. Apache 2.0."
)

with st.sidebar:
    st.header("Ask the chain")
    question = st.text_area(
        "Your on-chain question",
        value=(
            "What's TVL on Agni Finance right now and the most recent "
            "deposit to the WMNT contract? Walk the Mantle tools and "
            "quote verbatim from chain state."
        ),
        height=140,
    )
    model = st.selectbox(
        "Gemini model",
        options=["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.5-flash-lite"],
        index=0,
    )
    stub = st.toggle(
        "Use stub Mantle MCP",
        value=True,
        help=(
            "On = local stub with canned Mantle chain state. Off = real "
            "Mantle MCP server (set MANTLE_RPC_URL)."
        ),
    )
    run = st.button("Run query", type="primary", use_container_width=True)
    st.divider()
    st.caption(
        f"Project: `{os.getenv('GOOGLE_CLOUD_PROJECT', 'not-set')}`  "
        f"Vertex AI: `{os.getenv('GOOGLE_GENAI_USE_VERTEXAI', 'true')}`"
    )

st.markdown(
    """
The agent walks these Mantle MCP tools to answer on-chain questions:
- **get_block_height** to anchor the answer to a specific tip
- **get_protocol_tvl** for DefiLlama-shape TVL on a Mantle protocol
- **query_contract** for read-only contract calls (totalSupply, balanceOf, ...)
- **get_transaction** for receipt-shape tx data (from, to, gas, status)
- **list_top_protocols** to rank by TVL in a category (DEX, lending, ...)
"""
)

if run:
    with st.status("Running Vertex AI Gemini...", expanded=True) as status:
        t0 = time.perf_counter()
        try:
            resp = ask(question, stub=stub, model=model)
        except Exception as e:  # pragma: no cover
            status.update(label=f"Error: {e}", state="error")
            st.exception(e)
            st.stop()
        elapsed = (time.perf_counter() - t0) * 1000
        status.update(label=f"Done in {elapsed:.0f} ms", state="complete")

    st.subheader("On-chain answer")
    st.markdown(resp.final_text or "_(no final response)_")

    with st.expander(f"Agent event trace ({len(resp.events)} events)"):
        for i, ev in enumerate(resp.events):
            st.markdown(
                f"**{i}.** author=`{ev.get('author')}` final=`{ev.get('is_final')}`"
            )
            text = ev.get("text") or ""
            if text:
                st.code(text[:1500], language=None)
else:
    st.info(
        "Use the sidebar to fire an on-chain question through the stub "
        "Mantle MCP server."
    )
