
import asyncio
import logging
from os import getenv
from os.path import basename
from random import choice

import discord
from discord.ext import commands
from dotenv import load_dotenv
from pony.orm import db_session, select, commit

import steam
import util
import entities


# ---------------------> Logging setup


name = basename(__file__)[:-3]
log = logging.getLogger(name)


# ---------------------> Environment setup


load_dotenv()


# ---------------------> UI components

# TODO delete this code

"""

class SubscribeButton(discord.ui.Button):
    def __init__(self, steam_client: steam.Client, ctx: commands.Context, id: int,  *args, **kwargs) -> None:
        super().__init__(style=discord.ButtonStyle.green, label='Subscribe', emoji='📬' *args, **kwargs)
        self.steam_client = steam_client
        self.ctx = ctx
        self.id = id

    async def callback(self, interaction: discord.Interaction) -> None:

        # Only the original command author can interact with this button
        if interaction.user != self.ctx.author:
            return
        await interaction.response.defer()

        with db_session:
            db_user = entities.User.get(discord_id=self.ctx.author.id)
            db_pingGroup = entities.PingGroup.get(id=self.id)

            # Check if user is manually subscribed
            if db_pingGroup.id in db_user.whitelisted_pings:
                log.warning(f'User `{self.ctx.author.name}` ({self.ctx.author.id}) already subscribed to Ping group `{db_pingGroup.name}` ({db_pingGroup.id})')
                return

            # Check if user is automatically subscribed
            if db_pingGroup.steam_id and db_user.steam_id:
                steam_user = self.steam_client.getUser(db_user.steam_id)
                if db_pingGroup.steam_id in [game.id for game in steam_user.games]:
                    log.warning(f'User `{self.ctx.author.name}` ({self.ctx.author.id}) already subscribed to Ping group `{db_pingGroup.name}` ({db_pingGroup.id})')
                    return

            # Subscribe user to ping group
            db_user.blacklisted_pings.append(db_pingGroup.id)
            if db_pingGroup.id in db_user.blacklisted_pings:
                db_user.blacklisted_pings.remove(db_pingGroup.id)
            log.info(f'User `{self.ctx.author.name}` ({self.ctx.author.id}) subscribed to Ping group `{db_pingGroup.name}` ({db_pingGroup.id})')

class UnsubscribeButton(discord.ui.Button):
    def __init__(self, steam_client: steam.Client, ctx: commands.Context, id: int, *args, **kwargs) -> None:
        super().__init__(style=discord.ButtonStyle.red, label='Unsubscribe', emoji='📪', *args, **kwargs)
        self.steam_client = steam_client
        self.ctx = ctx
        self.id = id


    async def callback(self, interaction: discord.Interaction):

        # Only the original command author can interact with this button
        if interaction.user != self.ctx.author:
            return
        await interaction.response.defer()

        with db_session:
            db_user = entities.User.get(discord_id=self.ctx.author.id)
            db_pingGroup = entities.PingGroup.get(id=self.id)
            unsubscribed = False

            # Check if user is manually subscribed
            if db_pingGroup.id in db_user.whitelisted_pings:
                db_user.whitelisted_pings.remove(db_pingGroup.id)
                log.info(f'User `{self.ctx.author.name}` ({self.ctx.author.id}) unsubscribed from Ping group `{db_pingGroup.name}` ({db_pingGroup.id})')
                unsubscribed = True

            # Check if user is automatically subscribed
            if db_pingGroup.steam_id and db_user.steam_id:
                steam_user = self.steam_client.getUser(db_user.steam_id)
                if db_pingGroup.steam_id in [game.id for game in steam_user.games]:
                    db_user.blacklisted_pings.append(db_pingGroup.id)
                    log.info(f'User `{self.ctx.author.name}` ({self.ctx.author.id}) blacklisted Ping group `{db_pingGroup.name}` ({db_pingGroup.id})')
                    unsubscribed = True

            # Check if user was subscribed in the first place
            if unsubscribed:
                log.warning(f'User `{self.ctx.author.name}` ({self.ctx.author.id}) was never subscribed Ping group `{db_pingGroup.name}` ({db_pingGroup.id})')

class PingGroupMenu(discord.ui.View):
    def __init__(self, steam_client: steam.Client, ctx: commands.Context, id: int, subscribers: list[int], summary: util.Summary | None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.resolved = asyncio.Event()
        self.subscribers = subscribers
        self.summary = summary
        self.ctx = ctx
        self.id = id

        # Add (un)subscribe button
        if ctx.author.id in subscribers:
            self.add_item(UnsubscribeButton(steam_client, ctx, id))
        else:
            self.add_item(SubscribeButton(steam_client, ctx, id))
        self.children[1], self.children[2] = self.children[2], self.children[1]
    
    # Blocks until any button has been pressed, then disables all items
    async def await_resolution(self) -> None:
        await self.resolved.wait()
        self.disable_all_items()

    # Override Steam account
    @discord.ui.button(label='Ping', style=discord.ButtonStyle.blurple, emoji='📨')
    async def ping(self, _, interaction: discord.Interaction) -> None:

        # Only the original command author can interact with this view
        if interaction.user != self.ctx.author:
            return
        await interaction.response.defer()

        # Build message
        with db_session:
            pingGroup = entities.PingGroup.get(id=self.id)
            discord_users = [await self.ctx.bot.fetch_user(subscriber) for subscriber in self.subscribers]

            message = choice([
                f'Hear ye, hear ye! Thou art did request to attend the court of {pingGroup.name}.\n',
                f'Get in loser, we\'re going to do some {pingGroup.name}.\n',
                f'The definition of insanity is launching {pingGroup.name} and expecting success. Let\'s go insane.\n',
                f'Whats more important, working on your future or joining {pingGroup.name}? Exactly.\n',
                f'The ping extention wasted weeks of my life, so thank you for using it. Lets play {pingGroup.name}!\n',
                f'Vamos a la {pingGroup.name}, oh ohhhhhhhh yeah!\n',
                f'Inspiratie is voor de inspiratielozen. Something something {pingGroup.name}.\n'
            ]) + ' '.join([user.mention for user in discord_users])

        await self.ctx.reply(message)
    
    # Close menu
    @discord.ui.button(label='Exit', style=discord.ButtonStyle.gray, emoji='❌')
    async def exit(self, _, interaction: discord.Interaction) -> None:

        # Only the original command author can interact with this view
        if interaction.user != self.ctx.author:
            return
        await interaction.response.defer()
        self.resolved.set()

"""

