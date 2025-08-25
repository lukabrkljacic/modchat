from src.agent.mod import ResponseDecomposition
import os
import logging
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import a2a.types
from typing import Dict, Any
from fastapi import FastAPI, UploadFile, File, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool
from psycopg.rows import dict_row
from contextlib import asynccontextmanager
from urllib.parse import urlparse
import json

#-- Environment Variables -----------------------------------
class AppConfig(BaseModel):
    LogLevel: str = Field(default=os.getenv("LOG_LEVEL", "info"), 
                          description="The log verbosity level for the application. Default is `info`.")
    LogFile: str = Field(default=os.getenv("LOG_FILE", "app.log"), 
                         description="The path to the log file for the application. Default is `app.log`.")
    AgentBaseUrl: str = Field(default=os.getenv("AGENT_BASE_URL", "http://modchat.agent.com:9999"), 
                             description="The url for the MOD agent.")
    LanguageModelVendor: str = Field(default=os.environ.get("LLM_VENDOR", "openai"), description="The vendor for the language model used by the agent.")
    LanguageModelId: str = Field(default=os.environ.get("LLM_MODEL_ID", "gpt-4.1-mini"), descripton="The model id for the language model used by the agent.")
    DatabaseUrl: str = Field(default=os.getenv("DATABASE_URL", ""), description="The database url connection string.")
    FrontendUrl: str = Field(default=os.getenv("FRONTEND_URL", "http://modchat.frontend.com:8888"), 
                             description="The url for the frontend client.")
    BackendUrl: str = Field(default=os.getenv("BACKEND_URL", "http://modchat.backend.com:5000"), description="The url for the backend service.")
    AgentName: str = Field(default=os.getenv("AGENT_NAME", "DecomposeAgent"), description="The name of the agent. Default is `DecomposeAgent`")
    AgentDescription: str = Field(default=os.getenv("AGENT_DESCRIPTION", "Agent that decomposes a solution into components"), 
                                  description="A written description of the agent's functionality and purpose.")
    AgentVersion: str = Field(default=os.getenv("AGENT_VERSION", "1.0"), description="The agent's version.")
    AgentStreamingEnabled: bool = Field(default=os.getenv("AGENT_STREAMING_ENABLED", "false").lower() in ("true", "1", "y", "yes"),
                                        description="Whether or not the agent handles streaming via A2A")
    AgentPushNotificationsEnabled: bool = Field(default=os.getenv("AGENT_PUSH_NOTIFICATIONS_ENABLED", "false").lower() in ("true", "1", "y", "yes"),
                                                description="Whether or not the agent performs push notifications via A2A.")

app_config = AppConfig()

# Logger Setup
def get_log_level(log_level: str) -> int:
    log_level_map = {
        "info": logging.INFO,
        "debug": logging.DEBUG,
        "critical": logging.CRITICAL,
        "warning": logging.WARNING
    }
    return log_level_map.get(log_level)

log_level = get_log_level(log_level=app_config.LogLevel)
logging.basicConfig(
    level=log_level,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.FileHandler(app_config.LogFile), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Parse the base url
agent_base_url = app_config.AgentBaseUrl
parsed_url = urlparse(agent_base_url)
# Get the LLM vendor and model from the environment
llm_vendor = app_config.LanguageModelVendor
llm_model = app_config.LanguageModelId
db_url = app_config.DatabaseUrl

# -- FastAPI Configuration
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
            
        except Exception as e:
            logger.exception(f"Unable to connect to Postgres due to exception: {str(e)}")
            pass
        settings = {
            "contextLength": 32000
        }
        app.state.agent = ResponseDecomposition(model_id=llm_model, vendor=llm_vendor, checkpointer=memory_manager, settings=settings)
        app.state.connection_pool = pool
        yield

app = FastAPI(lifespan=lifespan)
# CORS settings
origins = [app_config.FrontendUrl, app_config.BackendUrl]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"]
)

# Define the Agent Card data (metadata about this agent)
AGENT_CARD = {
    "name": app_config.AgentName,
    "description": app_config.AgentDescription,
    "url": agent_base_url,  # The base URL where this agent is hosted
    "version": app_config.AgentVersion,
    "capabilities": {
        "streaming": app_config.AgentStreamingEnabled,           # This agent doesn't support streaming responses
        "pushNotifications": app_config.AgentPushNotificationsEnabled   # No push notifications in this simple example
    }
    # (In a full Agent Card, there could be more fields like authentication info, etc.)
}

# Container health check endpoint 
@app.get("/healthz")
async def health_check():
    """Endpoint for container health check"""
    return {
        "status": "ok"
    }

@app.get("/info")
async def info():
    return {
        "name": app.state.agent.name,
        "vendor": llm_vendor,
        "model": llm_model
    }

# Serve the Agent Card at the well-known URL.
@app.get("/.well-known/agent.json")
async def get_agent_card():
    """Endpoint to provide this agent's metadata (Agent Card)."""
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=AGENT_CARD
    )

# Handle incoming task requests at the A2A endpoint.
@app.post("/tasks/send")
async def handle_task(data: Dict[str, Any]):
    """Endpoint for A2A clients to send a new task (with an initial user message)."""
    # Extract the task ID and the user's message text from the request.
    task_id = data.get("id")
    conversation_id = data.get("conversation_id")
    user_token = data.get("userToken")
    thread_id = f"{user_token}-{conversation_id}"
    response_text = ""
    try:
        # According to A2A spec, the user message is in task_request["message"]["parts"][0]["text"]
        response_text = data["message"]["parts"][0]["text"]

        logger.debug(f"Passing the following response to the decompose tool:\n{response_text}")
        # Validate input
        if not response_text:
            err = a2a.types.InvalidRequestError(message="No response text provided")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=err.model_dump(mode='json')
            )

        logger.info("Decomposition request received")

        # Use the existing decompose_tool
        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }
        logger.debug("Decomposing task...")
        decomposed_response = await app.state.agent.ainvoke(response_text, config)
        if decomposed_data := decomposed_response.get("decomposed_response"):
            decomposed_data = decomposed_data.model_dump()
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="A decomposition request was sent but no response was found."
            )

        logger.debug("Task decomposed successfully!")
        # Extract components from decomposed response
        components = decomposed_data.get("components", [])

        # Determine output type based on response content
        output_type = "document"
        if "email" in response_text.lower():
            output_type = "email"
        elif "report" in response_text.lower():
            output_type = "report"

        # Prepare response
        response_data = {
            "components": components,
            "outputType": output_type,
            "outputStructure": (
                [list(component.keys())[0] for component in components]
                if components
                else []
            ),
        }

        logger.info(
            f"Successfully decomposed response into {len(components)} components"
        )

    except Exception as e:
        err = a2a.types.InternalError(message=str(e))
        logger.debug(err)
        logger.debug(str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=err.model_dump(mode='json')
        )
 
    # Formulate the response in A2A Task format.
    # We'll return a Task object with the final state = 'completed' and the agent's message.
    task_status = a2a.types.TaskStatus(state=a2a.types.TaskState.completed)
    # Create a DataPart
    data_part = a2a.types.DataPart(data=response_data)
    # Create a Part
    part = a2a.types.Part(data_part)
    # Create an Artifact
    artifact = a2a.types.Artifact(artifactId="myartifact", parts=[part])
    # Create the final response
    response_task = a2a.types.Task(contextId="1234", id="asdf", status=task_status, artifacts=[artifact])
    # Serialize to JSON and return
    j = response_task.model_dump(mode='json')
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=j
    )

# Run the Flask app (A2A server) if this script is executed directly.
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=parsed_url.port)
