from config import client, MODEL_NAME
from logger import logger

def Stylistic_Agent(state):
    logger.info("=== Stylistic_Agent START ===")
    
    current_context = state.get("graph_state", "")
    content = state.get("content", "")
    feedback = state.get("style_feedback", "")

    logger.info(f"Attempt: {state.get('style_attempts', 0) + 1}")
    logger.info(f"Feedback received: {feedback if feedback else 'None'}")
    
    prompt = f"""
    Based on the following content, craft a speech like Elon Musk:
    {content}
    
    {"Feedback to incorporate: " + feedback if feedback else ""}
    """
    
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )
    logger.info(f"Script generated:\n{response.text}")
    logger.info("=== Stylistic_Agent END ===")
    
    return {
        "graph_state": current_context + "\n\n[SCRIPT OUTPUT]\n" + response.text ,
        "stylistic_script": response.text
    }