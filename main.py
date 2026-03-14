from graph.graph import graph

def main():
    print("Speech Generator ready. Type 'quit' to exit.\n")

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break

        if not user_input:
            continue

        print("\nGenerating your speech...\n")

        result = graph.invoke({
            "graph_state": user_input
        })

        print("=== FINAL VOICE SCRIPT ===")
        print(result["stylistic_script"])
        print("==========================\n")


if __name__ == "__main__":
    main()