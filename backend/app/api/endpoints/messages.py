import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Message
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

class MessageCreate(BaseModel):
    content: str

class MessageResponse(BaseModel):
    id: int
    content: str

    class Config:
        from_attributes = True

@router.post("/messages/", response_model=MessageResponse, status_code=201)
def create_message(
    message: MessageCreate,
    db: Session = Depends(get_db)
):
    logger.info(f"Creating new message with content: {message.content}")
    try:
        db_message = Message(content=message.content)
        db.add(db_message)
        logger.info("Message added to session")
        
        db.commit()
        logger.info("Transaction committed successfully")
        
        db.refresh(db_message)
        logger.info(f"Message created with ID: {db_message.id}")
        
        return db_message
    except Exception as e:
        logger.error(f"Error creating message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))