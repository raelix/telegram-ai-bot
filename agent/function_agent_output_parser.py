import asyncio
import json
from json import JSONDecodeError
from typing import Union
from langchain.agents.agent import AgentOutputParser
from langchain.schema import (
    AgentAction,
    AgentFinish,
    OutputParserException,
)
from langchain.schema.agent import AgentActionMessageLog
from langchain.schema.messages import (
    AIMessage,
    BaseMessage,
)
from langchain.schema.output import ChatGeneration, Generation
from typing import List
from pydantic import BaseModel, Field


class CustomOpenAIFunctionsAgentOutputParser(AgentOutputParser):

    @property
    def _type(self) -> str:
        return "openai-functions-agent"

    @staticmethod
    def _parse_ai_message(message: BaseMessage) -> Union[AgentAction, AgentFinish]:
        """Parse an AI message."""
        if not isinstance(message, AIMessage):
            raise TypeError(f"Expected an AI message got {type(message)}")

        function_call = message.additional_kwargs.get("function_call", {})

        if function_call:
            function_name = function_call["name"]
            try:
                if len(function_call["arguments"].strip()) == 0:
                    # OpenAI returns an empty string for functions containing no args
                    _tool_input = {}
                else:
                    # otherwise it returns a json object
                    _tool_input = json.loads(function_call["arguments"])
            except JSONDecodeError:
                raise OutputParserException(
                    f"Could not parse tool input: {function_call} because "
                    f"the `arguments` is not valid JSON."
                )

            # HACK HACK HACK:
            # The code that encodes tool input into Open AI uses a special variable
            # name called `__arg1` to handle old style tools that do not expose a
            # schema and expect a single string argument as an input.
            # We unpack the argument here if it exists.
            # Open AI does not support passing in a JSON array as an argument.
            if "__arg1" in _tool_input:
                tool_input = _tool_input["__arg1"]
            else:
                tool_input = _tool_input

            # Here is where we stop once the call is to the Response tool
            if function_name == "Response":
                return AgentFinish(return_values=_tool_input, log=str(function_call))

            content_msg = f"responded: {message.content}\n" if message.content else "\n"
            log = f"\nInvoking: `{function_name}` with `{tool_input}`\n{content_msg}\n"
            return AgentActionMessageLog(
                tool=function_name,
                tool_input=tool_input,
                log=log,
                message_log=[message],
            )

        return AgentFinish(
            return_values={"output": message.content}, log=str(message.content)
        )

    def parse_result(
            self, result: List[Generation], *, partial: bool = False
    ) -> Union[AgentAction, AgentFinish]:
        if not isinstance(result[0], ChatGeneration):
            raise ValueError("This output parser only works on ChatGeneration output")
        message = result[0].message
        return self._parse_ai_message(message)

    async def aparse_result(
            self, result: List[Generation], *, partial: bool = False
    ) -> Union[AgentAction, AgentFinish]:
        return await asyncio.get_running_loop().run_in_executor(
            None, self.parse_result, result
        )

    def parse(self, text: str) -> Union[AgentAction, AgentFinish]:
        raise ValueError("Can only parse messages")


class Response(BaseModel):
    """Final response to the question being asked"""

    output: str = Field(description="The final answer to respond to the user")
    message_id: str = Field(
        description="The metadata message_id available in the document used to retrieve the data, if present."
    )
