#!/usr/bin/env python3
"""
Test script for local AI engine functionality
"""

from local_ai_engine import local_ai
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_local_ai():
    """Test the local AI engine"""
    print("🔍 Testing Local AI Engine")
    print("=" * 50)
    
    # Check available models
    print("\n📦 Available Models:")
    models = local_ai.get_available_models()
    for model_id, info in models.items():
        status = "✅ Downloaded" if info['downloaded'] else "⬇️ Available for download"
        print(f"  {model_id}: {info['name']} ({info['size']}) - {status}")
    
    # Test auto-download
    print("\n⬇️ Testing Auto-Download:")
    def progress_callback(message):
        print(f"  Progress: {message}")
    
    # Try to download a model
    downloaded_model = local_ai.auto_download_best_model(progress_callback)
    if downloaded_model:
        print(f"✅ Successfully downloaded: {downloaded_model}")
        
        # Try to load the model
        if local_ai.load_model(downloaded_model):
            print(f"✅ Successfully loaded: {downloaded_model}")
            
            # Test response generation
            print("\n💬 Testing Response Generation:")
            test_questions = [
                "How do I find SQL injection vulnerabilities?",
                "What tools should I use for binary exploitation?",
                "How do I decrypt a Caesar cipher?",
                "What is the best approach for reverse engineering?"
            ]
            
            for question in test_questions:
                print(f"\nQ: {question}")
                response = local_ai.generate_response(question)
                print(f"A: {response[:200]}...")
        else:
            print("❌ Failed to load model")
    else:
        print("⚠️ No model downloaded, testing mock responses:")
        
        # Test mock responses
        test_questions = [
            "How do I find SQL injection vulnerabilities?",
            "What tools should I use for binary exploitation?"
        ]
        
        for question in test_questions:
            print(f"\nQ: {question}")
            response = local_ai.generate_response(question)
            print(f"A: {response}")
    
    # Show final status
    print(f"\n📊 Final Status:")
    print(f"  Current Model: {local_ai.current_model_id or 'None'}")
    print(f"  Context Window: {local_ai.context_window}")
    print(f"  Model Type: {type(local_ai.current_model)}")
    
    updated_models = local_ai.get_available_models()
    downloaded_count = sum(1 for info in updated_models.values() if info['downloaded'])
    print(f"  Downloaded Models: {downloaded_count}/{len(updated_models)}")

if __name__ == "__main__":
    test_local_ai()