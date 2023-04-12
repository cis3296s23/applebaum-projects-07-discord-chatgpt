from asgiref.sync import sync_to_async

async def handle_response(message, client) -> str:
    return await sync_to_async(client.chatbot.ask)(message)