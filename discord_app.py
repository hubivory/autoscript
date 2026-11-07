from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

import store
from config import Config
from pipeline import Pipeline, Result, VerificationFailed

LOG = logging.getLogger("scriptbot.discord")

PINK = 0xFF8FAB
GREEN = 0x7BD88F
RED = 0xE75480
FOOTER = "made with 💖"

MODEL_OPTIONS: list[tuple[str, str, str]] = [
    ("✨ Account default", "", ""),
    ("🚀 DeepSeek Flash Slow", "DeepSeek V4.1 Flash Slow", "slow"),
    ("⚡ DeepSeek Flash Fast", "DeepSeek V4.1 Flash Fast", "fast"),
    ("💫 Muse Spark", "Spark", "spark"),
    ("🌙 GPT Luna", "Luna", "luna"),
    ("📚 Claude Haiku", "Haiku", "haiku"),
    ("☀️ Solar Pro", "Solar Pro", "solar pro"),
    ("🌱 Solar Mini", "Solar Mini", "solar mini"),
    ("🌩️ Nemotron Lightning", "Nemotron", "nemotron"),
    ("👻 Glyph Cluster", "Glyph", "glyph"),
]

class ScriptBot(commands.Bot):
    def __init__(self, config: Config) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(
            command_prefix=config.command_prefix,
            intents=intents,
            allowed_mentions=discord.AllowedMentions.none(),
        )
        self.config = config
        self.pipeline = Pipeline(config)
        self.store = store.Store(config.data_dir)
        self.pending: dict[int, dict] = {}

    async def setup_hook(self) -> None:
        self.add_view(ChannelMenuView(self))
        if self.config.guild_ids:
            for gid in self.config.guild_ids:
                guild = discord.Object(id=gid)
                self.tree.copy_global_to(guild=guild)
                await self.tree.sync(guild=guild)
                LOG.info("synced commands to guild %s", gid)
        else:
            await self.tree.sync()
            LOG.info("synced global commands")

    async def on_ready(self) -> None:
        LOG.info("logged in as %s (%s)", self.user, getattr(self.user, "id", "?"))


def embed(title: str, description: str, color: int = PINK) -> discord.Embed:
    embed_obj = discord.Embed(title=title, description=description[:4000], color=color)
    embed_obj.set_footer(text=FOOTER)
    return embed_obj


def menu_embed(pending: dict) -> discord.Embed:
    game = discord.utils.escape_markdown(str(pending.get("game") or "_not set_"))
    feature = discord.utils.escape_markdown(str(pending.get("feature") or "_general utility_"))
    model = pending.get("model_label") or "✨ Account default"
    return embed(
        "🌸 Script Menu 🌸",
        "・゚✧ Pick a game and I'll build and load-check a Snowy script for it.\n\n"
        f"🎮 **Game:** {game}\n"
        f"✨ **Feature:** {feature}\n"
        f"🤖 **Model:** {model}\n\n"
        "① Tap **Set game** ② press **Generate** 💖",
    )


def result_embed(result: Result, kind: str) -> discord.Embed:
    badge = "✅ Load checked" if result.verified else "⚠️ Unverified"
    lines = [
        f"**Game:** {result.game.label()} (`{result.game.place_id}`)",
        f"**Run:** {kind} · attempt(s): {result.attempts}",
        f"**Provider:** {result.provider}",
    ]
    if result.model_actual:
        lines.append(f"**Model:** {result.model_actual}")
    if result.client_name:
        lines.append(f"**Client:** {result.client_name}")
    if result.warnings:
        lines.append("**Warnings:** " + "; ".join(result.warnings)[:500])
    if result.verification:
        lines.append("**Verification:**")
        lines.extend(f"· {line}"[:220] for line in result.verification[-8:])
    color = GREEN if result.verified else RED
    return embed(f"🌸 {badge} — {kind} 🌸", "\n".join(lines)[:4000], color)


def failure_embed(kind: str, log: list[str]) -> discord.Embed:
    lines = ["The startup check did not pass, so no script was delivered. 💔", ""]
    lines.extend(f"· {line}"[:220] for line in log[-12:])
    return embed(f"🌸 Failed — {kind} 🌸", "\n".join(lines)[:4000], RED)


