# app.py
"""
Main Flask application for the LLM Chat Interface.
"""
import os
import json
import logging
import traceback
import a2a.types
import uuid
import httpx
from fastapi import FastAPI, UploadFile, File, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Dict, Any, Union
from pydantic import BaseModel, Field   
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool
from psycopg.rows import dict_row

#-- Environment Variables --------------------------------------
class AppConfig(BaseModel):
    LogLevel: str = Field(default=os.getenv("LOG_LEVEL", "info"), 
                          description="The log verbosity level for the application. Default is `info`.")
    LogFile: str = Field(default=os.getenv("LOG_FILE", "app.log"), description="The path to the log file for the application. Default is `app.log`.")
    DebugMode: bool = Field(default=os.getenv("DEBUG_MODE", "False").lower() in ("true", "1", "t"), 
                            description="Whether or not to start the app in debug mode. Default is `False`.")
    DatabaseUrl: str = Field(default=os.getenv("DATABASE_URL", ""), description="The database url connection string.")
    ConversationStorageDirectory: str =  Field(default=os.getenv('CONVERSATION_STORAGE_DIR', 'conversations'), 
                                               description="The path to the directory that stores conversations.")
    MaxConversationsInMemory: int = Field(default=int(os.getenv('MAX_CONVERSATIONS_IN_MEMORY', 100)), 
                                          description="The maximum number of conversations stored in memory.")
    UploadFolder: str = Field(default=os.getenv("UPLOAD_FOLDER", "uploads"), 
                              description="The location of the upload folder for context uploads from the client.")
    MaxUploadSize: int = Field(default=int(os.getenv("MAX_UPLOAD_SIZE", 16 * 1024 * 1024)), 
                               description="The maximum file size (in bytes) for file uploads from the client. Default is `16777216` (16MB).")
    FrontendUrl: str = Field(default=os.getenv("FRONTEND_URL", "http://modchat.frontend.com:8888"), 
                             description="The url for the frontend client.") 
    MODAgentUrl: str = Field(default=os.getenv("MOD_AGENT_URL", "http://modchat.agent.com:9999"), 
                             description="The url for the MOD agent.")
    DecomposeEndpoint: str = Field(default=os.getenv("DECOMPOSE_ENDPOINT", "decompose"), 
                                   description="The endpoint to send decomposition requests to. Default is `decompose`.")

app_config = AppConfig()

#-- ** Configure logging ** --------------------------------------
def get_log_level(log_level: str) -> int:
    log_level_map = {
        "info": logging.INFO,
        "debug": logging.DEBUG,
        "critical": logging.CRITICAL,
        "warning": logging.WARNING
    }
    return log_level_map.get(log_level)

logging.basicConfig(
    level=get_log_level(log_level=app_config.LogLevel),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(app_config.LogFile), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

#-- ** Import custom modules ** --------------------------------------
try:
    from mod.errors.error_handlers import (
        ModelInitializationError,
        FileProcessingError,
        ConversationError
    )
    from mod.file_handlers import (
        process_uploaded_files,
        extract_document_content,
        get_supported_file_types
    )
    from mod.models.model_factory import model_factory
    from mod.models.model_registry import AVAILABLE_VENDORS
    from mod.conversation_manager import ConversationManager

except ImportError as e:
    logger.critical(f"Error importing custom modules: {str(e)}")
    raise

#-- ** Database Connection Info ** -------------------------------------
db_url = app_config.DatabaseUrl
#-- ** FastAPI Application Setup ** -------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Set up memory manager at the start of the server lifecycle
    kwargs = {
        "autocommit": True,
        "row_factory": dict_row
    }
    async with AsyncConnectionPool(conninfo=db_url, kwargs=kwargs) as pool:
        memory_manager = None
        try:
            checkpointer = AsyncPostgresSaver(pool)
            await checkpointer.setup()
            memory_manager = checkpointer
            await init_feedback_db(pool=pool)
            
        except Exception as e:
            logger.exception(f"Unable to connect to Postgres due to exception: {str(e)}")
            pass
        # Initialize Conversation Manager
        conversation_manager = ConversationManager(
            storage_dir=app_config.ConversationStorageDirectory, 
            memory_manager=memory_manager, 
            max_conversations=app_config.MaxConversationsInMemory
        )
        app.state.conversation_manager = conversation_manager
        app.state.connection_pool = pool
        yield
        

app = FastAPI(lifespan=lifespan)

app.state.config = {}
app.state.config["UPLOAD_FOLDER"] = app_config.UploadFolder
app.state.config["MAX_CONTENT_LENGTH"] = app_config.MaxUploadSize
# CORS settings
frontend_url = app_config.FrontendUrl
origins = [frontend_url]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"]
)

