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
        client.guild_map[1075881043585937529] = Guild(1075881043585937529,
                                                      client.get_chatbot_model())  # Test server guild
        client.guild_map[1075881043585937529].reply_all_channel = "1093237764570484796"
        await client.tree.sync()
        logger.info(f'{client.user} is now running!')

    @client.event
    async def on_guild_join(guild: discord.Guild):
        chatbot = client.get_chatbot_model()
        client.guild_map[guild.id] = Guild(guild.id, chatbot)
        logger.info(f"\x1b[31mNew Chatbot initialized for guild={guild.id}\x1b[0m")

    @client.tree.command(name="save",
                         description="Save the key details of the session to be loaded again at another time.")
    async def save_campaign(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        guild = client.guild_map[interaction.guild_id]
        if interaction.user == client.user:
            return 
        # set up the json data
        data = {'guild_id': guild.id,
                'session_history': guild.session_history, 
                'is_private': guild.is_private, 
                'reply_all_channel' : guild.reply_all_channel,
                'is_replying_all' : guild.is_replying_all}
        # save to json
        with open('saves/' + str(guild.id) + '.json', 'w') as f:
            json.dump(data, f)
            await interaction.followup.send("Campaign saved!")
            
    @client.tree.command(name="load", description="Load the details of a previous session.")
    async def load_campaign(interaction: discord.Interaction):
        guild = client.guild_map[interaction.guild_id]
        await interaction.response.defer(ephemeral=True)

        if interaction.user == client.user:
            return 
        # load data from json
        try:
            with open('saves/' + str(guild.id) + '.json', 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            await interaction.followup.send("No save file found for this server!", ephemeral=guild.is_private)
            logger.warning(f"\x1b[31mNo save file found for guild={guild.id}\x1b[0m")
            return
        # set guild data from json
        guild.id = data['guild_id']
        guild.session_history = data['session_history']
        guild.is_private = data['is_private']
        guild.reply_all_channel = data['reply_all_channel']
        guild.is_replying_all = data['is_replying_all']
        #creating prompt -> passing to chatbot initializer --> chatbot knows --> continue from there
        prompt = client.prompt + ' The story so far is the following in quotes: \n "' + guild.session_history + "\""
        guild.chatbot = client.get_chatbot_model(prompt)
        
        await interaction.followup.send("Campaign loaded successfully!", ephemeral=guild.is_private)

    @client.tree.command(name="chat", description="Send a message to the Dungeon Master!")
    async def chat(interaction: discord.Interaction, *, user_input: str):
        guild = client.guild_map[interaction.guild_id]
        if guild.is_replying_all:
            await interaction.followup.defer(ephemeral=guild.is_private)
            await interaction.followup.send(
                "> **Warn: Slash commands disabled in reply all mode. If you want to use slash command, switch to normal mode using `/replyall`**"
            )
            return
        if interaction.user == client.user:
            return
        username = str(interaction.user)
        channel = str(interaction.channel)
        logger.info(
            f"\x1b[31m{username}\x1b[0m : '{user_input}' ({channel})")
        await client.send_message(interaction, user_input)

    @client.tree.command(name="private", description="Enable private mode!")
    async def private(interaction: discord.Interaction):
        guild = client.guild_map[interaction.guild_id]
        await interaction.response.defer(ephemeral=guild.is_private)
        if not guild.is_private:
            guild.is_private = not guild.is_private
            logger.warning(f"\x1b[31mSwitch to private mode in guild={guild.id}\x1b[0m")
            await interaction.followup.send(
                "> **Info: Responses are now private. If you want to switch back to public mode, use `/public`**"
            )
        else:
            await interaction.followup.send(
                "> **Warn: You already on private mode. If you want to switch to public mode, use `/public`**"
            )

    @client.tree.command(name="public", description="Enable public mode!")
    async def public(interaction: discord.Interaction):
        guild = client.guild_map[interaction.guild_id]
        await interaction.response.defer(ephemeral=guild.is_private)
        if guild.is_private:
            guild.is_private = not guild.is_private
            await interaction.followup.send(
                "> **Info: Responses are now public. If you want to switch back to private mode, use `/private`**")
            logger.warning(f"\x1b[31mSwitched to public mode in guild={guild.id}\x1b[0m")
        else:
            await interaction.followup.send(
                "> **Warn: You already on public mode. If you want to switch to private mode, use `/private`**")

    @client.tree.command(name="replyall", description="Enable reply all mode!")
    async def replyall(interaction: discord.Interaction, reply_all_channel: str = ""):
        guild = client.guild_map[interaction.guild_id]
        await interaction.response.defer(ephemeral=guild.is_private)
        # Optionally change reply all channel
        if reply_all_channel != "":
            guild.reply_all_channel = int(reply_all_channel)
            logger.info(f"\x1b[31mReply all channel changed for guild={guild.id}\x1b[0m")
        # Check if reply all channel exists
        if not guild.reply_all_channel:
            await interaction.followup.send(
                "> **WARN: replyAll channel not set, please use /initialize to set a reply all channel**")
            return
        # Disable reply all mode
        if guild.is_replying_all:
            guild.is_replying_all = False
            await interaction.followup.send(
                "> **INFO: Reply all mode disabled. If you want to switch back to replyAll mode, use `/replyall` again**")
            logger.warning(f"\x1b[31mSwitch to normal mode in guild={guild.id}\x1b[0m")
        # Enable reply all mode
        else:
            guild.is_replying_all = True
            await interaction.followup.send(
                "> **INFO: Reply all mode enabled. If you want to switch back to normal mode, use `/replyall` again**")
            logger.warning(f"\x1b[31mSwitch to replyAll mode in guild={guild.id}\x1b[0m")

    @client.tree.command(name="reset",
                         description="Reset ChatGPT conversation history and optionally give it a new starter prompt!")
    async def reset(interaction: discord.Interaction, prompt: str = ""):
        guild = client.guild_map[interaction.guild_id]
        await interaction.response.defer(ephemeral=guild.is_private)
        client.guild_map[interaction.guild_id].chatbot = client.get_chatbot_model(prompt)
        await interaction.followup.send(
            "> **Info: I have forgotten everything. If you gave a new prompt, your next /chat will be with the new Dungeon Master!**")
        logger.warning(
            f"\x1b[31mModel has been successfully reset in guild={guild.id}\x1b[0m"
        )

    @client.tree.command(name="roll", description="Roll XdY dice!")
    async def roll(interaction: discord.Interaction, count: int, sides: int):
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


    @client.tree.command(name="help", description="Show help message!")
    async def help(interaction: discord.Interaction):
        guild = client.guild_map[interaction.guild_id]
        await interaction.response.defer(ephemeral=guild.is_private)
        await interaction.followup.send(f"""**BASIC COMMANDS** \n
        - `/chat [message]` {client.tree.get_command("chat").description}
        - `/roll [<# of dice>d<# of faces>]` {client.tree.get_command("roll").description}
        - `/save` {client.tree.get_command("save").description}
        - `/load` {client.tree.get_command("load").description}
        - `/public` {client.tree.get_command("public").description}
        - `/private` {client.tree.get_command("private").description}
        - `/replyall` {client.tree.get_command("replyall").description}
        - `/reset` {client.tree.get_command("reset").description}
        - `/help` Show this message! \n
        For complete documentation and some tips & tricks, please visit https://github.com/cis3296s23/applebaum-projects-07-discord-chatgpt""")
        logger.info(
            f"\x1b[31mSomeone needs help in guild={guild.id}\x1b[0m"
        )

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
