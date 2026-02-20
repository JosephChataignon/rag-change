import os
import logging
import chromadb
from tqdm import tqdm
from sentence_transformers import SentenceTransformer

from ragchange.config.loader import config
from .data_collection import DataCollector
from .chunking import Chunker

logger = logging.getLogger('ragingestion')

class Ingestor:
    """
    Service for embedding and storing documents into a vector database.
    """

    def __init__(self):
        vector_db_path = config.get('vector_db_path')
        collection_name = config.get('vector_db_collection')
        embedding_model = config.get('embedding_model')
        
        self.client = chromadb.PersistentClient(path=vector_db_path)
        self.collection = self.client.get_or_create_collection(name=collection_name)
        self.data_collector = DataCollector()
        self.chunker = Chunker()
        self.embedding_model = SentenceTransformer(embedding_model, trust_remote_code=True)
        logger.info(f"Initialized Ingestor - DB at {vector_db_path} - collection '{collection_name}' - embedding model '{embedding_model}'")
        
    def ingest(self):
        logger.info("Collecting file paths...")
        self.data_collector.collect_file_paths()
        logger.info(f"Done, {len(self.data_collector.file_paths)} files found.")
        for file_path in tqdm(self.data_collector.file_paths, desc="Ingesting files"):
            error_count = 0
            try:
                relative_path = os.path.relpath(
                    file_path,
                    self.data_collector.data_source_path,
                )
                text = self.data_collector.read_file(file_path)
                chunks = self.chunker.chunk(text)
                for i, chunk_text in enumerate(chunks):
                    chunk_embedding = self.embedding_model.encode(chunk_text)
                    chunk_id = f"{relative_path}_chunk_{i}"
                    self.collection.add(
                        documents=[chunk_text],
                        embeddings=[chunk_embedding],
                        metadatas=[{"file_path": relative_path, "chunk_id": i}],
                        ids=[chunk_id]
                    )
                del chunks
                del text
            except Exception as e:
                logger.error(f"Failed to process file {file_path}: {e}")
                error_count += 1
                continue
        error_percent = (error_count / len(self.data_collector.file_paths))
        message = f"Ingest completed with {error_count} errors out of {len(self.data_collector.file_paths)} files ({error_percent:.2%})"
        if error_percent < 0.05:
            logger.info(message)
        elif error_percent < 0.2:
            logger.warning(message)
        else:
            logger.error(message)
            raise Exception("High error rate during ingestion - check logs for details")
        
        