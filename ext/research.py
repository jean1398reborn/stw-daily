"""
STW Daily Discord bot Copyright 2022 by the STW Daily team.
Please do not skid our hard work.
https://github.com/dippyshere/stw-daily

This file is the cog for the research command. collect and spend research points
"""

import asyncio
import orjson

import discord
import discord.ext.commands as ext
from discord import Option
from discord.commands import (  # Importing the decorator that makes slash commands.
    slash_command,
)

import stwutil as stw


async def add_fort_fields(client, embed, current_levels, extra_white_space=False):
    """
    Add the fields to the embed for the fort stats.

    Args:
        client: The client object.
        embed: The embed to add the fields to.
        current_levels: The dictionary of current levels of the stats.
        extra_white_space: Whether to add extra white space to the embed.

    Returns:
        The embed with the fields added.
    """
    print(current_levels)
    fortitude = current_levels["fortitude"]
    offense = current_levels["offense"]
    resistance = current_levels["resistance"]
    technology = current_levels["technology"]

    embed.add_field(name="\u200B", value="\u200B", inline=True)
    embed.add_field(name=f'**{client.config["emojis"]["fortitude"]} Fortitude: **',
                    value=f'```{fortitude}```\u200b', inline=True)
    embed.add_field(name=f'**{client.config["emojis"]["offense"]} Offense: **',
                    value=f'```{offense}```\u200b', inline=True)
    embed.add_field(name="\u200B", value="\u200B", inline=True)
    embed.add_field(name=f'**{client.config["emojis"]["resistance"]} Resistance: **',
                    value=f'```{resistance}```\u200b', inline=True)

    extra_white_space = "\u200b\n\u200b\n\u200b" if extra_white_space is True else ""
    embed.add_field(name=f'**{client.config["emojis"]["technology"]} Technology: **',
                    value=f'```{technology}```{extra_white_space}', inline=True)
    return embed


