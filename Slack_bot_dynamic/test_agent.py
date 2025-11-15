"""
Simple test agent endpoint
Mock LLM agent for testing the bot factory
"""
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/chat', methods=['POST'])
def chat():
    """Mock agent endpoint that echoes back messages"""
    data = request.get_json()
    
    message = data.get('message', '')
    user_id = data.get('user_id', 'unknown')
    bot_id = data.get('bot_id', 'unknown')
    
    # Simple echo response
    response = f"[{bot_id}] Echo: {message}"
    
    return jsonify({
        "response": response,
        "metadata": {
            "user_id": user_id,
            "bot_id": bot_id
        }
    })

if __name__ == '__main__':
    print("🧪 Starting test agent on port 8000")
    print("This is a mock agent endpoint for testing")
    app.run(host='0.0.0.0', port=8000, debug=True)