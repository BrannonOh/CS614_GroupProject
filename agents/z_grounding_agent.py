from config import client, MODEL_NAME
from logger import logger
import json

def Grounding_Agent(state):
    logger.info("=== Grounding_Agent START ===")
    logger.info(f"Attempt: {state.get('content_attempts', 0) + 1}")
    content = state.get("content", "")
    logger.info(f"Input content:\n{content}")
    
    prompt = f"""
Review the following content and determine if it is factual.

Content to be reviewed:{content}

Output format:
{{
  "approved": true or false,
  "feedback": "<what needs to amended or removed>"
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
    logger.info("=== Grounding_Agent END ===\n")
    return {
        "content_approved": result["approved"],
        "content_feedback": result["feedback"],
        "content_attempts": state.get("content_attempts", 0) + 1
    }