async def post_script(target, result: Result, kind: str, version: int = 1) -> None:
    await target.send(
        embed=result_embed(result, kind),
        file=discord.File(
            _io_bytes(result.script), filename=f"snowy_{result.game.place_id}_v{version}.lua"
        ),
    )


async def _safe_edit(message, title: str, description: str) -> None:
    """Edit an in-channel progress message; never raises."""
    try:
        await message.edit(embed=embed(title, description[:4000]))
    except discord.HTTPException:
        LOG.warning("progress edit failed")


def _io_bytes(text: str):
    import io

    return io.BytesIO(text.encode("utf-8"))


class GameModal(discord.ui.Modal, title="🎮 Pick a game"):
    def __init__(self, bot: ScriptBot) -> None:
        super().__init__(timeout=300)
        self.bot = bot
        self.game_input = discord.ui.TextInput(
            label="Game link, place id, or name",
            placeholder="https://www.roblox.com/games/… or Break and Steal an Egg",
            required=True,
            max_length=300,
        )
        self.feature_input = discord.ui.TextInput(
            label="What should it do? (optional)",
            placeholder="auto farm eggs, auto buy, speed hub…",
            style=discord.TextStyle.paragraph,
            required=False,
            max_length=1000,
        )
        self.add_item(self.game_input)
        self.add_item(self.feature_input)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        pending = self.bot.pending.setdefault(interaction.user.id, {})
        pending["game"] = str(self.game_input.value).strip()
        pending["feature"] = str(self.feature_input.value or "").strip()
        await interaction.response.edit_message(embed=menu_embed(pending), view=MenuView(self.bot))


