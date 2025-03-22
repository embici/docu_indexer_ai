# Adobe Analytics Documentation Indexer

An AI-powered documentation search and query system for Adobe Analytics documentation. This project uses LangChain, OpenAI, and FAISS to create a vector database of Adobe Analytics documentation and provides a FastAPI interface for querying the documentation.

## Features

- Automated documentation crawling and indexing
- Vector-based semantic search using FAISS
- OpenAI-powered question answering
- RESTful API interface
- Source URL tracking for answers
- Configurable URL patterns and content extraction

## Prerequisites

- Python 3.8 or higher
- OpenAI API key
- Virtual environment (recommended)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd docu_indexer_ai
```

2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root with your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

## Configuration

The project uses a YAML configuration file (`src/config.yaml`) for various settings:

- URLs to index
- URL patterns for crawling
- Document chunking settings
- Vector store settings
- OpenAI model settings

## Usage

### Running the API Server

1. Start the API server:
```bash
python3 src/api.py
```

The server will start on http://localhost:8001

### API Endpoints

#### GET /
Health check endpoint that returns API status and available endpoints.

#### POST /ask
Query the documentation with a question.

Request body:
```json
{
    "question": "What are the main features of Adobe Analytics Activity Map?"
}
```

Response:
```json
{
    "answer": "The answer to your question...",
    "sources": [
        "https://experienceleague.adobe.com/docs/analytics/analyze/activity-map/activity-map",
        "https://experienceleague.adobe.com/docs/analytics/components/dimensions/activity-map-link"
    ]
}
```

### Interactive Documentation

Access the Swagger UI documentation at:
- http://localhost:8001/docs

### Example Usage with curl

```bash
curl -X POST "http://localhost:8001/ask" \
     -H "Content-Type: application/json" \
     -d '{"question": "What are the main features of Adobe Analytics Activity Map?"}'
```

### n8n Integration

To use this API in n8n:

1. Add an HTTP Request node
2. Configure the following:
   - Method: POST
   - URL: http://localhost:8001/ask
   - Headers: Content-Type: application/json
   - Body: JSON with your question

## Project Structure

```
docu_indexer_ai/
├── src/
│   ├── api.py              # FastAPI application
│   ├── doc_indexer.py      # Main documentation indexing logic
│   └── config.yaml         # Configuration file
├── faiss_index/           # Vector store directory
├── .env                   # Environment variables
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Dependencies

- langchain: Core framework for building applications with LLMs
- langchain-community: Community-maintained LangChain components
- langchain-openai: OpenAI integration for LangChain
- faiss-cpu: Vector similarity search library
- openai: OpenAI API client
- python-dotenv: Environment variable management
- beautifulsoup4: HTML parsing
- requests: HTTP client
- pyyaml: YAML configuration handling
- tiktoken: Token counting for OpenAI models
- fastapi: Web framework for building APIs
- uvicorn: ASGI server implementation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 