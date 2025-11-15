"""
REST API Service for Bot Factory
Exposes endpoints to dynamically create and manage Slack bots
"""
from flask import Flask, request, jsonify
import logging
from bot_factory import BotFactory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
bot_factory = BotFactory()


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok", "service": "slack-bot-factory"}), 200


@app.route('/bots', methods=['POST'])
def create_bot():
    """
    Create a new bot instance
    
    Request body:
    {
        "bot_token": "xoxb-...",
        "app_token": "xapp-...",
        "signing_secret": "...",
        "agent_url": "https://your-agent.com/api",
        "channel_id": "C1234567890",  // optional
        "bot_id": "custom_bot_id",    // optional
        "auto_start": true             // optional, default false
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['bot_token', 'app_token', 'signing_secret', 'agent_url']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return jsonify({
                "error": f"Missing required fields: {', '.join(missing_fields)}"
            }), 400
        
        # Create bot
        bot_id = bot_factory.create_bot(
            bot_token=data['bot_token'],
            app_token=data['app_token'],
            signing_secret=data['signing_secret'],
            agent_url=data['agent_url'],
            channel_id=data.get('channel_id'),
            bot_id=data.get('bot_id')
        )
        
        # Auto-start if requested
        if data.get('auto_start', False):
            bot_factory.start_bot(bot_id)
        
        return jsonify({
            "bot_id": bot_id,
            "status": "created",
            "agent_url": data['agent_url']
        }), 201
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error creating bot: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/bots', methods=['GET'])
def list_bots():
    """List all bot instances"""
    try:
        bots = bot_factory.list_bots()
        return jsonify({"bots": bots, "count": len(bots)}), 200
    except Exception as e:
        logger.error(f"Error listing bots: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/bots/<bot_id>', methods=['GET'])
def get_bot(bot_id):
    """Get specific bot details"""
    try:
        bots = bot_factory.list_bots()
        if bot_id not in bots:
            return jsonify({"error": "Bot not found"}), 404
        
        return jsonify({"bot_id": bot_id, **bots[bot_id]}), 200
    except Exception as e:
        logger.error(f"Error getting bot: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/bots/<bot_id>/start', methods=['POST'])
def start_bot(bot_id):
    """Start a bot"""
    try:
        bot_factory.start_bot(bot_id)
        return jsonify({"bot_id": bot_id, "status": "started"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/bots/<bot_id>/stop', methods=['POST'])
def stop_bot(bot_id):
    """Stop a bot"""
    try:
        bot_factory.stop_bot(bot_id)
        return jsonify({"bot_id": bot_id, "status": "stopped"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error(f"Error stopping bot: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/bots/<bot_id>', methods=['DELETE'])
def delete_bot(bot_id):
    """Delete a bot"""
    try:
        bot_factory.delete_bot(bot_id)
        return jsonify({"bot_id": bot_id, "status": "deleted"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error(f"Error deleting bot: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/bots/start-all', methods=['POST'])
def start_all_bots():
    """Start all bots"""
    try:
        bot_factory.start_all()
        return jsonify({"status": "all bots started"}), 200
    except Exception as e:
        logger.error(f"Error starting all bots: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/bots/stop-all', methods=['POST'])
def stop_all_bots():
    """Stop all bots"""
    try:
        bot_factory.stop_all()
        return jsonify({"status": "all bots stopped"}), 200
    except Exception as e:
        logger.error(f"Error stopping all bots: {e}")
        return jsonify({"error": "Internal server error"}), 500


if __name__ == '__main__':
    import os
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'false').lower() == 'true'
    
    logger.info(f"🚀 Starting Bot Factory API on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug, threaded=True)