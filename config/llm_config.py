from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

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

def get_judging_llm_a():
    llm = ChatOpenAI(model="gpt-5.4", temperature=0)
    judging_llm_a = llm.with_structured_output(JudgingOutput)
    return judging_llm_a

def get_judging_llm_b():
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", temperature=0)
    judging_llm_b = llm.with_structured_output(JudgingOutput)
    return judging_llm_b