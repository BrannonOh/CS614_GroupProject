# CS614_Group

## Introduction to Project
We create a multi-agentic system which helps a user turn a speech outline into a professional script based on TED-talk best practices, while personalised to the user's style. 

## File Structure
```
project/
│
├── agents/
│   ├── planner_agent.py
│   ├── ted_agent.py
│   └── etc
│
├── graph/
│   ├── state.py
│   └── graph.py
│
├── schemas/
│   ├── planner_blueprint.py
│   └── etc
│
├── utils/
│   ├── logger.py
│   ├── load_json.py
│   └── etc
│
├── mocks/
│   └── sample_planner_blueprint.json
│   └── etc
│
├── logs/
│
├── tests/
│   └── test_graph.py
│
├── .env
├── .gitignore
├── main.py
├── requirements.txt
├── README.md
└── Dockerfile
```
# Folder Descriptions
## main.py
The main file that does the execution
* load environment variables
* optionally load mock/sample input
* build the graph
* create the initial state
* invoke the graph
* print or save the result

## agents
Each file contains one agent node function.

## graph
* state.py: Defines the shared state shape.
* graph.py: Defines nodes and edges.

## schemas
* only required for data that needs validation

## utils
* Contains shared helper code, e.g. logging, loading of JSON

## mocks
* Sample JSON for development purposes
* Useful when other parts (upstream/downstream) not finished

## logs
* Produces logs for record keeping
* log files are ignored in .gitignore

## tests
* Scripts to run test cases