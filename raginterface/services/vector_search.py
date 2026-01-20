import chromadb, logging
from sentence_transformers import SentenceTransformer

from ragchange.config.loader import config
logger = logging.getLogger('raginterface')

class ChromaRetriever:
    """
    A class for retrieving documents from a ChromaDB collection based on semantic similarity using embeddings.
    """
    def __init__(self):
        embedding_model = config.get('embedding_model')
        vector_db_path = config.get('vector_db_path')
        vector_db_collection = config.get('vector_db_collection')
        self.n_results = config.get('n_results')
        
        self.model = SentenceTransformer(embedding_model, trust_remote_code=True)
        self.client = chromadb.PersistentClient(path=vector_db_path)
        self.collection = self.client.get_collection(name=vector_db_collection)

    def retrieve(self, query: str, n_results: int = None): 
        """Embeds the query and retrieves relevant documents from the collection."""
        try:
            if n_results is None:
                n_results = self.n_results
            embedded_query = self.model.encode(query)
            results = self.collection.query(
                query_embeddings=[embedded_query],
                n_results=n_results
            )
            #return results
            return {
                'documents': self._reformat_search_results(results),
                'formatted_data': self._format_results_for_prompt(results),
                'raw_results': results
            }
        except Exception as e:
            logger.exception("Error during document retrieval with ChomaRetriever")
            raise Exception(f"An error occurred during retrieval: {e}")
        

    def _format_results_for_prompt(self, results):
        """
        Formats the retrieval results from a dict into a string, including some metadata.

        Args:
            results: The dictionary returned by the retrieve method.

        Returns:
            A formatted string containing the retrieved data.
        """
        if not results:
            return "No relevant data found."

        formatted_data = ""
        for idx, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
            chunk_id = metadata.get('chunk_id', 'N/A')
            file_name = metadata.get('file_name', 'N/A')
            formatted_data += f"Document {idx + 1}:\n"
            formatted_data += f"Document ID: {chunk_id}\n"
            formatted_data += f"File Name: {file_name}\n"
            formatted_data += f"Content:\n{doc}\n"
            formatted_data += "-" * 80 + "\n"

        return formatted_data

    def _reformat_search_results(self, search_results):
        """
        Reformats the raw search results from chromadb default format into a more structured 
        format for easier consumption.
        """
        documents = []
        if search_results and 'metadatas' in search_results and search_results['metadatas']:
            # Access the first (and only) list in the nested structure
            metadatas = search_results['metadatas'][0]
            docs = search_results['documents'][0] if search_results['documents'] else []
            distances = search_results['distances'][0] if search_results['distances'] else []
            
            for i, metadata in enumerate(metadatas):
                documents.append({
                    'file_name': metadata.get('file_name', 'Unknown'),
                    'chunk_id': metadata.get('chunk_id', f'chunk_{i}'),
                    'content': docs[i] if i < len(docs) else '',
                    'distance': distances[i] if i < len(distances) else 0
                })
    
        return documents
    


    