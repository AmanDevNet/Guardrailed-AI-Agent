from typing import Literal, TypedDict

from langgraph.graph import END, StateGraph

from app.guardrails import REJECTION_REASON, validate_scope
from app.responder import generate_answer


class AgentState(TypedDict, total=False):
    query: str
    allowed: bool
    answer: str
    reason: str
    status: str


def guardrail_node(state: AgentState) -> AgentState:
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
    return {
        **state,
        "status": "success",
        "answer": generate_answer(state["query"]),
    }


def route_after_guardrail(state: AgentState) -> Literal["respond", "__end__"]:
    return "respond" if state.get("allowed") else END


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("guardrail", guardrail_node)
    graph.add_node("respond", answer_node)
    graph.set_entry_point("guardrail")
    graph.add_conditional_edges("guardrail", route_after_guardrail, {"respond": "respond", END: END})
    graph.add_edge("respond", END)
    return graph.compile()


agent_graph = build_graph()


def run_agent(query: str) -> dict:
    state = agent_graph.invoke({"query": query})
    if state.get("status") == "success":
        return {"status": "success", "response": {"answer": state["answer"]}}
    return {"status": "rejected", "reason": state.get("reason", REJECTION_REASON)}
