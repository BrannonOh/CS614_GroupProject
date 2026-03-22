from graph.graph_baseline import graph
from pathlib import Path
import json
from datetime import datetime
import warnings 
warnings.filterwarnings(
    "ignore",
    message=r"Pydantic serializer warnings:.*",
    category=UserWarning,
)

# Checks if user wants to quit programme
def prompt(field):
    value = input(f"{field}: ").strip()
    if value.lower() in {"quit", "exit", "q"}:
        print("Goodbye!")
        exit()
    return value

def main():
    print("Speech Generator ready. Type 'quit' to exit.\n")
    print("Please provide your speech details in the following format:\n")
    print("""Topic:
Audience:
Occasion:
Time limit:
Content: For each point, please state your Point and the Example/Fact to substantiate
""")

    while True: # Will keep generating scripts until user types quit.
        topic = prompt("Topic")
        audience = prompt("Audience")
        occasion = prompt("Occasion")
        time_limit = prompt("Time limit")
        content = prompt("Contents")

        print("\nGenerating your speech...\n")

        result = graph.invoke({
            "user_input": {
                "topic": topic,
                "audience": audience,
                "occasion": occasion,
                "time_limit": time_limit,
                "content": content
            }
        })

        print("=== FINAL SCRIPT ===")
        print(result["stylistic_script"])
        print("==========================\n")
        print("Ready to generate next speech. Type 'quit' to exit.\n")

        # Save results from Judge A & Judge B: 
        output_dir = Path("evaluation/eval_judgement_artifacts/judging_results_baseline_system")
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        payload = {
            "user_input": result.get("user_input"),
            "stylistic_script": result.get("stylistic_script"),
            "judge_a_result": (
                result["judge_a_result"].model_dump(mode="json")
                if result.get("judge_a_result") is not None else None 
            ),
            "judge_b_result": (
                result["judge_b_result"].model_dump(mode="json")
                if result.get("judge_b_result") is not None else None 
            ),
            "judge_a_error": result.get("judge_a_error"),
            "judge_b_error": result.get("judge_b_error"),
        }

        (output_dir / f"judging_results_{timestamp}.json").write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )        

if __name__ == "__main__":
    main()