# Ensure upload directory exists
try:
    os.makedirs(app.state.config["UPLOAD_FOLDER"], exist_ok=True)
except OSError as e:
    logger.error(f"Error creating upload directory: {str(e)}")
    raise

#-- ** MOD agent communication ** ------------------------------------
MOD_agent_url = app_config.MODAgentUrl
decompose_endpoint = app_config.DecomposeEndpoint
LLMOutput = Union[Dict[str, Any], BaseModel, str]

def call_mod_agent(output: LLMOutput, 
                   base_url: str, 
                   endpoint: str,
                   conversation_id: str,
                   user_token: str, 
                   timeout: float = 300.0):
    with httpx.Client(base_url=base_url, timeout=timeout) as client:
        if isinstance(output, BaseModel):
            output = output.model_dump_json()
        elif isinstance(output, dict):
            output = json.dumps(output)
        task_id = str(uuid.uuid4())
        payload = {
            "id": task_id,
            "userToken": user_token,
            "conversation_id": conversation_id,
            "message": {
                "role": "user",
                "parts": [
                    {"text": output}
                ]
            }
        }
        resp = client.post(f"/{endpoint}", json=payload)
        resp.raise_for_status()
        
    return resp.json()

async def acall_mod_agent(
        output: LLMOutput, 
        base_url: str, 
        endpoint: str,
        conversation_id: str,
        user_token: str, 
        timeout: float = 300.0):
    async with httpx.AsyncClient(base_url=base_url, timeout=timeout) as client:
        if isinstance(output, BaseModel):
            output = output.model_dump_json()
        elif isinstance(output, dict):
            output = json.dumps(output)
        task_id = str(uuid.uuid4())
        payload = {
            "id": task_id,
            "userToken": user_token,
            "conversation_id": conversation_id,
            "message": {
                "role": "user",
                "parts": [
                    {"text": output}
                ]
            }
        }
        resp = await client.post(f"/{endpoint}", json=payload)
        resp.raise_for_status()

    return resp.json()


def process_decomposed_response(task_response: Dict[str, Any]):
    task = a2a.types.Task.model_validate_json(json.dumps(task_response))
    response_data = {}
    if task.artifacts is not None:
        for artifact in task.artifacts:
            for part in artifact.parts:
                data = part.root
                components = data.data.get("components", [])
                if components:
                    response_data["components"] = components
                    response_data["outputType"] = data.data.get("outputType", "")
                    response_data["outputStructure"] = [
                        list(component.keys())[0] for component in components
                    ]
    return response_data


async def init_feedback_db(pool: AsyncConnectionPool) -> None:
    """Initialize the feedback database and table if it doesn't exist."""
    try:
        async with pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS feedback (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMP,
                        q1 INTEGER,
                        q2 INTEGER,
                        q3 INTEGER,
                        q4 INTEGER,
                        q5 INTEGER,
                        q6 INTEGER,
                        q7 INTEGER,
                        q8 INTEGER,
                        q9 INTEGER,
                        q10 INTEGER,
                        comments TEXT
                    )
                    """
                )
            await conn.commit()
    except Exception as ex:
        logger.exception(f"Encountered the following exception while trying to initialize feedback table: {str(ex)}")

#-- ** Routes ** -----------------------------------------------------
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Handle file uploads."""
    supported_file_types = {"jpg", "jpeg", "png", "pdf", "docx", "txt"}
    # Check for empty filename
    if file.filename == "":
        logger.warning("Upload request with empty filename")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No selected file"
        )

    try:
        filename = file.filename
        file_path = os.path.join(app.state.config["UPLOAD_FOLDER"], filename)
        with open(file_path, "wb") as buffer:
            while contents := await file.read(1024 * 1024):
                buffer.write(contents)

        logger.info(f"Successfully uploaded file: {filename}")

        # Check if file type is supported
        file_ext = filename.split(".")[-1].lower() if "." in filename else None
        is_supported = file_ext in supported_file_types

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "filename": filename,
                "file_path": file_path,
                "supported": is_supported,
            }
        )
    
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File upload failed: {str(e)}"
        )


