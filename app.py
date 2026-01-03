from fastapi import FastAPI
from models import UserInput, ChatResponse
from sessions import get_session
from logic import process_message

app = FastAPI(
    title="Marta do Tibino",
    description="Assistente IA para reservas no Tibino – Foz do Arelho"
)

# --- API Endpoints ---

@app.post("/chat", response_model=ChatResponse)
def chat_with_marta(user_input: UserInput):
    """Main chat endpoint to interact with Marta."""
    session = get_session(user_input.session_id)
    
    response_text = process_message(session, user_input.text)
    
    return ChatResponse(session_id=session.session_id, text=response_text)

@app.get("/")
def read_root():
    return {"message": "Marta is running. Use the /docs endpoint to see the API documentation."}