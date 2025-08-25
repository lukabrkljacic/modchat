# app.py
"""
Main Flask application for the LLM Chat Interface.
"""
import os
import requests
import logging
import json
from pydantic import BaseModel, Field
from typing import Dict, List, Any
from flask import Flask, render_template, jsonify, request, abort
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    retry_if_result
)
#-- Environment Variables ---------------------
class AppConfig(BaseModel):
    LogLevel: str = Field(default=os.getenv("LOG_LEVEL", "info"), description="The log verbosity level for the application. Default is `info`.")
    LogFile: str = Field(default=os.getenv("LOG_FILE", "app.log"), description="The path to the log file for the application. Default is `app.log`.")
    ExternalBackendUrl: str = Field(default=os.getenv("EXTERNAL_BACKEND_URL", "/api"), description="The client-side url for the backend service. Default is `http://modchat.backend.com:5000`.")
    InternalBackendUrl: str = Field(default=os.getenv("INTERNAL_BACKEND_URL", "http://modchat.backend.com:5000"), description="The server-side url for the backend service. Default is `http://modchat.backend.com:5000`.")
    ModelListingEndpoint: str = Field(default=os.getenv("MODEL_LISTING_ENDPOINT", "models"), description="The endpoint used to obtain the model listing from the backend. Default is `models`.")
    MODAgentUrl: str = Field(default=os.getenv('MOD_AGENT_URL', "http://modchat.agent.com:9999"), description="The url for the mod agent service. Default is `http://modchat.agent.com:9999`")
    DecomposeEndpoint: str = Field(default=os.getenv("DECOMPOSE_ENDPOINT", "decompose"), description="The endpoint to send decomposition requests to. Default is `decompose`.")
    ACLEnabled: bool = Field(default=os.getenv("ACCESS_CONTROL_ENABLED", "false").lower() in ("true", "1", "t"), description="Whether or not access control is enabled. Default is `False`.") 
    ACL: List[str] = Field(default=json.loads(os.getenv("MODCHAT_ACL", '[]')), description="The list of tokens that are allowed to access the frontend (if `ACCESS_CONTROL_ENABLED=true`). Default is '[]'.")
    RetryMaxAttempts: int = Field(default=int(os.getenv("RETRY_MAX_ATTEMPTS", 10)), 
                                  description="The maximum number of times to retry a network connection request. Default is `10`.")
    RetryWaitMultiplier: int = Field(default=int(os.getenv("RETRY_WAIT_MULTIPLIER", 1)), 
                                     description="The wait-time multiplier for retries (must be >=2 and <= 36). Default is `1`.")
    RetryWaitMin: int = Field(default=int(os.getenv("RETRY_WAIT_MIN", 4)), description="The minimum wait time in minutes for retries. Default is `4`.")
    RetryWaitMax: int = Field(default=int(os.getenv("RETRY_WAIT_MAX", 10)), description="The maximum wait time in minutes for retries. Default is `10`.")
    DebugMode: bool = Field(default=os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1", "t"), description="Whether or not to start the app in debug mode. Default is `False`.")

app_config = AppConfig()

## Logger Setup
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
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.FileHandler(app_config.LogFile), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Configure retries
RETRY_EXCEPTIONS = (
    requests.exceptions.RequestException,
    requests.exceptions.ConnectionError,
    requests.exceptions.Timeout,
    ValueError
)
is_retryable_status_code = lambda code: code in [429, 500, 502, 503, 504]

@retry(
        stop=stop_after_attempt(app_config.RetryMaxAttempts),
        wait=wait_exponential(
            multiplier=app_config.RetryWaitMultiplier, 
            min=app_config.RetryWaitMin, 
            max=app_config.RetryWaitMax),
        retry=retry_if_exception_type(RETRY_EXCEPTIONS) | retry_if_result(is_retryable_status_code)
)
def get_available_models(url: str) -> Dict[str, Any]:
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        vendors = resp.json().get("vendors")
        return vendors
    except Exception as ex:
        raise ValueError(f"Unable to load model list due to the following exception: {str(ex)}")

# -- Get URLs to other services
backend_server_side_url = app_config.InternalBackendUrl
mod_agent_service_url = app_config.MODAgentUrl
model_listing_endpoint = app_config.ModelListingEndpoint
decompose_endpoint = app_config.DecomposeEndpoint

logger.info(f"Checking for available vendors at {backend_server_side_url}/{model_listing_endpoint}")
vendors = get_available_models(url=f"{backend_server_side_url}/{model_listing_endpoint}")
logger.info(f"Available Vendors: {vendors}")

# Initialize Flask app
app = Flask(__name__)
    
@app.route("/")
def index():
    """Render the main chat interface."""
    token = request.args.get('token')
    if app_config.ACLEnabled == True:
        if not token or token not in app_config.ACL:
            abort(401)

    return render_template(
        "index.html", 
        vendors=vendors, 
        BACKEND_URL=app_config.ExternalBackendUrl,
        MOD_AGENT_URL=mod_agent_service_url,
        DECOMPOSE_ENDPOINT=decompose_endpoint,
        USER_TOKEN=token
    )

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for monitoring."""
    health = {
        "status": "ok"
    }
    return jsonify(health)

@app.errorhandler(401)
def not_authorized(error):
    """Handle 401 errors (user not authorized)"""
    error_msg = "Token provided is not valid. Please check the url and token again before retrying."
    return jsonify({"error": error_msg}), 401

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors."""
    logger.error(f"Server error: {str(error)}")
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    logger.info("Starting Flask application")
    debug_mode = app_config.DebugMode

    try:
        app.run(debug=debug_mode)
    except Exception as e:
        logger.critical(f"Failed to start application: {str(e)}")