@app.post("/chat")
async def chat(data: Dict[str, Any]):
    """Handle chat requests with structured component output."""
    logger.debug(f"Received data: {data}")
    try:
        user_input = data.get("message", "")
        model_id = data.get("model", "")
        user_token = data.get("userToken", "")
        vendor = data.get("vendor", "")
        settings = data.get("settings", {})
        files = data.get("files", [])
        decompose = data.get("decompose", False)  # Check if decomposition is requested
        session_id = data.get("session_id", str(uuid.uuid4()))

        # Validate required inputs
        if not user_input:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty message"
            )
        if not model_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No model selected"
            )
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No vendor specified"
            )

        logger.info(
            f"Chat request: model={model_id}, vendor={vendor}, decompose={decompose}"
        )

        # Generate a conversation ID (or use one if provided)
        conversation_id = data.get("conversation_id", str(uuid.uuid4()))
        # Get LLM instance from factory
        llm = model_factory.get_model(vendor, model_id, settings)
        # Get system prompt from settings
        system_prompt = settings.get("systemPrompt", "You are a helpful AI assistant.")
        response_format = settings.get("responseFormat")
        response_obj = None
        # Augment the system prompt to request structured output if needed
        if response_format and response_format != "{}":
            try:
                response_obj = json.loads(response_format)
                if "json" not in system_prompt.lower():
                    structured_request = f"""
                    Required JSON output:
                    ```json
                    {response_format.replace('{', '{{').replace('}', '}}')}
                    ```
                    """
                    system_prompt = f"{system_prompt}\n\n{structured_request}"
                format_method = "json_mode" if vendor.lower() == "openai" else None
                logger.info("Using structured output for responses")
                llm = llm.with_structured_output(response_obj, method=format_method)
            except json.JSONDecodeError:
                logger.info("Invalid structure given for response format. Skipping.")
                
            except Exception as ex:
                logger.info(f"Encountered the following exception while trying to set up structured output: {str(ex)}.\nSkipping structured output.")

        # Process any uploaded files
        file_paths = [file.get("path") for file in files if file.get("path")]
        documents = []

        if file_paths:
            try:
                # Set chunk size from settings if available
                chunk_size = int(settings.get("chunkSize", 1000))
                documents, failed_files = process_uploaded_files(
                    file_paths, chunk_size=chunk_size, chunk_overlap=100
                )

                # Log any failed files
                if failed_files:
                    logger.warning(f"Failed to process {len(failed_files)} files")
            except FileProcessingError as e:
                # Continue without documents if processing fails
                logger.error(f"File processing error: {str(e)}")

        # Add document content to user input if available
        if documents:
            doc_content = extract_document_content(documents)
            user_input = f"{user_input}\n\nRelevant document content:\n{doc_content}"

        # Create conversation chain
        try:
            conversation_id, chain = await app.state.conversation_manager.acreate_chain(
                llm, system_prompt, session_id, conversation_id
            )
            app.state.conversation_manager.record_metadata(session_id, conversation_id, model_id, settings)
        except ConversationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"An exception occurred while creating conversation chain: {str(e)}"
            )

        # Get response from the chain
        logger.info(f"Sending request to LLM for conversation {conversation_id}")
        thread_id = f"{user_token}-{conversation_id}"
        try:
            # Every invocation returns a full list of the chat history
            config = {
                "configurable": {
                    "thread_id": thread_id
                }
            }
            chat_history = await chain.ainvoke({"messages": [user_input]}, config=config)
            response_content = chat_history["messages"][-1].content

            # Prepare response data
            response_data = {
                "text": response_content,
                "model": model_id,
                "vendor": vendor,
                "conversation_id": conversation_id,
            }

            # If decompose is enabled, perform decomposition
           
            if decompose:
                try:
                    decomposed_data = await acall_mod_agent(
                        output=response_content, 
                        base_url=MOD_agent_url, 
                        endpoint=decompose_endpoint,
                        conversation_id=conversation_id,
                        user_token=user_token
                    )
                    decomposed_response =  process_decomposed_response(decomposed_data)
                    if not decomposed_response:
                        logger.warning("Decomposition returned no components")
                    # Add decomposed components to response
                    response_data.update(decomposed_response)
                    
                except Exception as e:
                    logger.error(f"Error during decomposition: {str(e)}")
                    logger.error(traceback.format_exc())
                    # Continue without components if decomposition fails

            logger.debug(f"Response payload for UI: {response_data}")
            return JSONResponse(
                status_code=status.HTTP_200_OK, 
                content=response_data
            )

        except Exception as e:
            logger.error(f"Error getting response from LLM: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error from language model: {str(e)}"
            )

    except ModelInitializationError as e:
        logger.error(f"Model initialization error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error in chat endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred. Please try again.\n{str(e)}"
        )

