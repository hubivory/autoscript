import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import Config
from llm import SYSTEM_PROMPT, extract_lua
from pipeline import Pipeline, VerificationFailed, _script_issues
from roblox import GameRef

SCRIPT = '''--// Snowy - Example
local url = "https://raw.githubusercontent.com/0x1s2s/Snowy-Ui-Library/refs/heads/main/SnowyUi"
local Library = loadstring(game:HttpGet(url))()
local window = Library:Window({ Title = "Snowy Studios", Subtitle = "Example" })
window:Tab({ Name = "UI Settings" })
getgenv().SnowyStudiosUnload = function() Library:Unload() end
print("Example loaded")
'''


class FakeLLM:
    last_provider = "fake"
    last_model_actual = ""

    def __init__(self, replies):
        self.replies = iter(replies)
        self.histories = []

    async def chat(self, history, **kwargs):
        self.histories.append(history)
        return next(self.replies)


class PromptTests(unittest.IsolatedAsyncioTestCase):
    def test_prompt_does_not_claim_model_verified_script(self):
        self.assertIn("Never claim you ran tests", SYSTEM_PROMPT)
        self.assertLess(len(SYSTEM_PROMPT), 6000)
        self.assertEqual(extract_lua("Here is a script, trust me."), "")
        self.assertEqual(extract_lua("```lua\nprint('ok')\n```\nNotes"), "print('ok')")
        self.assertEqual(_script_issues(SCRIPT), [])
        self.assertIn("Snowy window is missing", _script_issues("print('ok')"))

    async def test_missing_client_fails_before_model_call(self):
        llm = FakeLLM(["```lua\n" + SCRIPT + "\n```"])
        pipe = Pipeline(Config(), llm)
        with patch("roblox.resolve", new=AsyncMock(return_value=GameRef(123))), patch.object(
            pipe, "_gather", new=AsyncMock(return_value=("no client", ""))
        ):
            with self.assertRaises(VerificationFailed):
                await pipe.generate("Example", verify=True)
        self.assertEqual(llm.histories, [])

    async def test_empty_code_retry_is_actionable(self):
        llm = FakeLLM(["I cannot write it yet.", "```lua\n" + SCRIPT + "\n```"])
        pipe = Pipeline(Config(), llm)
        ref = GameRef(place_id=123, name="Example")
        with patch("roblox.resolve", new=AsyncMock(return_value=ref)), patch.object(
            pipe, "_gather", new=AsyncMock(return_value=("no client", ""))
        ):
            result = await pipe.generate("Example", "show a status", verify=False)
        self.assertEqual(result.attempts, 2)
        self.assertFalse(result.verified)
        self.assertIn("complete Luau file", llm.histories[1][-1]["content"])
        self.assertIn("<observations>", llm.histories[0][1]["content"])

    async def test_failure_feedback_preserves_scope(self):
        pipe = Pipeline(Config(), FakeLLM([]))
        feedback = pipe._fix_prompt(["console error at line 12"])
        self.assertIn("preserving the requested", feedback)
        self.assertIn("Do not claim the next run passed", feedback)
        self.assertIn("<diagnostics>", feedback)


if __name__ == "__main__":
    unittest.main()
