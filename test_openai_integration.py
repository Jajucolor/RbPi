#!/usr/bin/env python3
"""
OpenAI Integration Test
Test OpenAI API compatibility for INTA AI
"""

import json
from pathlib import Path

def test_openai_import():
    """Test OpenAI import and version detection"""
    print("Testing OpenAI import...")
    
    try:
        # Try new API first
        from openai import OpenAI
        print("✅ New OpenAI API (1.0.0+) available")
        
        # Test client creation
        client = OpenAI(api_key="test-key")
        print("✅ OpenAI client created successfully")
        
        return "new"
        
    except ImportError:
        print("❌ New OpenAI API not available")
        
        try:
            # Try old API
            import openai
            print("✅ Old OpenAI API (< 1.0.0) available")
            return "old"
            
        except ImportError:
            print("❌ OpenAI not installed")
            return None

def test_openai_config():
    """Test OpenAI configuration loading"""
    print("\nTesting OpenAI configuration...")
    
    config_path = Path("config.json")
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        openai_config = config.get('openai', {})
        api_key = openai_config.get('api_key', '')
        model = openai_config.get('model', 'gpt-4o-mini')
        
        if api_key and api_key != "your-openai-api-key-here":
            print(f"✅ OpenAI API key configured")
            print(f"✅ Model: {model}")
            return True
        else:
            print("⚠️  OpenAI API key not configured")
            print("   Add your API key to config.json to test full functionality")
            return False
    else:
        print("❌ config.json not found")
        return False

def test_openai_compatibility():
    """Test OpenAI API compatibility"""
    print("\nTesting OpenAI API compatibility...")
    
    api_type = test_openai_import()
    if not api_type:
        print("❌ OpenAI not available")
        return False
    
    config_ok = test_openai_config()
    
    if api_type == "new":
        print("✅ Using new OpenAI API (1.0.0+)")
        print("   This is the recommended version")
    elif api_type == "old":
        print("⚠️  Using old OpenAI API (< 1.0.0)")
        print("   Consider upgrading: pip install --upgrade openai")
    
    if config_ok:
        print("✅ OpenAI integration ready for testing")
        return True
    else:
        print("⚠️  OpenAI integration available but not configured")
        return False

def test_simple_query():
    """Test a simple OpenAI query (if configured)"""
    print("\nTesting simple OpenAI query...")
    
    config_path = Path("config.json")
    if not config_path.exists():
        print("❌ config.json not found")
        return False
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    api_key = config.get('openai', {}).get('api_key', '')
    if not api_key or api_key == "your-openai-api-key-here":
        print("⚠️  No valid API key configured")
        return False
    
    try:
        # Test with new API
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": "Say 'Hello from INTA AI'"}
            ],
            max_tokens=50
        )
        
        result = response.choices[0].message.content.strip()
        print(f"✅ OpenAI query successful: '{result}'")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI query failed: {str(e)}")
        return False

def main():
    """Main test function"""
    print("=" * 50)
    print("🤖 OpenAI Integration Test for INTA AI")
    print("=" * 50)
    
    # Test basic compatibility
    compatibility_ok = test_openai_compatibility()
    
    if compatibility_ok:
        # Test actual query if configured
        query_ok = test_simple_query()
        
        if query_ok:
            print("\n🎉 OpenAI integration is working perfectly!")
        else:
            print("\n⚠️  OpenAI integration available but query failed")
    else:
        print("\n❌ OpenAI integration not available")
    
    print("\n" + "=" * 50)
    print("Next steps:")
    print("• Configure OpenAI API key in config.json")
    print("• Run: python test_inta_ai.py")
    print("• Run: python demo_inta.py")

if __name__ == "__main__":
    main() 