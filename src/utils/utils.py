import json
from typing import Annotated, Optional, Dict


async def send_message(
    agents_chat: Annotated[Optional[Dict], "Dictionary containing the latest chat state from agents, if available."] = None,
    user_chat: Annotated[Optional[Dict], "Dictionary containing the latest chat response to the user, if available."] = None,
    websocket_manager = None,
    websocket = None
) -> None:
    """
    Sends a structured message to the front-end application via a WebSocket connection.

    This function serializes a dictionary containing optional fields of agents' chat state, user responses, and updated KPIs into a JSON string, and sends this information over an established WebSocket connection specified by the connection ID.

    Parameters:
        connection_id (str): The identifier for the WebSocket connection through which the message will be sent.
        agents_chat (Optional[Dict]): The latest state of chat from agents as a dictionary.
        user_chat (Optional[Dict]): The latest response for the user as a dictionary.
        updated_kpis (Optional[Dict]): Updated key performance indicators if they need to be communicated.

    Raises:
        conn.exceptions.GoneException: If the WebSocket connection no longer exists (i.e., the connection ID is no longer valid).
        Exception: For any other unexpected errors that occur during the post to connection.
    """

    result = {
        "agents_chat": agents_chat,
        "user_chat": user_chat,
    }

    try:
        message = json.dumps(result)
        await websocket_manager.send_message_to_connection(websocket, message)
    except Exception as e:
        print(f"Unexpected error during post_to_connection: {e}")

async def send_messages_to_front(recipient, messages, sender, config):
    """
    Sends the latest response from an Autogen Agent to the front end via a WebSocket connection.

    This function is registered as a reply function for each Autogen Agent. It facilitates real-time communication by sending the response of each agent during a chat session through a WebSocket, managing the connection lifecycle and handling any connection errors that may arise.

    Parameters:
        recipient (str): The identifier for the recipient. This could be a user ID or session ID.
        messages (list): A list of message strings where the last message is the most recent response from the agent.
        sender (str): The identifier of the sender, typically the agent's name or ID.
        config (dict): Configuration dictionary which may include settings necessary for message transmission such as API keys or other parameters.

    Returns:
        None

    Raises:
        conn.exceptions.GoneException: If the WebSocket connection no longer exists.
        Exception: For any other unexpected errors during message sending.

    Note:
        This function assumes that `request_context` contains a valid "ConnectionId" used for the WebSocket connection.
    """

    websocket_manager = config.get("websocket_manager")
    websocket = config.get("websocket")
    if messages and isinstance(messages[-1], dict):
        last_message_content = messages[-1].get("content", "")

        if last_message_content == "":
            messages[-1]["content"] = "Agents are working on the request..."
        elif "TERMINATE" in last_message_content:
            messages[-1]["content"] = last_message_content.replace("TERMINATE", "")

    await send_message(agents_chat=messages[-1], websocket_manager=websocket_manager, websocket=websocket)

    return False, None