class ModelSelect(discord.ui.Select):
    def __init__(self, bot: ScriptBot) -> None:
        self.bot = bot
        options = [
            discord.SelectOption(label=label, value=value or "__default__")
            for label, value, _ in MODEL_OPTIONS
        ]
        super().__init__(
            placeholder="🤖 Choose a model…",
            options=options,
            custom_id="scriptbot:model",
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        pending = self.bot.pending.setdefault(interaction.user.id, {})
        value = self.values[0]
        if value == "__default__":
            pending["model_filter"] = ""
            pending["model_label"] = "✨ Account default"
        else:
            label = next(
                (label for label, val, _ in MODEL_OPTIONS if val == value), value
            )
            pending["model_filter"] = value
            pending["model_label"] = label
        await interaction.response.edit_message(embed=menu_embed(pending), view=MenuView(self.bot))


class MenuView(discord.ui.View):
    def __init__(self, bot: ScriptBot) -> None:
        super().__init__(timeout=600)
        self.bot = bot
        if bot.config.freebuff_cli:
            self.add_item(ModelSelect(bot))

    @discord.ui.button(label="🎮 Set game", style=discord.ButtonStyle.primary, custom_id="scriptbot:setgame")
    async def set_game(
        self, interaction: discord.Interaction, _: discord.ui.Button
    ) -> None:
        await interaction.response.send_modal(GameModal(self.bot))

    @discord.ui.button(label="✨ Generate", style=discord.ButtonStyle.success, custom_id="scriptbot:generate")
    async def generate(
        self, interaction: discord.Interaction, _: discord.ui.Button
    ) -> None:
        bot = self.bot
        pending = bot.pending.get(interaction.user.id, {})
        query = (pending.get("game") or "").strip()
        if not query:
            await interaction.response.send_message(
                embed=embed("🌸 Hold on 🌸", "Set a game first with **🎮 Set game** 💖"),
                ephemeral=True,
            )
            return
        feature = (pending.get("feature") or "").strip()
        model_filter = (pending.get("model_filter") or "").strip()
        await interaction.response.defer(ephemeral=True, thinking=True)
        follow = interaction.followup
        try:
            import aiohttp

            import roblox

            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=60)
            ) as http:
                ref = await roblox.resolve(http, query)
        except Exception as exc:
            await follow.send(
                embed=embed("🌸 Couldn't resolve that game 🌸", f"```{exc}```"[:2000], RED),
                ephemeral=True,
            )
            return
        guild = interaction.guild
        if guild is None:
            await follow.send(
                embed=embed("🌸 Server only 🌸", "Channel creation needs a server — run /menu in a server 💖", RED),
                ephemeral=True,
            )
            return
        status = await follow.send(
            embed=embed("💖 Working 💖", f"Building for `{ref.place_id}`…"),
            ephemeral=True,
            wait=True,
        )
        try:
            result = await bot.pipeline.generate(
                str(ref.place_id), feature, model=model_filter, verify=True,
                on_stage=_stage,
            )
        except VerificationFailed as exc:
            await status.edit(embed=failure_embed("generate", exc.log))
            await _safe_edit(prog, "🌸 Verification failed 🌸", "The script did not pass the live check. Log posted above.")
            return
        except Exception:
            LOG.exception("generation failed")
            await status.edit(
                embed=embed("🌸 Failed 🌸", "Generation failed. Check the bot logs for details.", RED)
            )
            await _safe_edit(prog, "🌸 Failed 🌸", "Generation failed. Check the bot logs for details.")
            return
        slug = store.channel_slug(ref.name, ref.place_id)
        channel = next(
            (candidate for candidate in guild.text_channels
             if (existing := bot.store.load_session(candidate.id))
             and existing.get("guild_id") == guild.id
             and existing.get("place_id") == ref.place_id),
            None,
        )
        try:
            if channel is None:
                channel = await guild.create_text_channel(
                    slug,
                    topic=f"🌸 {ref.label()} · place {ref.place_id} · scripts by Snowy menu 💖"[:1024],
                )
        except discord.Forbidden:
            await status.edit(
                embed=embed(
                    "🌸 Missing permission 🌸",
                    "I need **Manage Channels** to create the game channel.",
                    RED,
                ),
            )
            return
        except discord.HTTPException:
            LOG.exception("could not create game channel for %s", ref.place_id)
            await status.edit(embed=embed("🌸 Channel failed 🌸", "I could not create the game channel. Try again shortly.", RED))
            return
        session = bot.store.load_session(channel.id)
        if session is None or session.get("place_id") != ref.place_id:
            session = store.new_session(
                guild.id,
                channel.id,
                ref.name or ref.label(),
                ref.place_id,
                ref.universe_id,
                model_filter,
            )
            session["channel_name"] = channel.name
            bot.store.save_session(session)
        else:
            session["model_filter"] = model_filter
            bot.store.save_session(session)
        try:
            menu_message = await channel.send(
                embed=embed(
                    f"🌸 {ref.name or 'Game menu'} 🌸",
                    f"・゚✧ place `{ref.place_id}` · model **{pending.get('model_label') or '✨ Account default'}**\n"
                    "Pick what to do, cutie 💅",
                ),
                view=ChannelMenuView(bot),
            )
        except discord.HTTPException:
            LOG.exception("could not post game menu to channel %s", channel.id)
            await status.edit(embed=embed("🌸 Channel failed 🌸", "I could not post in the game channel. Check my Send Messages permission.", RED))
            return
        session["menu_message_id"] = menu_message.id
        bot.store.save_session(session)
        try:
            prog = await channel.send(embed=embed("💖 Working 💖", "Warming up…"))
        except discord.HTTPException:
            LOG.exception("could not post progress to channel %s", channel.id)
            await status.edit(embed=embed("🌸 Channel failed 🌸", "I could not post progress in the game channel. Check my Send Messages permission.", RED))
            return

        async def _stage(text: str) -> None:
            await _safe_edit(prog, "💖 Working 💖", text)

        session = bot.store.append_turn(
            channel.id,
            "generate",
            feature or query,
            result.script,
            result.verified,
            result.attempts,
            result.provider,
            result.model_actual,
            result.verification,
        )
        bot.store.log_history(
            {
                "guild": guild.id,
                "channel": channel.id,
                "game": result.game.name,
                "place": result.game.place_id,
                "kind": "generate",
                "model": result.model_actual,
                "provider": result.provider,
                "verified": result.verified,
                "attempts": result.attempts,
            }
        )
        try:
            await post_script(channel, result, "generate", session["current_version"])
        except discord.HTTPException:
            LOG.exception("could not deliver generated script to channel %s", channel.id)
            await status.edit(embed=embed("🌸 Delivery failed 🌸", "I saved the script, but could not post the file. Check my channel permissions.", RED))
            await _safe_edit(prog, "🌸 Delivery failed 🌸", "I saved the script, but could not post the file. Check my channel permissions.")
            return
        await status.edit(embed=embed("💖 Done 💖", f"Posted in {channel.mention} ✨"))
        await _safe_edit(prog, "💖 Done 💖", f"Script v{session['current_version']} posted below ✨")


