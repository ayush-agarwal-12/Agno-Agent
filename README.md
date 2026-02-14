# Agno Research Assistant

A streaming AI chat application powered by Agno v2 framework with FastAPI backend and real-time web interface.
Demo Video : https://drive.google.com/file/d/1w8ALlzZnnOuXw4lN_hJhfKzICkiepGO4/view?usp=sharing

## Features

- AI-powered research assistant with web search capabilities
- Real-time streaming responses
- Session-based conversation memory
- Clean web interface with markdown rendering
- Custom tool support (weather, calculator, URL summarizer, time info)

## Quick Setup with UV

[UV](https://github.com/astral-sh/uv) is a fast Python package installer.

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate  # Unix/macOS
# or
.venv\Scripts\activate  # Windows

# Install dependencies
uv pip install -r requirements.txt
```

## Alternative Setup (Traditional pip)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # Unix/macOS
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
```

Get your API key from: https://console.groq.com/

## Running the Application

### Start the Server

```bash
python main.py
```

Server will run on: http://127.0.0.1:8000

### Web Interface

Open browser and navigate to: http://127.0.0.1:8000

### Test the API

```bash
python test_api.py
```

## Project Structure

```
.
├── main.py              # FastAPI server with streaming chat
├── enhanced_agent.py    # Custom tools and agent examples
├── test_api.py         # API test suite
├── index.html          # Web chat interface
├── requirements.txt    # Python dependencies
└── .env                # API keys (create this)
```

## Available Tools

### Built-in Tools
- **DuckDuckGo Search** - Web search for current information
- **Newspaper4k** - Article extraction and analysis

### Custom Tools
- **get_weather** - Current weather for cities
- **calculate_expression** - Safe math evaluation
- **summarize_url** - Fetch and preview web content
- **get_time_info** - Current time with timezone support

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web interface |
| `/chat` | POST | Streaming chat endpoint |
| `/health` | GET | API health check |
| `/sessions` | GET | List all sessions |
| `/session/{id}` | GET | Get session history |
| `/session/{id}` | DELETE | Delete session |

## Usage Examples

### Simple Query
```
User: What is the weather in Tokyo?
Assistant: [Uses get_weather tool] Current weather in Tokyo: Sunny, 22°C...
```

### Research Query
```
User: What are the latest developments in AI?
Assistant: [Uses DuckDuckGo search] Based on recent search results...
```

### Multi-turn Conversation
```
User: Tell me about Python
Assistant: Python is a high-level programming language...
User: What are its main advantages?
Assistant: [Remembers context] Python's main advantages include...
```

## Key Features of Agno v2

- Removed deprecated `show_tool_calls` parameter
- Temperature set to 0.0 for consistent outputs
- Proper tool registration (instances + functions)
- Clear instructions for tool usage
- Comprehensive error handling

## Troubleshooting

**Issue: ModuleNotFoundError**
```bash
# Ensure virtual environment is activated
# Reinstall dependencies
uv pip install -r requirements.txt --force-reinstall
```

**Issue: GROQ_API_KEY not found**
- Verify `.env` file exists in project root
- Check API key format: `GROQ_API_KEY=gsk_...`

**Issue: Connection refused**
- Ensure server is running: `python main.py`
- Check port 8000 is not in use
