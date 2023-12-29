from sqlmodel import Session, select

from .model.ai import AI
from .database import get_db_engine

DEFAULT_AI_MODEL = "gpt-4-1106-preview"

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
    return get_ai(DEFAULT_AI_MODEL) or create_ai(DEFAULT_AI_MODEL)