class DetailModal(discord.ui.Modal):
    def __init__(self, bot: ScriptBot, kind: str, title: str, placeholder: str) -> None:
        super().__init__(title=title, timeout=300)
        self.bot = bot
        self.kind = kind
        self.details = discord.ui.TextInput(
            label="Details",
            placeholder=placeholder,
            style=discord.TextStyle.paragraph,
            required=kind != "rewrite",
            max_length=2000,
        )
        self.add_item(self.details)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        bot = self.bot
        channel = interaction.channel
        if channel is None:
            await interaction.response.send_message(
                embed=embed("🌸 Oops 🌸", "Run this inside a game channel 💖", RED),
                ephemeral=True,
            )
            return
        session = bot.store.load_session(channel.id)
        if session is None:
            await interaction.response.send_message(
                embed=embed("🌸 No session here 🌸", "Use /menu to start one 💖", RED),
                ephemeral=True,
            )
            return
        await interaction.response.defer(thinking=True)
        try:
            prog = await channel.send(embed=embed("💖 Working 💖", f"{self.kind} in progress…"))
        except (discord.HTTPException, AttributeError):
            LOG.warning("progress post failed in channel %s", getattr(channel, "id", "?"))
            prog = None

        async def _stage(text: str) -> None:
            if prog is not None:
                await _safe_edit(prog, "💖 Working 💖", text)

        current = bot.store.get_script(channel.id)
        if not current:
            await interaction.followup.send(
                embed=embed("🌸 Nothing to work with 🌸", "Generate a script first 💖", RED)
            )
            return
        import roblox

        ref = roblox.GameRef(
            place_id=int(session.get("place_id") or 0),
            universe_id=session.get("universe_id"),
            name=str(session.get("game") or ""),
        )
        model_filter = str(session.get("model_filter") or "")
        details = str(self.details.value or "").strip()
        try:
            if self.kind == "fix":
                result = await bot.pipeline.fix(ref, current, details, model=model_filter, on_stage=_stage)
            elif self.kind == "update":
                result = await bot.pipeline.update(ref, current, details, model=model_filter, on_stage=_stage)
            else:
                original = next(
                    (str(turn.get("request") or "") for turn in session.get("turns", [])
                     if turn.get("kind") == "generate"),
                    "",
                )
                fresh = details or original or "a useful script for this game"
                result = await bot.pipeline.generate(
                    str(ref.place_id), fresh, model=model_filter, verify=True,
                    on_stage=_stage,
                )
        except VerificationFailed as exc:
            if prog is not None:
                await _safe_edit(prog, "🌸 Verification failed 🌸", "The script did not pass the live check.")
            await interaction.followup.send(embed=failure_embed(self.kind, exc.log))
            return
        except Exception:
            LOG.exception("%s failed", self.kind)
            if prog is not None:
                await _safe_edit(prog, "🌸 Failed 🌸", "The request failed. Check the bot logs for details.")
            await interaction.followup.send(
                embed=embed("🌸 Failed 🌸", "The request failed. Check the bot logs for details.", RED)
            )
            return
        session = bot.store.append_turn(
            channel.id,
            self.kind,
            details,
            result.script,
            result.verified,
            result.attempts,
            result.provider,
            result.model_actual,
            result.verification,
        )
        bot.store.log_history(
            {
                "guild": getattr(channel, "guild", None) and channel.guild.id,
                "channel": channel.id,
                "game": result.game.name,
                "place": result.game.place_id,
                "kind": self.kind,
                "model": result.model_actual,
                "provider": result.provider,
                "verified": result.verified,
                "attempts": result.attempts,
            }
        )
        try:
            await post_script(interaction.followup, result, self.kind, session["current_version"])
        except discord.HTTPException:
            LOG.exception("could not deliver %s script in channel %s", self.kind, channel.id)
            await interaction.followup.send(embed=embed(
                "🌸 Delivery failed 🌸", "The version was saved, but I could not attach the file here.", RED
            ))
            return
        if prog is not None:
            await _safe_edit(prog, "💖 Done 💖", f"{self.kind} v{session['current_version']} posted below ✨")


