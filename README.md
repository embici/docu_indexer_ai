# Documentation Indexer with LangChain and FAISS

This project implements a documentation indexing and retrieval system using LangChain and FAISS. It allows you to:
1. Index documentation from web pages
2. Store the embeddings in a FAISS vector store
3. Retrieve relevant information based on user questions
4. Generate answers using GPT-4

## Setup

1. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install the required packages:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root with your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

## Configuration

The project uses `src/config.yaml` for configuration. You can customize:

### OpenAI Settings
- `model_name`: The OpenAI model to use (default: "gpt-4")
- `temperature`: Temperature for answer generation (default: 0)

### Document Processing
- `chunk_size`: Size of text chunks for indexing (default: 1000)
- `chunk_overlap`: Overlap between chunks (default: 100)

### Vector Store
- `index_path`: Path to store the FAISS index (default: "faiss_index")
- `similarity_search_k`: Number of similar documents to retrieve (default: 4)

### URL Configuration
- Add URLs to index in the `urls` section
- Configure URL pattern restrictions:
  - `accepted`: Patterns for URLs to include
  - `blacklisted`: Patterns for URLs to exclude

### Prompt Template
Customize the prompt template used for generating answers.

## Usage

1. Configure your documentation URLs and settings in `src/config.yaml`

2. Run the indexing and question-answering system:
```bash
python src/doc_indexer.py
```

The script will:
- Load and index the documentation from the specified URLs
- Save the FAISS index locally
- Run an example question to demonstrate the system

## Features

- Efficient document indexing using FAISS
- Semantic search capabilities
- GPT-4 powered answer generation
- Persistent storage of the vector index
- Customizable prompt templates
- URL pattern-based filtering
- Easy-to-use API for question answering
- Recursive document crawling
- Automatic link extraction and filtering

## Requirements

- Python 3.8+
- OpenAI API key
- Internet connection for web scraping
- Required packages:
  - langchain>=0.1.0
  - langchain-community>=0.0.1
  - langchain-openai>=0.0.1
  - faiss-cpu>=1.7.4
  - openai>=1.0.0
  - python-dotenv>=1.0.0
  - beautifulsoup4>=4.12.0
  - requests>=2.31.0
  - pyyaml>=6.0.1
  - tiktoken>=0.9.0
  - urllib3>=2.0.0
  - typing-extensions>=4.8.0
  - pydantic>=2.5.0

## Project Structure

```
.
├── src/
│   ├── doc_indexer.py    # Main indexing and QA implementation
│   └── config.yaml       # Configuration file
├── requirements.txt      # Project dependencies
├── .env                 # Environment variables (create this)
└── README.md           # This file
```

## Example Usage

```python
from src.doc_indexer import DocumentationIndexer

# Initialize the indexer
indexer = DocumentationIndexer()

# Index documents from configured URLs
indexer.index_documents()

# Ask questions about the documentation
answer = indexer.ask_question("What is Adobe Analytics?")
print(answer)
``` 