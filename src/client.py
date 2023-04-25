import os
import discord
import json
from src import log
from dotenv import load_dotenv
from discord import app_commands
from revChatGPT.V3 import Chatbot
from asgiref.sync import sync_to_async

logger = log.setup_logger(__name__)
load_dotenv()


class Guild:
    def __init__(self, guild_id, guild_chatbot):
        self.id = guild_id
        self.chatbot = guild_chatbot
        self.is_replying_all = False
        self.reply_all_channel = None
        self.is_private = False
        self.session_history = ""


def chunkify(response: str) -> list:
    """Break a response into 1900 character or fewer chunks

    Keyword arguments:
    response -- the message needing chunked
    """
    char_limit = 1900
    return [response[i:i + char_limit] for i in range(0, len(response), char_limit)]


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
        self.openAI_API_key = os.getenv("OPENAI_KEY")
        self.openAI_gpt_engine = os.getenv("ENGINE")
        self.guild_map = {}
        self.session_history = ""

    async def send_message(self, message: discord.Interaction, user_input):
        if isinstance(message, discord.Message):
            guild = self.guild_map[message.guild.id]
        else:
            guild = self.guild_map[message.guild_id]
        if not guild.is_replying_all:
            author = message.user.id
            await message.response.defer(ephemeral=guild.is_private)
        else:
            author = message.channel.id
        try:
            # Format initial response string
            response = (f'> **{user_input}** - <@{str(author)}' + '> \n\n')
            # Pass input to chatgpt asynchronously
            response = f"{response}{await sync_to_async(guild.chatbot.ask)(user_input)}"
            # Save the state
            self.session_history += message.content + "\n"
            self.session_history += response + "\n"
            # Split the response into smaller chunks of no more than 1900 characters each(Discord limit is 2000 per chunk)
            response_chunks = chunkify(response)
            for chunk in response_chunks:
                if guild.is_replying_all:
                    await message.channel.send(chunk)
                else:
                    await message.followup.send(chunk, ephemeral=guild.is_private)
                logger.info(f"\x1b[31mChunk sent in guild={guild.id}\x1b[0m")
        except Exception as e:
            if guild.is_replying_all:
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
                guild = self.guild_map[interaction.guild_id]
                chatbot = guild.chatbot
                response = await sync_to_async(chatbot.ask)(prompt)
                await interaction.followup.send(response)
                logger.info(f"System prompt sent for guild={guild.id}")
        except Exception as e:
            logger.exception(f"Error while sending system prompt: {e}")

    def get_chatbot_model(self) -> Chatbot:
        """Instantiate and return a new OpenAI Chatbot object witht the default system prompt"""
        return Chatbot(api_key=self.openAI_API_key, engine=self.openAI_gpt_engine, system_prompt=self.prompt)


client = Client()
