import json

from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END

from graph.nodes import Nodes
from graph.state import AgentState
from langchain.memory import ConversationBufferWindowMemory


class Graph:
    RUN_NAME = "TelegramBot"

    def __init__(self, nodes: Nodes):
        self.nodes = nodes
        self.graph = self.create_graph()
        self.memory = ConversationBufferWindowMemory(memory_key="memory",
                                                     return_messages=True,
                                                     k=10)

    def create_graph(self):
        graph = StateGraph(AgentState)
        graph.add_node("agent", self.nodes.call_model)
        graph.add_node("action", self.nodes.call_tool)

        graph.set_entry_point("agent")
        graph.add_conditional_edges(
            "agent",
            self.nodes.should_continue,
            {
                "continue": "action",
                "end": END,
            }
        )
        graph.add_edge("action", "agent")
        return graph.compile()

    def run(self, input_message):
        memory = self.memory.load_memory_variables({})['memory']
        inputs = dict(messages=[HumanMessage(content=input_message)], memory=memory)
        # final_output=dict()
        # for output in self.graph.with_config(dict(run_name=Graph.RUN_NAME)).stream(inputs):
        #     for key, value in output.items():
        #         print(f"Output from node {key}:")
        #         print("-------")
        #         print(value)
        #     final_output=output
        #     print("-------")
        output = self.graph.with_config(dict(run_name=Graph.RUN_NAME)).invoke(inputs)
        response_message = ""
        message_id = None
        ai_message: AIMessage = output['messages'][-1]

        if "tool_calls" in ai_message.additional_kwargs and len(ai_message.additional_kwargs["tool_calls"]) > 0:
            resp_map = ai_message.additional_kwargs["tool_calls"][-1]["function"]
            if resp_map["name"] == "Response":
                result = json.loads(resp_map["arguments"])
                response_message = result["output"]
                if "message_id" in result:
                    message_id = result["message_id"]
        else:
            response_message = ai_message.content
        self.memory.save_context(dict(input=input_message), dict(output=response_message))
        return dict(response=response_message, message_id=message_id)



