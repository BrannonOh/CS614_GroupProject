from graph.graph import build_graph

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

if __name__ == "__main__":
    main()