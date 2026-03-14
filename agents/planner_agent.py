from config import client, MODEL_NAME
from logger import logger

def Planner_Agent(state):
    logger.info("=== Planner_Agent START ===")
    current_context = state.get("graph_state", "")
    logger.info(f"Input context:\n{current_context}")
    
    prompt = f"""
You are a Strategic Speech Planning Agent. Your task is to analyze the current context and produce a structured speech blueprint.

current context: {current_context}

Instructions:
1. Extract or infer:
   - Topic
   - Target audience
   - Occasion
   - Time constraint (if available)

2. Create a structured speech blueprint based on the time constraint.
3. **Output MUST be valid JSON.**
4. Do NOT include explanations, markdown, or commentary.

Output format:

{{
  "blueprint_version": "1.0",
  "request_summary": {{
    "topic": "<clear and concise topic>",
    "audience": "<primary audience>",
    "occasion": "<event or setting>",
    "time_limit_minutes": "<minutes>"
  }},
  "targets": {{
    "estimated_wpm": <to be defined>,
    "target_word_count": <to be defined>,
    "target_tone": <to be defined>
  }}
}}

"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )
    logger.info(f"Plan generated:\n{response.text}")
    logger.info("=== Planner_Agent END ===")
    return {
        "plan": response.text,
        "graph_state": current_context + "\n\n[PLANNER OUTPUT]\n" + response.text 
    }