from routes import create_app
import config
import logging
import sys
from fastapi import FastAPI

# Configure logging to print all logs to stdout
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

# Create the FastAPI application instance
app: FastAPI = create_app()