from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import os
import openai

app = Flask(__name__)
CORS(app)

# Set OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')

# Simple HTML template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Ora - Therapeutic AI</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f0f2f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 30px; }
        .header h1 { color: #4a90e2; margin: 0; }
        .header p { color: #666; margin: 5px 0; }
        .chat-area { height: 400px; border: 1px solid #ddd; border-radius: 5px; padding: 15px; overflow-y: auto; margin-bottom: 20px; background: #fafafa; }
        .message { margin: 10px 0; padding: 10px; border-radius: 5px; }
        .user-message { background: #4a90e2; color: white; text-align: right; }
        .ai-message { background: #e8f4f8; color: #333; }
        .input-area { display: flex; gap: 10px; }
        .input-area input { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
        .input-area button { padding: 10px 20px; background: #4a90e2; color: white; border: none; border-radius: 5px; cursor: pointer; }
        .input-area button:hover { background: #357abd; }
        .crisis-notice { background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin-bottom: 20px; color: #856404; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Ora</h1>
            <p>Your Therapeutic AI Companion</p>
        </div>
        
        <div class="crisis-notice">
            <strong>Crisis Support:</strong> If you're in immediate danger, please call emergency services (911, 999, etc.) or contact: US: 988, UK: 116 123, Canada: 1-833-456-4566
        </div>
        
        <div class="chat-area" id="chatArea">
            <div class="message ai-message">
                Hello! I'm Ora, your therapeutic AI companion. I'm here to listen and support you. How are you feeling today?
            </div>
        </div>
        
        <div class="input-area">
            <input type="text" id="messageInput" placeholder="Tell me what's on your mind..." onkeypress="if(event.key==='Enter') sendMessage()">
            <button onclick="sendMessage()">Send</button>
        </div>
    </div>

    <script>
        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const chatArea = document.getElementById('chatArea');
            const message = input.value.trim();
            
            if (!message) return;
            
            // Add user message
            chatArea.innerHTML += `<div class="message user-message">${message}</div>`;
            input.value = '';
            chatArea.scrollTop = chatArea.scrollHeight;
            
            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: message})
                });
                
                const data = await response.json();
                chatArea.innerHTML += `<div class="message ai-message">${data.response}</div>`;
                chatArea.scrollTop = chatArea.scrollHeight;
            } catch (error) {
                chatArea.innerHTML += `<div class="message ai-message">I'm sorry, I'm having technical difficulties. Please try again.</div>`;
            }
        }
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        message = data.get('message', '')
        
        # Crisis detection
        crisis_words = ['suicide', 'kill myself', 'want to die', 'hurt myself', 'end it all']
        is_crisis = any(word in message.lower() for word in crisis_words)
        
        if is_crisis:
            response = """I'm very concerned about what you've shared. Your life has value and there are people who want to help.

🚨 IMMEDIATE HELP:
• US: Call 988 (Suicide & Crisis Lifeline)
• UK: Call 116 123 (Samaritans)  
• Text "HELLO" to 741741 (Crisis Text Line)

Please reach out to emergency services if you're in immediate danger. You don't have to go through this alone."""
        else:
            # Get AI response
            try:
                ai_response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are Ora, a compassionate therapeutic AI companion. Provide supportive, empathetic responses using evidence-based therapeutic techniques. Be warm, understanding, and helpful."},
                        {"role": "user", "content": message}
                    ],
                    max_tokens=200,
                    temperature=0.7
                )
                response = ai_response.choices[0].message.content
            except:
                response = "I'm here to listen and support you. I'm experiencing some technical difficulties right now, but please know that your feelings are valid and you're not alone."
        
        return jsonify({"response": response})
        
    except Exception as e:
        return jsonify({"response": "I'm here to support you. I'm having some technical issues, but please know that help is available if you need it."})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)


