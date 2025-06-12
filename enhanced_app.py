# simplified_enhanced_app.py - Deployment-Ready Therapeutic AI
# Optimized for cloud deployment with minimal dependencies

import os
import json
import uuid
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from openai import OpenAI
import sqlite3
import schedule
import time
from threading import Thread
import logging

# Initialize Flask app
app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# In-memory storage for conversations (simplified for deployment)
conversations = {}
user_profiles = {}
therapeutic_sessions = {}

# Crisis keywords for detection
CRISIS_KEYWORDS = [
    "suicide", "kill myself", "end it all", "not worth living", 
    "hurt myself", "self harm", "cutting", "overdose", "jump off",
    "can't go on", "want to die", "better off dead"
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

def init_database():
    """Initialize SQLite database for persistent storage"""
    conn = sqlite3.connect('therapeutic_ai.db')
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            message TEXT,
            response TEXT,
            emotion TEXT,
            timestamp DATETIME,
            crisis_level INTEGER
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_profiles (
            user_id TEXT PRIMARY KEY,
            name TEXT,
            preferences TEXT,
            created_at DATETIME,
            last_active DATETIME
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS therapeutic_sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            session_type TEXT,
            techniques_used TEXT,
            effectiveness_rating INTEGER,
            timestamp DATETIME
        )
    ''')
    
    conn.commit()
    conn.close()

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
    """Generate therapeutic response using OpenAI with context"""
    
    # Get user context
    user_context = get_user_context(user_id)
    
    # Crisis intervention takes priority
    if crisis_level >= 2:
        crisis_response = get_crisis_response(crisis_level)
        if crisis_response:
            return crisis_response["message"] + "\n\n" + f"Crisis Hotline: {crisis_response['resources']['hotline']}"
    
    # Build therapeutic prompt
    system_prompt = f"""You are a compassionate therapeutic AI assistant. The user is experiencing {emotion}. 
    
    User context: {user_context}
    
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
        
        # Add technique suggestion
        if emotion in THERAPEUTIC_TECHNIQUES:
            techniques = THERAPEUTIC_TECHNIQUES[emotion]
            technique_key = list(techniques.keys())[0]  # Get first technique
            ai_response += f"\n\n💡 Try this technique: {techniques[technique_key]}"
        
        return ai_response
        
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return "I'm here to listen and support you. Sometimes I have technical difficulties, but your feelings are valid and important. Please consider reaching out to a mental health professional if you need immediate support."

def get_user_context(user_id):
    """Get recent conversation context for user"""
    if user_id in conversations:
        recent_conversations = conversations[user_id][-3:]  # Last 3 conversations
        context = "Recent conversations: "
        for conv in recent_conversations:
            context += f"User felt {conv.get('emotion', 'neutral')}. "
        return context
    return "New user, no previous context."

def store_conversation(user_id, user_message, ai_response, emotion, crisis_level):
    """Store conversation in memory and database"""
    conversation_id = str(uuid.uuid4())
    timestamp = datetime.now()
    
    # Store in memory
    if user_id not in conversations:
        conversations[user_id] = []
    
    conversations[user_id].append({
        "id": conversation_id,
        "user_message": user_message,
        "ai_response": ai_response,
        "emotion": emotion,
        "crisis_level": crisis_level,
        "timestamp": timestamp
    })
    
    # Store in database
    try:
        conn = sqlite3.connect('therapeutic_ai.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO conversations (id, user_id, message, response, emotion, timestamp, crisis_level)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (conversation_id, user_id, user_message, ai_response, emotion, timestamp, crisis_level))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Database storage error: {e}")

# Routes
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/health")
def health_check():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route("/classify", methods=["POST"])
def classify():
    """Enhanced emotion classification with therapeutic context"""
    try:
        data = request.get_json()
        text = data.get("text", "").strip()
        user_id = data.get("user_id", f"user_{uuid.uuid4().hex[:8]}")
        
        if not text:
            return jsonify({"error": "No text provided"}), 400
        
        # Classify emotion
        emotion = classify_emotion(text)
        
        # Detect crisis level
        crisis_level = detect_crisis(text)
        
        return jsonify({
            "emotion": emotion,
            "crisis_level": crisis_level,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Classification error: {e}")
        return jsonify({"error": "Classification failed"}), 500

@app.route("/respond", methods=["POST"])
def respond():
    """Generate therapeutic AI response"""
    try:
        data = request.get_json()
        user_message = data.get("text", "").strip()
        user_id = data.get("user_id", f"user_{uuid.uuid4().hex[:8]}")
        emotion = data.get("emotion", "neutral")
        
        if not user_message:
            return jsonify({"error": "No message provided"}), 400
        
        # Detect crisis level
        crisis_level = detect_crisis(user_message)
        
        # Generate therapeutic response
        ai_response = generate_therapeutic_response(user_message, emotion, user_id, crisis_level)
        
        # Store conversation
        store_conversation(user_id, user_message, ai_response, emotion, crisis_level)
        
        return jsonify({
            "response": ai_response,
            "emotion": emotion,
            "crisis_level": crisis_level,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Response generation error: {e}")
        return jsonify({"error": "Response generation failed"}), 500

@app.route("/chat", methods=["POST"])
def chat():
    """Combined classification and response endpoint"""
    try:
        data = request.get_json()
        user_message = data.get("message", "").strip()
        user_id = data.get("user_id", f"user_{uuid.uuid4().hex[:8]}")
        
        if not user_message:
            return jsonify({"error": "No message provided"}), 400
        
        # Classify emotion
        emotion = classify_emotion(user_message)
        
        # Detect crisis level
        crisis_level = detect_crisis(user_message)
        
        # Generate therapeutic response
        ai_response = generate_therapeutic_response(user_message, emotion, user_id, crisis_level)
        
        # Store conversation
        store_conversation(user_id, user_message, ai_response, emotion, crisis_level)
        
        return jsonify({
            "message": user_message,
            "response": ai_response,
            "emotion": emotion,
            "crisis_level": crisis_level,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({"error": "Chat processing failed"}), 500

@app.route("/insights/<user_id>")
def get_insights(user_id):
    """Get user insights and patterns"""
    try:
        if user_id not in conversations:
            return jsonify({"error": "User not found"}), 404
        
        user_conversations = conversations[user_id]
        
        # Analyze patterns
        emotions = [conv.get("emotion", "neutral") for conv in user_conversations]
        emotion_counts = {}
        for emotion in emotions:
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        # Calculate trends
        recent_emotions = emotions[-5:] if len(emotions) >= 5 else emotions
        crisis_levels = [conv.get("crisis_level", 1) for conv in user_conversations]
        avg_crisis_level = sum(crisis_levels) / len(crisis_levels) if crisis_levels else 1
        
        return jsonify({
            "user_id": user_id,
            "total_conversations": len(user_conversations),
            "emotion_patterns": emotion_counts,
            "recent_emotions": recent_emotions,
            "average_crisis_level": round(avg_crisis_level, 2),
            "last_conversation": user_conversations[-1]["timestamp"].isoformat() if user_conversations else None
        })
        
    except Exception as e:
        logger.error(f"Insights error: {e}")
        return jsonify({"error": "Failed to generate insights"}), 500

@app.route("/therapeutic_exercise", methods=["POST"])
def get_therapeutic_exercise():
    """Get personalized therapeutic exercise"""
    try:
        data = request.get_json()
        emotion = data.get("emotion", "neutral")
        user_id = data.get("user_id")
        
        if emotion in THERAPEUTIC_TECHNIQUES:
            techniques = THERAPEUTIC_TECHNIQUES[emotion]
            return jsonify({
                "emotion": emotion,
                "techniques": techniques,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "emotion": emotion,
                "techniques": {
                    "general": "Take a moment to breathe deeply and be present with your feelings. Remember that all emotions are temporary and valid."
                },
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            })
            
    except Exception as e:
        logger.error(f"Therapeutic exercise error: {e}")
        return jsonify({"error": "Failed to get exercise"}), 500

if __name__ == "__main__":
    # Initialize database
    init_database()
    
    # Start the application
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)


        
