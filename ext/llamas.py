"""
STW Daily Discord bot Copyright 2022 by the STW Daily team.
Please do not skid our hard work.
https://github.com/dippyshere/stw-daily

This file is the cog for the homebase command. renames homebase / displays current name + renders banner
"""

import discord
import discord.ext.commands as ext
from discord import Option, SelectOption
import orjson

import stwutil as stw


class LlamasView(discord.ui.View):
    """
    The view for the llama command.
    """

    def __init__(self, ctx, client, message, author, llama_store, free_llama, preroll_data, llama_options):
        super().__init__()
        self.ctx = ctx
        self.client = client
        self.message = message
        self.author = author
        self.llama_store = llama_store
        self.free_llama = free_llama
        self.preroll_data = preroll_data
        self.children[0].options = llama_options

    async def llama_purchase_embed(self, ctx, offer_id):
        """
        Creates an embed for the llama purchase command.

        Args:
            ctx: The context of the command.
            offer_id: The offer id of the llama to be purchased.

        Returns:
            The embed with the llama purchase
        """
        if offer_id == "back":
            self.children[0].options = await self.llamas.select_options_llamas(self.llama_store)
            return await self.llamas.llama_embed(ctx, self.free_llama, self.llama_store, self.preroll_data)
        else:
            self.children[0].options = await self.llamas.select_options_llamas(self.llama_store, True)
        embed = discord.Embed(
            title=await stw.add_emoji_title(self.client, "Store", "llama"),
            description=f"\u200b\n",
            colour=self.client.colours["generic_blue"])
        for entry in self.llama_store["catalogEntries"]:
            if entry["offerId"] == offer_id:
                llama_datatable = await stw.get_llama_datatable(self.client, entry['displayAssetPath'].split('/Game/Items/CardPacks/')[-1].split('.')[0])
                embed.description = f"\u200b\n{llama_datatable[2]}{llama_datatable[3]} **{llama_datatable[0]}**\n"
                embed.description += f"Price: {'~~' + str(entry['prices'][0]['regularPrice']) + '~~ ' if entry['prices'][0]['regularPrice'] != entry['prices'][0]['finalPrice'] else ''}**{entry['prices'][0]['finalPrice']:,}** {stw.get_item_icon_emoji(self.client, entry['prices'][0]['currencySubType'])}\n"  # TODO: make this sale_sticker_store
                for attr, val in self.preroll_data.items():
                    if offer_id == val["attributes"]["offerId"]:
                        embed.description += "Contents: " + stw.llama_contents_render(self.client,
                                                                                      val["attributes"]["items"])
                        break
                embed.description += f"\n*{llama_datatable[1]}*\n"
                break
        embed.description += f"\u200b\n"
        embed.description = stw.truncate(embed.description, 3999)
        embed = await stw.set_thumbnail(self.client, embed, "meme")
        embed = await stw.add_requested_footer(ctx, embed)
        return embed

    async def interaction_check(self, interaction):
        """
        Checks if the interaction is from the author of the command.

        Args:
            interaction: The interaction to check.

        Returns:
            True if the interaction is from the author of the command, False otherwise.
        """
        return await stw.view_interaction_check(self, interaction, "llamas")

    @discord.ui.select(
        placeholder="Choose a Llama to purchase",
        options=[],
    )
    async def selected_option(self, select, interaction):
        """
        Called when a help page is selected.

        Args:
            select: The select menu that was used.
            interaction: The interaction that was used.
        """
        embed = await self.llama_purchase_embed(self.ctx, select.values[0])
        await interaction.response.edit_message(embed=embed, view=self)