class ResearchView(discord.ui.View):
    """
    The UI View for the research command
    """

    async def disable_button_when_poor(self, button, index):
        """
        Disable the button if the user cannot afford the stat.

        Args:
            button: The button to disable.
            index: The index of the button.

        Returns:
            The button with the disabled attribute set.
        """
        button_map = ['fortitude', 'offense', 'resistance', 'technology']
        button.disabled = await self.check_stat_affordability(button_map[index])
        return button

    async def check_stat_affordability(self, stat):
        """
        Check if the stat can be afforded.

        Args:
            stat: The stat to check.

        Returns:
            bool: True if the stat can be afforded, False if not.
        """
        return self.total_points['quantity'] >= stw.research_stat_cost(stat, self.current_levels[stat])

    def map_button_emojis(self, button):
        """
        Map the button emojis to the buttons.

        Args:
            button: The button to map the emoji to.

        Returns:
            The button with the emoji mapped.
        """
        button.emoji = self.button_emojis[button.emoji.name]
        return button

    async def on_timeout(self):
        """
        Called when the view times out.

        Returns:
            None
        """
        green = self.client.colours["research_green"]

        for child in self.children:
            child.disabled = True
        total_points = self.total_points
        current_levels = self.current_levels
        embed = discord.Embed(
            title=await stw.add_emoji_title(self.client, "Research", "research_point"),
            description=f"""\u200b
            You currently have **{total_points['quantity']}** research point{'s' if total_points['quantity'] > 1 else ''} available.\n\u200b\n\u200b""",
            colour=green
        )

        embed = await stw.set_thumbnail(self.client, embed, "research")
        embed = await stw.add_requested_footer(self.ctx, embed)
        embed = await add_fort_fields(self.client, embed, current_levels)
        embed.add_field(name=f"\u200b", value=f"*Timed out, please reuse command to continue*\n\u200b")
        await self.message.edit(embed=embed, view=self)
        return

    async def universal_stat_process(self, interaction, stat):
        """
        Process the stat button press for any stat.

        Args:
            interaction: The interaction object.
            stat: The stat to process.

        Returns:
            None
        """
        gren = self.client.colours["research_green"]

        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)

        stat_purchase = await stw.profile_request(self.client, "purchase_research", self.auth_info[1],
                                                  json={'statId': stat})
        purchased_json = orjson.loads(await stat_purchase.read())

        total_points = self.total_points
        current_levels = self.current_levels

        for child in self.children:
            child.disabled = False

        try:
            if purchased_json['errorCode'] == 'errors.com.epicgames.fortnite.item_consumption_failed':
                embed = discord.Embed(
                    title=await stw.add_emoji_title(self.client, "Research", "research_point"),
                    description=f"""\u200b
                    You currently have **{total_points['quantity']}** research point{'s' if total_points['quantity'] > 1 else ''} available.\n\u200b\n\u200b""",
                    colour=gren
                )

                embed = await stw.set_thumbnail(self.client, embed, "research")
                embed = await stw.add_requested_footer(interaction, embed)
                embed = await add_fort_fields(self.client, embed, current_levels)
                embed.add_field(name=f"\u200b", value=f"*You do not have enough points to level up **{stat}***\n\u200b")
                await interaction.edit_original_response(embed=embed, view=self)
                return
        except:
            pass

        current_research_statistics_request = await stw.profile_request(self.client, "query", self.auth_info[1])
        json_response = orjson.loads(await current_research_statistics_request.read())
        current_levels = await research_query(interaction, self.client, self.auth_info, [], json_response)
        if current_levels is None:
            return

        self.current_levels = current_levels

        # What I believe happens is that epic games removes the research points item if you use it all... not to sure if they change the research token guid
        try:
            research_points_item = purchased_json['profileChanges'][0]['profile']['items'][self.research_token_guid]
        except:
            print(purchased_json)
            embed = discord.Embed(
                title=await stw.add_emoji_title(self.client, "Research", "research_point"),
                description=f"""\u200b
                You currently have **0** research points available.\n\u200b\n\u200b""",
                colour=gren
            )

            embed = await add_fort_fields(self.client, embed, current_levels)
            embed.add_field(name=f"\u200b", value=f"*No more research points!*\n\u200b")
            embed = await stw.set_thumbnail(self.client, embed, "research")
            embed = await stw.add_requested_footer(interaction, embed)
            for child in self.children:
                child.disabled = True
            await interaction.edit_original_response(embed=embed, view=self)
            return

        spent_points = self.total_points['quantity'] - research_points_item['quantity']
        embed = discord.Embed(
            title=await stw.add_emoji_title(self.client, "Research", "research_point"),
            description=f"""\u200b
            You currently have **{research_points_item['quantity']}** research point{'s' if research_points_item['quantity'] > 1 else ''} available.\n\u200b\n\u200b""",
            colour=gren
        )

        embed = await add_fort_fields(self.client, embed, current_levels)
        embed.add_field(name=f"\u200b", value=f"*Spent **{spent_points}** to level up **{stat}***\n\u200b")
        embed = await stw.set_thumbnail(self.client, embed, "research")
        embed = await stw.add_requested_footer(interaction, embed)
        self.total_points = research_points_item

        for i, child in enumerate(self.children):
            await self.disable_button_when_poor(child, i)

        await interaction.edit_original_response(embed=embed, view=self)

    # creo kinda fire though ngl
    def __init__(self, client, auth_info, author, total_points, current_levels, research_token_guid, ctx):
        super().__init__()
        self.client = client
        self.ctx = ctx
        self.auth_info = auth_info
        self.author = author
        self.interaction_check_done = {}
        self.total_points = total_points
        self.current_levels = current_levels
        self.research_token_guid = research_token_guid

        self.button_emojis = {
            'fortitude': self.client.config["emojis"]["fortitude"],
            'offense': self.client.config["emojis"]['offense'],
            'resistance': self.client.config["emojis"]['resistance'],
            'technology': self.client.config["emojis"]['technology']
        }

        self.children = list(map(self.map_button_emojis, self.children))

    async def interaction_check(self, interaction):
        """
        Check if the interaction is performed by the author

        Args:
            interaction: The interaction object.

        Returns:
            bool: True if the interaction is created by the view author, False if notifying the user
        """
        return await stw.view_interaction_check(self, interaction, "research")

    @discord.ui.button(style=discord.ButtonStyle.success, emoji="fortitude")
    async def fortitude_button(self, _button, interaction):
        """
        Process the fortitude button press.

        Args:
            _button: The button object.
            interaction: The interaction object.
        """
        await self.universal_stat_process(interaction, "fortitude")

    @discord.ui.button(style=discord.ButtonStyle.success, emoji="offense")
    async def offense_button(self, _button, interaction):
        """
        Process the offense button press.

        Args:
            _button: The button object.
            interaction: The interaction object.
        """
        await self.universal_stat_process(interaction, "offense")

    @discord.ui.button(style=discord.ButtonStyle.success, emoji="resistance")
    async def resistance_button(self, _button, interaction):
        """
        Process the resistance button press.

        Args:
            _button: The button object.
            interaction: The interaction object.
        """
        await self.universal_stat_process(interaction, "resistance")

    @discord.ui.button(style=discord.ButtonStyle.success, emoji="technology")
    async def technology_button(self, _button, interaction):
        """
        Process the technology button press.

        Args:
            _button: The button object.
            interaction: The interaction object.
        """
        await self.universal_stat_process(interaction, "technology")


