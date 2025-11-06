# python_backend/models/chat_models.py
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

# Define the roles in the chat
class ChatRole(str, Enum):
    user = "user"
    assistant = "assistant"
    system = "system"

# Represents a single message in the chat history
class Message(BaseModel):
    role: ChatRole = Field(..., description="Role of the message sender (user, assistant, or system).")
    content: str = Field(..., description="The content of the message.")

# Represents the request body for sending a new message to the chatbot
class ChatRequest(BaseModel):
    message: str = Field(..., description="The new message sent by the user.")
    # Chat history can be used to provide context for the current message
    chat_history: Optional[List[Message]] = Field(default_factory=list, description="Optional previous messages for context.")

# Represents a single quick action suggestion from the chatbot
class QuickAction(BaseModel):
    text: str = Field(..., description="The text of the quick action button.")
    payload: Optional[str] = Field(None, description="Optional payload associated with the quick action (e.g., a specific query).")

# Represents the response from the chatbot
class ChatResponse(BaseModel):
    response: str = Field(..., description="The chatbot's text response.")
    references: Optional[List[str]] = []  # 👈 NUEVO CAMPO
    is_typing: bool = Field(False, description="True if the assistant is still processing/typing, False otherwise.")
    quick_actions: Optional[List[QuickAction]] = Field(default_factory=list, description="Optional list of quick action suggestions.")
    #follow_up_questions: Optional[List[str]] = Field(default_factory=list, description="Preguntas adicionales sugeridas relacionadas con la respuesta.")
    error: Optional[str] = Field(None, description="Optional error message if something went wrong.")
