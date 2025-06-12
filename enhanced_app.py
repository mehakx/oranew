import os
import json
import uuid
import asyncio
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv

# Import enhanced memory and therapeutic services
from memory_api.src.cognee_service import cognee_service
from memory_api.src.therapeutic_service import therapeutic_service

load_dotenv()

# Initialize the OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

# In-memory conversation store (keeping for backward compatibility)
conversations = {}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/classify", methods=["POST"])
def classify():
    """Enhanced emotion classification with therapeutic context"""
    data = request.get_json()
    text = data.get("text", "").strip()
    user_id = data.get("user_id", f"user_{uuid.uuid4().hex[:8]}")
    
    if not text:
        return jsonify({"error": "No text"}), 400
    
    try:
        # Original emotion classification
        prompt = f"Classify the primary emotion in this text in one word (e.g. Happy, Sad, Angry, Neutral, Anxious, Fear, Excited):\n\n\"{text}\""
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=5
        )
        
        emotion = response.choices[0].message.content.strip().split()[0]
        
        # Enhanced response with therapeutic context
        return jsonify({
            "emotion": emotion,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "therapeutic_context": {
                "emotion_intensity": "moderate",  # Could be enhanced with ML model
                "requires_intervention": emotion.lower() in ["sad", "angry", "fear", "anxious"],
                "suggested_response_type": "supportive" if emotion.lower() in ["sad", "fear"] else "neutral"
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/respond", methods=["POST"])
def respond():
    """Enhanced response generation with therapeutic AI and memory integration"""
    data = request.get_json()
    emotion = data.get("emotion", "Neutral")
    text = data.get("text", "")
    user_id = data.get("user_id", f"user_{uuid.uuid4().hex[:8]}")
    
    try:
        # Get user context from Cognee
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        user_context = loop.run_until_complete(
            cognee_service.get_user_context(user_id)
        )
        
        # Generate therapeutic response
        therapeutic_response = loop.run_until_complete(
            therapeutic_service.generate_therapeutic_response(text, user_context, emotion)
        )
        
        ai_message = therapeutic_response.get("response", "I'm here to support you. How are you feeling?")
        
        # Store conversation in Cognee
        conversation_data = {
            "user_message": text,
            "ai_response": ai_message,
            "emotion": emotion,
            "emotion_intensity": 0.7,  # Could be enhanced
            "therapeutic_context": therapeutic_response.get("therapeutic_context", {}),
            "crisis_indicators": therapeutic_response.get("crisis_assessment", {}).get("indicators", []),
            "session_id": f"session_{uuid.uuid4().hex[:8]}",
            "timestamp": datetime.now().isoformat()
        }
        
        loop.run_until_complete(
            cognee_service.store_conversation(user_id, conversation_data)
        )
        
        # Create new chat session (backward compatibility)
        chat_id = uuid.uuid4().hex
        conversations[chat_id] = [
            {"role": "system", "content": "You are ORA, a compassionate therapeutic AI assistant."},
            {"role": "assistant", "content": ai_message}
        ]
        
        response_data = {
            "message": ai_message,
            "chat_id": chat_id,
            "user_id": user_id,
            "therapeutic_context": therapeutic_response.get("therapeutic_context", {}),
            "recommended_exercises": therapeutic_response.get("therapeutic_context", {}).get("recommended_exercises", []),
            "follow_up_suggestions": therapeutic_response.get("follow_up_suggestions", [])
        }
        
        # Add crisis intervention if needed
        crisis_assessment = therapeutic_response.get("crisis_assessment", {})
        if crisis_assessment.get("risk_level") == "high":
            response_data["crisis_intervention"] = {
                "risk_level": "high",
                "immediate_actions": crisis_assessment.get("recommended_actions", []),
                "crisis_resources": {
                    "national_suicide_prevention_lifeline": "988",
                    "crisis_text_line": "Text HOME to 741741"
                }
            }
        
        loop.close()
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/chat", methods=["POST"])
def chat():
    """Enhanced chat with therapeutic context"""
    data = request.get_json()
    chat_id = data.get("chat_id")
    user_msg = data.get("message", "").strip()
    user_id = data.get("user_id", "anonymous")
    
    if not chat_id or chat_id not in conversations:
        return jsonify({"error": "Invalid chat_id"}), 400
    
    try:
        # Get user context for therapeutic response
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        user_context = loop.run_until_complete(
            cognee_service.get_user_context(user_id)
        )
        
        # Classify emotion in current message
        emotion_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": f"Classify the primary emotion in this text in one word: \"{user_msg}\""}],
            temperature=0.0,
            max_tokens=5
        )
        
        current_emotion = emotion_response.choices[0].message.content.strip().split()[0]
        
        # Generate therapeutic response
        therapeutic_response = loop.run_until_complete(
            therapeutic_service.generate_therapeutic_response(user_msg, user_context, current_emotion)
        )
        
        assistant_msg = therapeutic_response.get("response")
        
        # Update conversation history
        conversations[chat_id].append({"role": "user", "content": user_msg})
        conversations[chat_id].append({"role": "assistant", "content": assistant_msg})
        
        # Store in Cognee
        conversation_data = {
            "user_message": user_msg,
            "ai_response": assistant_msg,
            "emotion": current_emotion,
            "therapeutic_context": therapeutic_response.get("therapeutic_context", {}),
            "session_id": chat_id,
            "timestamp": datetime.now().isoformat()
        }
        
        loop.run_until_complete(
            cognee_service.store_conversation(user_id, conversation_data)
        )
        
        loop.close()
        
        return jsonify({
            "reply": assistant_msg,
            "emotion_detected": current_emotion,
            "therapeutic_context": therapeutic_response.get("therapeutic_context", {}),
            "recommended_exercises": therapeutic_response.get("therapeutic_context", {}).get("recommended_exercises", [])
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# NEW THERAPEUTIC AI ENDPOINTS

@app.route("/insights/<user_id>", methods=["GET"])
def get_user_insights(user_id):
    """Get comprehensive user insights and patterns"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        insights = loop.run_until_complete(
            therapeutic_service.get_user_insights(user_id)
        )
        
        loop.close()
        return jsonify(insights)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/progress/<user_id>", methods=["GET"])
def get_user_progress(user_id):
    """Get user's therapeutic progress tracking"""
    try:
        timeframe_days = request.args.get("days", 30, type=int)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        progress = loop.run_until_complete(
            therapeutic_service.analyze_user_progress(user_id, timeframe_days)
        )
        
        loop.close()
        return jsonify(progress)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/therapeutic_exercise", methods=["POST"])
def get_therapeutic_exercise():
    """Get personalized therapeutic exercises"""
    data = request.get_json()
    user_id = data.get("user_id")
    emotion = data.get("emotion", "neutral")
    exercise_type = data.get("type", "any")  # breathing, mindfulness, cognitive, etc.
    
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        exercises = loop.run_until_complete(
            cognee_service.get_therapeutic_exercises(user_id, emotion)
        )
        
        # Filter by type if specified
        if exercise_type != "any":
            exercises = [ex for ex in exercises if ex.get("type") == exercise_type]
        
        loop.close()
        
        return jsonify({
            "exercises": exercises,
            "user_id": user_id,
            "emotion": emotion,
            "generated_at": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/proactive_checkin/<user_id>", methods=["GET"])
def get_proactive_checkin(user_id):
    """Get personalized proactive check-in message"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        checkin = loop.run_until_complete(
            cognee_service.generate_proactive_checkin(user_id)
        )
        
        loop.close()
        return jsonify(checkin)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/crisis_assessment", methods=["POST"])
def assess_crisis_risk():
    """Assess crisis risk in user message"""
    data = request.get_json()
    message = data.get("message", "")
    user_id = data.get("user_id")
    
    if not message:
        return jsonify({"error": "message is required"}), 400
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Get user context
        user_context = loop.run_until_complete(
            cognee_service.get_user_context(user_id or "anonymous")
        )
        
        # Assess crisis risk
        crisis_assessment = loop.run_until_complete(
            cognee_service.detect_crisis_indicators(message, user_context)
        )
        
        loop.close()
        
        return jsonify({
            "crisis_assessment": crisis_assessment,
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/schedule_checkin", methods=["POST"])
def schedule_checkin():
    """Schedule a proactive check-in for user"""
    data = request.get_json()
    user_id = data.get("user_id")
    checkin_type = data.get("type", "wellness")
    
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            therapeutic_service.schedule_proactive_checkin(user_id, checkin_type)
        )
        
        loop.close()
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ENHANCED MEMORY API ENDPOINTS

@app.route("/memory/context/<user_id>", methods=["GET"])
def get_memory_context(user_id):
    """Get user's memory context from Cognee"""
    try:
        limit = request.args.get("limit", 10, type=int)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        context = loop.run_until_complete(
            cognee_service.get_user_context(user_id, limit)
        )
        
        loop.close()
        return jsonify(context)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/memory/store", methods=["POST"])
def store_memory():
    """Store conversation in Cognee memory system"""
    data = request.get_json()
    user_id = data.get("user_id")
    conversation_data = data.get("conversation_data", {})
    
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        success = loop.run_until_complete(
            cognee_service.store_conversation(user_id, conversation_data)
        )
        
        loop.close()
        
        return jsonify({
            "success": success,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Health check endpoint
@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Enhanced ORA Therapeutic AI",
        "version": "2.0.0",
        "features": [
            "emotion_classification",
            "therapeutic_responses",
            "crisis_detection",
            "progress_tracking",
            "semantic_memory",
            "proactive_checkins"
        ],
        "timestamp": datetime.now().isoformat()
    })

if __name__ == "__main__":
    print("🚀 Starting Enhanced ORA Therapeutic AI...")
    print("🧠 Features: Emotion AI + Therapeutic Support + Semantic Memory")
    print("🔗 Cognee Integration: Enabled")
    print("🏥 Crisis Detection: Active")
    print("📊 Progress Tracking: Available")
    
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))