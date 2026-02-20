import logging
import nltk

from ragchange.config.loader import config

logger = logging.getLogger('ragingestion')

# Download necessary NLTK resources if not present
nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)


class Chunker:
    """
    A service class for chunking text into smaller overlapping segments.
    """

    def __init__(self):
        self.chunking_strategy = config.get('chunking_strategy')
        logger.info(f"Initialized Chunker with strategy: {self.chunking_strategy}")
    
    def chunk(self, text):
        if self.chunking_strategy['type'] == 'sentences':
            chunk_size = self.chunking_strategy['chunk_size']
            overlap_size = self.chunking_strategy['overlap_size']

            sentences = self._split_text_into_sentences(text)
            chunks = self._chunk_sentences(sentences, chunk_size, overlap_size)
            return chunks
        else:
            raise ValueError(f"Unsupported chunking strategy: {self.chunking_strategy}")
        
        
    def _split_text_into_sentences(self, text):
        """
        Splits the given text into a list of sentences using NLTK's sentence tokenizer.
        """
        sentences = nltk.sent_tokenize(text)
        return sentences


    def _chunk_sentences(self, sentences, chunk_size, overlap_size):
        """
        Groups a list of sentences into overlapping chunks.
        Returns a list of text chunks
        """
        if overlap_size > chunk_size/2:
            raise ValueError(f"overlap_size {overlap_size} must be smaller than halfchunk_size {chunk_size}.")

        chunks = []
        # The step of the range is the distance between the start of consecutive chunks.
        step = chunk_size - overlap_size
        for i in range(0, len(sentences)-overlap_size, step):
            chunk_end = min(i + chunk_size, len(sentences))
            chunk = " ".join(sentences[i:chunk_end])
            chunks.append(chunk)
        return chunks

