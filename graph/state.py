from typing import TypedDict, Sequence

from langchain.memory.chat_memory import BaseChatMemory
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    messages: Sequence[BaseMessage]
    memory: BaseChatMemory
