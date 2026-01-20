from langgraph.graph import END
from agent import decide, router
from browser import Browser
from crawler import observe

browser = Browser()

def observe_node(state):
    state["links"] = observe(state["url"])
    return state

def click_node(state):
    browser.click(state["action"].target)
    return state

def paginate_node(state):
    browser.paginate()
    return state

def extract_node(state):
    pdfs = [l for l in state["links"] if l.endswith(".pdf")]
    state["pdfs"] = pdfs
    return state

graph = StateGraph(dict)
graph.add_node("observe", observe_node)
graph.add_node("decide", decide)
graph.add_node("click", click_node)
graph.add_node("paginate", paginate_node)
graph.add_node("extract", extract_node)

graph.set_entry_point("observe")
graph.add_edge("observe", "decide")
graph.add_conditional_edges("decide", router, {
    "click": "click",
    "paginate": "paginate",
    "extract": "extract",
    "stop": END
})
graph.add_edge("click", "observe")
graph.add_edge("paginate", "observe")
graph.add_edge("extract", END)

agent = graph.compile()
