from pydantic import BaseModel
from typing import Literal, TypedDict, Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class Intent(BaseModel):
    name: Literal["order_status", "weather", "chat","refund_policy"]


class State(TypedDict):
    # add_messages appends instead of overwriting, so tool results accumulate
    messages: Annotated[list[BaseMessage], add_messages]
    intent: str
    result: str