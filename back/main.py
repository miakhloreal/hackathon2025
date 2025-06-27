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
RAG_CORPUS_NAME = "projects/365841691090/locations/europe-west4/ragCorpora/1179943102371069952"

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
    ingredients: List[str] = []
    advantages: List[str] = []
    suitability: List[str] = []
    questions: List[str] = []

class ChatResponse(BaseModel):
    text: str
    products: Optional[List[ProductRecommendation]] = None

SYSTEM_PROMPT = """IMPORTANT: Use ONLY the information provided by the RAG system in your response. Do not generate or invent any information.

You are a L'Oréal beauty advisor analyzing the RAG search results. 

If the user is asking for a product recommendation:
1. Choose ONLY ONE product that best matches their needs
2. Do not mention or compare multiple products
3. Focus on providing detailed information about the single chosen product

Structure your response for product recommendations as follows:

Product: [Single product name as found in RAG]

Reviews Summary: [Focused summary of reviews for this specific product]

## 👩🏼‍🔬 Information about the ingredients:
• [List key active ingredients found in RAG data]
• [Include concentration percentages if available]
• [Mention any notable ingredients that make this product effective]

## 🌟 PRODUCT ADVANTAGES
• [First key advantage of this product]
• [Second key advantage of this product]
• [Third key advantage of this product]

## ✨ WHY IT'S RIGHT FOR YOU
• [First reason this specific product matches user needs]
• [Second reason this specific product is suitable]
• [Third reason to choose this product]

## 💫 LET'S PERSONALIZE FURTHER
• Have you tried similar products before? What was your experience?
• What specific concerns would you like this product to address?
• When do you plan to use this product in your routine?

However, if the user is asking a general question about beauty, skincare, or product usage, provide a direct and informative response based on the RAG results without the structured format above. Always maintain a helpful and professional tone.

If the RAG system doesn't provide certain information, acknowledge what's missing rather than making assumptions."""

def extract_product_info(text: str) -> tuple[str, str, list[str], list[str], list[str], list[str]]:
    """Extract product name, review summary, ingredients, advantages, suitability reasons, and follow-up questions from RAG response."""
    # Take only the first occurrence of each section to avoid duplicates
    product_name = ""
    review_summary = ""
    ingredients = []
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

    # Extract ingredients (only first section)
    ingredients_section = re.search(r"## 👩🏼‍🔬 Here are the ingredients:\s*((?:•[^\n]+\n?)+)(?:##|$)", text)
    if ingredients_section:
        ingredients = [ing.strip().lstrip('•').strip() for ing in ingredients_section.group(1).split('\n') if ing.strip()]
    
    # Extract advantages (only first section)
    advantages_section = re.search(r"## 🌟 PRODUCT ADVANTAGES\s*((?:•[^\n]+\n?)+)(?:##|$)", text)
    if advantages_section:
        advantages = [adv.strip().lstrip('•').strip() for adv in advantages_section.group(1).split('\n') if adv.strip()]
    
    # Extract suitability reasons (only first section)
    suitability_section = re.search(r"## ✨ WHY IT'S RIGHT FOR YOU\s*((?:•[^\n]+\n?)+)(?:##|$)", text)
    if suitability_section:
        suitability = [reason.strip().lstrip('•').strip() for reason in suitability_section.group(1).split('\n') if reason.strip()]

    # Extract follow-up questions (only first section)
    questions_section = re.search(r"## 💫 LET'S PERSONALIZE FURTHER\s*((?:•[^\n]+\n?)+)(?:##|$)", text)
    if questions_section:
        questions = [q.strip().lstrip('•').strip() for q in questions_section.group(1).split('\n') if q.strip()]
    
    return product_name, review_summary, ingredients, advantages, suitability, questions

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

        # Clean up the response text to remove any duplicate sections
        cleaned_text = re.sub(r'(## 👩🏼‍🔬 Here are the ingredients:.*?(?=##|$))(.*\1)', r'\1', response.text, flags=re.DOTALL)
        cleaned_text = re.sub(r'(## 🌟 PRODUCT ADVANTAGES.*?(?=##|$))(.*\1)', r'\1', cleaned_text, flags=re.DOTALL)
        cleaned_text = re.sub(r'(## ✨ WHY IT\'S RIGHT FOR YOU.*?(?=##|$))(.*\1)', r'\1', cleaned_text, flags=re.DOTALL)
        cleaned_text = re.sub(r'(## 💫 LET\'S PERSONALIZE FURTHER.*?(?=##|$))(.*\1)', r'\1', cleaned_text, flags=re.DOTALL)

        # Remove any additional product mentions after the first one
        if "Product:" in cleaned_text:
            parts = cleaned_text.split("Product:", 1)
            if len(parts) > 1:
                additional_products = re.split(r'Product:', parts[1], flags=re.IGNORECASE)[1:]
                if additional_products:
                    # Keep only the content up to any additional product mentions
                    cleaned_text = "Product:" + re.split(r'Product:', parts[1], flags=re.IGNORECASE)[0]

        # Extract product information from cleaned text
        product_name, review_summary, ingredients, advantages, suitability, questions = extract_product_info(cleaned_text)

        # Create formatted response
        formatted_response = {
            "name": product_name,
            "description": review_summary,
            "ingredients": ingredients,
            "advantages": advantages,
            "suitability": suitability,
            "questions": questions
        }

        # Format the text response to include all sections
        text_response = (
            json.dumps(formatted_response, indent=2) + "\n\n" +
            cleaned_text
        )

        return ChatResponse(
            text=text_response,
            products=[ProductRecommendation(
                name=product_name,
                description=review_summary,
                ingredients=ingredients,
                advantages=advantages,
                suitability=suitability,
                questions=questions
            )] if product_name else []
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"} 