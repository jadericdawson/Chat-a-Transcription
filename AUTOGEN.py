### AUTOGEN ### Retrieval Augmented Generation ##

import autogen
import pinecone
import os
from autogen.agentchat.contrib.retrieve_user_proxy_agent import RetrieveUserProxyAgent
from autogen import AssistantAgent
import chromadb


class AUTOGEN():
    def __init__(self, path):
        self.docs_path = path
        self.config_list = autogen.config_list_from_json(
            "OAI_CONFIG_LIST.json",
            file_location = "/home/jadericdawson/Documents/EZSI/AUTOGEN",
            filter_dict = {
                "model": ["gpt-3.5-turbo", "gpt-35-turbo", "gpt-35-turbo-0613", "gpt-4", "gpt4", "gpt-4-32k", "gpt-3.5-turbo-16k"],
            },
            
        )
        print(self.config_list)              ############PRINT###############

        self.llm_config = {
            "request_timeout": 120,
            "seed": 42,
            "config_list": self.config_list,
            "temperature": 0,
        }

        autogen.ChatCompletion.start_logging()
        termination_msg = lambda x: isinstance(x, dict) and "TERMINATE" == str(x.get("content", ""))[-9:].upper()

        self.boss = autogen.UserProxyAgent(
            name="Boss",
            is_termination_msg=termination_msg,
            human_input_mode="TERMINATE",
            system_message="The boss who ask questions and give tasks.",
            code_execution_config=False,  # we don't want to execute code in this case.
        )

        self.planner = autogen.AssistantAgent(
            name="planner",
            llm_config=self.llm_config,
            # the default system message of the AssistantAgent is overwritten here
            system_message="You are a helpful AI assistant. You suggest coding and reasoning steps for another AI assistant to accomplish a task. Do not suggest concrete code. For any action beyond writing code or reasoning, convert it to a step that can be implemented by writing code. For example, browsing the web can be implemented by writing code that reads and prints the content of a web page. Finally, inspect the execution result. If the plan is not good, suggest a better plan. If the execution is wrong, analyze the error and suggest a fix."
        )
        self.planner_user = autogen.UserProxyAgent(
            name="planner_user",
            max_consecutive_auto_reply=0,  # terminate without auto-reply
            human_input_mode="NEVER",
        )

        
        # create an AssistantAgent instance named "assistant"
        self.assistant = autogen.AssistantAgent(
            name="assistant",
            llm_config={
                "temperature": 0,
                "timeout": 600,
                "seed": 42,
                "config_list": self.config_list,
                "functions": [
                    {
                        "name": "ask_planner",
                        "description": "ask planner to: 1. get a plan for finishing a task, 2. verify the execution result of the plan and potentially suggest new plan.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "message": {
                                    "type": "string",
                                    "description": "question to ask planner. Make sure the question include enough context, such as the code and the execution result. The planner does not know the conversation between you and the user, unless you share the conversation with the planner.",
                                },
                            },
                            "required": ["message"],
                        },
                    },
                ],
            }
        )

        # create a UserProxyAgent instance named "user_proxy"
        self.user_proxy = autogen.UserProxyAgent(
            name="user_proxy",
            human_input_mode="TERMINATE",
            max_consecutive_auto_reply=10,
            # is_termination_msg=lambda x: "content" in x and x["content"] is not None and x["content"].rstrip().endswith("TERMINATE"),
            code_execution_config={"work_dir": "planning"},
            function_map={"ask_planner": self.ask_planner},
        )
        self.boss_aid = RetrieveUserProxyAgent(
            name="Boss_Assistant",
            is_termination_msg=termination_msg,
            system_message="Assistant who has extra content retrieval power for solving difficult problems.",
            human_input_mode="TERMINATE",
            max_consecutive_auto_reply=3,
            retrieve_config={
                "task": "code",
                "docs_path": f"{self.docs_path}",
                "chunk_token_size": 1000,
                "model": self.config_list[0]["model"],
                "client": chromadb.EphemeralClient(),#chromadb.PersistentClient(path="/tmp/chromadb"),
                "collection_name": "groupchat",
                "get_or_create": False,
                "max_tokens": 4000,
            },
            code_execution_config=True,  # we don't want to execute code in this case.
        )

        self.coder = autogen.AssistantAgent(
            name="Senior_Python_Engineer",
            is_termination_msg=termination_msg,
            system_message="You are a senior systems engineer who is also an expert in Python."
            "Reply `TERMINATE` in the end when everything is done.",
            llm_config=self.llm_config,
        )
        self.teacher = autogen.AssistantAgent(
            name="teacher",
            is_termination_msg=termination_msg,
            system_message="You are an expert engineer and python coder capable of performing or teaching any relevent topic."
            "Reply `TERMINATE` in the end when everything is done.",
            llm_config=self.llm_config,
        )
        self.pm = autogen.AssistantAgent(
            name="Product_Manager",
            is_termination_msg=termination_msg,
            system_message="You are a product manager. Reply `TERMINATE` in the end when everything is done.",
            llm_config=self.llm_config,
        )

        self.reviewer = autogen.AssistantAgent(
            name="Document_Reviewer", #was code_reviewer
            is_termination_msg=termination_msg,
            system_message="You review the contents of documents or files in great detail to answer questions. Only review one document at a time. Ask for help, if needed. Reply `TERMINATE` in the end when everything is done.",
            llm_config=self.llm_config,
        )

        #PROBLEM = "Find two similar Data Item Description documents. State their similarities, differences, and overlaps or use and content."        

    def set_docs_path(self, paths):  # Remember to include 'self' as the first argument
        if isinstance(paths, list) and paths:
            self.docs_path = os.path.dirname(paths[0])
        elif isinstance(paths, str):
            self.docs_path = os.path.dirname(paths)
        else:
            raise ValueError("Invalid input. Expected a string or a list of strings.")



    def _reset_agents(self):
        self.boss.reset()
        self.boss_aid.reset()
        self.coder.reset()
        self.pm.reset()
        self.reviewer.reset()
        self.planner.reset()
        self.planner_user.reset()

    def ask_planner(self, message):
        self.planner_user.initiate_chat(self.planner, message=message)
        plan = self.planner_user.last_message(agent=self.planner)["content"]
        self.call_rag_chat(plan)
        # return the last message received from the planner
        return self.planner_user.last_message()["content"]

    def rag_chat(self, PROBLEM):
        self._reset_agents()
        groupchat = autogen.GroupChat(
            agents=[self.user_proxy, self.boss_aid, self.coder, self.pm, self.reviewer, self.teacher, self.planner, self.planner_user], messages=[], max_round=12
        )
        manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=self.llm_config)

        # Start chatting with boss_aid as this is the user proxy agent.
        self.boss_aid.initiate_chat(
            manager,
            problem=PROBLEM,
            n_results=3,
        )
        return manager.last_message(agent=self.boss_aid)["content"]

    def norag_chat(self, PROBLEM):
        self._reset_agents()
        groupchat = autogen.GroupChat(
            agents=[self.user_proxy, self.boss_aid, self.coder, self.pm, self.reviewer, self.teacher, self.planner, self.planner_user], messages=[], max_round=12
        )
        manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=self.llm_config)

        # Start chatting with boss as this is the user proxy agent.
        self.boss.initiate_chat(
            manager,
            message=PROBLEM,
        )
        return manager.last_message(agent=self.boss)["content"]

    def call_rag_chat(self, PROBLEM):
        self._reset_agents()
        print("self.docs_path:", self.docs_path)      
        # In this case, we will have multiple user proxy agents and we don't initiate the chat
        # with RAG user proxy agent.
        # In order to use RAG user proxy agent, we need to wrap RAG agents in a function and call
        # it from other agents.
        def retrieve_content(message, n_results=10):
            self.boss_aid.n_results = n_results  # Set the number of results to be retrieved.
            # Check if we need to update the context.
            update_context_case1, update_context_case2 = self.boss_aid._check_update_context(message)
            if (update_context_case1 or update_context_case2) and self.boss_aid.update_context:
                self.boss_aid.problem = message if not hasattr(self.boss_aid, "problem") else self.boss_aid.problem
                _, ret_msg = self.boss_aid._generate_retrieve_user_reply(message)
            else:
                ret_msg = self.boss_aid.generate_init_message(message, n_results=n_results)
            return ret_msg if ret_msg else message
        
        self.boss_aid.human_input_mode = "NEVER" # Disable human input for boss_aid since it only retrieves content.


        
        llm_config = {
            "functions": [
                {
                    "name": "retrieve_content",
                    "description": "retrieve content for document reviews and question answering.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "Refined message which keeps the original meaning and can be used to retrieve content of provided documents and question answering.",
                            }
                        },
                        "required": ["message"],
                    },
                },
            ],
            "config_list": self.config_list,
            "request_timeout": 120,
            "seed": 42,
        }

        for agent in [self.planner, self.pm, self.reviewer, self.teacher, self.coder]:
            # update llm_config for assistant agents.
            agent.llm_config.update(llm_config)
         

        for agent in [self.planner, self.pm, self.reviewer, self.teacher, self.coder]:
            # register functions for all agents.
            agent.register_function(
                function_map={
                    "retrieve_content": retrieve_content,
                }
            )

        groupchat = autogen.GroupChat(
            agents=[self.boss, self.user_proxy, self.boss_aid, self.coder, self.pm, self.reviewer, self.teacher, self.planner, self.planner_user], messages=[], max_round=12
        )
        manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config)

        # Start chatting with boss as this is the user proxy agent.
        self.boss.initiate_chat(
            manager,
            message=PROBLEM,
        )
        return manager.last_message(agent=self.boss)["content"]