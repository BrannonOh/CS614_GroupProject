# Install Packages
import re
import json
import os
from pathlib import Path

from pprint import pprint
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

# Import typing helpers for type hints 
from typing import TypedDict, Dict, List, Literal, Optional, Any

# BaseModel is the core class used to define structured data models 
from pydantic import BaseModel, Field, ConfigDict, model_validator, ValidationError

# Import schemas
from schemas.content_blueprint import ContentBlueprint

# Import LangGraph state
from graph.state import SpeechScriptState

# Load API Key
import os
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

def Content_Agent(state: SpeechScriptState):
    """Put in description of agent here"""
    print("\n========CONTENT AGENT (PLACEHOLDER)========")

    # Load mock data and store it inside the state first as a pass through
    BASE_DIR = Path(__file__).resolve().parent.parent  # go to root folder
    mock_data_path = BASE_DIR / "mocks" / "mock_content_blueprint.json"
    with open(mock_data_path, "r") as f:
        data = json.load(f)

    return {
        "content_blueprint": data
    }
