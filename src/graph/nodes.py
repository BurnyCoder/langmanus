import logging
from typing import Literal
from langchain_core.messages import HumanMessage
from langgraph.types import Command
from langgraph.graph import END

from src.agents import research_agent, coder_agent, file_manager_agent, browser_agent
from src.agents.llm import supervisor_llm
from src.config import TEAM_MEMBERS, SUPERVISOR_PROMPT
from .types import State, Router

logger = logging.getLogger(__name__)

def research_node(state: State) -> Command[Literal["supervisor"]]:
    """Node for the researcher agent that performs research tasks."""
    logger.info("Research agent starting task")
    result = research_agent.invoke(state)
    logger.info("Research agent completed task")
    logger.debug(f"Research agent response: {result['messages'][-1].content}")
    return Command(
        update={
            "messages": [
                HumanMessage(content=result["messages"][-1].content, name="researcher")
            ]
        },
        goto="supervisor",
    )

def code_node(state: State) -> Command[Literal["supervisor"]]:
    """Node for the coder agent that executes Python code."""
    logger.info("Code agent starting task")
    result = coder_agent.invoke(state)
    logger.info("Code agent completed task")
    logger.debug(f"Code agent response: {result['messages'][-1].content}")
    return Command(
        update={
            "messages": [
                HumanMessage(content=result["messages"][-1].content, name="coder")
            ]
        },
        goto="supervisor",
    )

def file_manager_node(state: State) -> Command[Literal["supervisor"]]:
    """Node for the file manager agent that handles file operations."""
    logger.info("File manager agent starting task")
    result = file_manager_agent.invoke(state)
    logger.info("File manager agent completed task")
    logger.debug(f"File manager agent response: {result['messages'][-1].content}")
    return Command(
        update={
            "messages": [
                HumanMessage(content=result["messages"][-1].content, name="file_manager")
            ]
        },
        goto="supervisor",
    )

def browser_node(state: State) -> Command[Literal["supervisor"]]:
    """Node for the browser agent that performs web browsing tasks."""
    logger.info("Browser agent starting task")
    result = browser_agent.invoke(state)
    logger.info("Browser agent completed task")
    logger.debug(f"Browser agent response: {result['messages'][-1].content}")
    return Command(
        update={
            "messages": [
                HumanMessage(content=result["messages"][-1].content, name="browser")
            ]
        },
        goto="supervisor",
    )

def supervisor_node(state: State) -> Command[Literal[*TEAM_MEMBERS, "__end__"]]:
    """Supervisor node that decides which agent should act next."""
    logger.info("Supervisor evaluating next action")
    messages = [
        {"role": "system", "content": SUPERVISOR_PROMPT},
    ] + state["messages"]
    response = supervisor_llm.with_structured_output(Router).invoke(messages)
    goto = response["next"]
    logger.debug(f"Current state messages: {state['messages']}")
    logger.debug(f"Supervisor response: {response}")
    
    if goto == "FINISH":
        goto = END
        logger.info("Workflow completion decided by supervisor")
    else:
        logger.info(f"Supervisor delegating to: {goto}")

    return Command(goto=goto, update={"next": goto}) 