import os
import discord
import openai
from random import randrange
from src.client import client
from discord import app_commands
from src import log, responses

logger = log.setup_logger(__name__)

async def send_message(message, user_message):
    global isReplyAll
    if not isReplyAll:
        author = message.user.id
        await message.response.defer(ephemeral=isPrivate)
    else:
        author = message.author.id
    try:
        response = '> **' + user_message + '** - <@' + \
            str(author) + '> \n\n'
        response = f"{response}{await responses.handle_response(user_message)}"
        if len(response) > 1900:
            # Split the response into smaller chunks of no more than 1900 characters each(Discord limit is 2000 per chunk)
            if "```" in response:
                # Split the response if the code block exists
                parts = response.split("```")
                # Send the first message
                if isReplyAll:
                    await message.channel.send(parts[0])
                else:
                    await message.followup.send(parts[0])
                # Send the code block in a seperate message
                code_block = parts[1].split("\n")
                formatted_code_block = ""
                for line in code_block:
                    while len(line) > 1900:
                        # Split the line at the 50th character
                        formatted_code_block += line[:1900] + "\n"
                        line = line[1900:]
                    formatted_code_block += line + "\n"  # Add the line and seperate with new line

                # Send the code block in a separate message
                if (len(formatted_code_block) > 2000):
                    code_block_chunks = [formatted_code_block[i:i+1900]
                                         for i in range(0, len(formatted_code_block), 1900)]
                    for chunk in code_block_chunks:
                        if isReplyAll:
                            await message.channel.send("```" + chunk + "```")
                        else:
                            await message.followup.send("```" + chunk + "```")
                else:
                    if isReplyAll:
                        await message.channel.send("```" + formatted_code_block + "```")
                    else:
                        await message.followup.send("```" + formatted_code_block + "```")
                # Send the remaining of the response in another message

                if len(parts) >= 3:
                    if isReplyAll:
                        await message.channel.send(parts[2])
                    else:
                        await message.followup.send(parts[2])
            else:
                response_chunks = [response[i:i+1900]
                                   for i in range(0, len(response), 1900)]
                for chunk in response_chunks:
                    if isReplyAll:
                        await message.channel.send(chunk)
                    else:
                        await message.followup.send(chunk)
                        
        else:
            if isReplyAll:
                await message.channel.send(response)
            else:
                await message.followup.send(response)
    except Exception as e:
        if isReplyAll:
            await message.channel.send("> **Error: Something went wrong, please try again later!**")
        else:
            await message.followup.send("> **Error: Something went wrong, please try again later!**")
        logger.exception(f"Error while sending message: {e}")


async def send_start_prompt(client):
    import os.path

    config_dir = os.path.abspath(__file__ + "/../../")
    prompt_name = 'starting-prompt.txt'
    prompt_path = os.path.join(config_dir, prompt_name)
    discord_channel_id = os.getenv("DISCORD_CHANNEL_ID")
    try:
        if os.path.isfile(prompt_path) and os.path.getsize(prompt_path) > 0:
            with open(prompt_path, "r") as f:
                prompt = f.read()
                if (discord_channel_id):
                    logger.info(f"Send starting prompt with size {len(prompt)}")
                    responseMessage = await responses.handle_response(prompt)
                    channel = client.get_channel(int(discord_channel_id))
                    await channel.send(responseMessage)
                    logger.info(f"Starting prompt response:{responseMessage}")
                else:
                    logger.info("No Channel selected. Skip sending starting prompt.")
        else:
            logger.info(f"No {prompt_name}. Skip sending starting prompt.")
    except Exception as e:
        logger.exception(f"Error while sending starting prompt: {e}")


