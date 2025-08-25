# conversation_manager.py
"""
Manager module for handling conversations and their state.
"""

import os
import logging
import uuid
import time
import sqlite3
import traceback
from typing import Dict, List, Any, Optional, Tuple

# Langchain imports
try:
    from langchain.schema import HumanMessage, SystemMessage
    from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain_core.runnables.base import Runnable
    from langgraph.graph import StateGraph, START, MessagesState
    from langgraph.checkpoint.sqlite import SqliteSaver
    from langgraph.checkpoint.postgres import PostgresSaver
    from langgraph.checkpoint.base import BaseCheckpointSaver

except ImportError as e:
    raise ImportError(f"Error importing Langchain modules: {str(e)}")

# Configure logging
logger = logging.getLogger(__name__)

class ConversationError(Exception):
    """Exception raised when conversation handling fails."""
    pass

class ConversationManager:
    """Manager class for conversations."""
    
    def __init__(self, 
                 storage_dir: Optional[str] = None, 
                 memory_manager: Optional[BaseCheckpointSaver] = None, 
                 max_conversations: int = 100):
        """
        Initialize the conversation manager.
        
        Args:
            storage_dir: Directory for persistent storage (optional)
            max_conversations: Maximum number of conversations to keep in memory
        """
        # Set up storage directory for persistence
        self._storage_dir = storage_dir
        if storage_dir:
            try:
                os.makedirs(storage_dir, exist_ok=True)
                logger.info(f"Using conversation storage directory: {storage_dir}")
            except OSError as e:
                logger.error(f"Failed to create storage directory: {str(e)}")
                self._storage_dir = None

        self._conn = None
        self.memory_manager: BaseCheckpointSaver = self._init_memory_manager(memory_manager=memory_manager)
        self._max_conversations = max_conversations # TODO: remove

        # Dictionary to store active conversations in memory
        self._conversations: Dict[str, Dict[str, Any]] = {}# TODO: remove
        # Last accessed timestamps for LRU eviction
        self._last_accessed: Dict[str, float] = {}# TODO: remove
        # Track user interaction events per conversation
        self._events: Dict[str, List[Dict[str, Any]]] = {}# TODO: remove
        # Track session timestamps for session-level logging
        self._session_timestamps: Dict[str, float] = {}# TODO: remove
        # Map conversations to their sessions
        self._conversation_sessions: Dict[str, str] = {}# TODO: remove
        # Track metadata such as model and settings used
        self._metadata: Dict[str, List[Dict[str, Any]]] = {}
        
        
    
    def _init_memory_manager(self, memory_manager: Optional[BaseCheckpointSaver|PostgresSaver] = None) -> BaseCheckpointSaver:
        if memory_manager is None:
            conn_str = f"{self._storage_dir}/checkpoint.sqlite"
            logger.info(
                "No memory manager provided. "
                f"Falling back to SQLite Checkpointer stored at {conn_str}")
            self._conn = sqlite3.connect(conn_str, check_same_thread=False)
            return SqliteSaver(conn=self._conn)
        
        if not isinstance(memory_manager, BaseCheckpointSaver):
            raise ConversationError(
                f"Invalid memory_manager of type {type(memory_manager)} provided - "
                "memory_manager must be of type `BaseCheckpointSaver`"
                )
        
        return memory_manager


    def get_or_create_memory(self, conversation_id: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Get or create conversation memory.
        
        Args:
            conversation_id: Unique identifier for the conversation
            
        Returns:
            Tuple of (conversation_id, memory)
        """
        # Generate an ID if none provided
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        # Check if conversation exists
        if conversation_id not in self._conversations:
            logger.info(f"Creating new conversation memory: {conversation_id}")
            
            # Try to load from storage first
            loaded = self._load_conversation(conversation_id)

            if loaded:
                self._conversations[conversation_id] = loaded
            else:
                # Create new memory
                self._conversations[conversation_id] = {}

            if conversation_id not in self._events:
                self._events[conversation_id] = []
        
        # Update access timestamp
        self._last_accessed[conversation_id] = time.time()
        
        return conversation_id, self._conversations[conversation_id]
    

    async def aget_or_create_memory(self, conversation_id: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Get or create conversation memory.
        
        Args:
            conversation_id: Unique identifier for the conversation
            
        Returns:
            Tuple of (conversation_id, memory)
        """
        # Generate an ID if none provided
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        # Check if conversation exists
        if conversation_id not in self._conversations:
            logger.info(f"Creating new conversation memory: {conversation_id}")
            
            # Try to load from storage first
            loaded = await self._aload_conversation(conversation_id)

            if loaded:
                self._conversations[conversation_id] = loaded
            else:
                # Create new memory
                self._conversations[conversation_id] = {}

            if conversation_id not in self._events:
                self._events[conversation_id] = []
        
        # Update access timestamp
        self._last_accessed[conversation_id] = time.time()
        
        return conversation_id, self._conversations[conversation_id]
    

    def create_chain(self, 
                     llm: Any, 
                     system_prompt: str,
                     session_id: str,
                     conversation_id: Optional[str] = None) -> Tuple[str, Runnable]:
        try:
            # Get or create memory
            conversation_id, _ = self.get_or_create_memory(conversation_id=conversation_id)
            # Map conversation to this session
            self._conversation_sessions[conversation_id] = session_id
            chat_prompt_template = ChatPromptTemplate.from_messages([
                SystemMessage(content=system_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                HumanMessage(content="{input}")
            ])
            prompt_chain = chat_prompt_template | llm
            call_model = lambda state: {"messages": prompt_chain.invoke(state["messages"])}
            workflow = StateGraph(state_schema=MessagesState)
            workflow.add_node("model", call_model)
            workflow.add_edge(START, "model")
            chain = workflow.compile(checkpointer=self.memory_manager)
            return conversation_id, chain
        
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error creating conversation chain: {error_msg}")
            logger.error(traceback.format_exc())
            raise ConversationError(f"Failed to create conversation: {error_msg}")


    async def acreate_chain(self, 
                     llm: Any, 
                     system_prompt: str,
                     session_id: str,
                     conversation_id: Optional[str] = None) -> Tuple[str, Runnable]:
        try:
            # Get or create memory
            conversation_id, _ = await self.aget_or_create_memory(conversation_id=conversation_id)
            # Map conversation to this session
            self._conversation_sessions[conversation_id] = session_id
            chat_prompt_template = ChatPromptTemplate.from_messages([
                SystemMessage(content=system_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                HumanMessage(content="{input}")
            ])
            prompt_chain = chat_prompt_template | llm
            call_model = lambda state: {"messages": prompt_chain.invoke(state["messages"])}
            workflow = StateGraph(state_schema=MessagesState)
            workflow.add_node("model", call_model)
            workflow.add_edge(START, "model")
            chain = workflow.compile(checkpointer=self.memory_manager)
            return conversation_id, chain
        
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error creating conversation chain: {error_msg}")
            logger.error(traceback.format_exc())
            raise ConversationError(f"Failed to create conversation: {error_msg}")
        

    def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """
        Get conversation history.
        
        Args:
            conversation_id: Unique identifier for the conversation
            
        Returns:
            List of message objects
        """
        if conversation_id not in self._conversations:
            return []
        
        try:
            # Update access timestamp
            self._last_accessed[conversation_id] = time.time()
            
            # Get the memory
            memory = self._conversations[conversation_id]
            
            return memory
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error retrieving conversation history: {error_msg}")
            logger.error(traceback.format_exc())
            return []

    def record_event(self, session_id: str, conversation_id: str, event_type: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Record a user interaction event."""
        if conversation_id not in self._events:
            self._events[conversation_id] = []

        self._events[conversation_id].append({
            'timestamp': time.time(),
            'session_id': session_id,
            'type': event_type,
            'data': data or {}
        })

    def record_metadata(self, session_id: str, conversation_id: str, model: str, settings: Dict[str, Any]) -> None:
        """Record model and settings metadata for a conversation."""
        if conversation_id not in self._metadata:
            self._metadata[conversation_id] = []

        self._metadata[conversation_id].append({
            'timestamp': time.time(),
            'session_id': session_id,
            'model': model,
            'settings': settings
        })
        
    def _load_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Load conversation from persistent storage.
        
        Args:
            conversation_id: Unique identifier for the conversation
            
        Returns:
            Conversation memory if successful, None otherwise
        """
        if not self._storage_dir:
            return None
        
        try:
            query = {
                "configurable": {"thread_id": conversation_id}
            }
            conversation = self.memory_manager.get(config=query)
            return conversation["channel_values"]["messages"]
        except TypeError:
            logger.info("New conversation detected. Continuing...")
            return None
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error loading conversation: {error_msg}")
            logger.error(traceback.format_exc())
            return None
        

    async def _aload_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Load conversation from persistent storage.
        
        Args:
            conversation_id: Unique identifier for the conversation
            
        Returns:
            Conversation memory if successful, None otherwise
        """
        if not self._storage_dir:
            return None
        
        try:
            query = {
                "configurable": {"thread_id": conversation_id}
            }
            conversation = await self.memory_manager.aget(config=query)
            return conversation["channel_values"]["messages"]
        except TypeError:
            logger.info("New conversation detected. Continuing...")
            return None
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error loading conversation: {error_msg}")
            logger.error(traceback.format_exc())
            return None