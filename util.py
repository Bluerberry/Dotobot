
import re as regex
from glob import iglob
from os.path import join

import discord
from discord.ext import commands

# Wraps around commands to split args into flags and params.
#  - func MUST follow async (self, ctx, flags, params) -> Any
#  - decorator should be placed below @bot.command() decorator

def extract_flags():
    def wrapper(func):
        async def wrapped(self, ctx, *args, **kwargs):
            flags  = []
            params = []

            for arg in list(args):
                if arg.startswith('--'):
                    flags.append(arg[2:])
                else:
                    params.append(arg)

            return await func(self, ctx, flags, params)
        return wrapped
    return wrapper

# Yields all extension files in path.
#   - path contains path to extensions                      default is 'extensions'
#   - prefix_path toggles prefixing with extension path     default is False
#   - recursive toggles recursive search                    default is True

def yield_extensions(path: str = 'extensions', prefix_path: bool = False, recursive: bool = True):
    path = join(path, '**\\*.py' if recursive else '*.py')             # Build path dependent on requirements
    for file in iglob(path, recursive = recursive):                    # Use iglob to match all python files
        components = regex.findall(r'\w+', file)[:-1]                  # Split into components and trim extension
        yield '.'.join(components) if prefix_path else components[-1]  # Either return import path or extension name

# Finds extension in path, returns full extension path if found
#   - extension contains extension to search for
#   - path contains path to extensions                      default is 'extensions'
#   - recursive toggles recursive search                    default is True

def extension_path(extension: str, path: str = 'extensions', recursive: bool = True) -> str:
    path = join(path, '**' if recursive else '', f'{extension_name(extension)}.py')  # Build path dependent on requirement
    for file in iglob(path, recursive = recursive):                                  # Use iglob to match all python files
        components = regex.findall(r'\w+', file)[:-1]                                # Split into components and trim extension
        return '.'.join(components)                                                  # Return full extension path
    return extension                                                                 # If not found return extensio

# Returns extension name from extension path
#   - extension_path contains path to extension with `.` seperation

def extension_name(extension_path: str) -> str:
    return extension_path.split('.')[-1]

# Returns default, empty embed.
#   - title & description are header strings                default is empty
#   - author toggles author                                 default is false
#   - footer toggles footer                                 default is true
#   - color loops through rainbow color palette             default is red

import discord
from discord.ext import commands

def default_embed(bot: commands.Bot, title: str = '', description: str = '', author: bool = False, footer: bool = True, color: int = 0) -> discord.Embed:
    palette = [
        discord.Colour.from_rgb(255, 89,  94 ),
        discord.Colour.from_rgb(255, 202, 58 ),
        discord.Colour.from_rgb(138, 201, 38 ),
        discord.Colour.from_rgb(25,  130, 196),
        discord.Colour.from_rgb(106, 76,  147)
    ]
    
    embed = discord.Embed(
        title = title,
        description = description,
        color = palette[color % 5]
    )

    if author:
        embed.set_author(name=bot.user.name) # TODO maybe add an icon?
    if footer:
        embed.set_footer(text=f'Powered by {bot.user.name}')

    return embed