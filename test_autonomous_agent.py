#!/usr/bin/env python3
"""
Quick test script for autonomous crypto trading agent setup.

This script will:
1. Start the ROMA-GLM API server with autonomous agent
2. Test basic agent functionality
3. Demonstrate agent control via CLI and API
"""

import asyncio
import subprocess
import sys
import time
from pathlib import Path

import httpx
from loguru import logger


async def test_api_server():
    """Test if API server is running."""
    try:
        response = httpx.get("http://localhost:8000/health", timeout=5.0)
        if response.status_code == 200:
            logger.success("✅ API server is running")
            return True
    except Exception as e:
        logger.warning(f"❌ API server not accessible: {e}")
    return False


async def test_agent_status():
    """Test agent status endpoint."""
    try:
        response = httpx.get("http://localhost:8000/api/v1/agent/status", timeout=10.0)
        if response.status_code == 200:
            data = response.json()
            logger.success("✅ Agent status endpoint working")

            # Display key info
            agent_data = data["data"]
            logger.info(f"🤖 Agent ID: {agent_data['agent_id']}")
            logger.info(f"🏃 Running: {'Yes' if agent_data['running'] else 'No'}")
            logger.info(
                f"💰 Portfolio Value: ${agent_data['agent_state']['portfolio']['total_value']:.2f}"
            )
            logger.info(
                f"📊 Total P&L: {agent_data['agent_state']['portfolio']['total_pnl_percent']:.2f}%"
            )

            return True
        else:
            logger.error(f"❌ Agent status returned: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Agent status failed: {e}")
    return False


async def test_agent_control():
    """Test agent control endpoints."""
    try:
        # Test portfolio endpoint
        response = httpx.get(
            "http://localhost:8000/api/v1/agent/portfolio", timeout=10.0
        )
        if response.status_code == 200:
            logger.success("✅ Portfolio endpoint working")
            data = response.json()
            portfolio = data["data"]["portfolio"]
            logger.info(f"💵 Cash: ${portfolio['cash']:.2f}")
            logger.info(
                f"📈 Positions: {data['data']['performance']['positions_count']}"
            )
        else:
            logger.error(f"❌ Portfolio endpoint returned: {response.status_code}")

        return True
    except Exception as e:
        logger.error(f"❌ Agent control test failed: {e}")
    return False


def setup_environment():
    """Setup development environment."""
    logger.info("🔧 Setting up development environment...")

    # Install dependencies
    try:
        subprocess.run(
            [sys.executable, "-m", "uv", "pip", "install", "-e", ".[agent]"],
            check=True,
            capture_output=True,
        )
        logger.success("✅ Dependencies installed")
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to install dependencies: {e}")
        return False

    return True


def start_api_server():
    """Start API server in background."""
    logger.info("🚀 Starting ROMA-GLM API server...")

    try:
        # Start server in background
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "roma_glm.api.main:app",
                "--host",
                "0.0.0.0",
                "--port",
                "8000",
                "--reload",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Wait a bit for server to start
        time.sleep(5)

        # Check if process is still running
        if process.poll() is None:
            logger.success("✅ API server started in background")
            return process
        else:
            stdout, stderr = process.communicate()
            logger.error(f"❌ API server failed to start")
            logger.error(f"STDOUT: {stdout.decode()}")
            logger.error(f"STDERR: {stderr.decode()}")
            return None

    except Exception as e:
        logger.error(f"❌ Failed to start API server: {e}")
        return None


async def run_tests():
    """Run all tests."""
    logger.info("🧪 Running autonomous agent tests...")

    # Test API server
    if not await test_api_server():
        logger.error("❌ Please start the API server first:")
        logger.error(
            "   uv run uvicorn roma_glm.api.main:app --host 0.0.0.0 --port 8000"
        )
        return False

    # Test agent status
    if not await test_agent_status():
        logger.error("❌ Agent status test failed")
        return False

    # Test agent control
    if not await test_agent_control():
        logger.error("❌ Agent control test failed")
        return False

    logger.success("✅ All tests passed!")
    return True


def show_usage_examples():
    """Show usage examples."""
    print("\n" + "=" * 60)
    print("🚀 AUTONOMOUS AGENT USAGE EXAMPLES")
    print("=" * 60)

    print("\n📋 CLI Commands:")
    print("  # Check agent status")
    print("  uv run python -m roma_glm agent status")
    print()
    print("  # Start agent")
    print("  uv run python -m roma_glm agent start")
    print()
    print("  # Get portfolio details")
    print("  uv run python -m roma_glm agent portfolio")
    print()
    print("  # Force manual trade")
    print("  uv run python -m roma_glm agent trade BTCUSDT buy 0.01")
    print()

    print("\n🌐 API Endpoints:")
    print("  # Agent status")
    print("  curl http://localhost:8000/api/v1/agent/status")
    print()
    print("  # Start agent")
    print("  curl -X POST http://localhost:8000/api/v1/agent/start")
    print()
    print("  # Get portfolio")
    print("  curl http://localhost:8000/api/v1/agent/portfolio")
    print()
    print("  # Manual trade")
    print("  curl -X POST http://localhost:8000/api/v1/agent/force-trade \\")
    print('       -H "Content-Type: application/json" \\')
    print('       -d \'{"symbol":"BTCUSDT","action":"buy","quantity":0.01}\'')
    print()

    print("\n🔧 Development:")
    print("  # Start API server with agent")
    print("  uv run uvicorn roma_glm.api.main:app --reload")
    print()
    print("  # View logs")
    print("  docker-compose logs -f roma-api")
    print()

    print("\n⚡ What the agent does:")
    print("  • Runs market analysis every 5 minutes")
    print("  • Monitors price changes in real-time")
    print("  • Executes trades based on alerts and analysis")
    print("  • Manages portfolio with risk controls")
    print("  • Persists state to PostgreSQL")
    print()


async def main():
    """Main function."""
    print("🤖 ROMA-GLM Autonomous Crypto Trading Agent Test")
    print("=" * 50)

    # Setup environment
    if not setup_environment():
        sys.exit(1)

    # Option to start server
    if len(sys.argv) > 1 and sys.argv[1] == "--start-server":
        server_process = start_api_server()
        if not server_process:
            sys.exit(1)

        # Wait a bit more for full startup
        time.sleep(10)

    # Run tests
    success = await run_tests()

    # Show usage examples
    show_usage_examples()

    if success:
        logger.success("🎉 Autonomous agent setup complete!")
    else:
        logger.error("❌ Setup failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
