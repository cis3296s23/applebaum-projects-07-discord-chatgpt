import os
import discord
import json
from random import randrange
from src.client import client
from src import log
from src.client import Guild

logger = log.setup_logger(__name__)


def run_discord_bot():
    @client.event
    async def on_ready():
        client.guild_map[1075881043585937529] = Guild(1075881043585937529, client.get_chatbot_model()) # Test server guild
        client.guild_map[1075881043585937529].reply_all_channel = "1093237764570484796"
        await client.tree.sync()
        logger.info(f'{client.user} is now running!')

    @client.event
    async def on_guild_join(guild: discord.Guild):
        chatbot = client.get_chatbot_model()
        client.guild_map[guild.id] = Guild(guild.id, chatbot)
        logger.info(f"\x1b[31mNew Chatbot initialized for guild={guild.id}\x1b[0m")

    @client.tree.command(name="save", description="Save the key details of the session to be loaded again at another time.")
    async def save_campaign(interaction: discord.Interaction):
        guild = client.guild_map[interaction.guild_id]
        if interaction.user == client.user:
            return 
        # set up the json data
        data = {'ID': interaction.guild_id,
                'session_history': guild.session_history, 
                'is_private': guild.is_private, 
                'reply_all_channel' : guild.replay_all_channel, 
                'is_replying_all' : guild.is_replying_all}
        # save to json
        with open('saves/' + str(interaction.guild_id) + '.json', 'w') as f:
            json.dump(data, f)

    @client.tree.command(name="load", description="Load the details of a previous session.")
    async def load_campaign(interaction: discord.Interaction):
        guild = client.guild_map[interaction.guild_id]
        if interaction.user == client.user:
            return 
        # load data from json
        try:
            with open('saves/' + str(interaction.guild_id) + '.json', 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            await interaction.response.send_message("No save file found for this server!", ephemeral=True)
            logger.warning(f"\x1b[31mNo save file found for guild={guild.id}\x1b[0m")
            return
        # set guild data from json
        guild.ID = data['ID']
        guild.session_history = data['session_history']
        guild.is_private = data['is_private']
        guild.reply_all_channel = data['reply_all_channel']
        guild.is_replying_all = data['is_replying_all']
        await interaction.response.send_message("Campaign loaded successfully!", ephemeral=True)

    #backup create version one
    @client.tree.command(name="create", description="Creates the Story by generating the DND campaign")
    async def create(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        if interaction.user == client.user:
            return
        username = str(interaction.user)
        prompt = "Begin a randomized simple Dungeon & Dragons campaign"
        channel = str(interaction.channel)
        logger.info(f"\x1b[31m{username}\x1b[0m : '{prompt}' ({channel})")
        await send_message(interaction, prompt)

    #backup continue version one
    @client.tree.command(name="continue", description="Continues a given story")
    async def prompt_continue(interaction: discord.Interaction, *, message: str):
        await interaction.response.defer(ephemeral=False)
        if interaction.user == client.user:
            return
        username = str(interaction.user)
        prompt = "Continue the story based on this input and expand upon it: " + message
        channel = str(interaction.channel)
        logger.info(f"\x1b[31m{username}\x1b[0m : '{prompt}' ({channel})")
        await send_message(interaction, prompt) 


    @client.tree.command(name="initialize", description="Setup some basic info with the DM!")
    async def initialize(interaction: discord.Interaction, *, reply_all_channel: str):
        guild = client.guild_map[interaction.guild_id]
        await interaction.response.defer(ephemeral=guild.is_private)
        if reply_all_channel:
            client.guild_map[interaction.guild_id].reply_all_channel = int(reply_all_channel)
            await interaction.followup.send("Reply all channel set!")
            logger.info(f"\x1b[31mReply all channel changed for guild={guild.id}\x1b[0m")
        else:
            await interaction.followup.send(
                "> **Warn: Bad channel ID, please try again.**"
            )
            logger.warning(f"\x1b[31mBad channel ID for guild={guild.id}\x1b[0m")

    @client.tree.command(name="chat", description="Have a chat with ChatGPT")
    async def chat(interaction: discord.Interaction, *, user_input: str):
        guild = client.guild_map[interaction.guild_id]
        if guild.is_replying_all:
            await interaction.followup.defer(ephemeral=guild.is_private)
            await interaction.followup.send(
                "> **Warn: Reply all mode is enabled. If you want to use slash command, switch to normal mode using `/replyall`**")
            logger.warning("\x1b[31mYou already on replyAll mode, can't use slash command!\x1b[0m")
            return
        if interaction.user == client.user:
            return
        username = str(interaction.user)
        channel = str(interaction.channel)
        logger.info(
            f"\x1b[31m{username}\x1b[0m : '{user_input}' ({channel})")
        await client.send_message(interaction, user_input)

    @client.tree.command(name="private", description="Toggle private access")
    async def private(interaction: discord.Interaction):
        guild = client.guild_map[interaction.guild_id]
        await interaction.response.defer(ephemeral=guild.is_private)
        if not guild.is_private:
            guild.is_private = not guild.is_private
            logger.warning("\x1b[31mSwitch to private mode\x1b[0m")
            await interaction.followup.send(
                "> **Info: Next, the response will be sent via private message. If you want to switch back to public mode, use `/public`**")
        else:
            logger.info("You already on private mode!")
            await interaction.followup.send(
                "> **Warn: You already on private mode. If you want to switch to public mode, use `/public`**")


    @client.tree.command(name="public", description="Toggle public access")
    async def public(interaction: discord.Interaction):
        guild = client.guild_map[interaction.guild_id]
        await interaction.response.defer(ephemeral=guild.is_private)
        if guild.is_private:
            guild.is_private = not guild.is_private
            await interaction.followup.send(
                "> **Info: Next, the response will be sent to the channel directly. If you want to switch back to private mode, use `/private`**")
            logger.warning("\x1b[31mSwitch to public mode\x1b[0m")
        else:
            await interaction.followup.send(
                "> **Warn: You already on public mode. If you want to switch to private mode, use `/private`**")
            logger.info("You already on public mode!")

    @client.tree.command(name="replyall", description="Toggle replyAll access")
    async def replyall(interaction: discord.Interaction):
        guild = client.guild_map[interaction.guild_id]
        await interaction.response.defer(ephemeral=guild.is_private)
        if not guild.reply_all_channel:
            await interaction.followup.send(
                "> **WARN: replyAll channel not set, please use /initialize to set a reply all channel**"
            )
            return
        if guild.is_replying_all:
            guild.is_replying_all = False
            await interaction.followup.send(
                "> **INFO: Next, the bot will response to the Slash Command. If you want to switch back to replyAll mode, use `/replyAll` again**"
            )
            logger.warning(f"\x1b[31mSwitched to normal mode for guild={guild.id}\x1b[0m")
        elif not guild.is_replying_all:
            guild.is_replying_all = True
            await interaction.followup.send(
                "> **INFO: Next, the bot will disable Slash Command and responding to all message in this channel only. If you want to switch back to normal mode, use `/replyAll` again**")
            logger.warning(f"\x1b[31mSwitch to reply all mode for guild={guild.id}\x1b[0m")

    @client.tree.command(name="reset", description="Complete reset ChatGPT conversation history")
    async def reset(interaction: discord.Interaction):
        guild = client.guild_map[interaction.guild_id]
        await interaction.response.defer(ephemeral=guild.is_private)
        client.guild_map[interaction.guild_id].chatbot = client.get_chatbot_model()
        await interaction.followup.send("> **Info: I have forgotten everything.**")
        logger.warning(
            "\x1b[31mModel has been successfully reset\x1b[0m")

    @client.tree.command(name="roll", description="Roll XdY dice!")
    async def roll(interaction: discord.Interaction, count: int, sides: int):
        response = ""
        if count <= 0 or sides <= 0:
            response = "Make sure that both count and sides are positive"
        else:
            rolls = []
            for _ in range(count):
                rolls.append(randrange(1, sides + 1))

            response = "You rolled " + str(count) + "d" + str(sides) + "!\n"
            for i in range(len(rolls)):
                response += str(rolls[i])
                if i < len(rolls) - 1:
                    response += " + "
                else:
                    response += " = " + str(sum(rolls))

        await interaction.response.send(response)

    @client.tree.command(name="help", description="Show help for the bot")
    async def help(interaction: discord.Interaction):
        guild = client.guild_map[interaction.guild_id]
        await interaction.response.defer(ephemeral=guild.is_private)
        await interaction.followup.send(""":star:**BASIC COMMANDS** \n
        - `/chat [message]` Chat with ChatGPT!
        - `/roll [<# of dice>d<# of faces>]` Roll dice! Format as 1d20, 3d6, etc.
        - `/public` ChatGPT switch to public mode 
        - `/private` ChatGPT switch to private mode
        - `/replyall` ChatGPT switch between replyall mode and default mode
        - `/reset` Clear ChatGPT conversation history\n
        For complete documentation and some tips & tricks, please visit https://github.com/cis3296s23/applebaum-projects-07-discord-chatgpt""")
        logger.info(
            f"\x1b[31mHelp command invoked in guild={guild.id}\x1b[0m")

    @client.event
    async def on_message(message):
        if isinstance(message, discord.Message):
            guild = client.guild_map[message.guild.id]
        else:
            guild = client.guild_map[message.guild_id]
        if guild.is_replying_all:
            if message.author == client.user:
                return
            if guild.reply_all_channel:
                if message.channel.id == guild.reply_all_channel:
                    username = str(message.author)
                    user_message = str(message.content)
                    channel = str(message.channel)
                    logger.info(f"\x1b[31m{username}\x1b[0m : '{user_message}' ({channel})")
                    await client.send_message(message, user_message)

    TOKEN = os.getenv("DISCORD_TOKEN")
    client.run(TOKEN)
