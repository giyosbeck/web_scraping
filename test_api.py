#!/usr/bin/env python3
"""
Simple test to verify OpenRouter API key and connection.
"""
import requests
import json

def test_openrouter_api():
    api_key = "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"
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'model': 'deepseek/deepseek-r1:free',
        'messages': [
            {'role': 'system', 'content': 'You are a helpful assistant.'},
            {'role': 'user', 'content': 'Say hello and return only valid JSON: {"message": "hello"}'}
        ],
        'max_tokens': 4000,  # Increased for reasoning models
        'temperature': 0.1
    }
    
    try:
        print("🔄 Testing OpenRouter API...")
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"📊 Status code: {response.status_code}")
        print(f"📝 Response headers: {dict(response.headers)}")
        print(f"📄 Raw response: {response.text[:500]}...")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success! AI response: {result}")
            if 'choices' in result and len(result['choices']) > 0:
                ai_message = result['choices'][0]['message']['content']
                print(f"🤖 AI said: {ai_message}")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            
    except requests.RequestException as e:
        print(f"❌ Request error: {e}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_openrouter_api() 