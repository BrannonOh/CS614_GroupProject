from langchain_openai import ChatOpenAI

from schemas.ted_blueprint import TEDBlueprint
from schemas.structure_checking import StructureCheckOutput
from schemas.judging_output import JudgingOutput

def get_ted_llm():
    llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0)
    ted_llm = llm.with_structured_output(TEDBlueprint)
    return ted_llm

def get_structure_llm():
    llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0)
    structure_llm = llm.with_structured_output(StructureCheckOutput)
    return structure_llm

def get_ted_revision_llm():
    llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0)
    ted_revision_llm = llm.with_structured_output(TEDBlueprint)
    return ted_revision_llm

def get_judging_llm():
    llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0)
    judging_llm = llm.with_structured_output(JudgingOutput)
    return judging_llm