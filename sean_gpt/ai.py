""" AI model functions. """
import chunk
from sqlmodel import Session, select
from openai.types.chat import ChatCompletionToolParam
from openai.types.shared_params import FunctionDefinition
import json
from pymilvus import connections, Collection
import openai

from .config import settings
from .model.ai import AI
from .util.database import get_db_engine

openai_client = openai.OpenAI(api_key = settings.openai_api_key)

def get_ai(name: str) -> AI | None:
    """ Gets an AI from the database.
    
    Args:
        session (Session): The database session.
        name (str): The name of the AI to get.
        
    Returns:
        AI: The AI with the specified name or None.
    """
    db_engine = get_db_engine()
    with Session(db_engine) as session:
        return session.exec(select(AI).where(AI.name == name)).first()

def create_ai(name: str) -> AI:
    """ Creates an AI in the database.
    
    Args:
        session (Session): The database session.
        name (str): The name of the AI to create.
    
    Returns:
        AI: The created AI.
    """
    db_engine = get_db_engine()
    with Session(db_engine) as session:
        ai = AI(name=name)
        session.add(ai)
        session.commit()
        session.refresh(ai)
    return ai

def default_ai() -> AI:
    """ Retrieve the default AI model.
    
    Returns:
        The default AI model.
    """
    return get_ai(settings.app_default_ai_model) or create_ai(settings.app_default_ai_model)

def get_molten_salt_documents(query:str):
    embedding = openai_client.embeddings.create(input=query)
    connections.connect(host=settings.milvus_host, port=settings.milvus_port)
    milvus_collection = Collection(name=settings.milvus_collection_name)
    milvus_collection.load()
    results = milvus_collection.search(
        data=[embedding],
        anns_field='chunk_embedding',
        limit=10, # TODO: Remove this magic number
        param={},
        output_fields=['file_id', 'chunk_txt']
    )
    # Finally, retrieve the files that match the results
    file_ids = [hit.entity.get('file_id') for hit in results[0]]
    chunks = [hit.entity.get('chunk_txt') for hit in results[0]]
    result = ('I, the assistant, chose to use a function to retrieve relevant documents for '
              'research about molten salt nuclear reactors. This tool returned the following:\n')
    for index, (file_id, chunk) in enumerate(zip(file_ids, chunks)):
        result += f'Result {index+1}:\n{chunk}\nDownload link: {settings.api_domain}/file?file_id={file_id}\n\n'
    return result

def run_tool(name: str, arguments: str):
    args = json.loads(arguments)
    if name == "get_molten_salt_documents":
        query = args["prompt"]
        return get_molten_salt_documents(query)

nuclear_tools = [ChatCompletionToolParam(
    type="function",
    function=FunctionDefinition(
        name="get_molten_salt_documents",
        description=(
"Retrieve relevant documents for research about molten salt nuclear reactors. This function will "
"perform a semantic search over a dataset of documents from moltensalt.org, a collection "
"titled 'Fluid Fluorides and Chlorides Reactor Research and Development on Molten Salt Reactors "
"(MSRs) Papers, Books, and Reports'. This function will return a list of chunks of text from the "
"documents, where each chunk is a paragraph or section of a document from the dataset, ordered by "
" their semantic relevance to the function input query, as calculated by L2 distance between the "
"query embedding and the document embedding.  Only use this function for user queries about "
"nuclear power and molten salt reactors."
        ),
        parameters={
        "properties": {
          "prompt": {
            "type": "string",
            "description": (
"The search prompt. The function will calculate the semantic relevance of the documents to this "
"prompt and return the most relevant content. Note that the function is semantically matching "
"against this prompt, so it should be statement to match against, not a question."),
          },
        },
        "required": ["query"],
      }
    )
)]
