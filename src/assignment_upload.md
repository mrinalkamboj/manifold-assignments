---

Executive Summary: Payments Desk Architecture



The Payments Desk is an agentic AI assistant designed to handle customer support inquiries by integrating LangGraph stateful workflows with the Model Context Protocol (MCP). It provides dynamic intent classification, automated routing, dynamic tool discovery, and multi-step reasoning to resolve customer requests regarding order statuses, refund calculations, live weather checks, and general domain Q&A.

---

 1. State Management & Data Schemas (entities.py)

State transitions throughout the graph lifecycle are governed by two core entities in [entities.py]

Intent Model (Pydantic): Constrains LLM outputs during classification to strict literals ("order_status", "weather", "chat", "refund_policy"), guaranteeing type-safe downstream routing.

State Schema (TypedDict): Maintains the execution memory:

  * messages: Utilizes LangGraph's add_messages reducer to accumulate human prompts, AI tool calls, and tool responses without overwriting conversation history.

  * intent: Tracks the active query classification.

  * result: Stores the final human-readable answer.

---

2. Model Context Protocol Server (mcp_server.py)

The server exposes four core tools:

1. **check_order_status**: Looks up order states (e.g., damaged, shipped, pending, cancelled).

2. **fetch_refund_policy**: Determines percentage eligibility based on order status (e.g., 80% for damaged items).

3. **refund_amount_calculator**: Computes ceiling refund values based on amount paid and percentage.

4. **get_live_weather**: Fetches real-time temperature and climate metrics via the OpenWeatherMap API.

Logging is strictly directed to sys.stderr so sys.stdout remains unpolluted for MCP JSON-RPC protocol communication.

---

3. LangGraph Workflow & Edge Routing (payments_desk.py)

Moves through a cyclic state graph:

* **classify Node**: Analyzes incoming user messages via structured output (Intent).

* **Conditional Intent Router (route)**: Directs state to one of four execution nodes (order_status, weather, chat, refund_policy).

* **Execution Nodes & Tool Evaluation (tools_condition)**: Each execution node invokes the tool-bound LLM. If tool calls are generated, prebuilt tools_condition routes to the **tools** (ToolNode) node; otherwise, execution proceeds to **END**.

* **Loopback Router (back_to_node)**: After ToolNode executes the requested MCP tool, back_to_node returns state back to the originating execution node, allowing the model to synthesize tool outputs into a final user response.

---

4. Lifecycle Summary

Upon initialization, MultiServerMCPClient launches the local MCP server, discovers tools dynamically, and binds them to the LLM. Each request flows from START $\rightarrow$ classify $\rightarrow$ Intent Routing $\rightarrow$ Tool Execution Loop (if needed) $\rightarrow$ Final Answer Synthesis $\rightarrow$ END.