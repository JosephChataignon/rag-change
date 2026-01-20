import os
from django.test import TestCase, SimpleTestCase

from ragingestion.services.chunking import Chunker

class Chunking_Test(SimpleTestCase):
    
    def test_sentence_chunking(self):

        chunker = Chunker()
        text = ("This is the first sentence. This is the second sentence. "
                "This is the third sentence. This is the fourth sentence. "
                "This is the fifth sentence.")
        
        chunk_size = 4
        overlap_size = 2
        
        expected_chunks = [
            "This is the first sentence. This is the second sentence. "
            "This is the third sentence. This is the fourth sentence.",
            "This is the third sentence. This is the fourth sentence. "
            "This is the fifth sentence."
        ]
        
        chunks = chunker._chunk_sentences(
            chunker._split_text_into_sentences(text),
            chunk_size,
            overlap_size
        )
        
        self.assertEqual(chunks, expected_chunks)
    
    def test_sentence_chunking_invalid_overlap(self):
        '''overlap shouldn't be bigger than half chunk size'''
        chunk_size = 3
        overlap_size = 2
        chunker = Chunker()
        text = "This is a test sentence. " * 10  # Dummy text
        
        with self.assertRaises(ValueError):  
            chunker._chunk_sentences(
                chunker._split_text_into_sentences(text),
                chunk_size,
                overlap_size
            )
        


