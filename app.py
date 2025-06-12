from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import os
import json
import openai
from datetime import datetime
import sqlite3
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Set OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('ora_conversations.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            message TEXT,
            response TEXT,
            emotion TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            crisis_level TEXT DEFAULT 'low'
        )
    ''')
    conn.commit()
    conn.close()

# Crisis keywords for detection
CRISIS_KEYWORDS = [
    'suicide', 'kill myself', 'end it all', 'want to die', 'hurt myself',
    'self harm', 'cutting', 'overdose', 'jump off', 'hanging',
    'worthless', 'hopeless', 'can\'t go on', 'better off dead'
]

def detect_crisis(message):
    """Detect crisis indicators in user message"""
    message_lower = message.lower()
    crisis_score = 0
    
    for keyword in CRISIS_KEYWORDS:
        if keyword in message_lower:
            crisis_score += 1
    
    if crisis_score >= 2:
        return 'high'
    elif crisis_score == 1:
        return 'medium'
    else:
        return 'low'

def get_crisis_response(crisis_level):
    """Get appropriate crisis response"""
    if crisis_level == 'high':
        return """
        I'm very concerned about what you've shared. Your life has value and there are people who want to help.
        
        🚨 IMMEDIATE HELP:
        • US: Call 988 (Suicide & Crisis Lifeline)
        • UK: Call 116 123 (Samaritans)
        • Text "HELLO" to 741741 (Crisis Text Line)
        
        Please reach out to emergency services (911/999) if you're in immediate danger.
        
        You don't have to go through this alone. Professional help is available 24/7.
        """
    elif crisis_level == 'medium':
        return """
        I hear that you're going through a really difficult time. It's important that you know support is available.
        
        💙 SUPPORT RESOURCES:
        • US: 988 (Suicide & Crisis Lifeline)
        • Crisis Text Line: Text HOME to 741741
        • Online chat: suicidepreventionlifeline.org
        
        Would you like to talk about what's making things feel so difficult right now?
        """
    else:
        return None

def get_therapeutic_response(message, emotion, user_id):
    """Generate therapeutic AI response using OpenAI"""
    try:
        # Get conversation history
        conn = sqlite3.connect('ora_conversations.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT message, response FROM conversations 
            WHERE user_id = ? 
            ORDER BY timestamp DESC LIMIT 5
        ''', (user_id,))
        history = cursor.fetchall()
        conn.close()
        
        # Build context
        context = "You are Ora, a compassionate therapeutic AI companion. You provide emotional support using evidence-based techniques like CBT and mindfulness. Be empathetic, non-judgmental, and helpful.\n\n"
        
        if history:
            context += "Recent conversation history:\n"
            for msg, resp in reversed(history):
                context += f"User: {msg}\nOra: {resp}\n\n"
        
        context += f"Current user message (emotion detected: {emotion}): {message}\n\nProvide a therapeutic, supportive response:"
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": context}
            ],
            max_tokens=300,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return "I'm here to listen and support you. Sometimes I have technical difficulties, but I want you to know that your feelings are valid and you're not alone."

def classify_emotion(message):
    """Simple emotion classification"""
    message_lower = message.lower()
    
    if any(word in message_lower for word in ['sad', 'depressed', 'down', 'crying', 'tears']):
        return 'sadness'
    elif any(word in message_lower for word in ['angry', 'mad', 'furious', 'annoyed', 'frustrated']):
        return 'anger'
    elif any(word in message_lower for word in ['anxious', 'worried', 'nervous', 'scared', 'panic']):
        return 'anxiety'
    elif any(word in message_lower for word in ['happy', 'joy', 'excited', 'great', 'wonderful']):
        return 'joy'
    elif any(word in message_lower for word in ['stressed', 'overwhelmed', 'pressure', 'burden']):
        return 'stress'
    else:
        return 'neutral'

