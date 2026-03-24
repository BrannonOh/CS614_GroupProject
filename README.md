# CS614_Group

# Introduction to Project
We create a multi-agentic system which helps a user turn a speech outline into a professional script based on TED-talk best practices, while personalised to the user's style. 

# File Structure
```
project/
│
├── agents/
│   ├── planner_agent.py
│   ├── ted_agent.py
│   └── etc
│
├── config/
│   ├── llm_config.py
│   └── etc
|
├── data/
│   ├── samples/
│   ├── samples_chunks
│   └── speech_drafts
│
├── evaluation/
│   ├── artifacts
│   └── Jupyter notebooks
│
├── graph/
│   ├── state.py
│   ├── graph.py
│   └── graph_baseline.py
│
├── logs/
│   └── log .txt files
|
├── mocks/
│   └── mock data files (JSON, .txt)
|
├── prompts/
│   ├── judging_agent.py
│   └── etc
|
├── schemas/
│   ├── planner_blueprint.py
│   └── etc
│
├── tests/
│   └── test_graph.py
│
├── utils/
│   ├── logger.py
│   ├── helpers.py
│   └── etc
│
├── .env
├── .gitignore
├── main.py
├── main_baseline.py
├── requirements.txt
├── README.md
└── Dockerfile
```

# Folder Descriptions
## main.py and main_baseline.py
The main file that does the execution of the workflow (enhanced and baseline)
* load environment variables
* build the graph
* create the initial state
* invoke the graph
* print or save the result

## agents
Each file contains one agent node function.

## config
Contains LLM configurations

## data
* samples: Contains raw speech sample(s) that will be used by Style-related agents
* samples_chunks: Contains chunks of the raw speech sample(s)
* speech_drafts: Contains speech outputs from the workflow 

## evaluation
* Contains Jupyter notebooks that produce evaluation metrics
* Stores evaluation artifacts

## graph
* state.py: Defines the shared state shape.
* graph.py and graph_baseline.py: Defines nodes and edges for respective workflows.

## logs
* Contains logfiles
* log files are ignored in .gitignore

## mocks
* Sample data for development purposes (e.g. JSON, user input text)
* Sample raw speeches
* Useful when other parts (upstream/downstream) not finished

## prompts
* Contains prompts for LLMs

## schemas
* Pydantic schemas
* only required for data that needs validation

## tests
* Scripts to run test cases (if applicable)

## utils
* Contains shared helper code (may not be used), e.g. logging

# How to Set Up Environment
1. Build the Docker container

```bash
docker-compose build
```

2. Spin up the Docker container

```bash
docker-compose up -d
```

3. To remove the Docker container

```bash
docker-compose down
```

# How to Obtain Models
1. We are using LLMs from OpenAI and Gemini
2. Simply prepare API keys from OpenAI and Gemini, and store them inside your .env file
3. The LLMs will be called via API calls using clients from the LangGraph package.

# How to Obtain Data
You just need to prepare a script outline that you want to be written as a script. For mock examples, refer to the `mocks/` folder.
* mock_userinput.json
* mock_userinput_2.json

# How to Run
1. Open a Terminal window inside the Docker environment. To execute the LangGraph, type
```bash
python main.py
```

2. Follow the input instructions to provide the corresponding user info to create the speech script. 