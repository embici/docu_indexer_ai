# Documentation Indexer AI

A powerful AI-powered documentation search and Q&A system that indexes Adobe Analytics documentation and provides intelligent answers to questions.

## Features

- 🔍 Intelligent document indexing with configurable depth and patterns
- 🤖 AI-powered question answering using GPT-4
- 💬 Conversation history support for context-aware responses
- 📝 Markdown rendering for better readability
- 🔗 Source linking for verification
- 🌐 Web-based interface with modern UI
- ⚡ FastAPI backend for high performance

## Prerequisites

- Python 3.8+
- Node.js 16+
- OpenAI API key
- Git

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/docu_indexer_ai.git
cd docu_indexer_ai
```

2. Set up Python environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Set up frontend:
```bash
cd frontend
npm install
```

4. Configure environment variables:
Create a `.env` file in the root directory with:
```
OPENAI_API_KEY=your_api_key_here
```

## Usage

1. Index the documentation:
```bash
python src/doc_indexer.py
```

2. Start the API server:
```bash
python src/api.py
```

3. Start the frontend development server:
```bash
cd frontend
npm run dev
```

4. Open your browser and navigate to `http://localhost:5173`

## Configuration

The system can be configured through `src/config.yaml`:

```yaml
urls:
  - "https://experienceleague.adobe.com/docs/analytics.html"

url_patterns:
  accepted:
    - "https://experienceleague.adobe.com/docs/analytics/*"
  blacklisted:
    - "https://experienceleague.adobe.com/docs/analytics/*/deprecated/*"

document:
  chunk_size: 1000
  chunk_overlap: 200
  max_depth: 3

vector_store:
  index_path: "data/faiss_index"
  similarity_search_k: 3

openai:
  model_name: "gpt-4-turbo-preview"
  temperature: 0.7

prompt_template: |
  You are a helpful AI assistant that answers questions about Adobe Analytics.
  Use the following pieces of context to answer the question at the end.
  If you don't know the answer, just say that you don't know, don't try to make up an answer.
  If the question is not about Adobe Analytics, politely inform the user that this system is specifically for Adobe Analytics questions.

  Context:
  {context}

  Question: {question}

  Answer:
```

## API Endpoints

- `POST /ask`: Ask a question about Adobe Analytics
  ```json
  {
    "question": "What is Adobe Analytics?",
    "conversation_history": [
      {
        "role": "user",
        "content": "Previous question"
      },
      {
        "role": "assistant",
        "content": "Previous answer",
        "sources": ["source1", "source2"]
      }
    ]
  }
  ```

- `GET /health`: Check API and indexer status
- `GET /`: Root endpoint with API information

## Development

### Code Style

The project uses:
- Black for Python code formatting
- isort for import sorting
- flake8 for linting
- ESLint and Prettier for frontend code

### Running Tests

```bash
pytest
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 