"""
STW Daily Discord bot Copyright 2023 by the STW Daily team.
Please do not skid our hard work.
https://github.com/dippyshere/stw-daily

This file is the cog for the homebase command. renames homebase / displays current name + renders banner
"""

import discord
import discord.ext.commands as ext
from discord import Option
import orjson

import stwutil as stw


class Homebase(ext.Cog):
    """
    Cog for the homebase command
    """

    def __init__(self, client):
        self.client = client
        self.emojis = client.config["emojis"]

    async def check_errors(self, ctx, public_json_response, auth_info, final_embeds, name=""):
        """
        Checks for errors in the public_json_response and edits the original message if an error is found.

        Args:
            ctx: The context of the command.
            public_json_response: The json response from the public API.
            auth_info: The auth_info tuple from get_or_create_auth_session.
            final_embeds: The list of embeds to be edited.
            name: The attempted name of the homebase. Used to check if empty (for no stw)

        Returns:
            True if an error is found, False otherwise.
        """
        try:
            # general error
            error_code = public_json_response["errorCode"]
            support_url = self.client.config["support_url"]
            acc_name = auth_info[1]["account_name"]
            embed = await stw.post_error_possibilities(ctx, self.client, "homebase", acc_name, error_code,
                                                       verbiage_action="change Homebase name")
            final_embeds.append(embed)
            await stw.slash_edit_original(ctx, auth_info[0], final_embeds)
            return error_code, True
        except:
            try:
                # if there is a homebase name, continue with command
                check_hbname = public_json_response["profileChanges"][0]["profile"]["stats"]["attributes"][
                    "homebase_name"]
                return False, False
            except:
                # trying to check homebase with no stw or homebase, assume error
                if name == "":
                    support_url = self.client.config["support_url"]
                    acc_name = auth_info[1]["account_name"]
                    error_code = "errors.com.epicgames.fortnite.check_access_failed"
                    embed = await stw.post_error_possibilities(ctx, self.client, "homebase", acc_name, error_code,
                                                               verbiage_action="change Homebase name")
                    final_embeds.append(embed)
                    await stw.slash_edit_original(ctx, auth_info[0], final_embeds)
                    return error_code, True
                # allow name change for no stw because it works somehow
                return "errors.stwdaily.no_stw", False

    async def hbrename_command(self, ctx, name, authcode, auth_opt_out):
        """
        The main function for the homebase command.

        Args:
            ctx: The context of the command.
            name: The name to change the homebase to.
            authcode: The authcode to use for the command.
            auth_opt_out: Whether or not to opt out of authcode usage.

        Returns:
            None
        """
        succ_colour = self.client.colours["success_green"]
        white = self.client.colours["auth_white"]

        auth_info = await stw.get_or_create_auth_session(self.client, ctx, "homebase", authcode, auth_opt_out, True)
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

        # get public info about current Homebase name
        public_request = await stw.profile_request(self.client, "query_public", auth_info[1],
                                                   profile_id="common_public")
        public_json_response = orjson.loads(await public_request.read())
        # ROOT.profileChanges[0].profile.stats.attributes.homebase_name

        file = None
        # check for le error code
        error_check = await self.check_errors(ctx, public_json_response, auth_info, final_embeds, name)
        if error_check[0] == "errors.stwdaily.no_stw":
            current = " "
            homebase_icon = "placeholder"
            homebase_colour = "defaultcolor1"
        elif error_check[1]:
            return
        else:
            # extract info from response
            current = public_json_response["profileChanges"][0]["profile"]["stats"]["attributes"]["homebase_name"]
            try:
                homebase_icon = public_json_response["profileChanges"][0]["profile"]["stats"]["attributes"][
                    "banner_icon"]
            except KeyError:
                homebase_icon = "placeholder"
            try:
                homebase_colour = public_json_response["profileChanges"][0]["profile"]["stats"]["attributes"][
                    "banner_color"]
            except KeyError:
                homebase_colour = "defaultcolor1"

        # Empty name should fetch current name
        if name == "":
            embed = discord.Embed(
                title=await stw.add_emoji_title(self.client, "Homebase Name", "storm_shield"),
                description=f"\u200b\n"
                            f"**Your current Homebase name is:**\n"
                            f"```{current}```\u200b", colour=white)
            if homebase_icon != "placeholder":
                try:
                    embed, file = await stw.generate_banner(self.client, embed, homebase_icon, homebase_colour,
                                                            ctx.author.id)
                    colour = await stw.get_banner_colour(homebase_colour, "rgb")
                    embed.colour = discord.Colour.from_rgb(colour[0], colour[1], colour[2])
                except:
                    embed.set_thumbnail(url=self.client.config["thumbnails"]["placeholder"])
            else:
                embed.set_thumbnail(url=self.client.config["thumbnails"]["placeholder"])
            embed = await stw.add_requested_footer(ctx, embed)
            final_embeds.append(embed)
            if file is not None:
                await stw.slash_edit_original(ctx, auth_info[0], final_embeds, files=file)
                return
            await stw.slash_edit_original(ctx, auth_info[0], final_embeds)
            return

        # failing this check means the name has problems thus we cannot accept it
        if not await stw.is_legal_homebase_name(name):
            if len(name) > 16:
                error_code = "errors.stwdaily.homebase_long"
                embed = await stw.post_error_possibilities(ctx, self.client, "homebase", name, error_code,
                                                           verbiage_action="change Homebase name")
                final_embeds.append(embed)
                await stw.slash_edit_original(ctx, auth_info[0], final_embeds)
                return
            error_code = "errors.stwdaily.homebase_illegal"
            embed = await stw.post_error_possibilities(ctx, self.client, "homebase", name, error_code,
                                                       verbiage_action="change Homebase name")
            final_embeds.append(embed)
            await stw.slash_edit_original(ctx, auth_info[0], final_embeds)
            return

        # wih all checks passed, we may now attempt to change name
        request = await stw.profile_request(self.client, "set_homebase", auth_info[1], profile_id="common_public",
                                            data=orjson.dumps({"homebaseName": f"{name}"}))
        request_json_response = orjson.loads(await request.read())

        # check for le error code
        error_check = await self.check_errors(ctx, request_json_response, auth_info, final_embeds, name)
        if error_check[1]:
            return

        # If passed all checks and changed name, present success embed
        embed = discord.Embed(title=await stw.add_emoji_title(self.client, "Success", "checkmark"),
                              description="\u200b",
                              colour=succ_colour)

        embed.add_field(name=f'{self.emojis["broken_heart"]} Changed Homebase name from:',
                        value=f"```{current}```\u200b",
                        inline=False)

        embed.add_field(name=f'{self.emojis["storm_shield"]} To:', value=f"```{name}```\u200b",
                        inline=False)

        if homebase_icon != "placeholder":
            try:
                embed, file = await stw.generate_banner(self.client, embed, homebase_icon, homebase_colour,
                                                        ctx.author.id)
                colour = await stw.get_banner_colour(homebase_colour, "rgb")
                embed.colour = discord.Colour.from_rgb(colour[0], colour[1], colour[2])
            except:
                embed = await stw.set_thumbnail(self.client, embed, "check")
        else:
            embed = await stw.set_thumbnail(self.client, embed, "check")

        embed = await stw.add_requested_footer(ctx, embed)
        final_embeds.append(embed)
        await stw.slash_edit_original(ctx, auth_info[0], final_embeds)
        return

    @ext.slash_command(name='homebase',
                       description='This command allows you to view / change the name of your Homebase in STW',
                       guild_ids=stw.guild_ids)
    async def slashhbrename(self, ctx: discord.ApplicationContext,
                            name: Option(str,
                                         "The new name for your Homebase. Leave blank to view your current name + banner") = "",
                            token: Option(str,
                                          "Your Epic Games authcode. Required unless you have an active session.") = "",
                            auth_opt_out: Option(bool, "Opt out of starting an authentication session") = False, ):
        """
        This function is the entry point for the homebase command when called via slash

        Args:
            ctx (discord.ApplicationContext): The context of the slash command
            name: The new name for your Homebase. Leave blank to view your current name + banner
            token: Your Epic Games authcode. Required unless you have an active session.
            auth_opt_out: Opt out of starting an authentication session
        """
        await self.hbrename_command(ctx, name, token, not auth_opt_out)

    @ext.command(name='homebase',
                 aliases=['hbrename', 'hbrn', 'rename', 'changehomebase', 'homebasename', 'hbname', 'hb', 'brn', 'hrn',
                          'hbn', 'hbr', 'hhbrn', 'hbbrn', 'hbrrn', 'hbrnn', 'bhrn', 'hrbn', 'hbnr', 'gbrn', 'ybrn',
                          'ubrn', 'jbrn', 'nbrn', 'bbrn', 'hvrn', 'hgrn', 'hhrn', 'hnrn', 'hben', 'hb4n', 'hb5n',
                          'hbtn', 'hbgn', 'hbfn', 'hbdn', 'hbrb', 'hbrh', 'hbrj', 'hbrm', 'ghbrn', 'hgbrn', 'yhbrn',
                          'hybrn', 'uhbrn', 'hubrn', 'jhbrn', 'hjbrn', 'nhbrn', 'hnbrn', 'bhbrn', 'hvbrn', 'hbvrn',
                          'hbgrn', 'hbhrn', 'hbnrn', 'hbern', 'hbren', 'hb4rn', 'hbr4n', 'hb5rn', 'hbr5n', 'hbtrn',
                          'hbrtn', 'hbrgn', 'hbfrn', 'hbrfn', 'hbdrn', 'hbrdn', 'hbrbn', 'hbrnb', 'hbrhn', 'hbrnh',
                          'hbrjn', 'hbrnj', 'hbrmn', 'hbrnm', 'omebase', 'hmebase', 'hoebase', 'hombase', 'homease',
                          'homebse', 'homebae', 'homebas', 'hhomebase', 'hoomebase', 'hommebase', 'homeebase',
                          'homebbase', 'homebaase', 'homebasse', 'homebasee', 'ohmebase', 'hmoebase', 'hoembase',
                          'hombease', 'homeabse', 'homebsae', 'homebaes', 'gomebase', 'yomebase', 'uomebase',
                          'jomebase', 'nomebase', 'bomebase', 'himebase', 'h9mebase', 'h0mebase', 'hpmebase',
                          'hlmebase', 'hkmebase', 'honebase', 'hojebase', 'hokebase', 'homwbase', 'hom3base',
                          'hom4base', 'homrbase', 'homfbase', 'homdbase', 'homsbase', 'homevase', 'homegase',
                          'homehase', 'homenase', 'homebqse', 'homebwse', 'homebsse', 'homebxse', 'homebzse',
                          'homebaae', 'homebawe', 'homebaee', 'homebade', 'homebaxe', 'homebaze', 'homebasw',
                          'homebas3', 'homebas4', 'homebasr', 'homebasf', 'homebasd', 'homebass', 'ghomebase',
                          'hgomebase', 'yhomebase', 'hyomebase', 'uhomebase', 'huomebase', 'jhomebase', 'hjomebase',
                          'nhomebase', 'hnomebase', 'bhomebase', 'hbomebase', 'hiomebase', 'hoimebase', 'h9omebase',
                          'ho9mebase', 'h0omebase', 'ho0mebase', 'hpomebase', 'hopmebase', 'hlomebase', 'holmebase',
                          'hkomebase', 'hokmebase', 'honmebase', 'homnebase', 'hojmebase', 'homjebase', 'homkebase',
                          'homwebase', 'homewbase', 'hom3ebase', 'home3base', 'hom4ebase', 'home4base', 'homrebase',
                          'homerbase', 'homfebase', 'homefbase', 'homdebase', 'homedbase', 'homsebase', 'homesbase',
                          'homevbase', 'homebvase', 'homegbase', 'homebgase', 'homehbase', 'homebhase', 'homenbase',
                          'homebnase', 'homebqase', 'homebaqse', 'homebwase', 'homebawse', 'homebsase', 'homebxase',
                          'homebaxse', 'homebzase', 'homebazse', 'homebasae', 'homebaswe', 'homebaese', 'homebadse',
                          'homebasde', 'homebasxe', 'homebasze', 'homebasew', 'homebas3e', 'homebase3', 'homebas4e',
                          'homebase4', 'homebasre', 'homebaser', 'homebasfe', 'homebasef', 'homebased', 'homebases',
                          'hhb', 'hbb', 'bh', 'gb', 'yb', 'ub', 'jb', 'nb', 'hv', 'hg', 'hh', 'hn', 'ghb', 'hgb', 'yhb',
                          'hyb', 'uhb', 'hub', 'jhb', 'hjb', 'nhb', 'hnb', 'bhb', 'hvb', 'hbv', 'hbg', 'hbh', 'brename',
                          'hrename', 'hbename', 'hbrname', 'hbreame', 'hbrenme', 'hbrenae', 'hbrenam', 'hhbrename',
                          'hbbrename', 'hbrrename', 'hbreename', 'hbrenname', 'hbrenaame', 'hbrenamme', 'hbrenamee',
                          'bhrename', 'hrbename', 'hbername', 'hbrneame', 'hbreanme', 'hbrenmae', 'hbrenaem',
                          'gbrename', 'ybrename', 'ubrename', 'jbrename', 'nbrename', 'bbrename', 'hvrename',
                          'hgrename', 'hhrename', 'hnrename', 'hbeename', 'hb4ename', 'hb5ename', 'hbtename',
                          'hbgename', 'hbfename', 'hbdename', 'hbrwname', 'hbr3name', 'hbr4name', 'hbrrname',
                          'hbrfname', 'hbrdname', 'hbrsname', 'hbrebame', 'hbrehame', 'hbrejame', 'hbremame',
                          'hbrenqme', 'hbrenwme', 'hbrensme', 'hbrenxme', 'hbrenzme', 'hbrenane', 'hbrenaje',
                          'hbrenake', 'hbrenamw', 'hbrenam3', 'hbrenam4', 'hbrenamr', 'hbrenamf', 'hbrenamd',
                          'hbrenams', 'ghbrename', 'hgbrename', 'yhbrename', 'hybrename', 'uhbrename', 'hubrename',
                          'jhbrename', 'hjbrename', 'nhbrename', 'hnbrename', 'bhbrename', 'hvbrename', 'hbvrename',
                          'hbgrename', 'hbhrename', 'hbnrename', 'hberename', 'hb4rename', 'hbr4ename', 'hb5rename',
                          'hbr5ename', 'hbtrename', 'hbrtename', 'hbrgename', 'hbfrename', 'hbrfename', 'hbdrename',
                          'hbrdename', 'hbrwename', 'hbrewname', 'hbr3ename', 'hbre3name', 'hbre4name', 'hbrername',
                          'hbrefname', 'hbredname', 'hbrsename', 'hbresname', 'hbrebname', 'hbrenbame', 'hbrehname',
                          'hbrenhame', 'hbrejname', 'hbrenjame', 'hbremname', 'hbrenmame', 'hbrenqame', 'hbrenaqme',
                          'hbrenwame', 'hbrenawme', 'hbrensame', 'hbrenasme', 'hbrenxame', 'hbrenaxme', 'hbrenzame',
                          'hbrenazme', 'hbrenanme', 'hbrenamne', 'hbrenajme', 'hbrenamje', 'hbrenakme', 'hbrenamke',
                          'hbrenamwe', 'hbrenamew', 'hbrenam3e', 'hbrename3', 'hbrenam4e', 'hbrename4', 'hbrenamre',
                          'hbrenamer', 'hbrenamfe', 'hbrenamef', 'hbrenamde', 'hbrenamed', 'hbrenamse', 'hbrenames',
                          '/hbrn', '/homebase', '/hbrename', '/homebasern', '/rename', '/hbname'],
                 extras={'emoji': "storm_shield", "args": {
                     'name': 'The new name for your Homebase. Leave blank to view your current name + banner (Optional)',
                     'authcode': 'Your Epic Games authcode. Required unless you have an active session. (Optional)',
                     'opt-out': 'Any text given will opt you out of starting an authentication session (Optional)'},
                         'dev': False},
                 brief="View / change the name of your Homebase in STW (authentication required)",
                 description=(
                         "This command allows you to view / change the name of your Homebase in STW. You must be authenticated to use this command.\n"
                         "\u200b\n"
                         "**Please note there are limitations on what your Homebase name can be:**\n"
                         "⦾ It must be between 1-16 characters\n"
                         "⦾ It may only contain alphanumerics (0-9, a-z) + additional characters ('-._~) + spaces\n"
                         "⦾ When entering a name with spaces while not using slash commands, please put \"quote marks\" around the new name\n"
                         "⦾ Support for other languages will be available in the future\n"
                         "⦾ STW isn't required but what's the point?\n"))
    async def hbrename(self, ctx, name='', authcode='', optout=None):
        """
        This is the entry point for the homebase command when called traditionally

        Args:
            ctx: The context of the command
            name: The new name for the homebase
            authcode: The authcode for the account
            optout: Any text given will opt out of starting an auth session
        """
        if optout is not None:
            optout = True
        else:
            optout = False

        await self.hbrename_command(ctx, name, authcode, not optout)


def setup(client):
    """
    This function is called when the cog is loaded via load_extension

    Args:
        client: The bot client
    """
    client.add_cog(Homebase(client))