# ok i have no clue how sets work in python ok now i do prepare for your cpu to explode please explode already smhhh nya hi
class Llamas(ext.Cog):
    """
    Cog for the llama command
    """

    def __init__(self, client):
        self.client = client
        self.emojis = client.config["emojis"]

    async def check_errors(self, ctx, public_json_response, auth_info, final_embeds):
        """
        Checks for errors in the public_json_response and edits the original message if an error is found.

        Args:
            ctx: The context of the command.
            public_json_response: The json response from the public API.
            auth_info: The auth_info tuple from get_or_create_auth_session.
            final_embeds: The list of embeds to be edited.

        Returns:
            True if an error is found, False otherwise.
        """
        try:
            # general error
            error_code = public_json_response["errorCode"]
            support_url = self.client.config["support_url"]
            acc_name = auth_info[1]["account_name"]
            embed = await stw.post_error_possibilities(ctx, self.client, "llamas", acc_name, error_code, support_url)
            final_embeds.append(embed)
            await stw.slash_edit_original(ctx, auth_info[0], final_embeds)
            return True
        except KeyError:
            # no error
            return False

    async def select_options_llamas(self, llama_store, return_visible=False):
        """
        Creates the options for the select menu for the llamas command.

        Args:
            llama_store: The llama store data.
            return_visible: Whether the return value should be the visible options or the hidden options.

        Returns:
            The options for the select menu.
        """
        options = []
        if return_visible:
            options.append(SelectOption(label="Return", value="back", emoji=self.emojis["left_arrow"],
                                        description="Return to the shop"))
        for entry in llama_store["catalogEntries"]:
            if entry['devName'] == "Always.UpgradePack.03":
                continue
            llama_datatable = await stw.get_llama_datatable(self.client,
                                                            entry['displayAssetPath'].split('/Game/Items/CardPacks/')[
                                                                -1].split('.')[0])
            options.append(discord.SelectOption(label=llama_datatable[0], value=entry['offerId'],
                                                description=f"Price: {entry['prices'][0]['finalPrice']:,}",
                                                emoji=llama_datatable[2]))
        return options

    async def llama_entry(self, catalog_entry, client):
        """
        Creates an embed entry string for a single llama catalog entry.

        Args:
            catalog_entry: The catalog entry to be processed.
            client: The bot client.

        Returns:
            The embed entry string.
        """
        llama_datatable = await stw.get_llama_datatable(self.client, catalog_entry['displayAssetPath'].split('/Game/Items/CardPacks/')[-1].split('.')[0])
        entry_string = f"\u200b\n{llama_datatable[2]}{llama_datatable[3]} **{llama_datatable[0]}**\n"
        # entry_string += f"Rarity: {catalog_entry['itemGrants'][0]['templateId'].split('CardPack:cardpack_')[1]}\n"
        entry_string += f"Price: {'~~' + str(catalog_entry['prices'][0]['regularPrice']) + '~~ ' if catalog_entry['prices'][0]['regularPrice'] != catalog_entry['prices'][0]['finalPrice'] else ''}**{catalog_entry['prices'][0]['finalPrice']:,}** {stw.get_item_icon_emoji(client, catalog_entry['prices'][0]['currencySubType'])} \n"
        # entry_string += f"OfferID: {catalog_entry['offerId']}\n"
        # entry_string += f"Dev name: {catalog_entry['devName']}\n"
        # entry_string += f"Daily limit: {catalog_entry['dailyLimit']}\n"
        # entry_string += f"Event limit: {catalog_entry['meta']['EventLimit']}\n"
        # entry_string += f"Icon: {catalog_entry['displayAssetPath'].split('/Game/Items/CardPacks/')[-1].split('.')[0]}\n"
        return entry_string

    async def llama_embed(self, ctx, free_llama, llama_store, preroll_data):
        """
        Creates the embed for the llama command.

        Args:
            ctx: The context of the command.
            free_llama: The free llama data.
            llama_store: The llama store data.
            preroll_data: The preroll data.

        Returns:
            The embed.
        """
        embed = discord.Embed(
            title=await stw.add_emoji_title(self.client, "Store", "llama"),
            description=f"\u200b\nHere's the current shop:\u200b\n\u200b",
            colour=self.client.colours["generic_blue"])
        if free_llama[0] > 0:
            embed.description += f"\u200b\n{self.client.config['emojis']['new_item_store']} **There is a free llama available!** {self.client.config['emojis']['new_item_store']}\n"
        for entry in llama_store["catalogEntries"]:
            if entry['devName'] == "Always.UpgradePack.03":
                continue
            embed.description += await self.llama_entry(entry, self.client)
            for attr, val in preroll_data.items():  # :>
                if entry["offerId"] == val["attributes"]["offerId"]:
                    embed.description += "Contents: " + stw.llama_contents_render(self.client,
                                                                                  val["attributes"]["items"])
                    break
            embed.description += f"\n"
        embed.description += f"\u200b\n"
        embed.description = stw.truncate(embed.description, 3999)
        embed = await stw.set_thumbnail(self.client, embed, "meme")
        embed = await stw.add_requested_footer(ctx, embed)
        return embed

    async def llamas_command(self, ctx, authcode, auth_opt_out):
        """
        The main function for the llamas command.

        Args:
            ctx: The context of the command.
            authcode: The authcode of the account.
            auth_opt_out: Whether the user has opted out of auth.

        Returns:
            None
        """
        auth_info = await stw.get_or_create_auth_session(self.client, ctx, "llamas", authcode, auth_opt_out, True)
        if not auth_info[0]:
            return

        final_embeds = []

        ainfo3 = ""
        try:
            ainfo3 = auth_info[3]
        except IndexError:
            pass

        # what is this black magic???????? I totally forgot what any of this is and how is there a third value to the auth_info??
        # okay I discovered what it is, it's basically the "welcome whoever" embed that is edited
        if ainfo3 != "logged_in_processing" and auth_info[2] != []:
            final_embeds = auth_info[2]

        shop_json_response = await stw.shop_request(self.client, auth_info[1]["token"])

        populate_preroll_request = await stw.profile_request(self.client, "llamas", auth_info[1], profile_id="stw")
        populate_preroll_json = orjson.loads(await populate_preroll_request.read())
        preroll_data = stw.extract_profile_item(populate_preroll_json, "PrerollData")

        # preroll_file = io.BytesIO()
        # preroll_file.write(orjson.dumps(preroll_data, option=orjson.OPT_INDENT_2 | orjson.OPT_NON_STR_KEYS))
        # preroll_file.seek(0)
        #
        # json_file = discord.File(preroll_file,
        #                          filename=f"PrerollData-{datetime.datetime.now().strftime('%d-%m-%Y_%H-%M-%S')}.json")

        # check for le error code
        if await self.check_errors(ctx, shop_json_response, auth_info, final_embeds):
            return

        llama_store = await stw.get_llama_store(shop_json_response)

        free_llama = await stw.free_llama_count(llama_store)

        llama_option = await self.select_options_llamas(llama_store)

        # With all info extracted, create the output

        embed = await self.llama_embed(ctx, free_llama, llama_store, preroll_data)

        final_embeds.append(embed)
        llama_view = LlamasView(ctx, self.client, auth_info[0], ctx.author, llama_store, free_llama, preroll_data,
                                llama_option)
        llama_view.llamas = self
        await stw.slash_edit_original(ctx, auth_info[0], final_embeds, view=llama_view)
        return

    @ext.slash_command(name='llamas',
                       description='Get llamas info from stw',
                       guild_ids=stw.guild_ids)
    async def slashllamas(self, ctx: discord.ApplicationContext,
                          token: Option(str,
                                        "Your Epic Games authcode. Required unless you have an active session.") = "",
                          auth_opt_out: Option(bool, "Opt out of starting an authentication session") = False, ):
        """
        This function is the entry point for the llama command when called via slash

        Args:
            ctx (discord.ApplicationContext): The context of the slash command
            token: Your Epic Games authcode. Required unless you have an active session.
            auth_opt_out: Opt out of starting an authentication session
        """
        await self.llamas_command(ctx, token, not auth_opt_out)

    @ext.command(name='llamas',
                 extras={'emoji': "llama", "args": {
                     'authcode': 'Your Epic Games authcode. Required unless you have an active session. (Optional)',
                     'opt-out': 'Any text given will opt you out of starting an authentication session (Optional)'},
                         'dev': False},
                 brief="Get llamas info from stw",
                 description="Get llamas info from stw")
    async def llamas(self, ctx, authcode='', optout=None):
        """
        This is the entry point for the llama command when called traditionally

        Args:
            ctx: The context of the command
            authcode: The authcode for the account
            optout: Any text given will opt out of starting an auth session
        """
        if optout is not None:
            optout = True
        else:
            optout = False

        await self.llamas_command(ctx, authcode, not optout)


def setup(client):
    """
    This function is called when the cog is loaded via load_extension

    Args:
        client: The bot client
    """
    client.add_cog(Llamas(client))
