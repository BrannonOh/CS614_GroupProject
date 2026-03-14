from config import client, MODEL_NAME
from logger import logger
import json

def Structure_Checking_Agent(state):
    logger.info("=== Structure_Checking_Agent START ===")
    logger.info(f"Attempt: {state.get('ted_attempts', 0) + 1}")
    ted_structure = state.get("ted_structure", "")
    logger.info(f"Input ted_structure:\n{ted_structure}")
    
    prompt = f"""
You are a Structure Checking Agent. Review the following speech structure and determine if it is coherent for a TED-style speech.

Structure:{ted_structure}

Output format:
{{
  "approved": true or false,
  "feedback": "<what needs to improve, or empty string if approved>"
}}
"""
    
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )
    
    # Clean and parse the JSON response
    raw = response.text.strip().replace("```json", "").replace("```", "")
    result = json.loads(raw)
    logger.info(f"Approved: {result['approved']} | Feedback: {result['feedback']}")
    logger.info("=== Structure_Checking_Agent END ===\n")
    
    return {
        "ted_approved": result["approved"],
        "ted_feedback": result["feedback"],
        "ted_attempts": state.get("ted_attempts", 0) + 1
    }