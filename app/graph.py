from typing import Literal, TypedDict

from langgraph.graph import END, StateGraph

from app.guardrails import REJECTION_REASON, validate_scope
from app.responder import generate_answer

# =====================================================================
# LANGGRAPH STATE DEFINITION
# =====================================================================
# AgentState defines the shared data schema passed between nodes in the graph.
# Using TypedDict with total=False allows nodes to return partial updates 
# to the state, which LangGraph automatically merges.
class AgentState(TypedDict, total=False):
    query: str      # The raw incoming question from the user.
    allowed: bool    # Boolean flag indicating whether the query complies with allowed scope.
    answer: str     # The generated educational answer (populated only if allowed=True).
    reason: str     # The rejection reason (populated if allowed=False).
    status: str     # State status indicator: "success" or "rejected".


# =====================================================================
# GRAPH NODES (Execution steps)
# =====================================================================

def guardrail_node(state: AgentState) -> AgentState:
    """
    First Node in the graph. 
    Performs boundary checks on the query using the guardrails logic.
    - If rejected: Updates state with allowed=False and records the rejection reason.
    - If allowed: Updates state with allowed=True.
    """
    decision = validate_scope(state["query"])
    if not decision.allowed:
        return {
            **state,
            "allowed": False,
            "status": "rejected",
            "reason": decision.reason or REJECTION_REASON,
        }
    return {**state, "allowed": True}


def answer_node(state: AgentState) -> AgentState:
    """
    Second Node in the graph.
    Runs the responder module to generate the educational plain-text answer.
    This node is only reached if the guardrail conditional edge permits it.
    """
    return {
        **state,
        "status": "success",
        "answer": generate_answer(state["query"]),
    }


# =====================================================================
# CONDITIONAL ROUTING EDGE
# =====================================================================

def route_after_guardrail(state: AgentState) -> Literal["respond", "__end__"]:
    """
    Evaluates the 'allowed' flag in graph state to determine the next node.
    - If allowed is True -> Proceeds to the 'respond' node.
    - If allowed is False -> Terminates early and routes to '__end__'.
    """
    return "respond" if state.get("allowed") else END


# =====================================================================
# GRAPH COMPILATION
# =====================================================================

def build_graph():
    """
    Constructs and compiles the StateGraph workflow:
    1. Instantiates a StateGraph tracking AgentState.
    2. Adds our two main processing nodes.
    3. Sets 'guardrail' as the starting node.
    4. Adds conditional routing edges out of the 'guardrail' node.
    5. Connects 'respond' to 'END' to complete the success path.
    6. Compiles and returns the graph.
    """
    graph = StateGraph(AgentState)
    graph.add_node("guardrail", guardrail_node)
    graph.add_node("respond", answer_node)
    graph.set_entry_point("guardrail")
    
    # Conditional routing edge maps routing decisions to actual node destinations:
    # "respond" string maps to 'respond' node; END maps to the terminal '__end__' state.
    graph.add_conditional_edges("guardrail", route_after_guardrail, {"respond": "respond", END: END})
    
    # Normal directed edge: respond node always goes directly to terminate.
    graph.add_edge("respond", END)
    return graph.compile()


# Build a single, reusable compiled instance of our graph.
agent_graph = build_graph()


# =====================================================================
# GRAPH INVOCATION ENTRYPOINT
# =====================================================================

def run_agent(query: str) -> dict:
    """
    Runs the compiled graph workflow synchronously for a client request.
    Invokes the graph with the initial state containing only the user's query,
    interprets the final merged state output, and maps it to the API response schemas.
    """
    # invoke() passes the dictionary into the graph, runs the nodes, and returns the final state dict.
    state = agent_graph.invoke({"query": query})
    
    if state.get("status") == "success":
        return {"status": "success", "response": {"answer": state["answer"]}}
        
    return {"status": "rejected", "reason": state.get("reason", REJECTION_REASON)}
