#!/usr/bin/env python3
"""Setup script for Z.AI API key configuration."""

import os
import sys
from pathlib import Path


def setup_zai_api_key():
    """Help user set up Z.AI API key in .env file."""
    
    print("🔧 ROMA-GLM Z.AI API Key Setup")
    print("=" * 40)
    
    # Check if .env file exists
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_example.exists():
        print("❌ .env.example file not found!")
        print("Please ensure you're in the ROMA-GLM project directory.")
        return False
    
    # Create .env from example if it doesn't exist
    if not env_file.exists():
        print("📝 Creating .env file from .env.example...")
        try:
            with open(env_example, 'r') as f:
                content = f.read()
            with open(env_file, 'w') as f:
                f.write(content)
            print("✅ .env file created successfully!")
        except Exception as e:
            print(f"❌ Failed to create .env file: {e}")
            return False
    else:
        print("✅ .env file already exists")
    
    # Check if Z_AI_API_KEY is already set
    with open(env_file, 'r') as f:
        env_content = f.read()
    
    if "Z_AI_API_KEY=your_zai_api_key" not in env_content and "Z_AI_API_KEY=" in env_content:
        # Check if it has a real value (not the placeholder)
        for line in env_content.split('\n'):
            if line.startswith('Z_AI_API_KEY=') and 'your_' not in line and line.count('=') == 1:
                print("✅ Z.AI API key is already configured!")
                print(f"   Current value: Z_AI_API_KEY={'*' * 10}{line[-4:] if len(line) > 14 else ''}")
                return True
    
    print("\n📋 To get your Z.AI API key:")
    print("1. Visit: https://z.ai/manage-apikey/apikey-list")
    print("2. Sign in or create an account")
    print("3. Generate a new API key")
    print("4. Copy the API key")
    
    # Ask user to input API key
    api_key = input("\n🔑 Enter your Z.AI API key (or press Enter to skip): ").strip()
    
    if not api_key:
        print("⏭️  Skipping API key setup.")
        print("You can manually add it to .env file later:")
        print("   Z_AI_API_KEY=your_actual_api_key_here")
        return True
    
    # Update .env file with the API key
    try:
        updated_content = []
        for line in env_content.split('\n'):
            if line.startswith('Z_AI_API_KEY='):
                updated_content.append(f'Z_AI_API_KEY={api_key}')
            else:
                updated_content.append(line)
        
        with open(env_file, 'w') as f:
            f.write('\n'.join(updated_content))
        
        print("✅ Z.AI API key saved to .env file!")
        print("🎉 Setup complete! You can now use Z.AI web search.")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to save API key: {e}")
        return False


if __name__ == "__main__":
    success = setup_zai_api_key()
    
    if success:
        print("\n🚀 Next steps:")
        print("1. Test the integration:")
        print("   uv run python -m roma_glm.cli solve 'search for AI news' --config config/examples/basic/zai_websearch.yaml")
        print("\n2. Or run the integration demo:")
        print("   uv run python test_integration_demo.py")
        sys.exit(0)
    else:
        print("\n💥 Setup failed!")
        sys.exit(1)