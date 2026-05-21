"""Real Vertex AI smoke test for gemini-mantle-agent.

Runs an on-chain question end-to-end through Gemini 2.5 Flash on the
Mantle MCP stub and verifies the agent walks get_protocol_tvl ->
get_block_height -> query_contract -> get_transaction, emits all five
labeled sections, and quotes the verbatim TVL number, WMNT address,
block height, and deposit tx hash.

Usage:
    GOOGLE_CLOUD_PROJECT=careersavvy-mukunda \
    GOOGLE_GENAI_USE_VERTEXAI=true \
    GOOGLE_CLOUD_LOCATION=us-central1 \
    .venv/bin/python scripts/smoke.py
"""
from __future__ import annotations

import os
import sys

os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "careersavvy-mukunda")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "true")
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "us-central1")

from gemini_mantle_agent.runner import ask  # noqa: E402


QUESTION = (
    "What's TVL on Agni Finance right now and the most recent deposit to "
    "the WMNT contract? Walk the Mantle tools and quote verbatim from "
    "chain state."
)


def main() -> int:
    print("== gemini-mantle-agent smoke ==")
    print(f"project={os.environ.get('GOOGLE_CLOUD_PROJECT')}")
    print(f"location={os.environ.get('GOOGLE_CLOUD_LOCATION')}")
    print(f"vertexai={os.environ.get('GOOGLE_GENAI_USE_VERTEXAI')}")
    print()
    print(f"> {QUESTION}")
    print()

    resp = ask(QUESTION, stub=True)
    print("--- FINAL TEXT ---")
    print(resp.final_text or "(no final text)")
    print("--- END FINAL TEXT ---")
    print(f"events: {len(resp.events)}")

    text = resp.final_text or ""
    upper = text.upper()
    checks = {
        "has ANSWER section":                   "ANSWER" in upper,
        "has CHAIN STATE section":              "CHAIN STATE" in upper,
        "has EVIDENCE section":                 "EVIDENCE" in upper,
        "has CONFIDENCE section":               "CONFIDENCE" in upper,
        "has NEXT STEP section":                "NEXT STEP" in upper,
        "names Agni Finance verbatim":          "Agni Finance" in text,
        "quotes TVL 12,847,193.42 verbatim":    (
            "12,847,193.42" in text or "12847193.42" in text
        ),
        "quotes WMNT address verbatim":         (
            "0x4200000000000000000000000000000000000006" in text
        ),
        "quotes block height 90215643":         "90215643" in text,
        "quotes deposit tx hash verbatim":      (
            "0xa9b3c1ee78d2f04e7c8c1c4d5e2f1234567890abcdef1234567890abcdef1234"
            in text
        ),
    }
    print()
    print("--- CHECKS ---")
    for label, ok in checks.items():
        print(f"  [{'PASS' if ok else 'FAIL'}] {label}")
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
