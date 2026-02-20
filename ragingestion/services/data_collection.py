import os
import pdfplumber

from ragchange.config.loader import config


class DataCollector:
    """
    Service for collecting and reading data files from a directory.
    """
    
    def __init__(self):
        self.data_source_path = config.get('data_source_path')
        self.file_extensions = config.get('index_file_types')
        self.file_paths = []
    
    def collect_file_paths(self):
        """
        Retrieves a list of paths to all files with specified extensions in the given root directory and 
        its subdirectories. 
        """
        file_paths = []
        
        for dirpath, _, filenames in os.walk(self.data_source_path):
            for filename in filenames:
                if any(filename.endswith(f".{ext}") for ext in self.file_extensions):
                    file_paths.append(os.path.join(dirpath, filename))
        
        self.file_paths = file_paths

    
    def read_file(self, file_path):
        if file_path.endswith('.txt'):
            return self.read_text_file(file_path)
        elif file_path.endswith('.pdf'):
            return self.read_pdf_file(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_path}")
    
    
    def read_text_file(self, file_path):
        """
        Reads the content of a text file and returns it as a single string.
        """
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        return content


    def read_pdf_file(self, file_path):
        """
        Reads the content of a PDF file and returns it as a single string.
        """
        text_content = []
        
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                # Extract text from each page
                page_text = page.extract_text()
                if page_text:  # Ensure the page has text
                    text_content.append(page_text)
        
        # Join all pages' text into a single string
        return "\n".join(text_content)