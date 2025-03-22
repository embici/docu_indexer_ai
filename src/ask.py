import sys
from doc_indexer import DocumentationIndexer

def main():
    if len(sys.argv) < 2:
        print("Please provide a question as a command line argument.")
        print("Usage: python ask.py \"your question here\"")
        sys.exit(1)

    # Initialize the indexer
    indexer = DocumentationIndexer()
    
    try:
        # Load the existing index
        indexer.load_index()
        
        # Get the question from command line arguments
        question = " ".join(sys.argv[1:])  # Join all arguments to support questions with spaces
        
        # Setup QA chain and get answer
        indexer.setup_qa_chain()
        result = indexer.ask_question(question)
        
        # Print results
        print(f"\nQ: {question}")
        print(f"\nA: {result['answer']}")
        print("\nSources:")
        for url in result['sources']:
            print(f"- {url}")
            
    except FileNotFoundError:
        print("Error: No index found. Please run 'python doc_indexer.py' first to create the index.")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 