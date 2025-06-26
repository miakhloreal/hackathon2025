from sentence_transformers import SentenceTransformer
from typing import List, Union

class DocumentEmbedder:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize the document embedder with a sentence transformer model.
        
        Args:
            model_name (str): Name of the sentence transformer model to use
        """
        self.model = SentenceTransformer(model_name)
    
    def embed_documents(self, texts: Union[str, List[str]]) -> List[float]:
        """Generate embeddings for one or more documents.
        
        Args:
            texts: Single text string or list of text strings to embed
            
        Returns:
            List of embeddings
        """
        if isinstance(texts, str):
            texts = [texts]
        
        embeddings = self.model.encode(texts)
        return embeddings.tolist() 