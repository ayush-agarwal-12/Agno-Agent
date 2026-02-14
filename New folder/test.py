"""
Test script for the Agno Streaming Chat API

This script demonstrates:
1. Single message request
2. Session-based conversation with memory
3. Streaming response handling
"""

import requests
import json
import time


API_URL = "http://localhost:8000"


def print_separator():
    print("\n" + "="*80 + "\n")


def test_api_health():
    """Test if the API is running"""
    print("Testing API health...")
    try:
        response = requests.get(f"{API_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"API is healthy! Active sessions: {data['active_sessions']}")
            return True
        else:
            print(f"API health check failed with status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("Could not connect to API. Make sure the server is running!")
        print("   Run: python main.py")
        return False


def chat_streaming(message, session_id=None):
    """
    Send a message and receive streaming response
    
    Args:
        message: The message to send
        session_id: Optional session ID for conversation continuity
    """
    print(f"\nUser: {message}")
    print("Assistant: ", end="", flush=True)
    
    try:
        response = requests.post(
            f"{API_URL}/chat",
            json={
                "message": message,
                "session_id": session_id
            },
            stream=True,
            timeout=60
        )
        
        if response.status_code != 200:
            print(f"\nError: HTTP {response.status_code}")
            print(response.text)
            return None
        
        full_response = ""
        actual_session_id = None
        
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    try:
                        data = json.loads(line[6:])
                        
                        if data.get('type') == 'start':
                            actual_session_id = data.get('session_id')
                            
                        elif data.get('type') == 'token':
                            content = data.get('content', '')
                            full_response += content
                            print(content, end="", flush=True)
                            
                        elif data.get('type') == 'error':
                            print(f"\nError: {data.get('error')}")
                            
                        elif data.get('type') == 'done':
                            print()  # New line after response
                            
                    except json.JSONDecodeError as e:
                        # Skip malformed JSON
                        pass
        
        return actual_session_id
        
    except requests.exceptions.Timeout:
        print("\nRequest timed out")
        return None
    except Exception as e:
        print(f"\nError: {e}")
        return None


def test_conversation_memory():
    """Test 1: Conversation with memory"""
    print_separator()
    print("TEST 1: Conversation with Memory")
    print_separator()
    
    session_id = f"test_session_{int(time.time())}"
    
    # First message
    print(f"Session ID: {session_id}")
    session_id = chat_streaming(
        "Tell me about Python programming language in one sentence.",
        session_id=session_id
    )
    
    time.sleep(1)
    
    # Follow-up question - should remember context
    print("\nFollow-up question (testing memory)...")
    chat_streaming(
        "What are its main advantages?",
        session_id=session_id
    )
    
    time.sleep(1)
    
    # Another follow-up
    print("\nAnother follow-up...")
    chat_streaming(
        "Can you give me a simple example?",
        session_id=session_id
    )


def test_research_task():
    """Test 2: Complex research task"""
    print_separator()
    print("TEST 2: Complex Research Task")
    print_separator()
    
    chat_streaming(
        "Research and summarize the key features of the Groq LLM inference engine. "
        "Include information about its speed and performance."
    )


def get_session_history(session_id):
    """Get conversation history for a session"""
    try:
        response = requests.get(f"{API_URL}/session/{session_id}")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to get session: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error getting session: {e}")
        return None


def list_all_sessions():
    """List all active sessions"""
    print_separator()
    print("Active Sessions")
    print_separator()
    
    try:
        response = requests.get(f"{API_URL}/sessions")
        if response.status_code == 200:
            data = response.json()
            sessions = data.get('sessions', [])
            
            if not sessions:
                print("No active sessions found.")
            else:
                for session in sessions:
                    print(f"Session: {session['session_id']}")
                    print(f"  Messages: {session['message_count']}")
                    print(f"  Last activity: {session['last_message']}")
                    print()
        else:
            print(f"Failed to list sessions: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("Agno Streaming Chat API - Test Suite")
    print("="*80)
    
    # Check if API is running
    if not test_api_health():
        return
    
    # Run tests
    try:
        test_conversation_memory()
        time.sleep(2)
        
        test_research_task()
        time.sleep(2)
        
        list_all_sessions()
        
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
    
    print_separator()
    print("Test suite completed!")
    print_separator()


if __name__ == "__main__":
    main()