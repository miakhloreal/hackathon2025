# RAG-Powered Streamlit Application

This project implements a Retrieval-Augmented Generation (RAG) system with a Streamlit interface, allowing for efficient document processing and intelligent querying.

## Project Structure

```
.
├── venv/                  # Virtual environment
├── src/                  # Source code
│   ├── rag/             # RAG implementation
│   │   ├── embeddings/  # Embedding models and utilities
│   │   ├── retriever/   # Document retrieval logic
│   │   └── utils/       # Utility functions
│   ├── streamlit/       # Streamlit application code
│   └── data/           # Data storage and processing
├── docs/               # Documentation
├── tests/             # Test files
├── .env              # Environment variables (create this file)
└── requirements.txt   # Project dependencies
```

## Setup Instructions

1. **Clone the Repository**

   ```bash
   git clone <repository-url>
   cd <project-directory>
   ```

2. **Set Up Virtual Environment**

   ```bash
   # The virtual environment is already created
   source venv/bin/activate  # On macOS/Linux
   # or
   .\venv\Scripts\activate  # On Windows
   ```

3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables**
   Create a `.env` file in the root directory and add your configuration:

   ```
   OPENAI_API_KEY=your_api_key_here
   # Add other necessary environment variables
   ```

5. **Running the Application**
   ```bash
   streamlit run src/streamlit/app.py
   ```

## Features

- Document processing and embedding generation
- Efficient vector storage and retrieval
- Interactive Streamlit interface
- RAG-powered question answering
- Document similarity search

## Development

- Use the virtual environment for all development work
- Follow PEP 8 style guidelines
- Write tests for new features
- Document code changes

## Testing

```bash
python -m pytest tests/
```

## Contributing

1. Create a new branch for features
2. Write tests for new features
3. Submit pull requests with detailed descriptions

## License

[Add your license information here]

## Contact

[Add your contact information here]
