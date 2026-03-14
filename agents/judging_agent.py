from config import client, MODEL_NAME
from logger import logger

def Judging_Agent(state):
    logger.info("=== Judging_Agent START ===")

    current_context = state.get("graph_state", "")
    ted_structure = state.get("ted_structure","")
    feedback = state.get("content_feedback", "")
    
    logger.info(f"Attempt: {state.get('content_attempts', 0) + 1}")
    logger.info(f"Feedback received: {feedback if feedback else 'None'}")
    
    prompt = f"""
    Based on the following structure:{ted_structure}
    {"Feedback to incorporate: " + feedback if feedback else ""}
    Elaborate further on the content and return in JSON.

    Example of output format:

{{
  "total_target_word_count": <to be defined>,
  "sections": [
    {{
      "section_id": "S1",
      "name": "<define section>",
      "purpose": "<clear objective of this opening>",
      "word_budget": <define word budget>,
      "must_include": [
        "<required narrative or factual elements>"
      ],
      "rhetorical_moves": [
        "contrast",
        "short punchy sentences",
        "hook question"
      ],
      "claim_slots": [
        {{
          "claim_id": "C1",
          "type": "principle | definition | evidence | projection",
          "risk_level": "low | medium | high",
          "needs_citation": true,
          "allowed_sources": ["academic", "industry report", "internal", "none"]
        }}
      ],
      "retrieval_intent": {{
        "structure_queries": [],
        "voice_queries": [],
        "facts_queries": []
      }}
    }}
  ]
}}

    """
    
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )
    
    logger.info(f"Content generated\n{response.text}")
    logger.info("=== Content_Agent END ===")
    
    return {
    "content": response.text,
    "graph_state": current_context + "\n\n[CONTENT OUTPUT]\n" + response.text 
}