# Enhanced Ora Application with Ash.ai-like Capabilities
# Deployment-ready with semantic memory and therapeutic features

import os
import json
import uuid
import logging
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from openai import OpenAI

# Import our custom memory system
from ora_memory import OraMemory

# Initialize Flask app
app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize our semantic memory system
memory = OraMemory(db_path="ora_memory.db")

# Crisis keywords for detection
CRISIS_KEYWORDS = [
    "suicide", "kill myself", "end it all", "not worth living", 
    "hurt myself", "self harm", "cutting", "overdose", 
    "jump off", "can't go on", "want to die", "better off dead"
]

# Therapeutic techniques database
THERAPEUTIC_TECHNIQUES = {
    "anxiety": {
        "breathing": "Try the 4-7-8 breathing technique: Inhale for 4 counts, hold for 7, exhale for 8. Repeat 3-4 times.",
        "grounding": "Use the 5-4-3-2-1 technique: Name 5 things you see, 4 you can touch, 3 you hear, 2 you smell, 1 you taste.",
        "cognitive": "Challenge anxious thoughts: Is this thought realistic? What evidence supports or contradicts it?"
    },
    "depression": {
        "behavioral": "Try behavioral activation: Choose one small, enjoyable activity to do today.",
        "cognitive": "Practice gratitude: Write down 3 things you're grateful for, no matter how small.",
        "mindfulness": "Try a 5-minute body scan meditation to reconnect with the present moment."
    },
    "stress": {
        "relaxation": "Progressive muscle relaxation: Tense and release each muscle group for 5 seconds.",
        "time_management": "Break overwhelming tasks into smaller, manageable steps.",
        "mindfulness": "Take 3 mindful breaths, focusing only on the sensation of breathing."
    }
}

# Crisis resources
CRISIS_RESOURCES = {
    "US": {
        "hotline": "988 (Suicide & Crisis Lifeline)",
        "text": "Text HOME to 741741 (Crisis Text Line)",
        "chat": "suicidepreventionlifeline.org"
    },
    "UK": {
        "hotline": "116 123 (Samaritans)",
        "text": "Text SHOUT to 85258",
        "chat": "samaritans.org"
    },
    "Canada": {
        "hotline": "1-833-456-4566 (Talk Suicide Canada)",
        "text": "Text 45645",
        "chat": "talksuicide.ca"
    }
}

def detect_crisis(text):
    """Detect crisis indicators in user message"""
    text_lower = text.lower()
    crisis_score = 0
    
    for keyword in CRISIS_KEYWORDS:
        if keyword in text_lower:
            crisis_score += 1
    
    # Additional pattern detection
    if any(phrase in text_lower for phrase in ["can't take it", "no point", "give up"]):
        crisis_score += 1
    
    if crisis_score >= 2:
        return 3  # High risk
    elif crisis_score == 1:
        return 2  # Medium risk
    else:
        return 1  # Low risk

def get_crisis_response(crisis_level, country="US"):
    """Generate appropriate crisis response"""
    resources = CRISIS_RESOURCES.get(country, CRISIS_RESOURCES["US"])
    
    if crisis_level >= 3:
        return {
            "message": "I'm very concerned about what you're sharing. Your safety is the most important thing right now. Please reach out for immediate help:",
            "resources": resources,
            "immediate_action": "If you're in immediate danger, please call emergency services (911, 999, etc.) or go to your nearest emergency room."
        }
    elif crisis_level == 2:
        return {
            "message": "I hear that you're going through a really difficult time. You don't have to face this alone. Here are some resources that can help:",
            "resources": resources,
            "immediate_action": "Consider reaching out to a trusted friend, family member, or mental health professional."
        }
    else:
        return None

def classify_emotion(text):
    """Simple emotion classification using OpenAI"""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Classify the emotion in this text. Respond with only one word: anxiety, depression, anger, joy, fear, sadness, stress, or neutral."},
                {"role": "user", "content": text}
            ],
            max_tokens=10
        )
        return response.choices[0].message.content.strip().lower()
    except Exception as e:
        logger.error(f"Emotion classification error: {e}")
        return "neutral"

def generate_therapeutic_response(user_message, emotion, user_id, crisis_level):
    """Generate therapeutic response using OpenAI with semantic memory context"""
    # Get user context from semantic memory
    user_context = memory.get_user_context(user_id, query=user_message)
    
    # Crisis intervention takes priority
    if crisis_level >= 2:
        crisis_response = get_crisis_response(crisis_level)
        if crisis_response:
            return crisis_response["message"] + "\n\n" + f"Crisis Hotline: {crisis_response['resources']['hotline']}"
    
    # Build therapeutic prompt with semantic memory context
    system_prompt = f"""You are a compassionate therapeutic AI assistant. The user is experiencing {emotion}.

User context from memory:
{user_context}

Provide a therapeutic response that:
1. Validates their feelings
2. Offers gentle guidance
3. Suggests a specific coping technique
4. Encourages professional help if needed
5. Maintains hope and support

Keep responses warm, empathetic, and under 200 words."""
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=300
        )
        
        ai_response = response.choices[0].message.content.strip()
        
        # Add technique suggestion if emotion in THERAPEUTIC_TECHNIQUES
        if emotion in THERAPEUTIC_TECHNIQUES:
            techniques = THERAPEUTIC_TECHNIQUES[emotion]
            technique_key = list(techniques.keys())[0]  # Get first technique
            ai_response += f"\n\n💡 Try this technique: {techniques[technique_key]}"
        
        return ai_response
        
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return "I'm here to listen and support you. Sometimes I have technical difficulties, but your feelings are valid and important. Please consider reaching out to a mental health professional if you need immediate support."

