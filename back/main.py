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

app = FastAPI(title="KnowLi Advisor API")

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
    price: str = "€18.99"  # Default price if not available
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

Requirements:
1. Choose ONLY ONE product that best matches their needs
2. Do not mention or compare multiple products
3. Focus on providing a clear recommendation

Format your response EXACTLY as follows:
Product: [Single product name as found in RAG]"""

PRODUCT_REVIEW_PROMPT = """IMPORTANT: Use ONLY the information provided by the RAG system in your response. Do not generate or invent any information.

You are a L'Oréal product reviewer analyzing the RAG search results for:
{product_name}

Provide a brief but compelling summary of user reviews and experiences.
Focus on:
1. Overall user satisfaction
2. Key benefits users experienced
3. Notable results or effects

Format your response EXACTLY as follows:
## 💭 What other users say about this product:
[2-3 sentences summarizing user experiences and results]"""

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

PRODUCT_INGREDIENTS_PROMPT = """IMPORTANT: Use ONLY the information provided by the RAG system in your response. Do not generate or invent any information.

You are a L'Oréal cosmetic ingredients expert analyzing the RAG search results for:
{product_name}

Focus ONLY on the ingredients information. List the key active ingredients with their benefits and concentrations if available.
Format your response with bullet points:

## 👩🏼‍🔬 Key Ingredients:
• [First key ingredient with concentration if available]
• [Second key ingredient with its benefits]
• [Additional notable ingredients that make this product effective]"""

PRODUCT_ADVANTAGES_PROMPT = """IMPORTANT: Use ONLY the information provided by the RAG system in your response. Do not generate or invent any information.

You are a L'Oréal product expert analyzing the RAG search results for:
{product_name}

Focus ONLY on the product's main advantages and benefits. List 3-4 key advantages.
Format your response with bullet points:

## 🌟 Main Product Benefits
• [First key advantage with supporting evidence]
• [Second key advantage with specific benefits]
• [Third key advantage with unique selling point]"""

PRODUCT_SUITABILITY_PROMPT = """IMPORTANT: Use ONLY the information provided by the RAG system in your response. Do not generate or invent any information.

You are a L'Oréal beauty advisor analyzing the RAG search results for:
{product_name}

Focus on creating a personalized response that connects with the user's needs. List 3 main reasons that specifically address their concerns.
Format your response with bullet points:

## ✨ WHY IT'S RIGHT FOR YOU
• [First reason with specific skin/hair type suitability]
• [Second reason with specific concerns it addresses]
• [Third reason with expected benefits]"""

PRODUCT_QUESTIONS_PROMPT = """IMPORTANT: Use ONLY the information provided by the RAG system in your response. Do not generate or invent any information.

You are a L'Oréal beauty consultant analyzing the RAG search results for:
{product_name}

Create 2-3 relevant follow-up questions that build on the previous conversation and help personalize the recommendation further.
The questions should feel natural and connected to what we already know about the user's needs.

Format your response with bullet points:

## 💫 PERSONALIZATION QUESTIONS
• [Question that builds on previous responses]
• [Question about specific concerns mentioned earlier]
• [Question to further personalize the recommendation]"""

def extract_product_name(text: str) -> str:
    """Extract product name from the RAG response."""
    name_match = re.search(r"Product:\s*([^\n]+)", text, re.IGNORECASE)
    if name_match:
        return name_match.group(1).strip()
    return ""

def extract_review_summary(text: str) -> str:
    """Extract review summary from the RAG response."""
    summary_match = re.search(r"Reviews Summary:\s*([^\n]+(?:\.[^\n]+){0,2}\.)", text, re.IGNORECASE)
    if summary_match:
        return summary_match.group(1).strip()
    return ""

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

def extract_section_items(text: str, emoji: str) -> list[str]:
    """Extract bullet points from a section marked with the given emoji."""
    # Look for section header with emoji and any text after it
    section = re.search(fr"## [{emoji}][^\n]*\s*((?:•[^\n]+\n?)+)", text)
    if section:
        # Extract bullet points, clean them up, and filter out empty lines
        items = [
            item.strip().lstrip('•').strip()
            for item in section.group(1).split('\n')
            if item.strip() and '•' in item  # Only include lines with bullet points
        ]
        return items
    return []

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # Get the current message and maintain conversation context
        current_message = request.messages[-1].content
        conversation_history = [msg.content for msg in request.messages[:-1]]
        
        # Extract previous product and user concerns from conversation history
        previous_product = None
        user_concerns = set()
        
        for msg in conversation_history:
            # Look for previous product recommendations
            product_match = re.search(r"Product:\s*([^\n]+)", msg)
            if product_match:
                previous_product = product_match.group(1).strip()
            
            # Extract user concerns (hair/skin conditions, preferences)
            concerns = re.findall(r"(?:have|my)\s+((?:very|really|extremely|slightly)?\s*(?:oily|dry|damaged|sensitive|frizzy|thin|thick|colored|treated|curly|straight)\s+(?:hair|skin))", msg.lower())
            user_concerns.update(concerns)

        # Modify the current query based on conversation history
        if previous_product and "ingredients" in current_message.lower():
            # Direct ingredients query about previous product
            product_name = previous_product
            recommendation_response = type('Response', (), {'text': f"Product: {product_name}"})()
        else:
            # Build context-aware recommendation prompt
            context_prompt = PRODUCT_RECOMMENDATION_PROMPT
            if previous_product:
                context_prompt += f"\n\nNote: User previously asked about {previous_product}."
            if user_concerns:
                context_prompt += f"\n\nUser mentioned these conditions: {', '.join(user_concerns)}."
            
            recommendation_response = client.models.generate_content(
                model=MODEL_ID,
                contents=current_message,
                config=GenerateContentConfig(
                    tools=[rag_retrieval_tool],
                    system_instruction=context_prompt
                )
            )

            if not recommendation_response.text:
                return ChatResponse(
                    text="I apologize, I couldn't generate a response.",
                    products=[]
                )

            product_name = extract_product_name(recommendation_response.text)
            if not product_name:
                return ChatResponse(
                    text=recommendation_response.text,
                    products=[]
                )

        # Build context-aware suitability prompt
        suitability_context = PRODUCT_SUITABILITY_PROMPT.format(product_name=product_name)
        if user_concerns:
            suitability_context += f"\n\nAddress these specific concerns: {', '.join(user_concerns)}."
        
        # Get suitability information
        suitability_response = client.models.generate_content(
            model=MODEL_ID,
            contents=f"Why is {product_name} right for the user?",
            config=GenerateContentConfig(
                tools=[rag_retrieval_tool],
                system_instruction=suitability_context
            )
        )

        # Get product advantages with context
        advantages_context = PRODUCT_ADVANTAGES_PROMPT.format(product_name=product_name)
        if user_concerns:
            advantages_context += f"\n\nHighlight benefits relevant to: {', '.join(user_concerns)}."
        
        advantages_response = client.models.generate_content(
            model=MODEL_ID,
            contents=f"What are the main advantages of {product_name}",
            config=GenerateContentConfig(
                tools=[rag_retrieval_tool],
                system_instruction=advantages_context
            )
        )

        # Get review summary with context
        review_prompt = PRODUCT_REVIEW_PROMPT.format(product_name=product_name)
        if user_concerns:
            review_prompt += f"\n\nFocus on reviews relevant to: {', '.join(user_concerns)}."
        
        review_response = client.models.generate_content(
            model=MODEL_ID,
            contents=f"What do users say about {product_name}",
            config=GenerateContentConfig(
                tools=[rag_retrieval_tool],
                system_instruction=review_prompt
            )
        )

        # Extract review summary
        review_summary = extract_review_summary(review_response.text if review_response.text else "")

        # Get image
        image_response = client.models.generate_content(
            model=MODEL_ID,
            contents=f"Give me the image url for the product: {product_name}",
            config=GenerateContentConfig(
                tools=[rag_retrieval_tool],
                system_instruction=PRODUCT_IMAGE_PROMPT.format(product_name=product_name)
            )
        )

        image_url = extract_image_url(image_response.text if image_response.text else "")

        # Initialize ingredients
        ingredients = []
        ingredients_response_text = ""

        # Get ingredients if requested
        if "ingredients" in current_message.lower():
            ingredients_response = client.models.generate_content(
                model=MODEL_ID,
                contents=f"Tell me about the ingredients in {product_name}",
                config=GenerateContentConfig(
                    tools=[rag_retrieval_tool],
                    system_instruction=PRODUCT_INGREDIENTS_PROMPT.format(product_name=product_name)
                )
            )
            ingredients = extract_section_items(ingredients_response.text if ingredients_response.text else "", "👩🏼‍🔬")
            ingredients_response_text = ingredients_response.text if ingredients_response.text else ""

        # Get personalized follow-up questions
        questions_context = PRODUCT_QUESTIONS_PROMPT.format(product_name=product_name)
        if user_concerns:
            questions_context += f"\n\nConsider these concerns in your questions: {', '.join(user_concerns)}."
        
        questions_response = client.models.generate_content(
            model=MODEL_ID,
            contents=f"What follow-up questions should we ask about {product_name}",
            config=GenerateContentConfig(
                tools=[rag_retrieval_tool],
                system_instruction=questions_context
            )
        )

        # Create formatted response
        formatted_response = {
            "name": product_name,
            "image_url": image_url,
            "description": review_summary,
            "ingredients": ingredients,
            "advantages": extract_section_items(advantages_response.text if advantages_response.text else "", "🌟"),
            "suitability": extract_section_items(suitability_response.text if suitability_response.text else "", "✨"),
            "questions": extract_section_items(questions_response.text if questions_response.text else "", "💫")
        }

        # Combine all responses
        text_response = json.dumps(formatted_response, indent=2)
        text_response += "\n\n" + (recommendation_response.text or "")
        text_response += "\n\n" + (suitability_response.text or "")
        text_response += "\n\n" + (review_response.text or "")
        if ingredients_response_text:
            text_response += "\n\n" + ingredients_response_text
        text_response += "\n\n" + (questions_response.text or "")

        return ChatResponse(
            text=text_response,
            products=[ProductRecommendation(
                name=product_name,
                description=review_summary,
                image_url=image_url,
                ingredients=ingredients,
                advantages=extract_section_items(advantages_response.text if advantages_response.text else "", "🌟"),
                suitability=extract_section_items(suitability_response.text if suitability_response.text else "", "✨"),
                questions=extract_section_items(questions_response.text if questions_response.text else "", "💫")
            )]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"} 