async def research_query(ctx, client, auth_info, final_embeds, json_response):
    """
    Query the research endpoint for the current research levels.

    Args:
        ctx: The context object.
        client: The client object.
        auth_info: The auth info object.
        final_embeds: The final embeds object.
        json_response: The json response object.

    Returns:
        dict: The current research levels. hi hi
    """
    crown_yellow = client.colours["crown_yellow"]

    support_url = client.config["support_url"]
    acc_name = auth_info[1]["account_name"]

    try:
        error_code = json_response["errorCode"]
        embed = await stw.post_error_possibilities(ctx, client, "research", acc_name, error_code, support_url)
        final_embeds.append(embed)
        await stw.slash_edit_original(ctx, auth_info[0], final_embeds)
        return
    except:
        pass

    try:
        current_levels = json_response['profileChanges'][0]['profile']['stats']['attributes']['research_levels']
    except Exception as e:
        # account may not have stw
        try:
            # check if account has daily reward stats, if not, then account doesn't have stw
            check_stw = json_response['profileChanges'][0]['profile']['stats']['attributes']['daily_rewards']
            print(e, "no research stat, but daily reward; must have zero research stats", json_response)
            # assume all stats are at 0 because idk it cant be max surely not, the stats are here for max so...
            current_levels = {'fortitude': 0, 'offense': 0, 'resistance': 0, 'technology': 0}
            pass
        except:
            # account doesn't have stw
            error_code = "errors.com.epicgames.fortnite.check_access_failed"
            embed = await stw.post_error_possibilities(ctx, client, "research", acc_name, error_code, support_url)
            final_embeds.append(embed)
            await stw.slash_edit_original(ctx, auth_info[0], final_embeds)
            return

    # I'm not too sure what happens here but if current_levels doesn't exist im assuming its at maximum.
    proc_max = False
    try:
        if current_levels["offense"] + current_levels["fortitude"] + current_levels["resistance"] + current_levels[
            "technology"] == 480:
            proc_max = True
    except:
        for stat in ["offense", "fortitude", "resistance", "technology"]:
            if stat not in current_levels:
                current_levels[stat] = 0

        pass

    if proc_max:
        embed = discord.Embed(
            title=await stw.add_emoji_title(client, "Max", "crown"),
            description="""\u200b
                Congratulations, you have **maximum** FORT stats.\n\u200b\n\u200b""",
            colour=crown_yellow
        )

        await add_fort_fields(client, embed, current_levels, True)
        embed = await stw.set_thumbnail(client, embed, "crown")
        embed = await stw.add_requested_footer(ctx, embed)
        final_embeds.append(embed)
        await stw.slash_edit_original(ctx, auth_info[0], final_embeds)
        return None

    return current_levels


