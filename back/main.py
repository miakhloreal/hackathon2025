from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from google import genai
from google.genai.types import GenerateContentConfig, Retrieval, Tool, VertexRagStore
import vertexai
import os
import json
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="L'Oréal Beauty Advisor API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite's default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini client
PROJECT_ID =  "365841691090"
LOCATION =  "europe-west4"
MODEL_ID =  "gemini-2.0-flash-001"
RAG_CORPUS_NAME = "projects/365841691090/locations/europe-west4/ragCorpora/666532744850833408"

# Retrieval configuration
RETRIEVAL_TOP_K = 10
VECTOR_DISTANCE_THRESHOLD = 0.5


# Initialize Vertex AI
vertexai.init(project=PROJECT_ID, location=LOCATION)

# Initialize GenAI client
client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

# Create RAG retrieval tool
rag_retrieval_tool = Tool(
    retrieval=Retrieval(
        vertex_rag_store=VertexRagStore(
            rag_corpora=[RAG_CORPUS_NAME],
            similarity_top_k=RETRIEVAL_TOP_K,
            vector_distance_threshold=VECTOR_DISTANCE_THRESHOLD,
        )
    )
)

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]

class ProductRecommendation(BaseModel):
    name: str
    price: str = "€XX.XX"  # Default price if not available
    url: str = "#"  # Default URL if not available
    description: str
    advantages: List[str] = []
    suitability: List[str] = []
    questions: List[str] = []

class ChatResponse(BaseModel):
    text: str
    products: Optional[List[ProductRecommendation]] = None

SYSTEM_PROMPT = """IMPORTANT: Use ONLY the information provided by the RAG system in your response. Do not generate or invent any information.

You are a L'Oréal beauty advisor analyzing the RAG search results. For each product query:

1. First identify the exact product name from the RAG results
2. Provide a summary of the reviews found in the RAG results
3. List the key product advantages and benefits
4. Explain why this product would be suitable for the user
5. Ask relevant follow-up questions to personalize recommendations

Format your response using ONLY information from the RAG results:

Product: [Exact product name as found in RAG]

Reviews Summary: [Summary based strictly on RAG review data]

## 🌟 PRODUCT ADVANTAGES
• [First key advantage from RAG data]
• [Second key advantage from RAG data]
• [Third key advantage from RAG data]

## ✨ WHY IT'S RIGHT FOR YOU
• [First reason based on product benefits and user needs]
• [Second reason based on customer experiences]
• [Third reason based on product effectiveness]

## 💫 LET'S PERSONALIZE FURTHER
• Have you tried similar products before? What was your experience?
• What specific concerns would you like this product to address?
• When do you plan to use this product in your routine?

If the RAG system doesn't provide certain information, acknowledge what's missing rather than making assumptions."""

def extract_product_info(text: str) -> tuple[str, str, list[str], list[str], list[str]]:
    """Extract product name, review summary, advantages, suitability reasons, and follow-up questions from RAG response."""
    product_name = ""
    review_summary = ""
    advantages = []
    suitability = []
    questions = []
    
    # Look for product name patterns
    name_match = re.search(r"(?:Product:|Name:|^)([^\.]+?)(?:\.|\n|$)", text, re.MULTILINE | re.IGNORECASE)
    if name_match:
        product_name = name_match.group(1).strip()
    
    # Look for review summary patterns
    review_patterns = [
        r"Reviews? Summary:?\s*([^\.]+(?:\.[^\.]+){0,3}\.)",
        r"Summary:?\s*([^\.]+(?:\.[^\.]+){0,3}\.)",
        r"(?:overall|generally),?\s*([^\.]+(?:\.[^\.]+){0,3}\.)"
    ]
    
    for pattern in review_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            review_summary = match.group(1).strip()
            break
    
    # Extract advantages
    advantages_section = re.search(r"## 🌟 PRODUCT ADVANTAGES\s*((?:•[^\n]+\n?)+)", text)
    if advantages_section:
        advantages = [adv.strip().lstrip('•').strip() for adv in advantages_section.group(1).split('\n') if adv.strip()]
    
    # Extract suitability reasons
    suitability_section = re.search(r"## ✨ WHY IT'S RIGHT FOR YOU\s*((?:•[^\n]+\n?)+)", text)
    if suitability_section:
        suitability = [reason.strip().lstrip('•').strip() for reason in suitability_section.group(1).split('\n') if reason.strip()]

    # Extract follow-up questions
    questions_section = re.search(r"## 💫 LET'S PERSONALIZE FURTHER\s*((?:•[^\n]+\n?)+)", text)
    if questions_section:
        questions = [q.strip().lstrip('•').strip() for q in questions_section.group(1).split('\n') if q.strip()]
    
    return product_name, review_summary, advantages, suitability, questions

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # Get the last user message
        last_message = request.messages[-1].content
        
        # Generate content with RAG
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=last_message,
            config=GenerateContentConfig(
                tools=[rag_retrieval_tool],
                system_instruction=SYSTEM_PROMPT
            )
        )

        if not response.text:
            return ChatResponse(
                text="I apologize, I couldn't generate a response.",
                products=[]
            )

        # Extract product information
        product_name, review_summary, advantages, suitability, questions = extract_product_info(response.text)

        # Create formatted response
        formatted_response = {
            "name": product_name,
            "description": review_summary,
            "advantages": advantages,
            "suitability": suitability,
            "questions": questions
        }

        # Format the text response to include all sections
        text_response = (
            json.dumps(formatted_response, indent=2) + "\n\n" +
            response.text
        )

        return ChatResponse(
            text=text_response,
            products=[ProductRecommendation(
                name=product_name,
                description=review_summary,
                advantages=advantages,
                suitability=suitability,
                questions=questions
            )]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"} 