class SelectPingGroup(discord.ui.Select):
    def __init__(self, parent: discord.ui.View, options: list[str], *args, **kwargs) -> None:
        super().__init__(
            placeholder='Select a Ping group', 
            options=[discord.SelectOption(label=option, value=option) for option in options], 
            *args, **kwargs
        )

        self.parent = parent
    
    async def callback(self, interaction: discord.Interaction) -> None:

         # Only authorised users can interact
        if interaction.user != self.parent.authorised_user:
            return

        await interaction.response.defer()
        self.parent.result = self.values[0]
        self.parent.disable_all_items()
        self.parent.resolved.set()

class VaguePingGroup(discord.ui.View):
    def __init__(self, authorised_user: discord.User, options: list[str], *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.authorised_user = authorised_user
        self.resolved = asyncio.Event()
        self.result = None

        # Create select menu
        select = SelectPingGroup(self, options)
        self.add_item(select)
    
    async def await_resolution(self) -> str | None:
        await self.resolved.wait()
        return self.result
    
    @discord.ui.button(label='Abort', style=discord.ButtonStyle.red, emoji='👶', row=1)
    async def abort(self, _, interaction: discord.Interaction) -> None:

        # Only authorised users can interact
        if interaction.user != self.authorised_user:
            return

        await interaction.response.defer()
        self.disable_all_items()
        self.resolved.set()

class VerifySteamOverride(discord.ui.View):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.responded = asyncio.Event()
        self.result = None

    async def await_response(self) -> None:
        await self.responded.wait()
        self.disable_all_items()

    @discord.ui.button(label='Override', style=discord.ButtonStyle.green, emoji='📝')
    async def override(self, _, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        self.result = True
        self.responded.set()

    @discord.ui.button(label='Abort', style=discord.ButtonStyle.red, emoji='👶')
    async def abort(self, _, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        self.result = False
        self.responded.set()   

# ---------------------> Ping cog


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Ping(bot))
    log.info(f'Extension has been created: {name}')

def teardown(bot: commands.Bot) -> None:
    log.info(f'Extension has been destroyed: {name}')

class Ping(commands.Cog, name = name, description = 'Better ping utility'):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.steam = steam.Client(getenv('STEAM_TOKEN'))

    def find_subscribers(self, ping_id: int) -> list[int]:
        # TODO maybe move find_subscribers inside ping command. currently thats the only reference
       
        with db_session:

            # Find explicit subscribers
            pingGroup = entities.PingGroup.get(id=ping_id)
            subscribers = list(select(db_user.discord_id for db_user in entities.User if pingGroup.id in db_user.whitelisted_pings))

            # Find implicit subscribers
            if pingGroup.steam_id:
                for db_user in entities.User.select(lambda db_user: db_user.steam_id):
                    if pingGroup.id not in db_user.blacklisted_pings and db_user.discord_id not in subscribers:
                        steam_user = self.steam.getUser(db_user.steam_id)
                        if pingGroup.steam_id in [game.id for game in steam_user.games]:
                            subscribers.append(db_user.discord_id)

        return subscribers

    async def update_pings(self, summary: util.Summary | None = None) -> None:
        # TODO fix the issue where it doesnt detect Metro Exodus for some reason
        
        with db_session:

            # Fetch new Steam data and update ping groups
            for db_user in entities.User.select(lambda db_user: db_user.steam_id):
                steam_user = self.steam.getUser(db_user.steam_id)

                # Check if Steam profile is private
                if steam_user.private:
                    log.warning(f'User `{ await self.bot.fetch_user(db_user.discord_id).name }` ({db_user.discord_id}) has their Steam library on private')
                    continue

                # Update ping groups
                new = 0
                for game in steam_user.games:
                    if not entities.PingGroup.exists(steam_id=game.id):
                        try:
                            game.unlazify()
                        except steam.errors.GameNotFound:
                            log.warning(f'No game with id ({game.id}) could be found in the Steam store')
                            continue

                        # Create new ping group
                        entities.PingGroup(name=game.name, steam_id=game.id)
                        log.info(f'Created Ping Group `{game.name}` ({game.id})')
                        new += 1

                if summary and new:
                    summary.set_field('New Ping Groups', f'Created {new} new Ping Group(s). For specifics, consult the logs.')


    # ---------------------> Commands


    @commands.group(name='ping', description='Better ping utility', invoke_without_command=True)
    @util.default_command(thesaurus={'q': 'quiet', 'v': 'verbose'})
    @util.summarized()
    async def ping(self, ctx: commands.Context, flags: list[str], params: list[str]) -> util.Summary:
        summary = util.Summary(ctx)
        dialog = util.Dialog(ctx)

        # Check params
        if len(params) < 1:
            log.error(f'No parameters given')
            summary.set_header('No parameters given')
            summary.set_field('ValueError', 'User provided no parameters, while command usage dictates `$ping [query] -[flags]`')
            await dialog.cleanup()
            return summary

        # Update pings
        if 'quiet' not in flags:
            await dialog.set('DoSsing the Steam API...')
        await self.update_pings(summary)

        # Search ping groups
        with db_session:
            options = select(pg.name for pg in entities.PingGroup)
            conclusive, results = util.fuzzy_search(options, ' '.join(params))

            if not results:
                log.warning('No ping groups found')
                summary.set_header('No ping groups found')
                await dialog.cleanup()
                return summary


            # Results were conclusive
            if conclusive:
                pingGroup = entities.PingGroup.get(name=results[0]['name'])
                log.debug(f'Search results were conclusive, found Ping group `{pingGroup.name}`')

            # Results weren't conclusive, send VaguePingGroup menu
            else:
                log.debug(f'Search results were inconclusive')
                view = VaguePingGroup(ctx.author, [result['name'] for result in results[:min(5, len(results))]])
                await dialog.set('Search results were inconclusive! Did you mean any of these Ping groups?', view=view)
                result = await view.await_resolution()

                # Parse result
                if not result:
                    log.warning(f'User `{ctx.author.name}` ({ctx.author.id}) aborted Ping command.')
                    summary.set_header('Ping command was aborted')
                    await dialog.cleanup()
                    return summary

                pingGroup = entities.PingGroup.get(name=result)
                log.debug(f'User chose `{pingGroup.name} from inconclusive search results')

            # Build and send ping message
            subscribers = self.find_subscribers(pingGroup.id)
            discord_users = [await self.bot.fetch_user(subscriber) for subscriber in subscribers]
            message = choice([
                f'Hear ye, hear ye! Thou art did request to attend the court of {pingGroup.name}.\n',
                f'Get in loser, we\'re going to do some {pingGroup.name}.\n',
                f'The definition of insanity is launching {pingGroup.name} and expecting success. Let\'s go insane.\n',
                f'Whats more important, working on your future or joining {pingGroup.name}? Exactly.\n',
                f'The ping extention wasted weeks of my life, so thank you for using it. Lets play {pingGroup.name}!\n',
                f'Vamos a la {pingGroup.name}, oh ohhhhhhhh yeah!\n',
                f'Inspiratie is voor de inspiratielozen. Something something {pingGroup.name}.\n'
            ]) + ' '.join([user.mention for user in discord_users])

            await dialog.add(message, view=None, mention_author=False)

        summary.send_on_return = False
        summary.set_header('Successfully sent out Ping')
        summary.set_field('Subscribers', '\n'.join([user.name for user in discord_users]))
        await dialog.cleanup()
        return summary

    @ping.command(name='setup', description='Ping setup')
    @util.default_command(thesaurus={'f': 'force', 'q': 'quiet', 'v': 'verbose'})
    @util.summarized()
    async def setup(self, ctx: commands.Context, flags: list[str], params: list[str]) -> util.Summary:
        summary = util.Summary(ctx)
        dialog = util.Dialog(ctx)

        # Check params
        if len(params) != 1:
            await dialog.cleanup()
            summary.set_header('Bad parameters Given')
            summary.set_field('ValueError', f'User provided the following parameters:\n\t`{" ".join(params)}`\n\nWhile command usage dictates `$ping setup [SteamID] -[flags]`')
            log.warn(f'Bad parameters given: `{" ".join(params)}`')

            return summary

        # Validate SteamID
        try:
            if 'quiet' not in flags:
                await dialog.set('DoSsing the Steam API...')
            steam_user = self.steam.getUser(id64=params[0])

        except steam.errors.UserNotFound:
            await dialog.cleanup()
            summary.set_header('Invalid SteamID')
            summary.set_field('ValueError', f'SteamID `{params[0]}` could not be found. Make sure you provide your Steam ID64, found in your profile url.')
            log.warn(f'Invalid SteamID: `{params[0]}`')

            return summary

        # Link Steam account
        with db_session:
            db_user = entities.User.get(discord_id=ctx.author.id)

            # Check if there already is a SteamID registered to this user
            if db_user.steam_id and 'force' not in flags:
                log.debug(f'User `{ctx.author.name}` ({ctx.author.id}) already has linked Steam account')
                
                # Prompt with override
                view = VerifySteamOverride()
                await dialog.set('You already have a linked Steam account. Do you want to override the old account, or keep it?', view=view)
                await view.await_response()

                # Cleanup
                if not view.result:
                    log.info(f'User `{ctx.author.name}` ({ctx.author.id}) aborted ping setup')
                    summary.set_field('Subscriptions', 'No subscriptions added.')
                    summary.set_header('User aborted Ping setup')
                    await dialog.cleanup()
                    return summary
                
                await dialog.set('DoSsing the Steam API...', view=None)
                 
            # Update log and summary
            if db_user.steam_id:
                summary.set_header(f'Sucessfully overrode Steam account to `{steam_user.name}` for user `{ctx.author.name}`')
                log.info(f'Succesfully overrode Steam account to `{steam_user.name}` ({steam_user.id64}) for user `{ctx.author.name}` ({ctx.author.id})')
            
            else:
                summary.set_header(f'Sucessfully linked Steam account `{steam_user.name}` to user `{ctx.author.name}`')
                log.info(f"Succesfully linked Steam account `{steam_user.name}` ({steam_user.id64}) to user `{ctx.author.name}` ({ctx.author.id})")

            if steam_user.private:
                summary.set_field('New Subscriptions', 'No subscriptions added, Steam profile is set to private. When you set your profile to public you will be automatically subscribed to all games in your library.')
            
            else:
                summary.set_field('New Subscriptions', 'Steam library added to subscribed Ping Groups!')

            # Link Steam account
            db_user.steam_id = steam_user.id64

        await self.update_pings(summary)
        await dialog.cleanup()            
        return summary

    @ping.command(name='add', description='Add a Ping group')
    @util.default_command(thesaurus={'q': 'quiet', 'v': 'verbose'})
    @util.summarized()
    async def add(self, ctx: commands.Context, flags: list[str], params: list[str]) -> util.Summary:
        summary = util.Summary(ctx)
        dialog = util.Dialog(ctx)

        # Check params
        if len(params) < 1:
            log.error(f'No parameters given')
            summary.set_header('No parameters given')
            summary.set_field('ValueError', 'User provided no parameters, while command usage dictates `$ping add [name] -[flags]`')
            await dialog.cleanup()
            return summary
        
        # Update pings
        if 'quiet' not in flags:
            await dialog.set('DoSsing the Steam API...')
        await self.update_pings(summary)

        # Search ping groups
        with db_session:
            options = select(pg.name for pg in entities.PingGroup)
            conclusive, results = util.fuzzy_search(options, ' '.join(params))

            # If conclusive, there is another pinggroup with a conflicting name
            if conclusive:
                log.warn(f'Failed to create Ping group by name of `{" ".join(params)}` due to conflicting Ping group `{results[0]["name"]}`')
                summary.set_header('Failed to create Ping group')
                summary.set_field('ConflictingNameError', f'There already is a similar Ping group with the name `{results[0]["name"]}`. If your new Ping group targets a different audience, try giving it a different name. Stupid.')
                await dialog.cleanup()
                return summary

            # Create new ping group
            pingGroup = entities.PingGroup(name=' '.join(params))
            commit()
            pingGroup = entities.PingGroup.get(name=' '.join(params))
            log.info(f'Created new ping group `{pingGroup.name}` ({pingGroup.id}) at the request of user `{ctx.author.name}` ({ctx.author.id})')
    
        summary.set_header(f'Successfully created Ping group `{pingGroup.name}`')
        await dialog.cleanup()
        return summary

    @ping.command(name='subscribe', description='Subscribe to a Ping group')