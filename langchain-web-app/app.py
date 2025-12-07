"""
LangChain Web Application
A modern web interface for demonstrating LangChain capabilities
"""
from flask import Flask, render_template, request, jsonify, stream_with_context, Response
from flask_cors import CORS
import os
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Configure app
app.config['SECRET_KEY'] = os.urandom(24)

@app.route('/')
def index():
    """Main application page"""
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat requests"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        # For now, return a demo response
        # In production, this would integrate with LangChain
        response = {
            'message': f"Echo: {user_message}",
            'timestamp': datetime.now().isoformat(),
            'model': 'demo-mode'
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/models', methods=['GET'])
def get_models():
    """Get available LangChain models"""
    models = [
        {'id': 'gpt-3.5-turbo', 'name': 'GPT-3.5 Turbo', 'provider': 'OpenAI'},
        {'id': 'gpt-4', 'name': 'GPT-4', 'provider': 'OpenAI'},
        {'id': 'claude-3', 'name': 'Claude 3', 'provider': 'Anthropic'},
        {'id': 'llama-2', 'name': 'Llama 2', 'provider': 'Meta'},
    ]
    return jsonify(models)

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'langchain_version': '0.3.15'
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
