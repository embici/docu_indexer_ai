from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import traceback
from doc_indexer import DocumentationIndexer
import sys
from pathlib import Path
import os

# Add the src directory to the Python path to allow imports
sys.path.append(str(Path(__file__).parent))

# Get the absolute path of the script's directory
script_dir = Path(__file__).parent.absolute()
config_path = os.path.join(script_dir, "config.yaml")

app = FastAPI(
    title="Adobe Analytics Documentation API",
    description="API for querying Adobe Analytics documentation using AI",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Default Vite port
        "http://localhost:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the documentation indexer
indexer = None

def initialize_indexer():
    """Initialize the indexer and load the index"""
    global indexer
    if indexer is None:
        try:
            indexer = DocumentationIndexer(config_path=config_path)
            indexer.load_index()  # Try to load existing index
            indexer.setup_qa_chain()  # Set up the QA chain
            print("✅ Successfully loaded documentation index")
        except FileNotFoundError:
            print("❌ No existing index found. Please run 'python doc_indexer.py' first.")
            indexer = None  # Reset the indexer
            raise HTTPException(
                status_code=503,
                detail="Documentation index not found. Please create the index first."
            )
        except Exception as e:
            print(f"❌ Error initializing documentation indexer: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            indexer = None  # Reset the indexer
            raise HTTPException(
                status_code=503,
                detail="Error initializing documentation indexer."
            )
    return indexer

class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    sources: Optional[List[str]] = None

class QuestionRequest(BaseModel):
    question: str
    conversation_history: Optional[List[Message]] = []

class QuestionResponse(BaseModel):
    answer: str
    sources: List[str]
    conversation_history: List[Message]

@app.on_event("startup")
async def startup_event():
    """Initialize the indexer when the API starts"""
    try:
        initialize_indexer()
    except Exception as e:
        print(f"❌ Error during startup: {e}")
        # Don't raise an exception here, let the API start anyway
        # The error will be handled when endpoints are called

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "status": "ok",
        "message": "Adobe Analytics Documentation API is running",
        "endpoints": {
            "ask": "/ask (POST) - Ask a question about Adobe Analytics",
            "health": "/health (GET) - Check API and indexer status"
        }
    }

@app.get("/health")
async def health_check():
    """Check if the API and index are working properly"""
    global indexer
    return {
        "status": "healthy",
        "index_loaded": indexer is not None and hasattr(indexer, 'vectorstore'),
        "qa_chain_ready": indexer is not None and hasattr(indexer, 'qa_chain')
    }

@app.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """
    Ask a question about the Adobe Analytics documentation
    """
    try:
        # Ensure indexer is initialized
        indexer = initialize_indexer()
        
        # Format conversation history for context
        conversation_context = ""
        if request.conversation_history:
            for msg in request.conversation_history:
                conversation_context += f"{msg.role}: {msg.content}\n"
        
        # Combine conversation history with current question
        full_question = f"{conversation_context}User: {request.question}"
        
        # Get answer using the indexer
        result = indexer.ask_question(full_question)
        
        # Create response with updated conversation history
        response = QuestionResponse(
            answer=result["answer"],
            sources=result["sources"],
            conversation_history=request.conversation_history + [
                Message(role="user", content=request.question),
                Message(role="assistant", content=result["answer"], sources=result["sources"])
            ]
        )
        
        return response
    except HTTPException:
        raise  # Re-raise HTTP exceptions as they are already formatted
    except Exception as e:
        error_detail = f"Error processing question: {str(e)}\nTraceback: {traceback.format_exc()}"
        print(error_detail)  # Log the error on the server side
        raise HTTPException(
            status_code=500,
            detail=error_detail
        )

def main():
    """Run the API server"""
    uvicorn.run(app, host="0.0.0.0", port=8001)

if __name__ == "__main__":
    main() 