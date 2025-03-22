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

## Usage

1. Modify the URLs in `src/doc_indexer.py` to include your documentation pages.

2. Run the indexing and question-answering system:
```bash
python src/doc_indexer.py
```

The script will:
- Load and index the documentation from the specified URLs
- Save the FAISS index locally
- Run an example question to demonstrate the system

## Customization

You can customize the following parameters in `src/doc_indexer.py`:
- `chunk_size`: Size of text chunks for indexing (default: 1000)
- `chunk_overlap`: Overlap between chunks (default: 100)
- `temperature`: GPT-4 temperature for answer generation (default: 0)

## Features

- Efficient document indexing using FAISS
- Semantic search capabilities
- GPT-4 powered answer generation
- Persistent storage of the vector index
- Customizable prompt templates
- Easy-to-use API for question answering

## Requirements

- Python 3.8+
- OpenAI API key
- Internet connection for web scraping 