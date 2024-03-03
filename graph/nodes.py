import json

from langchain_core.messages import FunctionMessage, ToolMessage
from langchain_core.runnables import RunnableSerializable
from langgraph.prebuilt import ToolInvocation, ToolExecutor

from graph.state import AgentState


class Nodes:

    def __init__(self, model: RunnableSerializable, tool_executor: ToolExecutor):
        self.model = model
        self.tool_executor = tool_executor

    def should_continue(self, state: AgentState):
        last_message = state["messages"][-1]
        if "tool_calls" not in last_message.additional_kwargs:
            return "end"
        elif any(
                tool_call["function"]["name"] == "Response"
                for tool_call in last_message.additional_kwargs["tool_calls"]
        ):
            return "end"
        else:
            return "continue"

    def call_model(self, state: AgentState):
        messages = state["messages"]
        memory = state["memory"]
        response = self.model.invoke({"messages": messages, "memory": memory})
        messages.append(response)
        return dict(messages=messages)

    def call_tool(self, state: AgentState):
        messages = state["messages"]
        last_message = messages[-1]
        for tool_call in last_message.additional_kwargs["tool_calls"]:
            action = ToolInvocation(
                tool=tool_call["function"]["name"],
                tool_input=json.loads(tool_call["function"]["arguments"])
            )
            response = self.tool_executor.invoke(action)
            function_message = ToolMessage(content=str(response), name=action.tool, tool_call_id=tool_call["id"])
            messages.append(function_message)
        return dict(messages=messages, memory=state["memory"])
