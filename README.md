# Scriptbot

A Discord bot that generates Luau scripts for a selected Roblox place, gathers context from an MCP bridge, and optionally checks the generated script in a connected client.

## Setup

1. Use Python 3.11 or newer and install dependencies with `python -m pip install -r requirements.txt`.
2. Copy `.env.example` to `.env`. Set `DISCORD_TOKEN`, `MCP_URL`, and one LLM provider. For the CLI provider, install and authenticate `freebuff`, then set `FREEBUFF_BIN` to its executable path. Set `FREEBUFF_CLI=0` when using only an API provider.
3. Set `MCP_AUTH_TOKEN` on both sides of the bridge if the bridge requires authentication. Keep `.env` private.
4. Run `python bot.py --check`, then `python bot.py`.

Configure more than one provider to let the bot try the next one if an earlier provider fails. Supported keys are `FREEBUFF_API_KEY`, `PERPLEXITY_API_KEY`, `GEMINI_API_KEY`, and the optional `FALLBACK_API_KEY` with `FALLBACK_URL` and `FALLBACK_MODEL`.

Use `/menu` to generate into a game channel, or `/script` for a one-off result. `/connect` returns the bridge connector privately when invoked as a slash command. If a token is configured, the prefix command does not display the connector in a channel.

Invite the bot with application-command access and permissions to send messages and attach files. `/menu` also needs Manage Channels. Prefix commands additionally need the privileged Message Content intent enabled for the application in the Discord developer portal; slash commands are the simpler default. Generated files are posted as `.lua` attachments with their saved version number. A failed generation does not create an empty game channel.

## Verification

Live verification requires a bridge with `list-clients`, `set-active-client`, `get-data-by-code`, and an execute tool. The bot checks that the selected client's `game.PlaceId` exactly matches the requested place before it runs generated code. It then checks console errors, a later place probe, and a UI or load marker. These are smoke checks; they do not prove the script's behavior is correct. `/script verify:false` delivers an **Unverified** result.

One request triggers automatic context gathering, generation, structural checks, and up to three total attempts with live error feedback. The generated script is asked to rebind evidenced paths when the character or game state changes, avoiding edits for routine respawns or moved instances. Game-specific server mechanics that are absent from client evidence cannot be guaranteed or safely inferred; the bot reports those limits instead of inventing working controls. A matching client must be connected for live verification, and the bot stops before calling a model when it is not.

Generated code runs in the connected executor. Review the script and use a client you control. Keep the bridge token and the `/connect` response private.

## Tests

Run `python -m unittest discover -s tests -p 'test_core.py' -v` for fast safety checks. The existing integration scripts can be run with `python tests/test_mcp.py`, `python tests/test_llm.py`, `python tests/test_llm_cli.py`, and `python tests/test_verify.py`; the last takes about a minute. `python tests/test_ui.py` needs `discord.py` installed.

The system prompt lives in `llm.py`. Request framing and verification feedback live in `pipeline.py`. Run `python -m unittest discover -s tests -p 'test_prompts.py' -v` after editing either. These checks cover output extraction and retry behavior; a real game and model are still needed to assess generated feature quality.

The `deploy/` directory includes exploratory probes and deployment helpers. Review and adapt service paths and host settings before using them in another environment.