# Flask routes
@app.route('/')
def home():
    """Render home page"""
    return render_template('index.html')

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"})

@app.route('/chat', methods=['POST'])
def chat():
    """Main chat endpoint with semantic memory and therapeutic features"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        user_id = data.get('user_id', str(uuid.uuid4()))
        
        # Detect crisis level
        crisis_level = detect_crisis(message)
        
        # Classify emotion
        emotion = classify_emotion(message)
        
        # Generate therapeutic response with semantic memory context
        response = generate_therapeutic_response(message, emotion, user_id, crisis_level)
        
        # Store conversation in semantic memory
        conversation_id = str(uuid.uuid4())
        memory.store_conversation(user_id, conversation_id, message, response, emotion, crisis_level)
        
        # Generate insights periodically (every 5 conversations)
        try:
            # This would normally be done asynchronously or on a schedule
            insights = memory.generate_user_insights(user_id, client)
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
        
        return jsonify({
            "response": response,
            "emotion": emotion,
            "user_id": user_id
        })
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        return jsonify({
            "response": "I'm here to support you. I'm having some technical issues, but please know that help is available if you need it.",
            "error": str(e)
        })

@app.route('/insights/<user_id>', methods=['GET'])
def get_insights(user_id):
    """Get therapeutic insights for user"""
    try:
        # Generate fresh insights
        insights = memory.generate_user_insights(user_id, client)
        
        return jsonify({
            "user_id": user_id,
            "insights": insights
        })
    except Exception as e:
        logger.error(f"Insights endpoint error: {e}")
        return jsonify({
            "error": str(e)
        }), 500

@app.route('/progress/<user_id>', methods=['GET'])
def get_progress(user_id):
    """Get emotional progress tracking for user"""
    try:
        # This would normally query the database for emotion trends
        # For now, we'll return a placeholder
        return jsonify({
            "user_id": user_id,
            "progress": "Progress tracking is available in the full version."
        })
    except Exception as e:
        logger.error(f"Progress endpoint error: {e}")
        return jsonify({
            "error": str(e)
        }), 500

@app.route('/therapeutic_exercise', methods=['POST'])
def get_therapeutic_exercise():
    """Get therapeutic exercise recommendation"""
    try:
        data = request.get_json()
        emotion = data.get('emotion', 'anxiety')
        
        if emotion in THERAPEUTIC_TECHNIQUES:
            techniques = THERAPEUTIC_TECHNIQUES[emotion]
            return jsonify({
                "emotion": emotion,
                "techniques": techniques
            })
        else:
            return jsonify({
                "emotion": emotion,
                "techniques": THERAPEUTIC_TECHNIQUES["anxiety"]  # Default to anxiety
            })
    except Exception as e:
        logger.error(f"Therapeutic exercise endpoint error: {e}")
        return jsonify({
            "error": str(e)
        }), 500

@app.route('/crisis_assessment', methods=['POST'])
def assess_crisis():
    """Assess crisis level in text"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        crisis_level = detect_crisis(text)
        response = get_crisis_response(crisis_level)
        
        return jsonify({
            "crisis_level": crisis_level,
            "response": response
        })
    except Exception as e:
        logger.error(f"Crisis assessment endpoint error: {e}")
        return jsonify({
            "error": str(e)
        }), 500

# Legacy endpoints for backward compatibility
@app.route('/classify', methods=['POST'])
def classify():
    """Legacy emotion classification endpoint"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        emotion = classify_emotion(text)
        
        return jsonify({
            "emotion": emotion
        })
    except Exception as e:
        logger.error(f"Classification endpoint error: {e}")
        return jsonify({
            "error": str(e)
        }), 500

@app.route('/respond', methods=['POST'])
def respond():
    """Legacy response generation endpoint"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        emotion = data.get('emotion', 'neutral')
        user_id = data.get('user_id', str(uuid.uuid4()))
        
        # Use the enhanced response generation
        response = generate_therapeutic_response(message, emotion, user_id, 1)
        
        return jsonify({
            "response": response
        })
    except Exception as e:
        logger.error(f"Response endpoint error: {e}")
        return jsonify({
            "error": str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
