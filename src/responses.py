from asgiref.sync import sync_to_async


async def handle_response(message, chatbot) -> str:
    return await sync_to_async(chatbot.ask)(message)
