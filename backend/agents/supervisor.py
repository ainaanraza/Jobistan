from typing import Sequence
from langgraph.graph import StateGraph, END
from agents.search_agents import AgentState, global_search_node, company_career_node
from agents.processing_agents import deduplication_node, ranking_node

def create_supervisor_graph():
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("global_search", global_search_node)
    workflow.add_node("company_career", company_career_node)
    workflow.add_node("deduplication", deduplication_node)
    workflow.add_node("ranking", ranking_node)
    
    # Define edges
    # Supervisor starts by routing to search agents
    workflow.set_entry_point("global_search")
    
    # For now, serial execution for testing
    workflow.add_edge("global_search", "company_career")
    workflow.add_edge("company_career", "deduplication")
    workflow.add_edge("deduplication", "ranking")
    workflow.add_edge("ranking", END)
    
    return workflow.compile()

def run_workflow(user_profile: dict, companies: list = [], urls: list = []):
    graph = create_supervisor_graph()
    initial_state = {
        "messages": [],
        "jobs_found": [],
        "companies_to_search": companies,
        "urls_to_scrape": urls,
        "user_profile": user_profile,
        "final_report": ""
    }
    
    # Run the graph
    print("Starting Jobistan Agent Workflow...")
    result = graph.invoke(initial_state)
    print(f"Workflow completed! Found {len(result.get('jobs_found', []))} jobs.")
    return result
