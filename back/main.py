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
    image_url: str = ""  # Product image URL
    description: str
    ingredients: List[str] = []
    advantages: List[str] = []
    suitability: List[str] = []
    questions: List[str] = []

class ChatResponse(BaseModel):
    text: str
    products: Optional[List[ProductRecommendation]] = None

PRODUCT_RECOMMENDATION_PROMPT = """IMPORTANT: Use ONLY the information provided by the RAG system in your response. Do not generate or invent any information.

You are a L'Oréal beauty advisor analyzing the RAG search results. Your task is to recommend a single product that best matches the user's needs.

1. Choose ONLY ONE product that best matches their needs
2. Do not mention or compare multiple products
3. Focus on providing a clear recommendation

Structure your response as follows:

Product: [Single product name as found in RAG]
Reviews Summary: [Brief summary of reviews for this specific product]"""

PRODUCT_IMAGE_PROMPT = """IMPORTANT: Use ONLY the information provided by the RAG system in your response.

You are a L'Oréal product image specialist. Your task is to find EXACTLY ONE image URL for this specific product from the RAG data:
{product_name}

Requirements:
1. Return EXACTLY ONE image URL from the RAG data
2. The URL must be a direct link to the product image
3. Do NOT search external sources or L'Oréal's website
4. Only use URLs found in the RAG search results

Format your response EXACTLY like this:
PRODUCT_IMAGE_URL: [paste the single URL from RAG data here]"""

PRODUCT_DETAILS_PROMPT = """IMPORTANT: Use ONLY the information provided by the RAG system in your response. Do not generate or invent any information.

You are a L'Oréal beauty advisor analyzing the RAG search results for the following product:

{product_name}

Please provide detailed information about this specific product using the following format:

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
• When do you plan to use this product in your routine?"""

def extract_product_info_basic(text: str) -> tuple[str, str]:
    """Extract product name and review summary from RAG response."""
    product_name = ""
    review_summary = ""
    
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
    
    return product_name, review_summary

def extract_image_url(text: str) -> str:
    """Extract image URL from the RAG response."""
    # Look for any URLs in the text that might be images
    url_patterns = [
        r"PRODUCT_IMAGE_URL:\s*(https?://[^\s\n]+)",  # Our specified format
        r"(?:image_url|image|img|src):\s*(https?://[^\s\n]+)",  # Common image URL patterns
        r"https?://[^\s\n]+\.(?:jpg|jpeg|png|gif|webp)"  # Direct image URLs
    ]
    
    for pattern in url_patterns:
        image_match = re.search(pattern, text, re.IGNORECASE)
        if image_match:
            url = image_match.group(1) if len(image_match.groups()) > 0 else image_match.group(0)
            return url.strip().rstrip('.,)')  # Clean up any trailing punctuation
    return ""

def extract_product_details(text: str) -> tuple[list[str], list[str], list[str], list[str]]:
    """Extract ingredients, advantages, suitability reasons, and follow-up questions from RAG response."""
    ingredients = []
    advantages = []
    suitability = []
    questions = []
    
    # Extract ingredients (only first section)
    ingredients_section = re.search(r"## 👩🏼‍🔬 Information about the ingredients:\s*((?:•[^\n]+\n?)+)(?:##|$)", text)
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
    
    return ingredients, advantages, suitability, questions

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # First RAG call: Get product recommendation
        recommendation_response = client.models.generate_content(
            model=MODEL_ID,
            contents=request.messages[-1].content,
            config=GenerateContentConfig(
                tools=[rag_retrieval_tool],
                system_instruction=PRODUCT_RECOMMENDATION_PROMPT
            )
        )

        if not recommendation_response.text:
            return ChatResponse(
                text="I apologize, I couldn't generate a response.",
                products=[]
            )

        # Extract basic product info
        product_name, review_summary = extract_product_info_basic(recommendation_response.text)

        if not product_name:
            return ChatResponse(
                text=recommendation_response.text,
                products=[]
            )

        # Second RAG call: Get product image
        image_response = client.models.generate_content(
            model=MODEL_ID,
            contents=f"Give me the image url for the product: {product_name}",
            config=GenerateContentConfig(
                tools=[rag_retrieval_tool],
                system_instruction=PRODUCT_IMAGE_PROMPT.format(product_name=product_name)
            )
        )

        print('image_response', image_response.text)

        # Extract image URL
        image_url = extract_image_url(image_response.text if image_response.text else "")

        # Third RAG call: Get detailed product information
        details_response = client.models.generate_content(
            model=MODEL_ID,
            contents=f"Tell me about {product_name}",
            config=GenerateContentConfig(
                tools=[rag_retrieval_tool],
                system_instruction=PRODUCT_DETAILS_PROMPT.format(product_name=product_name)
            )
        )

        if not details_response.text:
            return ChatResponse(
                text="I apologize, I couldn't generate detailed product information.",
                products=[]
            )

        # Extract detailed product information
        ingredients, advantages, suitability, questions = extract_product_details(details_response.text)

        # Create formatted response
        formatted_response = {
            "name": product_name,
            "image_url": image_url,
            "description": review_summary,
            "ingredients": ingredients,
            "advantages": advantages,
            "suitability": suitability,
            "questions": questions
        }

        # Combine both responses
        text_response = (
            json.dumps(formatted_response, indent=2) + "\n\n" +
            recommendation_response.text + "\n\n" +
            details_response.text
        )

        return ChatResponse(
            text=text_response,
            products=[ProductRecommendation(
                name=product_name,
                description=review_summary,
                image_url=image_url,
                ingredients=ingredients,
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