class Research(ext.Cog):
    """
    Cog for the research related commands.
    """

    def __init__(self, client):
        self.client = client
        self.emojis = client.config["emojis"]
        self.token_guid_research = "Token_collectionresource_nodegatetoken01"
        self.item_templateid_research = "Token:collectionresource_nodegatetoken01"

    def check_for_research_points_item(self, query_json):
        """
        Check if the research points item is in the inventory.

        Args:
            query_json: The query json object.

        Returns:
            tuple: the research points item and key, otherwise None
        """
        # Yes you can use the itemGuid from the notifications response from the claimcollectedresources response
        # but, you do not get notifications when you are at maximum research points!
        items = query_json['profileChanges'][0]['profile']['items']

        for key, item in items.items():
            try:
                if item['templateId'] == f"{self.item_templateid_research}":
                    return item, key
            except:
                pass

        return None

    def check_for_research_guid_key(self, query_json):
        """
        Check if the research points item is in the inventory.

        Args:
            query_json: The query json object.

        Returns:
            tuple: the research points key, otherwise None
        """
        items = query_json['profileChanges'][0]['profile']['items']
        for key, item in items.items():
            try:
                if item['templateId'] == f"CollectedResource:{self.token_guid_research}":
                    return key
            except:
                pass

        return None

    async def research_command(self, ctx, authcode, auth_opt_out):
        """
        The main function for the research command.

        Args:
            ctx: The context object.
            authcode: The authcode object.
            auth_opt_out: The auth_opt_out object.

        Returns:
            None
        """
        gren = self.client.colours["research_green"]

        auth_info = await stw.get_or_create_auth_session(self.client, ctx, "daily", authcode, auth_opt_out, True)
        if not auth_info[0]:
            return

        final_embeds = []

        ainfo3 = ""
        try:
            ainfo3 = auth_info[3]
        except:
            pass

        # what is this black magic???????? I totally forgot what any of this is and how is there a third value to the auth_info??
        # okay I discovered what it is, it's basically the "welcome whoever" embed that is edited
        if ainfo3 != "logged_in_processing" and auth_info[2] != []:
            final_embeds = auth_info[2]

        current_research_statistics_request = await stw.profile_request(self.client, "query", auth_info[1])
        json_response = orjson.loads(await current_research_statistics_request.read())
        current_levels = await research_query(ctx, self.client, auth_info, final_embeds, json_response)
        if current_levels is None:
            return

        # assign variables for error embeds
        support_url = self.client.config["support_url"]
        acc_name = auth_info[1]["account_name"]

        # Find research guid to post to required for ClaimCollectedResources json
        research_guid_check = await asyncio.gather(asyncio.to_thread(self.check_for_research_guid_key, json_response))
        print(research_guid_check)
        if research_guid_check[0] is None:
            print("errors.stwdaily.failed_guid_research encountered:", json_response)
            error_code = "errors.stwdaily.failed_guid_research"
            embed = await stw.post_error_possibilities(ctx, self.client, "research", acc_name, error_code, support_url)
            final_embeds.append(embed)
            await stw.slash_edit_original(ctx, auth_info[0], final_embeds)
            return

        research_guid = research_guid_check[0]
        pass

        current_research_statistics_request = await stw.profile_request(self.client, "resources", auth_info[1],
                                                                        json={"collectorsToClaim": [research_guid]})
        json_response = orjson.loads(await current_research_statistics_request.read())

        try:
            error_code = json_response["errorCode"]
            embed = await stw.post_error_possibilities(ctx, self.client, "research", acc_name, error_code, support_url)
            final_embeds.append(embed)
            await stw.slash_edit_original(ctx, auth_info[0], final_embeds)
        except:
            pass

        # Get total points
        total_points_check = await asyncio.gather(asyncio.to_thread(self.check_for_research_points_item, json_response))
        if total_points_check[0] is None:
            print("errors.stwdaily.failed_total_points encountered:", json_response)
            error_code = "errors.stwdaily.failed_total_points"
            embed = await stw.post_error_possibilities(ctx, self.client, "research", acc_name, error_code, support_url)
            final_embeds.append(embed)
            await stw.slash_edit_original(ctx, auth_info[0], final_embeds)
            return

        total_points, rp_token_guid = total_points_check[0][0], total_points_check[0][1]

        # I do believe that after some testing if you are at le maximum research points
        # you do not receive notifications so this must be wrapped in a try statement
        # assume that research points generated is none since it is at max!
        # TODO: the above statement is false
        research_points_claimed = None
        try:
            research_feedback, check = json_response["notifications"], False

            for notification in research_feedback:
                if notification["type"] == "collectedResourceResult":
                    research_feedback, check = notification, True
                    break

            if not check:
                error_code = "errors.stwdaily.failed_get_collected_resource_type"
                embed = await stw.post_error_possibilities(ctx, self.client, "research", acc_name, error_code,
                                                           support_url)
                final_embeds.append(embed)
                await stw.slash_edit_original(ctx, auth_info[0], final_embeds)
                return

            available_research_items, check = research_feedback["loot"]["items"], False
            for research_item in available_research_items:
                try:
                    if research_item["itemType"] == self.item_templateid_research:
                        research_item, check = research_item, True
                        break
                except:
                    pass

            if not check:
                error_code = "errors.stwdaily.failed_get_collected_resource_item"
                embed = await stw.post_error_possibilities(ctx, self.client, "research", acc_name, error_code,
                                                           support_url)
                final_embeds.append(embed)
                await stw.slash_edit_original(ctx, auth_info[0], final_embeds)
                return
            # this variable might be referenced before assignment hmm
            research_points_claimed = research_item['quantity']
        except:
            pass

        # Create the embed for displaying nyaa~

        if research_points_claimed is not None:
            if research_points_claimed == 1:
                claimed_text = f"*Claimed **{research_points_claimed}** research point*\n\u200b"
            else:
                claimed_text = f"*Claimed **{research_points_claimed}** research points*\n\u200b"
        else:
            claimed_text = f"*Did not claim any research points*\n\u200b"
        embed = discord.Embed(
            title=await stw.add_emoji_title(self.client, "Research", "research_point"),
            description=f"""\u200b
            You currently have **{total_points['quantity']}** research point{'s' if total_points['quantity'] > 1 else ''} available. \n\u200b\n\u200b""",
            colour=gren
        )

        embed = await add_fort_fields(self.client, embed, current_levels)
        embed.add_field(name=f"\u200b", value=claimed_text)
        embed = await stw.set_thumbnail(self.client, embed, "research")
        embed = await stw.add_requested_footer(ctx, embed)

        final_embeds.append(embed)
        research_view = ResearchView(self.client, auth_info, ctx.author, total_points, current_levels, rp_token_guid,
                                     ctx)
        research_view.message = await stw.slash_edit_original(ctx, auth_info[0], final_embeds, view=research_view)

    @ext.command(name='research',
                 aliases=['rse', 'des', 'rgesearch', 'r4es', 'reas',
                          'resd', 'resa', 're', 're4s', 'researtch', 're3search',
                          'rexearch', 'resw', 'rfesearch', 'researhc', 'rea', 'rers',
                          'reswarch', 'resdarch', 'resarch', 'redearch', 'researchh',
                          'researfh', 'reseach', 'reseatrch', 'rsesearch', 'r3s', 'rews',
                          'reseadrch', 'ers', 'rewearch', 'rese3arch', 'rssearch', 'gesearch',
                          'esearch', 'resezrch', 're3s', 'reseearch', 'reasearch', 'rew', 'reds',
                          'rses', 'researcyh', 'researdh', 'res4arch', 'ressearch', '5esearch', 'rezearch',
                          'reseatch', 'researcfh', 'rrsearch', 'ees', 'researcgh', 'rseearch', 'reesarch', 'resaearch',
                          'resear4ch', 'rds', 'rewsearch', 'tresearch', 'resefarch', 'reseaarch', 'researcxh', '4res',
                          'resx',
                          'resesrch', 'resexarch', 'r4search', 'r4esearch', '4es', 'rresearch', 'resrearch', 'rs',
                          'resea4ch', 'fes',
                          'gresearch', 'reseagch', 'es', 'r5es', 'rsearch', 'researvh', 'r3esearch', 'res4earch',
                          'researcjh', 'researech',
                          'researchn', 'resesarch', 'researcy', 'researrch', 'resfearch', 'researcj', 'reseasrch',
                          'resear5ch', 'rez', 'r3es',
                          'r3search', 'researc', 'res', 'researchj', 'refsearch', 'dres', 'rex', 'researchg', 'rrs',
                          'researchu', 'redsearch', 'rersearch',
                          'reseafch', 'reesearch', 'researcvh', 'eesearch', 'resezarch', '5research', 'res3earch',
                          'resewarch', 'fesearch', 'reearch', 'resxearch',
                          'rwes', 'rees', 'reswearch', 'reseaxrch', 'researcuh', 'refs', 'reseaqrch', 'resea4rch',
                          'rfs', 'fres', 'researgch', 'gres', 'reeearch',
                          'resea5ch', 'rtes', 'resexrch', 'rws', 'tres', 'researchy', 'researcnh', 'rdesearch',
                          'researcch', 'rexs', 'rges', 'reserch',
                          'resaerch', 'rese4arch', 'reserarch', 'researcu', 'researcbh', 'fresearch', 'rdes',
                          'rwesearch', 'rexsearch', 'desearch',
                          'reseqarch', 'dresearch', 'rezsearch', 'researchb', 'reseaech', 'eresearch', 'researxch',
                          'researdch', 'r4s',
                          'rfsearch', 'rres', 'reseagrch', 'reseaerch', 'ress', 'resaesaer', 'reseqrch', 'rfes',
                          '4esearch',
                          'rwsearch', 'resea5rch', 'rtesearch', 'researfch', '5res', 'researcdh', 'eres', 'ressarch',
                          'resfarch', 'reseadch', 'rss', 'reszearch', 'reserach', 'reach', 'ersearch', 'reseazrch',
                          'rdsearch', 'ges', 'researcn', 'researcg', '4research', 'researcb', 'ree', 'resz',
                          'reseacrh', 'red', 'resdearch', 'reseawrch', '5es', 'rese', 'reseafrch', 'reaearch',
                          'researh', 'tesearch', 'researxh', 'r5esearch', 'resrarch', 'researvch', 'res3arch',
                          'resewrch', 'rezs', 're4search', 'tes', 'resedarch', '/res', '/r', '/research'],
                 extras={'emoji': "research_point", "args": {
                     'authcode': 'Your Epic Games authcode. Required unless you have an active session. (Optional)',
                     'opt-out': 'Any text given will opt you out of starting an authentication session (Optional)'},
                         "dev": False},
                 brief="Claim and spend your research points (authentication required)",
                 description="""This command lets you claim your available research points, view your FORT research levels, and upgrade those levels. Press the button corresponding with the stat you want to upgrade.
                 """)
    async def research(self, ctx, authcode='', optout=None):
        """
        This function is the entry point for the research command when called traditionally

        Args:
            ctx: The context of the command
            authcode: The authcode of the user
            optout: Whether or not the user wants to opt out of starting a session
        """
        if optout is not None:
            optout = True
        else:
            optout = False

        await self.research_command(ctx, authcode, not optout)

    @slash_command(name='research',
                   description="Claim and spend your research points (authentication required)",
                   guild_ids=stw.guild_ids)
    async def slashresearch(self, ctx: discord.ApplicationContext,
                            token: Option(str,
                                          "Your Epic Games authcode. Required unless you have an active session.") = "",
                            auth_opt_out: Option(bool, "Opt out of starting an authentication session") = False, ):
        """
        This function is the entry point for the research command when called via slash command

        Args:
            ctx: The context of the command
            token: The authcode of the user
            auth_opt_out: Whether or not the user wants to opt out of starting a session
        """
        await self.research_command(ctx, token, not auth_opt_out)


def setup(client):
    """
    This function is called when the cog is loaded via load_extension

    Args:
        client: The bot client
    """
    client.add_cog(Research(client))
