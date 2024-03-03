from pydantic.v1 import BaseModel, Field


class Response(BaseModel):
    """Final response to the question being asked"""

    output: str = Field(description="The final answer to respond to the user")
    message_id: str = Field(
        description="The metadata 'message_id' value available in the retrieved document, if present. Otherwise do not invent set 0."
    )
