from autogen import ConversableAgent


def setup_nl_to_sql_agent(llm_config: dict):

    return ConversableAgent(
        name="NL2SQL",
        system_message="""
        Your primary role is to convert natural language queries into accurate and efficient SQL queries. 
        Focus on understanding the user's intent and the context of the database schema provided. 
        Your responses should be precise and optimized for the given database structure. 
        Ensure you can handle a variety of query types and complexities, providing reliable and accurate SQL statements.
        Once you have generated the final SQL query, respond with the query followed by 'Terminate' to end the conversation.
        """,
        llm_config=llm_config,
        human_input_mode="NEVER",
        code_execution_config=False,
    )
