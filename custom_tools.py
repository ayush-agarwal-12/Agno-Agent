"""
Enhanced Agent Example with Custom Tools
Demonstrates proper Agno v2 usage with:
- Custom function tools
- Built-in toolkits
- Proper error handling
- Deterministic output configuration
"""

import os
import requests
from typing import Optional
from dotenv import load_dotenv

from agno.agent import Agent
from agno.models.groq import Groq
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.newspaper4k import Newspaper4kTools


# ============================================================================
# CUSTOM TOOL FUNCTIONS
# ============================================================================
# In Agno v2, any Python function can be used as a tool.
# Requirements:
# 1. Type hints for all parameters
# 2. Docstring explaining what the function does
# 3. Clear parameter descriptions in docstring
# ============================================================================

def get_weather(city: str) -> str:
    """
    Get current weather information for a specific city.
    
    Args:
        city: Name of the city to get weather for (e.g., "Tokyo", "New York")
    
    Returns:
        str: Weather information including temperature, conditions, and wind
    """
    # In production, replace this with an actual weather API call
    # Example: OpenWeatherMap, WeatherAPI, etc.
    weather_data = {
        "Tokyo": "Sunny, 22°C (72°F), Wind: 10 km/h",
        "New York": "Partly Cloudy, 18°C (64°F), Wind: 15 km/h",
        "London": "Rainy, 12°C (54°F), Wind: 20 km/h",
        "Paris": "Clear, 20°C (68°F), Wind: 8 km/h",
    }
    
    weather = weather_data.get(
        city, 
        f"Weather data for {city}: Sunny, 22°C (72°F), Wind: 10 km/h"
    )
    return f"Current weather in {city}: {weather}"


def calculate_expression(expression: str) -> str:
    """
    Safely evaluate a mathematical expression and return the result.
    
    Args:
        expression: Mathematical expression to evaluate (e.g., "2 + 2", "10 * 5 + 3")
    
    Returns:
        str: Calculation result or error message
    """
    try:
        # Safe evaluation: restrict to basic math operations only
        # Block access to builtins and dangerous functions
        allowed_names = {
            'abs': abs, 'round': round, 'min': min, 'max': max,
            'sum': sum, 'pow': pow
        }
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return f"Calculation Result: {expression} = {result}"
    except Exception as e:
        return f"Calculation Error: Unable to evaluate '{expression}'. Error: {str(e)}"


def summarize_url(url: str, max_length: int = 200) -> str:
    """
    Fetch content from a URL and return a brief summary.
    
    Args:
        url: Web URL to fetch and summarize
        max_length: Maximum length of the summary in characters (default: 200)
    
    Returns:
        str: Content preview or error message
    """
    try:
        # Add timeout to prevent hanging requests
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; AgnoBot/1.0)'
        })
        response.raise_for_status()
        
        # Get text content and clean it
        content = response.text.replace("\n", " ").replace("\r", "")
        
        # Return preview
        if len(content) > max_length:
            return f"Content preview for {url}: {content[:max_length]}..."
        else:
            return f"Content for {url}: {content}"
            
    except requests.exceptions.Timeout:
        return f"Error: Request to {url} timed out after 10 seconds"
    except requests.exceptions.RequestException as e:
        return f"Error fetching URL {url}: {str(e)}"
    except Exception as e:
        return f"Unexpected error processing {url}: {str(e)}"


def get_time_info(timezone: Optional[str] = None) -> str:
    """
    Get current time information.
    
    Args:
        timezone: Optional timezone (e.g., "UTC", "America/New_York")
    
    Returns:
        str: Current time information
    """
    from datetime import datetime
    import pytz
    
    try:
        if timezone:
            tz = pytz.timezone(timezone)
            current_time = datetime.now(tz)
            return f"Current time in {timezone}: {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}"
        else:
            current_time = datetime.now()
            return f"Current local time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}"
    except Exception as e:
        return f"Error getting time: {str(e)}"


# ============================================================================
# AGENT CREATION FUNCTION
# ============================================================================

