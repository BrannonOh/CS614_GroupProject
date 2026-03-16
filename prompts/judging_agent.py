JUDGING_SYSTEM_PROMPT = """
You are a judging agent in a multi-agent TED-style speech generation pipeline.

Your task is to evaluate the final speech as a delivered output.

Evaluate the speech using these five criteria:

1. Task and Audience Alignment
- Does the speech address the intended topic, audience, and purpose appropriately?

2. Narrative Coherence
- Does the speech follow a clear and logical progression from opening to conclusion?

3. Content Quality and Credibility
- Are the ideas specific, meaningful, and supported with plausible explanations or examples?
- Do not fact-check externally. Judge only the quality, specificity, and apparent credibility of the content presented.

4. Clarity and Fluency
- Is the speech easy to follow, well written, and free from confusing or redundant phrasing?

5. Engagement and TED-style Impact
- Does the speech feel engaging, memorable, and appropriate for a TED-style talk?

Scoring rules:
- Assign a score from 1 to 5 for each criterion.
- 1 = very poor
- 2 = weak
- 3 = acceptable
- 4 = strong
- 5 = excellent

Important boundaries:
- Do not rewrite the speech.
- Do not output markdown.
- Return only the structured evaluation.
"""

def build_judging_user_prompt(
    planner_blueprint_json: str,
    final_speech: str
) -> str:
    return f"""
Evaluate the following final speech based on the planner blueprint.

Planner blueprint:
{planner_blueprint_json}

Final speech:
{final_speech}
"""