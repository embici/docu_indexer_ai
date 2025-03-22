import os
import yaml
import fnmatch
from typing import List, Dict, Any
from dotenv import load_dotenv
from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin, urlparse
from langchain.docstore.document import Document

# Load environment variables
load_dotenv()

# Set a user agent to identify our requests
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

class DocumentationIndexer:
    def __init__(self, config_path: str = "src/config.yaml"):
        self.config = self._load_config(config_path)
        self.embeddings = OpenAIEmbeddings()
        self.vectorstore = None
        self.qa_chain = None
        self.url_patterns = self.config.get('url_patterns', {
            'accepted': [],
            'blacklisted': []
        })
        self.processed_urls = set()
        
        # Content extraction settings
        self.content_selectors = {
            'main_content': ['main', 'article', '.content', '#content', '.main-content', 'div[role="main"]'],
            'exclude': [
                'nav', 'header', 'footer', '.navigation', '.sidebar',
                '.breadcrumb', '.pagination', '.social-share', '.related-content',
                'script', 'style', 'noscript', 'iframe', 'form'
            ]
        }

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file"""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def _is_url_allowed(self, url: str) -> bool:
        """
        Check if a URL is allowed based on accepted and blacklisted patterns
        """
        # First check if URL matches any accepted patterns
        matches_accepted = any(fnmatch.fnmatch(url, pattern) for pattern in self.url_patterns['accepted'])
        if not matches_accepted:
            print(f"URL {url} did not match any accepted patterns")
            return False

        # Then check if URL matches any blacklisted patterns
        matches_blacklisted = any(fnmatch.fnmatch(url, pattern) for pattern in self.url_patterns['blacklisted'])
        if matches_blacklisted:
            print(f"URL {url} matched blacklisted pattern")
            return False

        return True

    def _get_links_from_page(self, url: str) -> List[str]:
        """
        Extract all links from a page that match our patterns
        """
        try:
            print(f"Fetching links from: {url}")
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            links = []
            for a in soup.find_all('a', href=True):
                href = a['href']
                full_url = urljoin(url, href)
                
                # Only include URLs from the same domain and matching our patterns
                if (urlparse(full_url).netloc == urlparse(url).netloc and 
                    self._is_url_allowed(full_url) and
                    full_url not in self.processed_urls):
                    links.append(full_url)
            
            print(f"Found {len(links)} valid links on {url}")
            return links
        except Exception as e:
            print(f"Error extracting links from {url}: {e}")
            return []

    def _extract_content(self, soup: BeautifulSoup) -> str:
        """
        Extract the main content from the page using BeautifulSoup
        """
        # First try to find the main content area
        main_content = None
        for selector in self.content_selectors['main_content']:
            main_content = soup.select_one(selector)
            if main_content:
                print(f"Found main content with selector: {selector}")
                break

        # If no main content area found, use the body
        if not main_content:
            print("No main content area found, using body")
            main_content = soup.body

        if not main_content:
            print("No content found at all")
            return ""

        # Remove excluded elements
        for selector in self.content_selectors['exclude']:
            for element in main_content.select(selector):
                element.decompose()

        # Extract text while preserving some structure
        content = []
        
        # Process headings
        for heading in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            level = int(heading.name[1])
            content.append(f"{'#' * level} {heading.get_text().strip()}\n")

        # Process paragraphs and lists
        for element in main_content.find_all(['p', 'li']):
            text = element.get_text().strip()
            if text:
                if element.name == 'li':
                    content.append(f"- {text}\n")
                else:
                    content.append(f"{text}\n\n")

        # Process code blocks
        for code in main_content.find_all(['pre', 'code']):
            if code.name == 'pre':
                content.append(f"```\n{code.get_text().strip()}\n```\n\n")

        extracted_content = "".join(content).strip()
        print(f"Extracted {len(extracted_content)} characters of content")
        return extracted_content

    def _process_page(self, url: str, all_documents: List) -> None:
        """
        Process a single page and its linked pages recursively
        """
        if url in self.processed_urls:
            return

        print(f"\nProcessing page: {url}")
        self.processed_urls.add(url)

        try:
            # Fetch and parse the page
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract content using our custom extractor
            content = self._extract_content(soup)
            
            if content:
                # Create a Document object with metadata
                metadata = {
                    "source": url,
                    "title": soup.title.string if soup.title else url
                }
                document = Document(
                    page_content=content,
                    metadata=metadata
                )
                all_documents.append(document)
                print(f"Successfully extracted content from: {url}")
            else:
                print(f"No content extracted from: {url}")

            # Get links from the current page and process them
            links = self._get_links_from_page(url)
            for link in links:
                self._process_page(link, all_documents)

        except Exception as e:
            print(f"Error processing {url}: {e}")

    def index_documents(self, urls: List[str] = None):
        """
        Index documents from the provided URLs or from config
        """
        # Use URLs from config if none provided
        urls = urls or self.config['urls']
        all_documents = []

        print(f"\nStarting indexing with URLs: {urls}")
        print(f"URL patterns: {self.url_patterns}")

        # Process each starting URL and its linked pages
        for url in urls:
            if self._is_url_allowed(url):
                self._process_page(url, all_documents)

        if not all_documents:
            raise ValueError("No documents were loaded from any of the provided URLs")

        # Split documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config['document']['chunk_size'],
            chunk_overlap=self.config['document']['chunk_overlap']
        )
        docs = text_splitter.split_documents(all_documents)

        # Create and store embeddings
        self.vectorstore = FAISS.from_documents(docs, self.embeddings)
        
        # Save the index locally
        self.vectorstore.save_local(self.config['vector_store']['index_path'])
        print(f"\nIndexed {len(docs)} document chunks from {len(all_documents)} pages")

    def load_index(self):
        """
        Load an existing index from disk
        """
        index_path = self.config['vector_store']['index_path']
        if os.path.exists(index_path):
            self.vectorstore = FAISS.load_local(index_path, self.embeddings, allow_dangerous_deserialization=True)
            print("Loaded existing index")
        else:
            raise FileNotFoundError(f"No existing index found at {index_path}. Please index documents first.")

    def setup_qa_chain(self):
        """
        Set up the question-answering chain with GPT-4
        """
        if not self.vectorstore:
            raise ValueError("No vector store available. Please index documents or load an existing index first.")

        # Initialize the language model
        llm = ChatOpenAI(
            model_name=self.config['openai']['model_name'],
            temperature=self.config['openai']['temperature']
        )

        # Create a custom prompt template
        PROMPT = PromptTemplate(
            template=self.config['prompt_template'],
            input_variables=["context", "question"]
        )

        # Create the chain
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(
                search_kwargs={"k": self.config['vector_store']['similarity_search_k']}
            ),
            chain_type_kwargs={"prompt": PROMPT}
        )

    def ask_question(self, question: str) -> str:
        """
        Ask a question and get an answer based on the indexed documentation
        """
        if not self.qa_chain:
            self.setup_qa_chain()
        
        return self.qa_chain.invoke({"query": question})["result"]

def main():
    # Example usage
    indexer = DocumentationIndexer()
    
    # Force rebuilding the index
    print("Building new index...")
    indexer.index_documents()
    
    # Set up QA chain
    indexer.setup_qa_chain()
    
    # Test with a question
    question = "What is Adobe Analytics?"
    print(f"\nQuestion: {question}")
    answer = indexer.ask_question(question)
    print(f"Answer: {answer}")

if __name__ == "__main__":
    main() 