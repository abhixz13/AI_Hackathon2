"""
Main entry point for the Bot Factory Service
Can run as API server or load bots from configuration
"""
import os
import sys
import logging
from bot_factory import BotFactory
from bot_storage import BotStorage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_api_server():
    """Run the REST API server"""
    from api_service import app
    
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'false').lower() == 'true'
    
    logger.info(f"🚀 Starting Bot Factory API Server on port {port}")
    logger.info("API Endpoints:")
    logger.info("  POST   /bots              - Create new bot")
    logger.info("  GET    /bots              - List all bots")
    logger.info("  GET    /bots/<id>         - Get bot details")
    logger.info("  POST   /bots/<id>/start   - Start bot")
    logger.info("  POST   /bots/<id>/stop    - Stop bot")
    logger.info("  DELETE /bots/<id>         - Delete bot")
    logger.info("  POST   /bots/start-all    - Start all bots")
    logger.info("  POST   /bots/stop-all     - Stop all bots")
    
    app.run(host='0.0.0.0', port=port, debug=debug, threaded=True)


def run_from_config():
    """Load bots from storage and start them"""
    storage = BotStorage()
    factory = BotFactory()
    
    configs = storage.get_all()
    
    if not configs:
        logger.warning("No bot configurations found in storage")
        logger.info("Use API mode to create bots or add to bots_config.json")
        return
    
    logger.info(f"Loading {len(configs)} bot(s) from storage...")
    
    for bot_id, config in configs.items():
        try:
            factory.create_bot(
                bot_id=bot_id,
                bot_token=config['bot_token'],
                app_token=config['app_token'],
                signing_secret=config['signing_secret'],
                agent_url=config['agent_url'],
                channel_id=config.get('channel_id')
            )
            factory.start_bot(bot_id)
            logger.info(f"✅ Started bot {bot_id}")
        except Exception as e:
            logger.error(f"Failed to start bot {bot_id}: {e}")
    
    logger.info(f"✅ {len(factory.list_bots())} bot(s) running")
    
    # Keep running
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping all bots...")
        factory.stop_all()


def main():
    """Main entry point"""
    mode = os.getenv('MODE', 'api').lower()
    
    if mode == 'api':
        run_api_server()
    elif mode == 'standalone':
        run_from_config()
    else:
        logger.error(f"Unknown mode: {mode}. Use 'api' or 'standalone'")
        sys.exit(1)


if __name__ == "__main__":
    main()