def run_discord_bot():

    @client.event
    async def on_ready():
        await client.send_start_prompt()
        await client.tree.sync()
        logger.info(f'{client.user} is now running!')

    @client.tree.command(name="chat", description="Have a chat with ChatGPT")
    async def chat(interaction: discord.Interaction, *, message: str):
        if client.is_replying_all == "True":
            await interaction.response.defer(ephemeral=False)
            await interaction.followup.send(
                "> **Warn: You already on replyAll mode. If you want to use slash command, switch to normal mode, use `/replyall` again**")
            logger.warning("\x1b[31mYou already on replyAll mode, can't use slash command!\x1b[0m")
            return
        if interaction.user == client.user:
            return
        username = str(interaction.user)
        channel = str(interaction.channel)
        logger.info(
            f"\x1b[31m{username}\x1b[0m : '{message}' ({channel})")
        await send_message(interaction, message)

    @client.tree.command(name="private", description="Toggle private access")
    async def private(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        if not client.isPrivate:
            client.isPrivate = not client.isPrivate
            logger.warning("\x1b[31mSwitch to private mode\x1b[0m")
            await interaction.followup.send(
                "> **Info: Next, the response will be sent via private message. If you want to switch back to public mode, use `/public`**")
        else:
            logger.info("You already on private mode!")
            await interaction.followup.send(
                "> **Warn: You already on private mode. If you want to switch to public mode, use `/public`**")

    @client.tree.command(name="public", description="Toggle public access")
    async def public(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        if client.isPrivate:
            client.isPrivate = not client.isPrivate
            await interaction.followup.send(
                "> **Info: Next, the response will be sent to the channel directly. If you want to switch back to private mode, use `/private`**")
            logger.warning("\x1b[31mSwitch to public mode\x1b[0m")
        else:
            await interaction.followup.send(
                "> **Warn: You already on public mode. If you want to switch to private mode, use `/private`**")
            logger.info("You already on public mode!")

    @client.tree.command(name="replyall", description="Toggle replyAll access")
    async def replyall(interaction: discord.Interaction):
        client.replying_all_discord_channel_id = str(interaction.channel_id)
        await interaction.response.defer(ephemeral=False)
        if client.is_replying_all == "True":
            client.is_replying_all = "False"
            await interaction.followup.send(
                "> **INFO: Next, the bot will response to the Slash Command. If you want to switch back to replyAll mode, use `/replyAll` again**")
            logger.warning("\x1b[31mSwitch to normal mode\x1b[0m")
        elif client.is_replying_all == "False":
            client.is_replying_all = "True"
            await interaction.followup.send(
                "> **INFO: Next, the bot will disable Slash Command and responding to all message in this channel only. If you want to switch back to normal mode, use `/replyAll` again**")
            logger.warning("\x1b[31mSwitch to replyAll mode\x1b[0m")


    @client.tree.command(name="reset", description="Complete reset ChatGPT conversation history")
    async def reset(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        client.chatbot = client.get_chatbot_model()
        await interaction.followup.send("> **Info: I have forgotten everything.**")
        logger.warning(
            "\x1b[31mModel has been successfully reset\x1b[0m")

    @client.tree.command(name="help", description="Show help for the bot")
    async def help(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        await interaction.followup.send(""":star:**BASIC COMMANDS** \n
        - `/chat [message]` Chat with ChatGPT!
        - `/public` ChatGPT switch to public mode 
        - `/private` ChatGPT switch to private mode
        - `/replyall` ChatGPT switch between replyall mode and default mode
        - `/reset` Clear ChatGPT conversation history\n
        For complete documentation, please visit https://github.com/Zero6992/chatGPT-discord-bot""")
        logger.info(
            "\x1b[31mSomeone need help!\x1b[0m")

    @client.event
    async def on_message(message):
        if client.is_replying_all == "True":
            if message.author == client.user:
                return
            if client.replying_all_discord_channel_id:
                if message.channel_id == int(client.replying_all_discord_channel_id):
                    username = str(message.author)
                    user_message = str(message.content)
                    channel = str(message.channel)
                    logger.info(f"\x1b[31m{username}\x1b[0m : '{user_message}' ({channel})")
                    await client.send_message(message, user_message)
    
    TOKEN = os.getenv("DISCORD_BOT_TOKEN")
    client.run(TOKEN)