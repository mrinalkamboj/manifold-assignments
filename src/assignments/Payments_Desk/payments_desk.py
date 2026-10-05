"""
---------------------------------------------------------------------------------
Single ReAct loop + human-in-the-loop approval gate:
- one agent node decides which tools to call
- a damaged-item refund above Rs 2000 is diverted to an `approval` node
  that calls interrupt() and pauses the graph until a human resumes it
- approved refunds go to the tools node; rejected ones get a ToolMessage
  so the agent can tell the user the refund was denied
---------------------------------------------------------------------------------
1. `Order 8812 arrived damaged. I paid Rs 3000 total. Process my refund.`  -> approval needed
2. `Courier is stuck. What is the weather in Bangalore right now?`        -> no approval
3. `What is a chargeback, in one sentence?`                               -> no tools
"""

import asyncio
import sys
from pathlib import Path
from typing import Literal

from langchain_core.messages import HumanMessage, ToolMessage
from langgraph.graph import START, END, StateGraph
from langgraph.types import Command, interrupt
from langgraph.checkpoint.memory import MemorySaver
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import ToolNode

# llm import
#from agentic_developer_bootcamp.session_910_MCP.lessons.zero.init_llm import llm
from assignments.init_llm import llm

# Entities import
#from agentic_developer_bootcamp.session_910_MCP.lessons.assignment_work.entities import State
from assignments.Payments_Desk.entities import State

# Approval threshold: damaged-item refunds above this need a human
APPROVAL_THRESHOLD = 2000

# tools list (filled at runtime with the MCP tools)
tools = []

# Agent node: the LLM decides whether to answer directly or call a tool
def execute(state: State):
    model = llm.bind_tools(tools)
    result = model.invoke(state["messages"])
    # With the add_messages reducer, return only the delta
    return {"messages": [result]}

# Router after the agent: detect refund calls that need human approval
def route_after_agent(state: State) -> Literal["approval", "tools", "__end__"]:
    last = state["messages"][-1]
    if not getattr(last, "tool_calls", None):
        return "__end__" # no tool calls -> final answer, stop
    for tc in last.tool_calls:
        if tc["name"] == "process_refund" and float(tc["args"].get("amount", 0)) > APPROVAL_THRESHOLD:
            return "approval"
    return "tools"

# Human approval node: pauses the whole graph with interrupt().
# Whoever drives the graph resumes it with Command(resume={"approved": True/False}).
def approval(state: State):
    last = state["messages"][-1]
    tc = next(t for t in last.tool_calls if t["name"] == "process_refund")
    decision = interrupt({
        "message": "Human approval required: damaged-item refund above Rs "
                   f"{APPROVAL_THRESHOLD}",
        "tool": tc["name"],
        "args": tc["args"],
    })
    if isinstance(decision, dict) and decision.get("approved"):
        return Command(goto="tools") # approved -> let the tools node run it
    # rejected -> inject a ToolMessage for EVERY pending tool call so none is
    # left unanswered (an unanswered call breaks the next model invoke),
    # then go back to the agent to tell the user the refund was denied
    rejections = []
    for c in last.tool_calls:
        if c["name"] == "process_refund":
            content = ("Refund REJECTED by human approver. Do not process it; "
                       "inform the customer.")
        else:
            content = "Not executed: the related refund was rejected by the human approver."
        rejections.append(ToolMessage(content=content, tool_call_id=c["id"]))
    return Command(update={"messages": rejections}, goto="agent")

# Establish a connection with the MCP server
MCP_SERVER = str(Path(__file__).resolve().parent / "mcp_server.py") # Resolve MCP Server

# Create MCP client
mcp_client = MultiServerMCPClient({
    "incident": {
        "transport": "stdio",
        "command": sys.executable,
        "args": [MCP_SERVER],
    },
    })

async def run_until_done(graph, payload, config):
    """Stream the graph; on an interrupt, BLOCK for a human decision, then resume.

    The graph truly halts here: input() waits for the approver to type y/n.
    In a real app you would instead return the interrupt payload to the UI and
    resume later in a separate invocation with the same thread_id.
    """
    while True:
        paused = False
        async for event in graph.astream(payload, config, stream_mode="updates"):
            if "__interrupt__" in event:
                intr = event["__interrupt__"][0]
                print("PAUSED FOR APPROVAL --->", intr.value)
                paused = True
        if not paused:
            break
        # blocking input() is fine here: nothing else needs the event loop
        answer = await asyncio.to_thread(
            input, "Approve this refund? [y/n]: "
        )
        approved = answer.strip().lower() in ("y", "yes")
        print(f"Human decision ---> {'APPROVED' if approved else 'REJECTED'}")
        payload = Command(resume={"approved": approved})
    return await graph.aget_state(config)

async def main():

    tools = await mcp_client.get_tools() # list of mcp tools
    print("MCP tools:", [tool.name for tool in tools]) # print mcp tools
    globals()["tools"].extend(tools) # make tools visible to execute()

    builder = StateGraph(State) #lang graph state graph
    builder.add_node("agent", execute) # adding agent node
    builder.add_node("tools", ToolNode(tools)) # adding tools node
    builder.add_node("approval", approval) # adding human approval node

    builder.add_edge(START, "agent") # adding edge from start to agent
    builder.add_conditional_edges("agent", route_after_agent) # approval / tools / END
    builder.add_edge("tools", "agent") # loop back so the agent can chain tools
    # approval routes itself via Command (-> tools when approved, -> agent when rejected)

    # interrupt() requires a checkpointer so the paused state can be saved and resumed
    graph = builder.compile(checkpointer=MemorySaver())

    print(graph.get_graph().draw_ascii())
    print("--------------------------------------------------------------------------------------------------------------------------------")

    for question in (
        "Order 8812 arrived damaged. I paid Rs 1000 total. Process my refund.",
        "Courier is stuck. What is the weather in Bangalore right now?",
        "What is a chargeback, in one sentence?",
    ):
        config = {"configurable": {"thread_id": question[:40]}}
        # halts and waits for keyboard input if a large refund needs approval
        state = await run_until_done(graph, {"messages": [HumanMessage(content=question)]}, config)
        print(f"Question Asked ---> {question}")
        print(f"Final Response ---> {state.values['messages'][-1].content}")
        print("--------------------------------------------------------------------------------------------------------------------------------")

# Initiate Async code
if __name__ == "__main__":
    asyncio.run(main())
