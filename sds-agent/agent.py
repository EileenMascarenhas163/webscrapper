from langgraph.graph import StateGraph
from langchain.chat_models import ChatOpenAI
from models import AgentAction
import json

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

class AgentState(dict):
    pass

def decide(state: AgentState):
    prompt = f"""
You are an SDS crawling agent.

Links:
{state['links'][:40]}

Decide next action:
- click (if SDS section exists)
- paginate (if more pages)
- extract (if PDF SDS found)
- stop (if done)

Return JSON: {{ "action": "...", "target": "..." }}
"""
    response = llm.predict(prompt)
    action = AgentAction(**json.loads(response))
    state["action"] = action
    return state

def router(state: AgentState):
    return state["action"].action
