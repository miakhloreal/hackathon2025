#!/usr/bin/env python3
"""
Simple RAG proof of concept script using existing Vertex AI corpus.
Demonstrates connecting to a RAG corpus and getting responses from Gemini.
"""

from google import genai
import vertexai
from google.genai.types import GenerateContentConfig, Retrieval, Tool, VertexRagStore

# Configuration
PROJECT_ID = "365841691090"  # Extracted from corpus path
LOCATION = "europe-west4"
MODEL_ID = "gemini-2.0-flash-001"

# Existing RAG corpus (no need to create or load)
RAG_CORPUS_NAME = "projects/365841691090/locations/europe-west4/ragCorpora/666532744850833408"

# Retrieval configuration
RETRIEVAL_TOP_K = 10
VECTOR_DISTANCE_THRESHOLD = 0.5

# Question to ask (easily changeable)
QUESTION = "can you summarize the reviews in one parragraph for Vitamin C Clarifying Wash? "

def main():
    print("Initializing Vertex AI...")
    # Initialize Vertex AI
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    
    # Initialize GenAI client
    client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
    
    print(f"Creating RAG retrieval tool for corpus: {RAG_CORPUS_NAME}")
    # Create RAG retrieval tool using existing corpus
    rag_retrieval_tool = Tool(
        retrieval=Retrieval(
            vertex_rag_store=VertexRagStore(
                rag_corpora=[RAG_CORPUS_NAME],
                similarity_top_k=RETRIEVAL_TOP_K,
                vector_distance_threshold=VECTOR_DISTANCE_THRESHOLD,
            )
        )
    )
    
    print(f"\nAsking: {QUESTION}")
    print("-" * 50)
    
    # Generate content with RAG
    response = client.models.generate_content(
        model=MODEL_ID,
        contents=QUESTION,
        config=GenerateContentConfig(tools=[rag_retrieval_tool]),
    )
    
    # Print the response
    print("\nResponse:")
    print("-" * 50)
    print(response.text)
    print("-" * 50)

if __name__ == "__main__":
    main()