"""
Slack Bot Factory Service
Dynamically creates and manages multiple Slack bot instances, each connected to different agent endpoints
"""
import logging
import threading
from typing import Dict, Optional
import uuid
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BotInstance:
    """Represents a single Slack bot instance connected to an agent endpoint"""
    
    def __init__(self, bot_id: str, bot_token: str, app_token: str, 
                 signing_secret: str, agent_url: str, channel_id: Optional[str] = None):
        self.bot_id = bot_id
        self.bot_token = bot_token
        self.app_token = app_token
        self.signing_secret = signing_secret
        self.agent_url = agent_url
        self.channel_id = channel_id
        self.app = None
        self.handler = None
        self.thread = None
        self.running = False
        self.bot_user_id = None
        
        logger.info(f"Bot instance {bot_id} initialized for agent: {agent_url}")
    
    def _setup_handlers(self):
        """Setup Slack event handlers for this bot instance"""
        
        @self.app.event("app_mention")
        def handle_mention(event, say, client):
            self._handle_message(event, say, client, is_mention=True)
        
        @self.app.event("message")
        def handle_message(event, say, client):
            # Ignore bot messages and message changes
            if event.get("subtype") or event.get("bot_id"):
                return
            
            # Handle DMs or messages in designated channel
            channel_type = event.get("channel_type")
            channel = event.get("channel")
            
            if channel_type == "im" or (self.channel_id and channel == self.channel_id):
                self._handle_message(event, say, client, is_mention=False)
    
    def _handle_message(self, event, say, client, is_mention=False):
        """Handle incoming messages and forward to agent endpoint"""
        try:
            user = event.get("user")
            text = event.get("text", "")
            channel = event.get("channel")
            thread_ts = event.get("thread_ts") or event.get("ts")
            
            # Initialize bot user ID if not set
            if not self.bot_user_id:
                auth_response = client.auth_test()
                self.bot_user_id = auth_response["user_id"]
            
            # Clean mention from text
            if is_mention and self.bot_user_id:
                import re
                text = re.sub(f"<@{self.bot_user_id}>", "", text).strip()
            
            if not text:
                return
            
            logger.info(f"Bot {self.bot_id} received message: {text[:50]}...")
            
            # Forward to agent endpoint
            try:
                response = self._call_agent(text, user, channel, thread_ts)
                
                if response:
                    say(text=response, thread_ts=thread_ts)
                    logger.info(f"Bot {self.bot_id} sent response")
            except Exception as e:
                logger.error(f"Error calling agent for bot {self.bot_id}: {e}")
                say(
                    text="Sorry, I encountered an error processing your request.",
                    thread_ts=thread_ts
                )
        
        except Exception as e:
            logger.error(f"Error handling message for bot {self.bot_id}: {e}")
    
    def _call_agent(self, message: str, user: str, channel: str, thread_ts: str) -> str:
        """Call the agent endpoint with the message"""
        try:
            payload = {
                "message": message,
                "user_id": user,
                "channel_id": channel,
                "thread_id": thread_ts,
                "bot_id": self.bot_id
            }
            
            response = requests.post(
                self.agent_url,
                json=payload,
                timeout=30,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            data = response.json()
            return data.get("response") or data.get("message") or data.get("text", "")
        
        except Exception as e:
            logger.error(f"Agent call failed for bot {self.bot_id}: {e}")
            raise
    
    def start(self):
        """Start the bot in a separate thread"""
        if self.running:
            logger.warning(f"Bot {self.bot_id} is already running")
            return
        
        try:
            # Initialize Slack app
            self.app = App(
                token=self.bot_token,
                signing_secret=self.signing_secret
            )
            
            # Setup handlers
            self._setup_handlers()
            
            # Start in separate thread
            def run_bot():
                self.handler = SocketModeHandler(self.app, self.app_token)
                self.running = True
                logger.info(f"✅ Bot {self.bot_id} started")
                self.handler.start()
            
            self.thread = threading.Thread(target=run_bot, daemon=True)
            self.thread.start()
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to start bot {self.bot_id}: {e}")
            self.running = False
            raise
    
    def stop(self):
        """Stop the bot"""
        if not self.running:
            return
        
        try:
            if self.handler:
                self.handler.close()
            self.running = False
            logger.info(f"Bot {self.bot_id} stopped")
        except Exception as e:
            logger.error(f"Error stopping bot {self.bot_id}: {e}")


class BotFactory:
    """Factory service to create and manage multiple Slack bot instances"""
    
    def __init__(self, persist: bool = True):
        self.bots: Dict[str, BotInstance] = {}
        self.persist = persist
        if persist:
            from bot_storage import BotStorage
            self.storage = BotStorage()
        logger.info("Bot Factory initialized")
    
    def create_bot(self, bot_token: str, app_token: str, signing_secret: str,
                   agent_url: str, channel_id: Optional[str] = None,
                   bot_id: Optional[str] = None) -> str:
        """
        Create a new bot instance
        
        Args:
            bot_token: Slack bot token (xoxb-...)
            app_token: Slack app token (xapp-...)
            signing_secret: Slack signing secret
            agent_url: URL of the agent/LLM endpoint
            channel_id: Optional specific channel to monitor
            bot_id: Optional custom bot ID
            
        Returns:
            str: Bot ID
        """
        if not bot_id:
            bot_id = f"bot_{uuid.uuid4().hex[:8]}"
        
        if bot_id in self.bots:
            raise ValueError(f"Bot {bot_id} already exists")
        
        bot = BotInstance(
            bot_id=bot_id,
            bot_token=bot_token,
            app_token=app_token,
            signing_secret=signing_secret,
            agent_url=agent_url,
            channel_id=channel_id
        )
        
        self.bots[bot_id] = bot
        
        # Persist to storage if enabled
        if self.persist:
            self.storage.save_bot(
                bot_id=bot_id,
                bot_token=bot_token,
                app_token=app_token,
                signing_secret=signing_secret,
                agent_url=agent_url,
                channel_id=channel_id
            )
        
        logger.info(f"Created bot {bot_id} for agent {agent_url}")
        
        return bot_id
    
    def start_bot(self, bot_id: str):
        """Start a specific bot"""
        if bot_id not in self.bots:
            raise ValueError(f"Bot {bot_id} not found")
        
        self.bots[bot_id].start()
    
    def stop_bot(self, bot_id: str):
        """Stop a specific bot"""
        if bot_id not in self.bots:
            raise ValueError(f"Bot {bot_id} not found")
        
        self.bots[bot_id].stop()
    
    def delete_bot(self, bot_id: str):
        """Delete a bot instance"""
        if bot_id in self.bots:
            self.stop_bot(bot_id)
            del self.bots[bot_id]
            
            # Remove from storage if enabled
            if self.persist:
                self.storage.delete_bot(bot_id)
            
            logger.info(f"Deleted bot {bot_id}")
    
    def list_bots(self) -> Dict[str, dict]:
        """List all bots and their status"""
        return {
            bot_id: {
                "agent_url": bot.agent_url,
                "channel_id": bot.channel_id,
                "running": bot.running
            }
            for bot_id, bot in self.bots.items()
        }
    
    def start_all(self):
        """Start all bots"""
        for bot_id in self.bots:
            try:
                self.start_bot(bot_id)
            except Exception as e:
                logger.error(f"Failed to start bot {bot_id}: {e}")
    
    def stop_all(self):
        """Stop all bots"""
        for bot_id in self.bots:
            try:
                self.stop_bot(bot_id)
            except Exception as e:
                logger.error(f"Failed to stop bot {bot_id}: {e}")