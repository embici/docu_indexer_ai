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
from playwright.sync_api import sync_playwright
import requests
from urllib.parse import urljoin, urlparse
from langchain.docstore.document import Document
import time
from pathlib import Path

# Load environment variables
load_dotenv()

# Set a user agent to identify our requests
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

class DocumentationIndexer:
    def __init__(self, config_path: str = "src/config.yaml"):
        # Get the absolute path of the script's directory
        script_dir = Path(__file__).parent.absolute()
        
        # If config_path is relative, make it absolute relative to script directory
        if not os.path.isabs(config_path):
            config_path = os.path.join(script_dir, config_path)
        
        print(f"Loading config from: {config_path}")
        self.config = self._load_config(config_path)
        self.embeddings = OpenAIEmbeddings()
        self.vectorstore = None
        self.qa_chain = None
        self.url_patterns = self.config.get('url_patterns', {
            'accepted': [],
            'blacklisted': []
        })
        self.processed_urls = set()
        self.max_depth = self.config.get('document', {}).get('max_depth', 5)  # Get max_depth from config, default to 5
        print(f"Initialized with max_depth: {self.max_depth} from config file: {config_path}")
        
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
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"❌ Config file not found at: {config_path}")
            raise
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            raise

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

    def _get_links_from_page(self, page) -> List[str]:
        """
        Extract all links from a page that match our patterns
        """
        try:
            # Get all links from the page using JavaScript evaluation
            links = page.evaluate('''() => {
                const links = Array.from(document.querySelectorAll('a[href]'));
                return links.map(link => link.href);
            }''')
            
            # Filter links based on our patterns
            valid_links = []
            for link in links:
                if (self._is_url_allowed(link) and
                    link not in self.processed_urls):
                    valid_links.append(link)
            
            print(f"Found {len(valid_links)} valid links")
            return valid_links
        except Exception as e:
            print(f"Error extracting links: {e}")
            return []

    def _extract_content(self, page) -> str:
        """
        Extract the main content from the page using Playwright
        """
        try:
            # Wait for the main content to be available
            main_content = None
            for selector in self.content_selectors['main_content']:
                try:
                    main_content = page.wait_for_selector(selector, timeout=5000)
                    if main_content:
                        print(f"Found main content with selector: {selector}")
                        break
                except Exception as e:
                    print(f"Failed to find content with selector {selector}: {e}")
                    continue

            # If no main content area found, use the body
            if not main_content:
                print("No main content area found, using body")
                main_content = page.locator('body')

            if not main_content:
                print("No content found at all")
                return ""

            # Remove excluded elements
            for selector in self.content_selectors['exclude']:
                try:
                    page.evaluate(f'''(selector) => {{
                        const elements = document.querySelectorAll(selector);
                        elements.forEach(el => el.remove());
                    }}''', selector)
                except Exception as e:
                    print(f"Failed to remove excluded elements with selector {selector}: {e}")
                    continue

            # Get the element's selector and HTML
            element_info = main_content.evaluate('''(el) => {
                const tag = el.tagName.toLowerCase();
                const id = el.id ? '#' + el.id : '';
                const classes = el.className ? '.' + el.className.split(' ').join('.') : '';
                return {
                    selector: tag + id + classes,
                    html: el.outerHTML
                };
            }''')

            # Extract text while preserving structure using JavaScript evaluation
            content = page.evaluate('''(elementInfo) => {
                const mainContent = document.querySelector(elementInfo.selector);
                if (!mainContent) return '';
                
                const content = [];
                
                // Process headings
                const headings = mainContent.querySelectorAll('h1, h2, h3, h4, h5, h6');
                headings.forEach(heading => {
                    const level = parseInt(heading.tagName[1]);
                    const text = heading.innerText.trim();
                    if (text) {
                        content.push(`${'#'.repeat(level)} ${text}\\n`);
                    }
                });

                // Process paragraphs and lists
                const elements = mainContent.querySelectorAll('p, li');
                elements.forEach(element => {
                    const text = element.innerText.trim();
                    if (text) {
                        if (element.tagName === 'LI') {
                            content.push(`- ${text}\\n`);
                        } else {
                            content.push(`${text}\\n\\n`);
                        }
                    }
                });

                // Process code blocks
                const codeBlocks = mainContent.querySelectorAll('pre, code');
                codeBlocks.forEach(code => {
                    if (code.tagName === 'PRE') {
                        const text = code.innerText.trim();
                        if (text) {
                            content.push(`\\`\\`\\`\\n${text}\\n\\`\\`\\`\\n\\n`);
                        }
                    }
                });

                return content.join('');
            }''', element_info)

            extracted_content = content.strip()
            print(f"Extracted {len(extracted_content)} characters of content")
            return extracted_content
        except Exception as e:
            print(f"Error extracting content: {e}")
            return ""

    def _process_page(self, url: str, all_documents: List, page, depth: int = 0) -> None:
        """
        Process a single page and its linked pages recursively
        """
        if url in self.processed_urls or depth >= self.max_depth:
            return

        print(f"\nProcessing page: {url} (depth: {depth})")
        self.processed_urls.add(url)

        try:
            # Navigate to the page
            page.goto(url, wait_until='domcontentloaded', timeout=60000)
            
            # Wait for the main content to be available
            try:
                page.wait_for_load_state('networkidle', timeout=30000)
            except Exception as e:
                print(f"Warning: Page did not reach networkidle state: {e}")
                # Continue anyway as we'll handle missing content gracefully
            
            # Extract content using our custom extractor
            content = self._extract_content(page)
            
            if content:
                # Create a Document object with metadata
                metadata = {
                    "source": url,
                    "title": page.title() or url
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
            links = self._get_links_from_page(page)
            for link in links:
                if link not in self.processed_urls:
                    self._process_page(link, all_documents, page, depth + 1)

            # Add a small delay to be nice to the server
            time.sleep(1)

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
        print(f"Maximum recursion depth: {self.max_depth}")

        # Initialize Playwright
        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            try:
                # Process each starting URL and its linked pages
                for url in urls:
                    if self._is_url_allowed(url):
                        self._process_page(url, all_documents, page, depth=0)
            finally:
                browser.close()

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

    def ask_question(self, question: str) -> dict:
        """
        Ask a question and get an answer based on the indexed documentation
        Returns a dictionary containing the answer and source URLs
        """
        if not self.qa_chain:
            self.setup_qa_chain()
        
        # Get the answer and source documents
        result = self.qa_chain.invoke({"query": question})
        answer = result["result"]
        
        # Get source documents from the retriever
        docs = self.vectorstore.similarity_search(question, k=3)
        source_urls = [doc.metadata.get("source", "Unknown source") for doc in docs]
        
        return {
            "answer": answer,
            "sources": source_urls
        }

def main():
    # Initialize the indexer
    indexer = DocumentationIndexer()
    
    print("Indexing documents...")
    indexer.index_documents()
    print("Indexing completed!")

if __name__ == "__main__":
    main() 