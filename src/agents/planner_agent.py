import os
from autogen import AssistantAgent

def setup_planner_agent(llm_config):
    return AssistantAgent(
        name="PlannerAgent",
        system_message="""You are an agent that processes and interprets user queries to understand their intent and extract key information. 
        You should have the following responsibilities: Use Natural Language Understanding (NLU) to determine the intent of each query. 
        Extract entities and key phrases from user input to gather essential details.
        Disambiguate and clarify user queries to ensure accurate and relevant responses. 
        Focus on creating a user-friendly and efficient interaction experience.

        Your first action is always call retrieve_content function.
        """,
        llm_config=llm_config,
        human_input_mode= "NEVER",
        code_execution_config=False,
    )