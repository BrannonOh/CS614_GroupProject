from config import client, MODEL_NAME
from logger import logger
import json

def Reflection_Agent(state):
    logger.info("=== Reflection_Agent START ===")
    logger.info(f"Attempt: {state.get('style_attempts', 0) + 1}")
    
    stylistic_script = state.get("stylistic_script", "")
    plan = state.get("plan", "")
    logger.info(f"Input stylistic_script:\n{stylistic_script}")
    
    prompt = f"""
Review the following script and satisfy the requirements.

Script:{stylistic_script}
Requirements: {plan}

Output format:
{{
  "approved": true or false,
  "feedback": "<what needs to amended>"
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
    logger.info("=== Reflection_Agent END ===\n")
    
    return {
        "style_approved": result["approved"],
        "style_feedback": result["feedback"],
        "style_attempts": state.get("content_attempts", 0) + 1
    }