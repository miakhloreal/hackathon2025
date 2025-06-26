from src.rag.embeddings.embedding_model import DocumentEmbedder

def test_document_embedder_initialization():
    embedder = DocumentEmbedder()
    assert embedder is not None
    assert embedder.model is not None

def test_embed_single_document():
    embedder = DocumentEmbedder()
    text = "This is a test document"
    embeddings = embedder.embed_documents(text)
    assert isinstance(embeddings, list)
    assert len(embeddings) == 1
    assert isinstance(embeddings[0], list)

def test_embed_multiple_documents():
    embedder = DocumentEmbedder()
    texts = ["First document", "Second document", "Third document"]
    embeddings = embedder.embed_documents(texts)
    assert isinstance(embeddings, list)
    assert len(embeddings) == 3
    assert all(isinstance(emb, list) for emb in embeddings) 