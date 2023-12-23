from sqlmodel import Session, select

from .model.ai import AI
from .database import db_engine

DEFAULT_AI_MODEL = "gpt-4-1106-preview"

def get_ai(name: str) -> AI | None:
    """ Gets an AI from the database.
    
    Args:
        session (Session): The database session.
        name (str): The name of the AI to get.
        
    Returns:
        AI: The AI with the specified name or None.
    """
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
    with Session(db_engine) as session:
        ai = AI(name=name)
        session.add(ai)
        session.commit()
        session.refresh(ai)
    return ai

default_ai:AI = get_ai(DEFAULT_AI_MODEL) or create_ai(DEFAULT_AI_MODEL)