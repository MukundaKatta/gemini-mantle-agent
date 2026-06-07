"""Unit tests for the programmatic ADK Runner wrapper.

Uses only the Python standard library (``unittest``). Without
``google-adk`` installed, :func:`gemini_mantle_agent.runner.ask` must
return a well-formed :class:`AgentResponse` describing the offline
fallback rather than raising — these tests pin that contract.

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

from gemini_mantle_agent.runner import (  # noqa: E402
    AgentResponse,
    _ADK_AVAILABLE,
    ask,
)


class AskTests(unittest.TestCase):
    def test_ask_returns_agent_response(self):
        resp = ask("What's TVL on Agni Finance?", stub=True)
        self.assertIsInstance(resp, AgentResponse)
        self.assertIsInstance(resp.final_text, str)
        self.assertIsInstance(resp.events, list)

    def test_offline_fallback_contract(self):
        if _ADK_AVAILABLE:
            self.skipTest("google-adk installed; offline path not exercised")
        resp = ask("anything", stub=True)
        self.assertEqual(resp.error, "ADK not available")
        self.assertIn("offline-fallback", resp.final_text)
        self.assertEqual(resp.events, [])


class AgentResponseDataclassTests(unittest.TestCase):
    def test_defaults(self):
        resp = AgentResponse(final_text="hi", events=[])
        self.assertIsNone(resp.error)

    def test_fields_roundtrip(self):
        resp = AgentResponse(
            final_text="answer",
            events=[{"author": "agent"}],
            error="boom",
        )
        self.assertEqual(resp.final_text, "answer")
        self.assertEqual(resp.events[0]["author"], "agent")
        self.assertEqual(resp.error, "boom")


if __name__ == "__main__":
    unittest.main()