def create_enhanced_agent() -> Agent:
    """
    Create an enhanced Agent with both built-in and custom tools.
    
    Key v2 improvements applied:
    1. Removed deprecated 'show_tool_calls' parameter
    2. Set temperature to 0.0 for deterministic outputs
    3. Clear, specific instructions for tool usage
    4. Proper tool registration (instances for toolkits, functions for custom)
    
    Returns:
        Agent: Configured agent ready to use
    """
    
    # Configure model with deterministic settings
    model = Groq(
        id="openai/gpt-oss-120b",
        temperature=0.0  # Deterministic outputs
    )
    
    # Create agent with mixed tools
    agent = Agent(
        name="Enhanced Assistant",
        role="Helpful assistant with multiple capabilities",
        model=model,
        
        # Tools list: Mix of built-in toolkits and custom functions
        tools=[
            # Built-in toolkits (instantiated)
            DuckDuckGoTools(),
            Newspaper4kTools(),
            
            # Custom function tools (passed as functions)
            get_weather,
            calculate_expression,
            summarize_url,
            get_time_info,
        ],
        
        # Clear instructions for tool usage
        instructions=[
            "You are a helpful assistant with access to multiple tools.",
            "When asked about weather, use the get_weather tool.",
            "When asked to calculate or compute something, use the calculate_expression tool.",
            "When asked to fetch or summarize a webpage, use the summarize_url tool.",
            "When asked about the time, use the get_time_info tool.",
            "For current news or web searches, use the DuckDuckGo tools.",
            "For article analysis, use the Newspaper4k tools.",
            "Always include the tool's result in your final answer.",
            "Be specific and cite your sources when using search tools.",
            "Do no Add special symbols and emojis",
        ],
        
        # Formatting options
        markdown=True,
        
        # Debug mode OFF for production (set True only when debugging)
        debug_mode=False,
        
        # Note: show_tool_calls is REMOVED in v2
        # Tool calls are always visible by default
        # Use debug_mode=True if you need detailed logging
    )
    
    return agent


# ============================================================================
# TESTING FUNCTIONS
# ============================================================================

def test_weather_tool():
    """Test the weather tool functionality."""
    print("\n" + "="*70)
    print("Testing Weather Tool")
    print("="*70)
    
    agent = create_enhanced_agent()
    agent.print_response("What is the weather like in Tokyo?", stream=True)


def test_calculator_tool():
    """Test the calculator tool functionality."""
    print("\n" + "="*70)
    print("Testing Calculator Tool")
    print("="*70)
    
    agent = create_enhanced_agent()
    agent.print_response("Calculate 1234 * 5678 + 999", stream=True)


def test_url_summarizer_tool():
    """Test the URL summarizer tool functionality."""
    print("\n" + "="*70)
    print("Testing URL Summarizer Tool")
    print("="*70)
    
    agent = create_enhanced_agent()
    agent.print_response("Summarize the content at https://example.com", stream=True)


def test_web_search_tool():
    """Test the web search tool functionality."""
    print("\n" + "="*70)
    print("Testing Web Search Tool")
    print("="*70)
    
    agent = create_enhanced_agent()
    agent.print_response("What are the latest developments in AI?", stream=True)


def test_time_tool():
    """Test the time tool functionality."""
    print("\n" + "="*70)
    print("Testing Time Tool")
    print("="*70)
    
    agent = create_enhanced_agent()
    agent.print_response("What time is it now?", stream=True)


def test_multiple_tools():
    """Test using multiple tools in one conversation."""
    print("\n" + "="*70)
    print("Testing Multiple Tools")
    print("="*70)
    
    agent = create_enhanced_agent()
    agent.print_response(
        "Calculate 100 * 5, then tell me the weather in Paris, and search for recent AI news",
        stream=True
    )


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Check for API key
    if not os.getenv("GROQ_API_KEY"):
        print("Error: GROQ_API_KEY not found in environment")
        print("Please create a .env file with your GROQ_API_KEY")
        exit(1)
    
    print("\n" + "="*70)
    print("AGNO V2 ENHANCED AGENT DEMO")
    print("="*70)
    print("\nKey improvements applied:")
    print("✓ Removed deprecated 'show_tool_calls' parameter")
    print("✓ Set temperature to 0.0 for consistent outputs")
    print("✓ Proper tool registration (instances + functions)")
    print("✓ Clear instructions for tool usage")
    print("✓ Comprehensive error handling")
    print("="*70)
    
    # Run tests
    try:
        test_weather_tool()
        test_calculator_tool()
        test_web_search_tool()
        test_time_tool()
        test_multiple_tools()
        
        print("\n" + "="*70)
        print("All tests completed successfully!")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()