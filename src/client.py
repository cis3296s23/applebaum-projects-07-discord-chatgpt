import os
import discord
from src import log, responses
from dotenv import load_dotenv
from discord import app_commands
from revChatGPT.V3 import Chatbot

logger = log.setup_logger(__name__)
load_dotenv()

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
        self.activity = discord.Activity(type=discord.ActivityType.listening, name="/chat | /help")
        self.isPrivate = False
        self.is_replying_all = os.getenv("REPLYING_ALL")
        self.replying_all_discord_channel_id = os.getenv("REPLY_ALL_CHANNEL_ID")
        self.openAI_API_key = os.getenv("OPENAI_KEY")
        self.openAI_gpt_engine = os.getenv("ENGINE")
        self.chatbot = self.get_chatbot_model()

    async def send_message(self, message, user_message):
        if self.is_replying_all == "False":
            author = message.user.id
            await message.response.defer(ephemeral=self.isPrivate)
        else:
            author = message.channel.id
        try:
            response = (f'> **{user_message}** - <@{str(author)}' + '> \n\n')
            response = f"{response}{await responses.handle_response(user_message, self)}"
            char_limit = 1900
            if len(response) > char_limit:
                # Split the response into smaller chunks of no more than 1900 characters each(Discord limit is 2000 per chunk)
                response_chunks = [response[i:i + char_limit] for i in range(0, len(response), char_limit)]
                for chunk in response_chunks:
                    if self.is_replying_all == "True":
                        await message.channel.send(chunk)
                    else:
                        await message.followup.send(chunk)
            elif self.is_replying_all == "True":
                await message.channel.send(response)
            else:
                await message.followup.send(response)
        except Exception as e:
            if self.is_replying_all == "True":
                await message.channel.send("> **ERROR: Something went wrong, please try again later!**")
            else:
                await message.followup.send("> **ERROR: Something went wrong, please try again later!**")
            logger.exception(f"Error while sending message: {e}")

    async def send_start_prompt(self):
        import os.path

        config_dir = os.path.abspath(f"{__file__}/../../")
        prompt_name = 'system-prompt.txt'
        prompt_path = os.path.join(config_dir, prompt_name)
        discord_channel_id = os.getenv("DISCORD_CHANNEL_ID")
        try:
            if os.path.isfile(prompt_path) and os.path.getsize(prompt_path) > 0:
                with open(prompt_path, "r", encoding="utf-8") as f:
                    prompt = f.read()
                    if discord_channel_id:
                        logger.info(f"Send system prompt with size {len(prompt)}")
                        response = ""
                        response = f"{response}{await responses.handle_response(prompt, self)}"
                        channel = self.get_channel(int(discord_channel_id))
                        await channel.send(response)
                        logger.info(f"System prompt response:{response}")
                    else:
                        logger.info("No Channel selected. Skip sending system prompt.")
            else:
                logger.info(f"No {prompt_name}. Skip sending system prompt.")
        except Exception as e:
            logger.exception(f"Error while sending system prompt: {e}")

    def get_chatbot_model(self) -> Chatbot:
        return Chatbot(api_key=self.openAI_API_key, engine=self.openAI_gpt_engine, system_prompt=self.prompt)


client = Client()
