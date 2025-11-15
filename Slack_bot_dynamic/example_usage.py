"""
Example usage of the Bot Factory API
Shows how to programmatically create Slack bots
"""
import requests
import time

# API base URL
API_BASE = "http://localhost:5000"


def create_bot_example():
    """Example: Create a new bot"""
    
    # Bot configuration
    bot_config = {
        "bot_token": "xoxb-your-slack-bot-token",
        "app_token": "xapp-your-slack-app-token",
        "signing_secret": "your-signing-secret",
        "agent_url": "https://your-agent-api.com/chat",  # Your LLM/agent endpoint
        "channel_id": "C1234567890",  # Optional: specific channel
        "bot_id": "my_custom_bot",    # Optional: custom ID
        "auto_start": True             # Start immediately
    }
    
    response = requests.post(f"{API_BASE}/bots", json=bot_config)
    
    if response.status_code == 201:
        bot_info = response.json()
        print(f"✅ Bot created: {bot_info['bot_id']}")
        return bot_info['bot_id']
    else:
        print(f"❌ Error: {response.json()}")
        return None


def list_bots_example():
    """Example: List all bots"""
    response = requests.get(f"{API_BASE}/bots")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n📋 Total bots: {data['count']}")
        for bot_id, info in data['bots'].items():
            status = "🟢 Running" if info['running'] else "🔴 Stopped"
            print(f"  {bot_id}: {status}")
            print(f"    Agent: {info['agent_url']}")
    else:
        print(f"❌ Error: {response.json()}")


def start_bot_example(bot_id: str):
    """Example: Start a bot"""
    response = requests.post(f"{API_BASE}/bots/{bot_id}/start")
    
    if response.status_code == 200:
        print(f"✅ Bot {bot_id} started")
    else:
        print(f"❌ Error: {response.json()}")


def stop_bot_example(bot_id: str):
    """Example: Stop a bot"""
    response = requests.post(f"{API_BASE}/bots/{bot_id}/stop")
    
    if response.status_code == 200:
        print(f"✅ Bot {bot_id} stopped")
    else:
        print(f"❌ Error: {response.json()}")


def delete_bot_example(bot_id: str):
    """Example: Delete a bot"""
    response = requests.delete(f"{API_BASE}/bots/{bot_id}")
    
    if response.status_code == 200:
        print(f"✅ Bot {bot_id} deleted")
    else:
        print(f"❌ Error: {response.json()}")


def create_multiple_bots_example():
    """Example: Create multiple bots for different agents"""
    
    agents = [
        {
            "bot_id": "customer_support_bot",
            "agent_url": "https://api.example.com/customer-support",
            "channel_id": "C1234567890"
        },
        {
            "bot_id": "sales_bot",
            "agent_url": "https://api.example.com/sales-agent",
            "channel_id": "C0987654321"
        },
        {
            "bot_id": "technical_bot",
            "agent_url": "https://api.example.com/technical-support",
            "channel_id": "C1122334455"
        }
    ]
    
    # Same Slack credentials for all (or you can use different workspaces)
    base_config = {
        "bot_token": "xoxb-your-token",
        "app_token": "xapp-your-token",
        "signing_secret": "your-secret",
        "auto_start": True
    }
    
    for agent in agents:
        config = {**base_config, **agent}
        response = requests.post(f"{API_BASE}/bots", json=config)
        
        if response.status_code == 201:
            print(f"✅ Created {agent['bot_id']}")
        else:
            print(f"❌ Failed to create {agent['bot_id']}: {response.json()}")
        
        time.sleep(1)  # Small delay between creations


if __name__ == "__main__":
    print("🤖 Bot Factory API Examples\n")
    print("Make sure the API service is running: python main.py")
    print("=" * 50)
    
    # Example 1: Create a single bot
    print("\n1️⃣ Creating a bot...")
    # bot_id = create_bot_example()
    
    # Example 2: List all bots
    print("\n2️⃣ Listing all bots...")
    list_bots_example()
    
    # Example 3: Create multiple bots
    print("\n3️⃣ Creating multiple bots...")
    # create_multiple_bots_example()
    
    print("\n✅ Examples completed!")