# HTML Template for the chat interface
CHAT_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ora - Therapeutic AI Companion</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh; display: flex; align-items: center; justify-content: center;
        }
        .chat-container {
            width: 90%; max-width: 800px; height: 90vh; background: white;
            border-radius: 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            display: flex; flex-direction: column; overflow: hidden;
        }
        .chat-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 20px; text-align: center;
        }
        .chat-header h1 { font-size: 2rem; margin-bottom: 5px; }
        .chat-header p { opacity: 0.9; font-size: 1rem; }
        .chat-messages {
            flex: 1; padding: 20px; overflow-y: auto; background: #f8f9fa;
        }
        .message { margin-bottom: 20px; display: flex; align-items: flex-start; }
        .message.user { justify-content: flex-end; }
        .message-content {
            max-width: 70%; padding: 15px 20px; border-radius: 20px;
            font-size: 1rem; line-height: 1.5;
        }
        .message.user .message-content {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; border-bottom-right-radius: 5px;
        }
        .message.ai .message-content {
            background: white; color: #333; border: 1px solid #e9ecef;
            border-bottom-left-radius: 5px;
        }
        .chat-input-container {
            padding: 20px; background: white; border-top: 1px solid #e9ecef;
        }
        .chat-input-form { display: flex; gap: 10px; }
        .chat-input {
            flex: 1; padding: 15px 20px; border: 2px solid #e9ecef;
            border-radius: 25px; font-size: 1rem; outline: none;
            transition: border-color 0.3s;
        }
        .chat-input:focus { border-color: #667eea; }
        .send-button {
            padding: 15px 25px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; border: none; border-radius: 25px; font-size: 1rem;
            cursor: pointer; transition: transform 0.2s;
        }
        .send-button:hover { transform: translateY(-2px); }
        .send-button:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
        .welcome-message {
            text-align: center; padding: 40px 20px; color: #666;
        }
        .welcome-message h2 { color: #333; margin-bottom: 10px; }
        .crisis-notice {
            background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 10px;
            padding: 15px; margin: 10px 0; font-size: 0.9rem; color: #856404;
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <h1>Ora</h1>
            <p>Your Therapeutic AI Companion</p>
        </div>
        
        <div class="chat-messages" id="chatMessages">
            <div class="welcome-message">
                <h2>Welcome to Ora 🌟</h2>
                <p>I'm here to listen, support, and help you through whatever you're experiencing.</p>
                <p>Feel free to share what's on your mind - I'm here for you.</p>
                
                <div class="crisis-notice">
                    <strong>Crisis Support:</strong> If you're in immediate danger, please call emergency services (911, 999, etc.) or contact a crisis hotline in your area.
                </div>
            </div>
        </div>
        
        <div class="chat-input-container">
            <form class="chat-input-form" id="chatForm">
                <input type="text" class="chat-input" id="messageInput" 
                       placeholder="Tell me what's on your mind..." autocomplete="off" required>
                <button type="submit" class="send-button" id="sendButton">Send</button>
            </form>
        </div>
    </div>

    <script>
        const chatMessages = document.getElementById('chatMessages');
        const chatForm = document.getElementById('chatForm');
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        
        let userId = 'user_' + Math.random().toString(36).substr(2, 9);
        
        function addMessage(content, isUser = false) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isUser ? 'user' : 'ai'}`;
            
            const messageContent = document.createElement('div');
            messageContent.className = 'message-content';
            messageContent.textContent = content;
            
            messageDiv.appendChild(messageContent);
            
            const welcomeMessage = chatMessages.querySelector('.welcome-message');
            if (welcomeMessage) welcomeMessage.remove();
            
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
        
        async function sendMessage(message) {
            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: message, user_id: userId })
                });
                
                if (!response.ok) throw new Error('Network response was not ok');
                
                const data = await response.json();
                return data.response || 'I apologize, but I encountered an issue. Please try again.';
            } catch (error) {
                console.error('Error:', error);
                return 'I apologize, but I encountered a technical issue. Please try again in a moment.';
            }
        }
        
        chatForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const message = messageInput.value.trim();
            if (!message) return;
            
            addMessage(message, true);
            messageInput.value = '';
            sendButton.disabled = true;
            messageInput.disabled = true;
            
            try {
                const response = await sendMessage(message);
                addMessage(response, false);
            } catch (error) {
                addMessage('I apologize, but I encountered an issue. Please try again.', false);
            } finally {
                sendButton.disabled = false;
                messageInput.disabled = false;
                messageInput.focus();
            }
        });
        
        messageInput.focus();
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    """Serve the chat interface"""
    return render_template_string(CHAT_TEMPLATE)

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "message": "Ora Therapeutic AI is running!"})

@app.route('/chat', methods=['POST'])
def chat():
    """Main chat endpoint"""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        user_id = data.get('user_id', 'anonymous')
        
        if not message:
            return jsonify({"error": "Message is required"}), 400
        
        # Classify emotion
        emotion = classify_emotion(message)
        
        # Detect crisis level
        crisis_level = detect_crisis(message)
        
        # Get crisis response if needed
        crisis_response = get_crisis_response(crisis_level)
        if crisis_response:
            response = crisis_response
        else:
            # Get therapeutic response
            response = get_therapeutic_response(message, emotion, user_id)
        
        # Store conversation
        try:
            conn = sqlite3.connect('ora_conversations.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO conversations (user_id, message, response, emotion, crisis_level)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, message, response, emotion, crisis_level))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Database error: {e}")
        
        return jsonify({
            "response": response,
            "emotion": emotion,
            "crisis_level": crisis_level,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({
            "response": "I'm here to support you. I'm experiencing some technical difficulties right now, but please know that your feelings are valid and help is available.",
            "error": str(e)
        }), 500

@app.route('/insights/<user_id>')
def get_insights(user_id):
    """Get user insights and patterns"""
    try:
        conn = sqlite3.connect('ora_conversations.db')
        cursor = conn.cursor()
        
        # Get conversation stats
        cursor.execute('''
            SELECT emotion, COUNT(*) as count 
            FROM conversations 
            WHERE user_id = ? 
            GROUP BY emotion
        ''', (user_id,))
        emotion_stats = dict(cursor.fetchall())
        
        cursor.execute('''
            SELECT COUNT(*) as total_conversations,
                   AVG(CASE WHEN crisis_level = 'high' THEN 1 ELSE 0 END) as crisis_rate
            FROM conversations 
            WHERE user_id = ?
        ''', (user_id,))
        stats = cursor.fetchone()
        
        conn.close()
        
        return jsonify({
            "user_id": user_id,
            "total_conversations": stats[0] if stats else 0,
            "crisis_rate": stats[1] if stats else 0,
            "emotion_patterns": emotion_stats,
            "generated_at": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Insights error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

