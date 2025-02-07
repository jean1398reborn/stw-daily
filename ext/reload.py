import discord
import discord.ext.commands as ext

import stwutil as stw


# cog for the reloading related commands.
class Reload(ext.Cog):

    def __init__(self, client):
        self.client = client

    async def reload_command(self, ctx, extension, slash=False):
        try:
            self.client.reload_extension(f"ext.{extension}")
            embed_colour = self.client.colours["auth_white"]
            embed = discord.Embed(title=await stw.add_emoji_title(self.client, "Reload cog", "hard_drive"),
                                  description=f'\u200b\nReloaded cog: {extension}\n\u200b',
                                  color=embed_colour)
        except Exception as e:
            embed_colour = self.client.colours["error_red"]
            embed = discord.Embed(title=await stw.add_emoji_title(self.client, "Reload cog", "hard_drive"),
                                  description=f'\u200b\nFailed to reload cog: {extension}\n\u200b',
                                  color=embed_colour)
            embed.add_field(name="Error:", value=f"```{e}```", inline=False)

        embed = await stw.set_thumbnail(self.client, embed, "keycard")
        embed = await stw.add_requested_footer(ctx, embed)

        await stw.slash_send_embed(ctx, slash, embed)

    @ext.command(name='rlcg',
                 extras={'emoji': "hard_drive", "args": {'ext': 'The cog to reload'}},
                 brief="reloads cogs",
                 description="Reloads cogs to apply changes")
    async def rlcg(self, ctx, extension):
        await self.reload_command(ctx, extension)

    async def load_command(self, ctx, extension, slash=False):
        try:
            self.client.load_extension(f"ext.{extension}")
            embed_colour = self.client.colours["auth_white"]
            embed = discord.Embed(title=await stw.add_emoji_title(self.client, "Load cog", "hard_drive"),
                                  description=f'\u200b\nLoaded cog: {extension}\n\u200b',
                                  color=embed_colour)
        except Exception as e:
            embed_colour = self.client.colours["error_red"]
            embed = discord.Embed(title=await stw.add_emoji_title(self.client, "Load cog", "hard_drive"),
                                  description=f'\u200b\nFailed to load cog: {extension}\n\u200b',
                                  color=embed_colour)
            embed.add_field(name="Error:", value=f"```{e}```", inline=False)

        embed = await stw.set_thumbnail(self.client, embed, "keycard")
        embed = await stw.add_requested_footer(ctx, embed)

        await stw.slash_send_embed(ctx, slash, embed)

    @ext.command(name='lcg',
                 extras={'emoji': "hard_drive", "args": {'ext': 'The cog to load'}},
                 brief="loads cogs",
                 description="Loads cogs to apply changes")
    async def lcg(self, ctx, extension):
        await self.load_command(ctx, extension)


def setup(client):
    client.add_cog(Reload(client))
