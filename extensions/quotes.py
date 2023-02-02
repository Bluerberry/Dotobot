import logging
import re

from dataclasses import dataclass
from entities import Quote
from os.path import basename
from pony.orm import db_session, max as pony_max, select
from pony.orm.core import Query
import discord
from discord import Colour
from discord.ext import commands

# ---------------------> Logging setup

name = basename(__file__)[:-2]
log = logging.getLogger(name)


# ---------------------> Example cog

def setup(bot: commands.Bot) -> None:
    bot.add_cog(Quotes(bot))
    log.info(f'Extension has been created: {name}')


def teardown(_: commands.Bot) -> None:
    log.info(f'Extension has been destroyed: {name}')


def split_quote(quote: str) -> tuple[str, str]:
    REGEX = r'["“](.*)["”] ?- ?(.*)'
    match = re.search(REGEX, quote)
    return match.group(1), match.group(2)


class Quotes(commands.Cog, name=name, description='Manages the quotes'):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @dataclass
    class QuoteBlock:
        message: str
        start_value: int
        end_value: int

    async def mass_quote(self, ctx: commands.Context, quotes: Query):
        if quotes is None or len(quotes) == 0:
            return await ctx.send(
                embed=discord.Embed(title="No quotes could be found",
                                    description="Try a different search term or submit your own using !q add",
                                    color=Colour.from_rgb(255, 0, 0)))

        starting_id = previous_id = quotes[:1][0].quote_id
        quote_blocks = []
        msg = ''

        for quote in quotes:
            next_quote = str(quote) + '\n'
            # prevent overflow, subheader can be no longer than 1000 chars
            if len(msg) + len(next_quote) >= 975:
                quote_blocks.append(self.QuoteBlock(message=msg, start_value=starting_id, end_value=previous_id))
                msg, starting_id = '', quote.quote_id
            msg, previous_id = msg + next_quote, quote.quote_id

        quote_blocks.append(self.QuoteBlock(message=msg, start_value=starting_id, end_value=previous_id))
        await self.mass_quote_embed(ctx, quote_blocks)

    async def mass_quote_embed(self, ctx: commands.Context, quote_blocks: list[QuoteBlock]) -> None:
        colours = [Colour.from_rgb(255, 0, 0), Colour.orange(), Colour.gold(), Colour.green(), Colour.blue(),
                   Colour.dark_blue(), Colour.purple()]
        embed = discord.Embed(title="Quotes", colour=colours[0])

        for index, quote_block in enumerate(quote_blocks):
            if index % 6 == 0 and index != 0:
                embed.set_footer(text=f"Powered by {self.bot.user.name}")
                await ctx.send(embed=embed)
                embed = discord.Embed(title="Quotes", colour=colours[(index // 6) % len(colours)])
            embed.add_field(name=f"Quotes {quote_block.start_value} : {quote_block.end_value}",
                            value=quote_block.message,
                            inline=False)
        embed.set_footer(text=f"Powered by {self.bot.user.name}")

        await ctx.send(embed=embed)

    @commands.group(aliases=['quote'], brief='Subgroup for quote functionality',
                    description='Subgroup for quote functionality. Use !help q')
    async def q(self, ctx: commands.Context) -> None:
        if ctx.invoked_subcommand is None:
            log.info(f'User {ctx.author.name} has passed an invalid quote subcommand: "{ctx.message.content}"')
            # run command as if it was a !q

    @q.command(brief='Add a quote', description='Add a quote to the database', usage='"[quote]" - [author]')
    async def add(self, ctx: commands.Context, *, args=None) -> None:
        guild_id = str(ctx.guild.id)
        quote_string, author = split_quote(args)

        with db_session:
            max_in_table = pony_max(quote.quote_id for quote in Quote if quote.guild_id == guild_id)
            logging.info(max_in_table)
            nextid = 0 if max_in_table is None else max_in_table + 1
            Quote(quote_id=nextid, guild_id=guild_id, quote=quote_string, author=author)

        log.info(f"A quote has been added; {nextid}: \"{quote_string}\" - {author}")
        await ctx.send(f'Quote added. Assigned ID: {nextid}')

    @q.command(brief='Return all quotes', description='Return all quotes', usage='')
    async def all(self, ctx: commands.Context) -> None:
        with db_session:
            quotes = select(quote for quote in Quote if quote.guild_id == ctx.guild.id).order_by(Quote.quote_id)
            await self.mass_quote(ctx, quotes)