class ChannelMenuView(discord.ui.View):
    def __init__(self, bot: ScriptBot) -> None:
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="🛠️ Fix", style=discord.ButtonStyle.primary, custom_id="scriptbot:fix")
    async def fix(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await interaction.response.send_modal(
            DetailModal(
                self.bot,
                "fix",
                "🛠️ Fix it, bestie",
                "What's broken? Paste the error or describe it…",
            )
        )

    @discord.ui.button(label="🔄 Update", style=discord.ButtonStyle.secondary, custom_id="scriptbot:update")
    async def update(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await interaction.response.send_modal(
            DetailModal(
                self.bot,
                "update",
                "🔄 Update time",
                "What should change or be added?…",
            )
        )

    @discord.ui.button(label="✏️ Rewrite", style=discord.ButtonStyle.secondary, custom_id="scriptbot:rewrite")
    async def rewrite(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await interaction.response.send_modal(
            DetailModal(
                self.bot,
                "rewrite",
                "✏️ Fresh start",
                "New direction? Leave blank to rebuild as-is…",
            )
        )

    @discord.ui.button(label="✅ Re-verify", style=discord.ButtonStyle.success, custom_id="scriptbot:reverify")
    async def reverify(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        bot = self.bot
        channel = interaction.channel
        if channel is None:
            return
        session = bot.store.load_session(channel.id)
        if session is None:
            await interaction.response.send_message(
                embed=embed("🌸 No session here 🌸", "Use /menu to start one 💖", RED),
                ephemeral=True,
            )
            return
        await interaction.response.defer(thinking=True)
        try:
            prog = await channel.send(embed=embed("💖 Working 💖", "Re-verifying…"))
        except (discord.HTTPException, AttributeError):
            LOG.warning("progress post failed in channel %s", getattr(channel, "id", "?"))
            prog = None

        async def _stage(text: str) -> None:
            if prog is not None:
                await _safe_edit(prog, "💖 Working 💖", text)

        import roblox

        ref = roblox.GameRef(
            place_id=int(session.get("place_id") or 0),
            universe_id=session.get("universe_id"),
            name=str(session.get("game") or ""),
        )
        current = bot.store.get_script(channel.id)
        if not current:
            await interaction.followup.send(
                embed=embed("🌸 Nothing to verify 🌸", "Generate a script first 💖", RED)
            )
            return
        try:
            result = await bot.pipeline.reverify(ref, current, on_stage=_stage)
        except VerificationFailed as exc:
            if prog is not None:
                await _safe_edit(prog, "🌸 Verification failed 🌸", "The script did not pass the live check.")
            await interaction.followup.send(embed=failure_embed("re-verify", exc.log))
            return
        except Exception:
            LOG.exception("re-verification failed")
            if prog is not None:
                await _safe_edit(prog, "🌸 Failed 🌸", "The check failed. Check the bot logs for details.")
            await interaction.followup.send(
                embed=embed("🌸 Failed 🌸", "The check failed. Check the bot logs for details.", RED)
            )
            return
        try:
            await post_script(interaction.followup, result, "re-verify", int(session.get("current_version") or 1))
        except discord.HTTPException:
            LOG.exception("could not deliver re-verified script in channel %s", channel.id)
            await interaction.followup.send(embed=embed(
                "🌸 Delivery failed 🌸", "I could not attach the script file here.", RED
            ))
            return
        if prog is not None:
            await _safe_edit(prog, "💖 Done 💖", "Re-verified and posted below ✨")

    @discord.ui.button(label="ℹ️ Info", style=discord.ButtonStyle.secondary, custom_id="scriptbot:info")
    async def info(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        channel = interaction.channel
        session = self.bot.store.load_session(channel.id) if channel else None
        if not session:
            await interaction.response.send_message(
                embed=embed("🌸 No session here 🌸", "Use /menu to start one 💖", RED),
                ephemeral=True,
            )
            return
        turns = session.get("turns", [])
        lines = [
            f"🎮 **Game:** {session.get('game')} (`{session.get('place_id')}`)",
            f"🤖 **Model:** {session.get('model_actual') or session.get('model_filter') or 'default'}",
            f"📦 **Versions:** {session.get('current_version', 0)}",
        ]
        for turn in turns[-8:]:
            mark = "✅" if turn.get("verified") else "❌"
            lines.append(
                f"{mark} v{turn.get('n')} · {turn.get('kind')} · "
                f"{str(turn.get('request') or '')[:80]}"
            )
        await interaction.response.send_message(
            embed=embed("🌸 Session memory 🌸", "\n".join(lines)[:4000]), ephemeral=True
        )


def build_bot(config: Config) -> ScriptBot:
    bot = ScriptBot(config)

    @bot.hybrid_command(
        name="menu",
        description="🌸 Open the script menu: pick a game + model, generate into its own channel.",
    )
    async def menu(ctx: commands.Context) -> None:
        pending = bot.pending.setdefault(ctx.author.id, {})
        # Public on purpose: everyone in the channel shares the menu.
        await ctx.send(embed=menu_embed(pending), view=MenuView(bot), ephemeral=False)

    @bot.hybrid_command(
        name="script",
        description="Generate a verified Snowy Luau script for a Roblox game.",
    )
    @app_commands.describe(
        query="Roblox game link, place id, or game name",
        feature="What the script should do (optional)",
        model="Model filter, e.g. Opus, Sonnet, DeepSeek (optional)",
        verify="Verify live before delivery (default true)",
    )
    async def script(
        ctx: commands.Context,
        query: str,
        feature: str = "",
        model: str = "",
        verify: bool = True,
    ) -> None:
        await ctx.defer(thinking=True)
        status = await ctx.send(embed=embed("💖 Working 💖", f"Resolving `{query}`…"))
        try:
            result = await bot.pipeline.generate(
                query, feature, model=model, verify=verify
            )
        except VerificationFailed as exc:
            await status.edit(embed=failure_embed("generate", exc.log))
            return
        except Exception:
            LOG.exception("generation failed")
            await status.edit(
                embed=embed("🌸 Failed 🌸", "Generation failed. Check the bot logs for details.", RED)
            )
            return
        bot.store.log_history(
            {
                "guild": ctx.guild.id if ctx.guild else None,
                "channel": ctx.channel.id if ctx.channel else None,
                "game": result.game.name,
                "place": result.game.place_id,
                "kind": "generate",
                "model": result.model_actual,
                "provider": result.provider,
                "verified": result.verified,
                "attempts": result.attempts,
            }
        )
        try:
            await post_script(ctx, result, "generate")
        except discord.HTTPException:
            LOG.exception("could not deliver one-off script")
            await status.edit(embed=embed("🌸 Delivery failed 🌸", "I could not post the script file here. Check my attachment permissions.", RED))
            return
        await status.edit(embed=embed("💖 Done 💖", "Script file posted below. ✨"))

    @bot.hybrid_command(name="mcpstatus", description="Check the Delta MCP bridge status.")
    async def mcpstatus(ctx: commands.Context) -> None:
        await ctx.defer(thinking=True)
        text = await bot.pipeline.status()
        await ctx.send(embed=embed("🔌 MCP status", f"```{text[:1900]}```"))

    @bot.hybrid_command(
        name="connect",
        description="Get the loadstring that connects an executor to this bridge.",
    )
    @app_commands.describe(
        host="Public host:port the phone should reach, e.g. 1.2.3.4:16384"
    )
    async def connect(ctx: commands.Context, host: str = "") -> None:
        await ctx.defer(thinking=True)
        if bot.config.mcp_token and not ctx.interaction:
            await ctx.send(embed=embed(
                "🔑 Private connection", "Use the /connect slash command to receive the token privately."
            ))
            return
        try:
            text = await bot.pipeline.connector_script(host)
        except Exception:
            LOG.exception("connector command failed")
            await ctx.send(
                embed=embed("Connect failed", "Check the host setting and bot logs.", RED)
            )
            return
        target = (
            ctx.send(embed=embed("🔑 Connect your executor (private)", f"```lua\n{text[:3900]}\n```"), ephemeral=True)
            if ctx.interaction
            else ctx.send(embed=embed("🔑 Connect your executor", f"```lua\n{text[:3900]}\n```"))
        )
        await target

    return bot


