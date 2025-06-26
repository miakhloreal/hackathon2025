import streamlit as st
from google import genai
from google.genai import types
import json

# Define project information
PROJECT_ID = "oa-bta-learning-dv"
LOCATION = "europe-west4"
MODEL_ID = "gemini-2.0-flash"

# Initialize the Gemini client
client = genai.Client(
    vertexai=True,
    project=PROJECT_ID,
    location=LOCATION
)

def display_product(product_info):
    """Display a product recommendation in a styled container."""
    try:
        # Parse the product info if it's a string
        if isinstance(product_info, str):
            product_info = json.loads(product_info)
        
        # Create a container for the product
        with st.container():
            # Add a border and padding using markdown
            st.markdown("""
                <style>
                .product-container {
                    border: 1px solid #ddd;
                    border-radius: 10px;
                    padding: 20px;
                    margin: 10px 0;
                    background-color: #f8f9fa;
                    transition: background-color 0.3s ease;
                }
                .product-container:hover {
                    background-color: #e9ecef;
                }
                .product-name {
                    font-size: 1.2em;
                    font-weight: bold;
                    margin-bottom: 10px;
                    color: #000;
                }
                .product-price {
                    color: #333;
                    font-weight: bold;
                    margin: 8px 0;
                }
                .product-link {
                    color: #000;
                    text-decoration: none;
                    display: block;
                }
                .product-link:hover {
                    text-decoration: none;
                    color: #000;
                }
                </style>
            """, unsafe_allow_html=True)
            
            # Create clickable product container
            with st.markdown(f"""
                <div class="product-container">
                    <a href="{product_info['url']}" target="_blank" class="product-link">
                        <div class="product-name">{product_info.get('name', 'Product Name Not Available')}</div>
                        <div class="product-price">Price: {product_info.get('price', 'Price Not Available')}</div>
                        <div style="margin-top: 10px;">🛍️ Click to Buy</div>
                    </a>
                </div>
                """, unsafe_allow_html=True):
                pass
    except (json.JSONDecodeError, KeyError) as e:
        st.error(f"Error displaying product: {str(e)}")

# Set page configuration
st.set_page_config(
    page_title="L'Oréal Product Advisor",
    page_icon="💄",
    layout="centered"
)

# Add header
st.title("L'Oréal Product Advisor 💄")
st.markdown("Chat with our AI to get personalized L'Oréal product recommendations!")

# Add a "Start New Conversation" button
if st.button("🔄 Start New Conversation"):
    # Reset the chat session
    st.session_state.chat = client.chats.create(model=MODEL_ID)
    # Clear the messages
    st.session_state.messages = []
    # Reinitialize with system prompt
    system_prompt = """You are a knowledgeable and proactive L'Oréal beauty advisor. Follow these steps for EVERY user message:

    1. ALWAYS provide at least one product recommendation based on ANY information the user shares, even if minimal. 
       Format each product recommendation as a JSON object with the following structure:
       ```json
       {
           "name": "Product Full Name",
           "price": "€XX.XX",
           "url": "https://www.loreal-paris.fr/[product-url]",
           "description": "Brief explanation of benefits"
       }
       ```
    2. After the JSON object, provide a brief explanation of why this product would help them
    3. Ask 1-2 follow-up questions to better understand their needs, such as:
       - Their skin type/concerns
       - Their current routine
       - Their preferences (texture, fragrance, etc.)
       - Their budget
       - Their previous experience with similar products
    
    Guidelines:
    - Be concise but informative
    - Focus only on L'Oréal products
    - Maintain a professional, friendly tone
    - Always format product recommendations in the specified JSON format
    - Use real L'Oréal product URLs when available
    
    Start by greeting the user and asking about their beauty needs or concerns."""
    
    response = st.session_state.chat.send_message(
        system_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.7,
        )
    )
    st.session_state.messages = [{"role": "assistant", "content": response.text}]
    st.rerun()

# Initialize chat session state
if "chat" not in st.session_state:
    st.session_state.chat = client.chats.create(model=MODEL_ID)
    
    # Set up the initial system prompt with the same prompt as above
    system_prompt = """You are a knowledgeable and proactive L'Oréal beauty advisor. Follow these steps for EVERY user message:

    1. ALWAYS provide at least one product recommendation based on ANY information the user shares, even if minimal. 
       Format each product recommendation as a JSON object with the following structure:
       ```json
       {
           "name": "Product Full Name",
           "price": "€XX.XX",
           "url": "https://www.loreal-paris.fr/[product-url]",
           "description": "Brief explanation of benefits"
       }
       ```
    2. After the JSON object, provide a brief explanation of why this product would help them
    3. Ask 1-2 follow-up questions to better understand their needs, such as:
       - Their skin type/concerns
       - Their current routine
       - Their preferences (texture, fragrance, etc.)
       - Their budget
       - Their previous experience with similar products
    
    Guidelines:
    - Be concise but informative
    - Focus only on L'Oréal products
    - Maintain a professional, friendly tone
    - Always format product recommendations in the specified JSON format
    - Use real L'Oréal product URLs when available
    
    Start by greeting the user and asking about their beauty needs or concerns."""
    
    response = st.session_state.chat.send_message(
        system_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.7,
        )
    )
    st.session_state.messages = [{"role": "assistant", "content": response.text}]
else:
    st.session_state.messages = st.session_state.messages

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        content = message["content"]
        
        # Try to extract and display product recommendations
        if message["role"] == "assistant":
            try:
                # Look for JSON objects in the message
                start_idx = content.find('{')
                end_idx = content.find('}')
                
                if start_idx != -1 and end_idx != -1:
                    # Extract the JSON part
                    json_str = content[start_idx:end_idx + 1]
                    # Display the product recommendation
                    display_product(json_str)
                    # Display the rest of the message
                    remaining_text = content[end_idx + 1:].strip()
                    if remaining_text:
                        st.markdown(remaining_text)
                else:
                    # If no JSON found, display the message as is
                    st.markdown(content)
            except Exception as e:
                # If there's any error, display the message as is
                st.markdown(content)
        else:
            st.markdown(content)

# Chat input
if prompt := st.chat_input("Tell me about your beauty needs..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get AI response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = st.session_state.chat.send_message(prompt)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
            # Display the response with product recommendations
            content = response.text
            try:
                # Look for JSON objects in the message
                start_idx = content.find('{')
                end_idx = content.find('}')
                
                if start_idx != -1 and end_idx != -1:
                    # Extract the JSON part
                    json_str = content[start_idx:end_idx + 1]
                    # Display the product recommendation
                    display_product(json_str)
                    # Display the rest of the message
                    remaining_text = content[end_idx + 1:].strip()
                    if remaining_text:
                        st.markdown(remaining_text)
                else:
                    # If no JSON found, display the message as is
                    st.markdown(content)
            except Exception as e:
                # If there's any error, display the message as is
                st.markdown(content) 