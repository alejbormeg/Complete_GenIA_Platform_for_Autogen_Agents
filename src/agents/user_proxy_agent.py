import os
from autogen import UserProxyAgent

def setup_user_proxy_agent():

    return UserProxyAgent(
        name="User proxy agent",
        system_message="A human admin. Manages the user interactions and interfaces, ensuring seamless communication between the user and the system",
        code_execution_config=False,
        human_input_mode="NEVER",
        is_termination_msg=lambda msg: "terminate" in msg["content"].lower(),
    )