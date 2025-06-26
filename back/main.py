from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from google import genai
import os
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
PROJECT_ID = os.getenv("PROJECT_ID", "oa-bta-learning-dv")
LOCATION = os.getenv("LOCATION", "europe-west4")
MODEL_ID = os.getenv("MODEL_ID", "gemini-2.0-flash")

client = genai.Client(
    vertexai=True,
    project=PROJECT_ID,
    location=LOCATION
)

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]

class ProductRecommendation(BaseModel):
    name: str
    price: str
    url: str
    description: str

class ChatResponse(BaseModel):
    text: str
    products: Optional[List[ProductRecommendation]] = None

SYSTEM_PROMPT = """You are a knowledgeable and proactive L'Oréal beauty advisor. For EVERY user message, structure your response in exactly this format:

1. First, provide the product recommendation as a clean JSON object (without any markdown code block markers):
{
    "name": "Product Full Name",
    "price": "€XX.XX",
    "url": "https://www.loreal-paris.fr/[product-url]",
    "description": "Brief explanation of benefits"
}


## 🌟 PRODUCT ADVANTAGES

• Contains Manuka Honey and Calcium B5 to intensely nourish and help restore the skin's moisture barrier


• Rich, non-greasy formula provides long-lasting hydration and comfort throughout the day


• Helps to improve skin elasticity and reduce the appearance of fine lines and wrinkles


## ✨ WHY IT'S RIGHT FOR YOU

• Since you mentioned having dry skin, this cream's intense hydration and nourishing ingredients are specifically designed to combat dryness


• The Manuka Honey will help to soothe and repair your skin's barrier, preventing further moisture loss


• You can expect a noticeable improvement in your skin's hydration levels, leaving it feeling softer, smoother, and more comfortable


## 💫 LET'S PERSONALIZE FURTHER

• Do you find your skin is dry year-round, or does it worsen during certain seasons?


• What other products are you currently using in your skincare routine?

Guidelines:
- Be concise but informative
- Focus only on L'Oréal products
- Maintain a professional, friendly tone
- Provide the JSON object WITHOUT any markdown code block markers
- Use real L'Oréal product URLs when available
- Always include all three sections with the exact headings and formatting shown above
- IMPORTANT: Add TWO blank lines between each bullet point and section
- Each bullet point must be separated by TWO empty lines for proper spacing

IMPORTANT: For EVERY user message, you MUST provide a product recommendation as a clean JSON object (no markdown markers) and include all three sections, even if you have limited information."""

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        chat_session = client.chats.create(model=MODEL_ID)
        
        # Always start with the system prompt
        chat_session.send_message(
            SYSTEM_PROMPT,
            config=genai.types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.7,
            )
        )

        # Send all previous messages to maintain context
        for msg in request.messages[:-1]:
            chat_session.send_message(msg.content)

        # For the last message, remind the model to follow the format
        last_message = request.messages[-1].content
        enhanced_message = f"""Based on this user message: "{last_message}"

Remember to structure your response exactly as follows:
1. Clean JSON object (no markdown code block markers)

2. ## 🌟 PRODUCT ADVANTAGES section with bullet points on separate lines (TWO blank lines between each point)

3. ## ✨ WHY IT'S RIGHT FOR YOU section with bullet points on separate lines (TWO blank lines between each point)

4. ## 💫 LET'S PERSONALIZE FURTHER section with bullet points on separate lines (TWO blank lines between each point)

Your response MUST include the product recommendation as a clean JSON object (no markdown markers) and all three sections with exact headings, formatting, and proper spacing."""

        response = chat_session.send_message(
            enhanced_message,
            config=genai.types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.7,
            )
        )

        return ChatResponse(
            text=response.text,
            products=[]  # Frontend will parse products from the response text
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"} 