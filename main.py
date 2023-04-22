
import logging
from logging import config
from os import getenv

import discord
from discord.ext import commands
from dotenv import load_dotenv
from pony.orm import db_session

import util
from entities import User, db
from extensions.ping import PingSetup

# ---------------------> Logging setup

config.fileConfig('log.conf')
log = logging.getLogger('root')

# ---------------------> Environment setup

load_dotenv()

# ---------------------> Configure database

db.bind(provider='postgres', user=getenv('DB_USER'), password=getenv('DB_PASSWORD'),
        host=getenv('DB_HOST'), port=getenv('DB_PORT'), database=getenv('DB_NAME'))
db.generate_mapping(check_tables=True, create_tables=True)

# ---------------------> Discord setup

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='$', intents=intents)

@bot.event
async def on_ready() -> None:
    log.info(f'Succesful login as {bot.user}')

@bot.event
async def on_member_join(member: discord.User) -> None:
    class View(discord.ui.View):
        @discord.ui.button(label='Setup', style=discord.ButtonStyle.blurple, emoji='📬')
        async def ping_setup(self, button, interaction) -> None:
            await ctx.send(view=PingSetup(ctx.author)) # TODO add message and send to dms
            for child in self.children:
                child.disabled = True
            await interaction.response.send_modal(SteamSetup(member))

        @discord.ui.button(label='Skip', style=discord.ButtonStyle.gray, emoji='👉')
        async def skip_setup(self, button, interaction) -> None:
            for child in self.children:
                child.disabled = True
            await interaction.response.edit_message(view=self)

    # Find greet chanel
    channel = bot.get_channel(int(getenv('GREET_CHANNEL_ID')))
    if channel == None:
        log.error(f'Failed to load greet channel ({getenv("GREET_CHANNEL_ID")}). Aborting...')
        return

    # Check if new user is already known
    with db_session:
        if User.exists(user_id=member.id):
            log.info(f"New user `{member.name}` ({member.id}) already known")
            return
        User(user_id=member.id)
    
    # Send greetings
    await channel.send(f'Welcome {member.mention}, to {channel.guild.name}! Do you want to set up pings?', view=View())
    log.info(f'New user `{member.name}` ({member.id}) added to the database')

# ---------------------> Main

if __name__ == '__main__':
    for ext in util.yield_extensions(prefix_path=True):
        try:
            bot.load_extension(ext)
        except Exception as err:
            log.error(err)
        
    # TODO also add all users to database

    bot.run(getenv('DISCORD_TOKEN'))