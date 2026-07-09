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

    def retrieve(self, queries: list, n_results: int = None):
        """Embeds the query/queries and retrieves relevant documents from the collection."""
        try:
            if n_results is None:
                n_results = self.n_results
            embedded_queries = [self.model.encode(q) for q in queries]
            results = self.collection.query(
                query_embeddings=embedded_queries,
                n_results=n_results
            )
            return self._reformat_search_results(results)
        except Exception as e:
            logger.exception("Error during document retrieval with ChromaRetriever")
            raise Exception(f"An error occurred during retrieval: {e}")
        

    def _reformat_search_results(self, results):
        """
        Reformats the raw search results from chromadb default format into a more structured 
        format for easier consumption.
        """
        documents = []
        ids_dedup, n_duplicates = set(), 0
        # Results should have fields 'ids', 'embeddings', 'documents', 'uris', 'included', 'data', 'metadatas', 'distances'
        # Each field has a list with one sub-list per query
        try:
            # we use 'ids' as the source to construct the documents list
            for q_i, ids in enumerate(results['ids']):
                for d_i, doc_id in enumerate(ids):
                    if doc_id not in ids_dedup:
                        ids_dedup.add(doc_id)
                        documents.append({
                            'id': doc_id,
                            'content': results['documents'][q_i][d_i],
                            'distance': results['distances'][q_i][d_i],
                            'chunk_id': results['metadatas'][q_i][d_i]['chunk_id'],
                            'file_name': results['metadatas'][q_i][d_i].get('file_path', results['metadatas'][q_i][d_i]['file_name'] ) #file_name in old versions
                        })
                    else:
                        n_duplicates += 1
        
            return documents
        except Exception as e:
            logger.exception("Error during reformatting of search results (probably wrong response format from Chroma)")
            raise Exception(f"An error occurred while reformatting search results: {e}")

    