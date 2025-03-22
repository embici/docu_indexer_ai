from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from doc_indexer import DocumentationIndexer
import uvicorn

app = FastAPI(
    title="Adobe Analytics Documentation API",
    description="API for querying Adobe Analytics documentation using AI",
    version="1.0.0"
)

# Initialize the documentation indexer
try:
    indexer = DocumentationIndexer()
    indexer.load_index()
    indexer.setup_qa_chain()
except Exception as e:
    print(f"Error initializing indexer: {e}")
    indexer = None

class QuestionRequest(BaseModel):
    question: str

class QuestionResponse(BaseModel):
    answer: str
    sources: list[str]

@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "Adobe Analytics Documentation API is running",
        "endpoints": {
            "ask": "/ask - POST endpoint to ask questions about Adobe Analytics"
        }
    }

@app.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    if not indexer:
        raise HTTPException(
            status_code=503,
            detail="Documentation indexer is not initialized. Please try again later."
        )
    
    try:
        result = indexer.ask_question(request.question)
        return QuestionResponse(
            answer=result["answer"],
            sources=result["sources"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing question: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001) 