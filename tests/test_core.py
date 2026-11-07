"""Fast checks for the bridge and verification safety boundaries."""
import asyncio
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import Config
from store import channel_slug
from pipeline import Pipeline, _loaded_marker, _new_lines
from roblox import GameRef, _rank_game


class FakeBridge:
    def __init__(self, clients: str, probe: str = ""):
        self.clients = clients
        self.probe = probe
        self.selected = []

    def find_tool(self, *names):
        return names[0]

    def arg_key(self, tool, *names):
        return names[0]

    async def call_tool(self, name, args):
        if name == "set-active-client":
            self.selected.append(args["clientId"])
            return "ok"
        if name == "get-data-by-code":
            return self.probe
        return self.clients


class CoreTests(unittest.IsolatedAsyncioTestCase):
    def test_channel_slug_is_unique_and_bounded(self):
        name = "A very long game title " * 20
        self.assertNotEqual(channel_slug(name, 101), channel_slug(name, 102))
        self.assertLessEqual(len(channel_slug(name, 101)), 100)

    def test_game_search_prefers_title_match(self):
        exact = {"name": "Egg Quest", "playerCount": 5}
        popular = {"name": "Other Egg Game", "playerCount": 50000}
        self.assertGreater(_rank_game(exact, "egg quest"),
                           _rank_game(popular, "egg quest"))

    def test_provider_chain_uses_all_configured_sources(self):
        pipe = Pipeline(Config(freebuff_key="a", perplexity_key="b", gemini_key="c"))
        self.assertEqual([client.name for client in pipe.llm.clients],
                         ["freebuff", "perplexity", "gemini"])

    def test_old_load_marker_does_not_count(self):
        previous = ["Example loaded"]
        self.assertEqual(_new_lines(previous, previous), [])
        self.assertEqual(_loaded_marker(_new_lines(previous, previous), GameRef(1, name="Example")), "")

    async def test_feature_source_search_is_bounded(self):
        class SourceBridge:
            tool_defs = {"script-grep": {"inputSchema": {"properties": {
                "query": {"type": "string"}, "limit": {"type": "integer"}}}}}
            calls = []

            def find_tool(self, *names):
                return "script-grep"

            def arg_key(self, tool, *names):
                return "query"

            async def call_tool(self, name, args):
                self.calls.append(args)
                return "matching source"

        bridge = SourceBridge()
        result = await Pipeline(Config(), llm=object())._script_evidence(
            bridge, "auto collect eggs and buy upgrades")
        self.assertEqual(len(bridge.calls), 2)
        self.assertEqual(bridge.calls[0], {"query": "collect", "limit": 8})
        self.assertIn("matching source", result)

    async def test_client_selection_requires_matching_place(self):
        pipe = Pipeline(Config(), llm=object())
        bridge = FakeBridge("aaaabbbb-cccc | T @ Other (place=123 job=x)")
        warnings = []
        self.assertFalse(await pipe._select_client(bridge, GameRef(456), warnings))
        self.assertEqual(bridge.selected, [])
        self.assertIn("requested game", warnings[0])

    async def test_place_probe_requires_exact_match(self):
        pipe = Pipeline(Config(), llm=object())
        bridge = FakeBridge("", "10050")
        self.assertFalse(await pipe._probe_place(bridge, GameRef(10000)))
        bridge.probe = "10000"
        self.assertTrue(await pipe._probe_place(bridge, GameRef(10000)))
        bridge.probe = "unknown"
        self.assertFalse(await pipe._probe_place(bridge, GameRef(10000)))

    async def test_connector_escapes_token_and_rejects_host_code(self):
        pipe = Pipeline(Config(mcp_token='x"\nprint("oops")'), llm=object())
        script = await pipe.connector_script("example.com:16384")
        self.assertIn('x\\"\\nprint(\\"oops\\")', script)
        with self.assertRaises(ValueError):
            await pipe.connector_script('example.com/");print("oops")')


if __name__ == "__main__":
    unittest.main()
