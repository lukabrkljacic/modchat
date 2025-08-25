"""A tool that performs task decomposition of a given prompt from a specified language model."""
import logging
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.types import Command
from langchain_core.prompts.chat import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
from typing import Dict, List, Union, Any, Optional, Callable, TypedDict
from typing_extensions import override
from contextlib import asynccontextmanager
import os

# Configure logging
logger = logging.getLogger(__name__)

try:
    from src.models.model_factory import model_factory
    from src.agent.base import BaseAgent
    from src.agent.role import task_decomposition
except ImportError as e:
    logger.critical(f"Error importing custom modules: {str(e)}")

LLMOutput = Union[Dict[str, Any], BaseModel, str]

class DecomposedResponse(BaseModel):
    """Always use this to structure your response to the user."""
    response: str = Field(description="The original response from the user/AI.")
    components: List[Dict[str, str]] = Field(description="The answer broken down into relevant components.")
    explanations: Dict[str, str] = Field(description="The reasoning for each individual component.")

class DecompositionState(TypedDict):
    task: str|Dict[str, Any] = Field({}, description="The task to decompose")
    decomposed_response: DecomposedResponse = Field(None, description="The decomposed task from the agent")

class ResponseDecomposition(BaseAgent):
    """An AI Agent responsible for taking in output from a LLM and decomposing it into smaller chunks of text
    that allow the key ideas to be distilled and worked on as separate pieces rather than as a whole chunk.
    """
    def __init__(self,
                 name: str = "modular_output_decomposer",
                 vendor: Optional[str] = None,
                 model_id: Optional[str] = None,
                 role: str = task_decomposition,
                 response_format: Optional[BaseModel] = DecomposedResponse,
                 checkpointer: Optional[BaseCheckpointSaver] = None,
                 settings: Optional[Dict[str, Any]] = None):
        super().__init__(vendor=vendor, model_id=model_id, role=role, settings=settings)
        self.name = name
        self._agent_chain = None
        self._agent = None
        self._response_format = response_format
        self._checkpointer = checkpointer
        self.init_agent()

    async def node(self, state: Dict[str, Any], config: Optional[Dict[str, Any]] = None):
        task: LLMOutput = state["task"]
        response = await self._agent_chain.ainvoke(task)
        return Command(goto=END, update={"decomposed_response": response})

    @override
    def init_agent(self) -> None:
        if not self._llm:
            raise ValueError("Language model not initialized. Check model_factory")

        if self._response_format:
            # Override LLM to handle structured output
            method = "json_mode" if self._vendor.lower() == "openai" else None
            self._llm = self._llm.with_structured_output(self._response_format, method=method)

        mod_prompt = ChatPromptTemplate.from_messages([
            ("system", self._role),
            ("human", "{task}"),
        ])
        self._agent_chain = mod_prompt | self._llm
        # Build agent graph
        workflow = StateGraph(DecompositionState)
        workflow.add_node("mod_agent", self.node)
        workflow.set_entry_point("mod_agent")
        graph = workflow.compile(checkpointer=self._checkpointer)
        self._agent = graph

    @override
    def invoke(self, response: LLMOutput, config: Optional[Dict[str, Any]] = None) -> DecomposedResponse:
        """Takes in a given task or prompt, decomposes it based on a predefined structure, and returns structured output."""
        # Invoke LLM with user response
        response_input = dict(task=response)
        decomposed_response = self._agent.invoke(response_input, config)
        # Return the DecomposedResponse object
        return decomposed_response
    
    @override
    async def ainvoke(self, response: LLMOutput, config: Optional[Dict[str, Any]] = None) -> DecomposedResponse:
        """Takes in a given task or prompt, decomposes it based on a predefined structure, and returns structured output."""
        # Invoke LLM with user response
        logger.debug(f"Response received in `ainvoke`:\n{response}")
        response_input = dict(task=response)
        decomposed_response = await self._agent.ainvoke(response_input, config)
        # Return the DecomposedResponse object
        return decomposed_response

# A context manager wrapper used to start the agent up at the beginning of the server's lifecycle
@asynccontextmanager
async def agent_context(model: str, vendor: str, settings: Optional[Dict[str, Any]] = None):
    agent = ResponseDecomposition(model_id=model, vendor=vendor, settings=settings)
    try:
        yield agent
    finally:
        pass