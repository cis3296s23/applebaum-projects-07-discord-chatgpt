import os
import discord
from src import log, responses
from dotenv import load_dotenv
from discord import app_commands
from revChatGPT.V3 import Chatbot
from asgiref.sync import sync_to_async
from typing import TypedDict

logger = log.setup_logger(__name__)
load_dotenv()

class Guild:
    def __init__(self, guild_chatbot, guild_is_replying_all, guild_reply_all_channel):
        self.chatbot = guild_chatbot
        self.is_replying_all = guild_is_replying_all
        self.reply_all_channel = guild_reply_all_channel

class Client(discord.Client):
    def __init__(self) -> None:
        config_dir = os.path.abspath(f"{__file__}/../../")
        prompt_name = 'system-prompt.txt'
        prompt_path = os.path.join(config_dir, prompt_name)
        with open(prompt_path, "r", encoding="utf-8") as f:
            self.prompt = f.read()

        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)

        self.tree = app_commands.CommandTree(self)
        self.activity = discord.Activity(type=discord.ActivityType.listening, name="/help")
        self.isPrivate = False
        self.is_replying_all = False
        self.openAI_API_key = os.getenv("OPENAI_KEY")
        self.openAI_gpt_engine = os.getenv("ENGINE")
        self.guild_map = TypedDict('guild_map', {"guild_id":int, "guild": Guild})

    async def send_message(self, message: discord.Interaction, user_message):
        if not self.is_replying_all:
            author = message.user.id
            await message.response.defer(ephemeral=False)
        else:
            author = message.channel.id
        try:
            response = (f'> **{user_message}** - <@{str(author)}' + '> \n\n')
            guild = self.guild_map[message.guild_id]
            response = f"{response}{await responses.handle_response(user_message, guild.chatbot)}"
            char_limit = 1900
            if len(response) > char_limit:
                # Split the response into smaller chunks of no more than 1900 characters each(Discord limit is 2000 per chunk)
                response_chunks = [response[i:i + char_limit] for i in range(0, len(response), char_limit)]
                for chunk in response_chunks:
                    if self.is_replying_all:
                        await message.channel.send(chunk)
                    else:
                        await message.followup.send(chunk)
            elif self.is_replying_all:
                await message.channel.send(response)
            else:
                await message.followup.send(response)
        except Exception as e:
            if self.is_replying_all:
                await message.channel.send("> **ERROR: Something went wrong, please try again later!**")
            else:
                await message.followup.send("> **ERROR: Something went wrong, please try again later!**")
            logger.exception(f"Error while sending message: {e}")

    async def send_start_prompt(self, interaction):
        import os.path

        config_dir = os.path.abspath(f"{__file__}/../../")
        prompt_name = 'system-prompt.txt'
        prompt_path = os.path.join(config_dir, prompt_name)
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                prompt = f.read()
                logger.info(f"Send system prompt with size {len(prompt)}")
                chatbot = self.guild_map[interaction.guild_id]
                response = await sync_to_async(chatbot.ask)(prompt)
                await interaction.followup.send(response)
                logger.info(f"System prompt response:{response}")
        except Exception as e:
            logger.exception(f"Error while sending system prompt: {e}")

    def get_chatbot_model(self) -> Chatbot:
        return Chatbot(api_key=self.openAI_API_key, engine=self.openAI_gpt_engine, system_prompt=self.prompt)


client = Client()
