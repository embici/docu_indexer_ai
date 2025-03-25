import sys
from pathlib import Path
import os
from doc_indexer import DocumentationIndexer

def main():
    # Get the absolute path of the script's directory
    script_dir = Path(__file__).parent.absolute()
    config_path = os.path.join(script_dir, "config.yaml")

    try:
        # Initialize the indexer with the config
        indexer = DocumentationIndexer(config_path=config_path)
        
        # Load the existing index
        indexer.load_index()
        
        # Set up the QA chain
        indexer.setup_qa_chain()
        
        print("✅ Successfully loaded documentation index")
        print("Type your questions about Adobe Analytics (or 'quit' to exit):")
        
        while True:
            # Get user input
            question = input("\nQuestion: ").strip()
            
            # Check for exit command
            if question.lower() in ['quit', 'exit', 'q']:
                break
            
            if not question:
                continue
            
            # Get answer
            result = indexer.ask_question(question)
            
            # Print answer
            print("\nAnswer:", result["answer"])
            
            # Print sources
            if result["sources"]:
                print("\nSources:")
                for source in result["sources"]:
                    print(f"- {source}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 