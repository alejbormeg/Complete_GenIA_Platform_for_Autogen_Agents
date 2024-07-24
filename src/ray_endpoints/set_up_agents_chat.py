from ray import serve

@serve.deployment()
class RAGChatEndpoint:
    def __init__(self) -> None:
        from utils.utils import send_messages_to_front
        from utils.config import create_openai_client, retrieve_config, config
        from agents.feedback_loop_agent import setup_feedback_loop_agent
        from agents.nl_to_sql_agent import setup_nl_to_sql_agent
        from agents.planner_agent import setup_planner_agent
        from agents.rag_pgvector_agent import setup_rag_pgvector_agent
        from agents.user_proxy_agent import setup_user_proxy_agent

        # These are now initialized within the instance to avoid serialization issues.
        self.openai_client = create_openai_client()
        self.retrieve_config_ = retrieve_config(self.openai_client)
        self.llm_config = config()
        
        self.document_retrieval_agent = setup_rag_pgvector_agent(name="DRA", retrieve_config=self.retrieve_config_, client=self.openai_client)
        self.user_proxy = setup_user_proxy_agent()
        self.planner = setup_planner_agent(self.llm_config)
        self.nl_to_sql = setup_nl_to_sql_agent(self.llm_config)
        self.feedback_loop_agent = setup_feedback_loop_agent(self.llm_config)

    async def call_rag_chat(self, task, database=None):
        from autogen import GroupChat, GroupChatManager
        from typing_extensions import Annotated
        from agents.rag_pgvector_agent import setup_rag_pgvector_agent

        if database:
            self.document_retrieval_agent = setup_rag_pgvector_agent(name="DRA", retrieve_config=self.retrieve_config_, client=self.openai_client, database=database)
 
        # Reset and setup agents - ideally this should be encapsulated in methods or managed statefully
        self.user_proxy.reset()
        self.planner.reset()
        self.document_retrieval_agent.reset()
        self.nl_to_sql.reset()
        self.feedback_loop_agent.reset()

        def retrieve_content(
            message: Annotated[
                str,
                "Refined message which keeps the original meaning and can be used to retrieve content for question answering.",
            ],
            n_results: Annotated[int, "number of results"] = 3,
        ) -> str:
            self.document_retrieval_agent.n_results = n_results
            # Check if we need to update the context.
            update_context_case1, update_context_case2 = self.document_retrieval_agent._check_update_context(message)
            print(f"Update_context_1: ")
            if (update_context_case1 or update_context_case2) and self.document_retrieval_agent.update_context:
                self.document_retrieval_agent.problem = message if not hasattr(self.document_retrieval_agent, "problem") else self.document_retrieval_agent.problem
                _, ret_msg = self.document_retrieval_agent._generate_retrieve_user_reply(message)
            else:
                _context = {"problem": message, "n_results": n_results}
                ret_msg = self.document_retrieval_agent.message_generator(self.document_retrieval_agent, None, _context)
            return ret_msg if ret_msg else message
    
        agents = [self.user_proxy, self.planner, self.nl_to_sql, self.feedback_loop_agent]

        self.document_retrieval_agent.human_input_mode = "NEVER"

        for caller in [self.planner]:
            d_retrieve_content = caller.register_for_llm(
                description= "Retrieve content for question answering", api_style="function"
            )(retrieve_content)

        for executor in agents:
            executor.register_for_execution()(d_retrieve_content)

        # Initialize chat components and start chatting process
        groupchat = GroupChat(
            agents=[self.user_proxy, self.planner, self.nl_to_sql, self.feedback_loop_agent],
            messages=[],
            max_round=12,
            speaker_selection_method=self.state_transition_manager,
            allow_repeat_speaker=False,
        )
        manager = GroupChatManager(groupchat=groupchat, llm_config=self.llm_config)
        
        if database:
            task = task + f"\n\nThe database is {database}"

        await self.user_proxy.a_initiate_chat(manager, message=task)
        return groupchat.messages

    # Define tranitions
    def state_transition_manager(self, last_speaker, groupchat):

        if last_speaker is self.user_proxy:
            print("-------------> time for PLANNER")
            return self.planner
        
        elif last_speaker is self.planner:
            print("-------------> time for Content analysis")
            return self.nl_to_sql
        
        elif last_speaker is self.nl_to_sql and "terminate" in groupchat.messages[-1]["content"].lower():
            print("-------------> time for User Proxy")
            return self.user_proxy

        elif last_speaker is self.nl_to_sql:
            print("-------------> time for Feedback")
            return self.feedback_loop_agent
        
        elif last_speaker is self.feedback_loop_agent:
            print("-------------> time for Content analysis")
            return self.nl_to_sql
        
        else:
            return "auto"
