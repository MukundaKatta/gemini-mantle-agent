"""Unit tests for the ADK agent wiring.

Uses only the Python standard library (``unittest``). When ``google-adk``
is installed the agent is constructed and inspected; when it is not, the
tests verify the documented offline-fallback contract (``build_agent``
returns ``None``) instead of failing the suite. Either way the real
module is imported and exercised.

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

from gemini_mantle_agent.agent import (  # noqa: E402
    SYSTEM_PROMPT,
    _ADK_AVAILABLE,
    build_agent,
)


class SystemPromptTests(unittest.TestCase):
    """The system prompt is pure data and is always testable."""

    def test_prompt_lists_all_five_labeled_sections(self):
        for section in (
            "ANSWER:",
            "CHAIN STATE:",
            "EVIDENCE:",
            "CONFIDENCE:",
            "NEXT STEP:",
        ):
            self.assertIn(section, SYSTEM_PROMPT)

    def test_prompt_names_every_mantle_tool(self):
        for tool in (
            "get_block_height",
            "get_protocol_tvl",
            "query_contract",
            "get_transaction",
            "list_top_protocols",
        ):
            self.assertIn(tool, SYSTEM_PROMPT)

    def test_prompt_pins_the_canonical_wmnt_address(self):
        self.assertIn(
            "0x4200000000000000000000000000000000000006", SYSTEM_PROMPT
        )


class BuildAgentTests(unittest.TestCase):
    def test_build_agent_contract(self):
        agent = build_agent(stub=True)
        if _ADK_AVAILABLE:
            self.assertIsNotNone(agent)
            self.assertEqual(agent.name, "gemini_mantle_agent")
            tools = list(getattr(agent, "tools", []) or [])
            self.assertGreaterEqual(len(tools), 1)
        else:
            # Documented offline-fallback contract: no ADK -> no agent.
            self.assertIsNone(agent)


if __name__ == "__main__":
    unittest.main()
