# Assignment 2 - Payments desk

## Goal

Build a small LangGraph payments desk. A customer message comes in. Your graph decides where it goes, then answers using tools.

This is an in-class assignment. You may look at the files in this `lessons` folder. Do not edit those files. Put your work in a new folder:

```text
session-7-8/assignment-work/
```

Use LangChain, LangGraph, and a real OpenAI key (same `.env` pattern as class).

## Customer messages

Your program must run these three, in this order, and print the path it took plus the final answer for each:

1. `Order 8812 arrived damaged. Estimate a refund for 2400 rupees and show the damaged-item policy.`
2. `Courier is stuck. What is the weather in Mumbai right now?`
3. `What is a chargeback, in one sentence?`

Do not hard-code the answers. The model and your tools have to produce them.

## What to build

You need both kinds of routing we did in class:

1. A `route()` function you write. Ordinary Python. It returns the next node name as a string.
2. At least one path that uses `tools_condition` + `ToolNode` (the model asked for a tool, so go run it).

Minimum graph shape (node names can be yours):

```text
START -> classify -> (your route)
              |-- work  -> assistant -> tools_condition -> tools -> assistant
              |-- chat  -> a plain LLM node -> END
```

`classify` should send message 1 and 2 to `work`, and message 3 to `chat`. Print the path (`work` or `chat`) before the answer.

## Tools

You need four tools, and they cannot all live in the same file.

| Tool | Where it lives | What it does |
| --- | --- | --- |
| `estimate_refund` | same file as the graph, `@tool` | Takes `amount_rupees`. Return 80 percent of that amount (damaged-item rule). |
| `lookup_policy` | a second Python file, imported | Takes `reason` like `damaged`, `late`, or `missing`. Return a short policy string you write. |
| `get_live_weather` | `@tool` that calls the internet | Live HTTP call. Open-Meteo is fine. Mumbai is latitude `19.08`, longitude `72.88`. No extra API key. |
| one MCP tool | `mcp_server.py` + `MultiServerMCPClient` | Your choice, but it must be used on message 1. Example: `rupees_to_thousands(amount)` that returns `amount / 1000`. |

Bind all four onto the `work` assistant. The `chat` path should not have tools.

Print the tool names grouped by source when the program starts, same idea as `09_integrated_demo.py`:

```text
local: ...
module: ...
live: ...
mcp: ...
```

Also print `graph.get_graph().draw_ascii()` once.

## Requirements

- `ChatOpenAI` with your class model. `load_dotenv()`. Do not commit `.env`.
- `TypedDict` state. Return new state from each node. Do not mutate the input dict.
- MCP tools are async. Load them with `await client.get_tools()` and run the graph with `ainvoke`. `invoke` will fail on MCP tools. We already hit that in class.
- stdio MCP config needs `command` and `args`, not a `url`.
- Keep the code readable. A few files is better than one long file.
- Include a short `README.md` in `assignment-work` with the exact command to run it.

## Stretch (if you finish early)

- Add a third route, `escalate`, for messages that sound like fraud or a legal threat. That node only returns a string, no tools.
- Keep a `MemorySaver` thread and ask a follow-up: `What refund did you just estimate?`
- Validate `estimate_refund` inputs with a small Pydantic model, like `ImpactInput` from earlier sessions.

## Submission

Submit one of the following:

- a GitHub repository link; or
- a zip of `assignment-work`

Must include:

- source (graph, tools module, MCP server)
- README
- a screenshot or pasted terminal output showing all three messages
- 4-6 lines: which path broke first, and what you changed

Leave out `.venv`, `__pycache__`, `.env`, and the lesson files.

## Rubric - 20 points

| Area | Points | Evidence |
|---|---:|---|
| Your router | 4 | `route()` is real Python, not only `tools_condition` |
| Tool sources | 6 | Local, imported module, live HTTP, and MCP are all actually called |
| The three messages | 4 | Message 3 goes to `chat`; 1 and 2 go to `work` and use tools |
| MCP wiring | 3 | Server starts over stdio, tools loaded async, graph uses `ainvoke` |
| README + reflection | 3 | Someone else can run it; you can explain one failure |

## Academic integrity

You can use AI tools. You still have to understand the graph. In review I may ask you to add a fourth message or rename a node without the tool open.