@app.post("/regenerate")
async def regenerate(data: Dict[str, Any]):
    """Regenerate a piece of text using the selected model and a user prompt."""
    try:
        text = data.get("text", "")
        prompt = data.get("prompt", "")
        model_id = data.get("model", "")
        vendor = data.get("vendor", "")
        settings = data.get("settings", {})
        conversation_id = data.get("conversation_id")
        session_id = data.get("session_id", str(uuid.uuid4()))

        # Additional context for regeneration
        component_title = data.get("component_title", "")
        original_response = data.get("original_response", "")
        original_prompt = data.get("original_prompt", "")


        f"You are editing the component titled '{component_title}'."
        f"Its current text is:\n{text}\n\n"
        f"Edit only that component using the user's instruction: {prompt}\n"
        "Return only the updated text for this component."

        llm = model_factory.get_model(vendor, model_id, settings)

        system_prompt = settings.get("systemPrompt", "You are a helpful AI assistant.")

        try:
            conversation_id, chain = await app.state.conversation_manager.acreate_chain(
                llm,
                system_prompt,
                session_id,
                conversation_id,
            )
            app.state.conversation_manager.record_metadata(session_id, conversation_id, model_id, settings)
            
            # Craft regeneration prompt with full context
            regen_input = (
                f"Original user request:\n{original_prompt}\n\n"
                f"Original assistant response:\n{original_response}\n\n"
                f"You are editing the component titled '{component_title}'. "
                f"Its current text is:\n{text}\n\n"
                f"Edit only that component using the user's instruction: {prompt}\n"
                "Return only the updated text for this component."
            )
            config = {
                "configurable": {
                    "thread_id": conversation_id
                }
            }
            regenerated = await chain.ainvoke({"messages": [regen_input]}, config=config)
            regenerated_content = regenerated["messages"][-1].content
        except Exception as e:
            logger.error(f"Error invoking model for regeneration: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Regeneration failed: {str(e)}"
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "text": regenerated_content, 
                "conversation_id": conversation_id
            }
        )

    except Exception as e:
        logger.error(f"Unexpected error in regenerate endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Regeneration failed: {str(e)}"
        )

@app.post("/save_settings")
def save_settings(settings: Dict[str, Any]):
    """Save user settings."""
    try:
        # Validate settings (optional)
        if "temperature" in settings:
            temp = float(settings["temperature"])
            if temp < 0 or temp > 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Temperature must be between 0 and 1"
                )

        # In a real app, you would save these to a database or session
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True, 
                "settings": settings
            }
        )
    except Exception as e:
        logger.error(f"Error saving settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save settings: {str(e)}"
        )

@app.post("/log_event")
def log_event(data: Dict[str, Any]):
    """Record a user interaction event."""
    try:
        event_type = data.get("event_type")
        conversation_id = data.get("conversation_id", "global")
        session_id = data.get("session_id", "")
        event_data = data.get("data", {})

        if not event_type:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content= {"error": "Missing event_type"}
            )

        app.state.conversation_manager.record_event(session_id, conversation_id, event_type, event_data)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"success": True}
        )
    except Exception as e:
        logger.error(f"Error logging event: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to log event: {str(e)}"
        )

@app.get("/models")
def get_models():
    """Get available models."""
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"vendors": AVAILABLE_VENDORS}
    )

@app.get("/health")
def health_check():
    """Health check endpoint for monitoring."""
    health = {
        "status": "ok",
        "api_keys": {
            "openai": bool(os.getenv("OPENAI_API_KEY")),
            "anthropic": bool(os.getenv("ANTHROPIC_API_KEY")),
        },
        "file_types": get_supported_file_types(),
        "vendors": model_factory.get_supported_vendors(),
    }
    return JSONResponse(
        status_code=status.HTTP_200_OK, 
        content=health
    )

@app.post("/feedback")
async def submit_feedback(data: Dict[str, Any]):
    """Store user feedback ratings and comments."""
    try:
        data = data or {}
        ratings = data.get("ratings")
        comments = data.get("comments", "")

        if not isinstance(ratings, list) or len(ratings) != 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Submitted invalid ratings"
            )

        values = [int(r) for r in ratings]
        pool = app.state.connection_pool
        async with pool.connection() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute(
                        """
                        INSERT INTO feedback (
                            timestamp, q1, q2, q3, q4, q5, q6, q7, q8, q9, q10, comments
                        ) VALUES (NOW(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        [*values, comments],
                    )
                    await conn.commit()
                except Exception as ex:
                    logger.exception(f"Encountered the following exception while trying to store feedback: {str(ex)}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detaiil=f"Encountered error: {str(ex)}"
                    )
                return JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content={"success": True}
                )
    
    except Exception as e:
        logger.error(f"Error saving feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Encountered error: {str(e)}"
        )

if __name__ == "__main__":
    logger.info("Starting server")
    debug_mode = app_config.DebugMode

    try:
        app.run(debug=debug_mode)
    except Exception as e:
        logger.critical(f"Failed to start application: {str(e)}")