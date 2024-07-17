import autogen
import asyncio
from utils.utils import send_messages_to_front
from utils.config import create_openai_client, retrieve_config, config
from dotenv import load_dotenv
from autogen import GroupChat, GroupChatManager
from agents.feedback_loop_agent import setup_feedback_loop_agent
from agents.nl_to_sql_agent import setup_nl_to_sql_agent
from agents.planner_agent import setup_planner_agent
from agents.rag_pgvector_agent import setup_rag_pgvector_agent
from agents.user_proxy_agent import setup_user_proxy_agent
from typing_extensions import Annotated


# Load environment variables
load_dotenv()

# Set up configurations
openai_client = create_openai_client()
retrieve_config_ = retrieve_config(openai_client)
llm_config = config()

document_retrieval_agent = setup_rag_pgvector_agent(name="DRA", retrieve_config=retrieve_config_, client=openai_client)
user_proxy = setup_user_proxy_agent()
planner = setup_planner_agent(llm_config)
nl_to_sql = setup_nl_to_sql_agent(llm_config)
feedback_loop_agent = setup_feedback_loop_agent(llm_config)


# Define tranitions
def state_transition_manager(last_speaker, groupchat):

    if last_speaker is user_proxy:
        print("-------------> time for PLANNER")
        return planner
    
    elif last_speaker is planner:
        print("-------------> time for Content analysis")
        return nl_to_sql
    
    elif last_speaker is nl_to_sql and "terminate" in groupchat.messages[-1]["content"].lower():
        print("-------------> time for User Proxy")
        return user_proxy

    elif last_speaker is nl_to_sql:
        print("-------------> time for Feedback")
        return feedback_loop_agent
    
    elif last_speaker is feedback_loop_agent:
        print("-------------> time for Content analysis")
        return nl_to_sql
    
    else:
        return "auto"
    
def _reset_agents():
    user_proxy.reset()
    planner.reset()
    document_retrieval_agent.reset()
    nl_to_sql.reset()
    feedback_loop_agent.reset()

async def call_rag_chat(task, websocket=None):
    _reset_agents()

    def retrieve_content(
        message: Annotated[
            str,
            "Refined message which keeps the original meaning and can be used to retrieve content for question answering.",
        ],
        n_results: Annotated[int, "number of results"] = 3,
    ) -> str:
        document_retrieval_agent.n_results = n_results
        # Check if we need to update the context.
        update_context_case1, update_context_case2 = document_retrieval_agent._check_update_context(message)
        print(f"Update_context_1: ")
        if (update_context_case1 or update_context_case2) and document_retrieval_agent.update_context:
            document_retrieval_agent.problem = message if not hasattr(document_retrieval_agent, "problem") else document_retrieval_agent.problem
            _, ret_msg = document_retrieval_agent._generate_retrieve_user_reply(message)
        else:
            _context = {"problem": message, "n_results": n_results}
            ret_msg = document_retrieval_agent.message_generator(document_retrieval_agent, None, _context)
        return ret_msg if ret_msg else message

    agents = [user_proxy, planner, nl_to_sql, feedback_loop_agent]

    # for agent in agents:
    #         agent.register_reply(
    #             [autogen.Agent, None],
    #             reply_func=send_messages_to_front,
    #             config={"websocket_manager" : websocket_manager, "websocket": websocket}
    #         )

    document_retrieval_agent.human_input_mode = "NEVER"

    for caller in [planner]:
        d_retrieve_content = caller.register_for_llm(
            description= " Retrieve content for question answering", api_style="function"
        )(retrieve_content)


    for executor in agents:
        executor.register_for_execution()(d_retrieve_content)

    groupchat = GroupChat(
        agents=agents,
        messages=[],
        max_round=12,
        speaker_selection_method=state_transition_manager,
        allow_repeat_speaker=False,
    )

    manager = GroupChatManager(groupchat=groupchat, llm_config=llm_config)

    # Start chatting with the boss as this is the user proxy agent.
    await user_proxy.a_initiate_chat(
        manager,
        message=task,
    )

    return groupchat.messages

if __name__ == "__main__":
    asyncio.run(call_rag_chat("Retrieve all users with their email addresses"))
