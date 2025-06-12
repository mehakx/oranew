import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import cognee
from dataclasses import dataclass
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class EmotionalContext:
    emotion: str
    intensity: float
    timestamp: datetime
    triggers: List[str]
    coping_strategies: List[str]

@dataclass
class TherapeuticInsight:
    pattern_type: str
    description: str
    confidence: float
    recommendations: List[str]
    created_at: datetime

class CogneeMemoryService:
    def __init__(self):
        """Initialize Cognee memory service with therapeutic capabilities"""
        self.setup_cognee()
        
    def setup_cognee(self):
        """Setup Cognee with proper configuration"""
        try:
            # Initialize Cognee
            cognee.config.set_llm_api_key(os.getenv("OPENAI_API_KEY"))
            cognee.config.set_vector_db_url("sqlite:///cognee_memory.db")
            logger.info("✅ Cognee initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Cognee: {e}")
            raise

    async def store_conversation(self, user_id: str, conversation_data: Dict) -> bool:
        """Store conversation with emotional and therapeutic context"""
        try:
            # Prepare conversation document with metadata
            document = {
                "user_id": user_id,
                "timestamp": conversation_data.get("timestamp", datetime.now().isoformat()),
                "user_message": conversation_data.get("user_message", ""),
                "ai_response": conversation_data.get("ai_response", ""),
                "emotion": conversation_data.get("emotion", "neutral"),
                "emotion_intensity": conversation_data.get("emotion_intensity", 0.5),
                "therapeutic_context": conversation_data.get("therapeutic_context", {}),
                "crisis_indicators": conversation_data.get("crisis_indicators", []),
                "session_id": conversation_data.get("session_id", ""),
                "conversation_type": "therapeutic_chat"
            }
            
            # Add to Cognee
            await cognee.add([document])
            await cognee.cognify()
            
            logger.info(f"✅ Stored conversation for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to store conversation: {e}")
            return False

    async def get_user_context(self, user_id: str, limit: int = 10) -> Dict:
        """Retrieve comprehensive user context with therapeutic insights"""
        try:
            # Query for user's conversation history
            query = f"conversations for user {user_id} emotional patterns therapeutic insights"
            
            search_results = await cognee.search("SIMILARITY", query)
            
            # Process results to extract meaningful context
            context = {
                "user_id": user_id,
                "recent_conversations": [],
                "emotional_patterns": {},
                "therapeutic_insights": [],
                "crisis_history": [],
                "progress_indicators": {},
                "recommended_interventions": []
            }
            
            for result in search_results[:limit]:
                if hasattr(result, 'payload') and result.payload.get('user_id') == user_id:
                    conversation = result.payload
                    context["recent_conversations"].append({
                        "timestamp": conversation.get("timestamp"),
                        "emotion": conversation.get("emotion"),
                        "intensity": conversation.get("emotion_intensity"),
                        "message": conversation.get("user_message", "")[:100] + "..."
                    })
            
            # Analyze emotional patterns
            context["emotional_patterns"] = await self._analyze_emotional_patterns(user_id)
            
            # Generate therapeutic insights
            context["therapeutic_insights"] = await self._generate_therapeutic_insights(user_id)
            
            return context
            
        except Exception as e:
            logger.error(f"❌ Failed to get user context: {e}")
            return {"user_id": user_id, "error": str(e)}

    async def _analyze_emotional_patterns(self, user_id: str) -> Dict:
        """Analyze user's emotional patterns over time"""
        try:
            query = f"emotional patterns trends for user {user_id}"
            results = await cognee.search("SIMILARITY", query)
            
            patterns = {
                "dominant_emotions": {},
                "emotional_volatility": 0.0,
                "improvement_trend": "stable",
                "trigger_patterns": [],
                "time_patterns": {}
            }
            
            emotions = []
            timestamps = []
            
            for result in results:
                if hasattr(result, 'payload') and result.payload.get('user_id') == user_id:
                    emotion = result.payload.get('emotion', 'neutral')
                    timestamp = result.payload.get('timestamp')
                    
                    emotions.append(emotion)
                    timestamps.append(timestamp)
            
            # Calculate dominant emotions
            if emotions:
                emotion_counts = {}
                for emotion in emotions:
                    emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
                
                total = len(emotions)
                patterns["dominant_emotions"] = {
                    emotion: count/total for emotion, count in emotion_counts.items()
                }
            
            return patterns
            
        except Exception as e:
            logger.error(f"❌ Failed to analyze emotional patterns: {e}")
            return {}

    async def _generate_therapeutic_insights(self, user_id: str) -> List[TherapeuticInsight]:
        """Generate therapeutic insights based on conversation history"""
        try:
            query = f"therapeutic insights recommendations for user {user_id}"
            results = await cognee.search("SIMILARITY", query)
            
            insights = []
            
            # Analyze conversation patterns for therapeutic insights
            conversation_themes = []
            crisis_indicators = []
            
            for result in results:
                if hasattr(result, 'payload') and result.payload.get('user_id') == user_id:
                    payload = result.payload
                    conversation_themes.append(payload.get('user_message', ''))
                    crisis_indicators.extend(payload.get('crisis_indicators', []))
            
            # Generate insights based on patterns
            if conversation_themes:
                insights.append(TherapeuticInsight(
                    pattern_type="communication_style",
                    description="User shows consistent patterns in emotional expression",
                    confidence=0.8,
                    recommendations=[
                        "Continue encouraging open emotional expression",
                        "Introduce mindfulness techniques for emotional regulation"
                    ],
                    created_at=datetime.now()
                ))
            
            if crisis_indicators:
                insights.append(TherapeuticInsight(
                    pattern_type="crisis_risk",
                    description="Detected potential crisis indicators in recent conversations",
                    confidence=0.9,
                    recommendations=[
                        "Implement immediate safety check protocols",
                        "Provide crisis intervention resources",
                        "Schedule more frequent check-ins"
                    ],
                    created_at=datetime.now()
                ))
            
            return insights
            
        except Exception as e:
            logger.error(f"❌ Failed to generate therapeutic insights: {e}")
            return []

    async def detect_crisis_indicators(self, message: str, user_context: Dict) -> Dict:
        """Detect crisis indicators in user messages"""
        crisis_keywords = [
            "suicide", "kill myself", "end it all", "not worth living",
            "hurt myself", "self-harm", "cutting", "overdose",
            "hopeless", "no point", "give up", "can't go on"
        ]
        
        message_lower = message.lower()
        detected_indicators = []
        
        for keyword in crisis_keywords:
            if keyword in message_lower:
                detected_indicators.append(keyword)
        
        risk_level = "low"
        if len(detected_indicators) > 0:
            risk_level = "high" if len(detected_indicators) > 2 else "medium"
        
        return {
            "risk_level": risk_level,
            "indicators": detected_indicators,
            "immediate_intervention_needed": risk_level == "high",
            "recommended_actions": self._get_crisis_recommendations(risk_level)
        }

    def _get_crisis_recommendations(self, risk_level: str) -> List[str]:
        """Get crisis intervention recommendations based on risk level"""
        if risk_level == "high":
            return [
                "Immediate safety assessment required",
                "Provide crisis hotline numbers",
                "Encourage immediate professional help",
                "Stay with user until safety is ensured"
            ]
        elif risk_level == "medium":
            return [
                "Gentle safety check",
                "Provide support resources",
                "Schedule follow-up conversation",
                "Encourage professional consultation"
            ]
        else:
            return [
                "Continue supportive conversation",
                "Monitor for changes in mood",
                "Provide general wellness resources"
            ]

    async def get_therapeutic_exercises(self, user_id: str, emotion: str) -> List[Dict]:
        """Get personalized therapeutic exercises based on user's emotional state"""
        exercises = {
            "anxiety": [
                {
                    "name": "4-7-8 Breathing",
                    "description": "Breathe in for 4, hold for 7, exhale for 8",
                    "duration": "5 minutes",
                    "type": "breathing",
                    "instructions": [
                        "Sit comfortably with your back straight",
                        "Exhale completely through your mouth",
                        "Inhale through nose for 4 counts",
                        "Hold breath for 7 counts",
                        "Exhale through mouth for 8 counts",
                        "Repeat 3-4 times"
                    ]
                },
                {
                    "name": "Progressive Muscle Relaxation",
                    "description": "Systematically tense and relax muscle groups",
                    "duration": "10-15 minutes",
                    "type": "relaxation",
                    "instructions": [
                        "Start with your toes, tense for 5 seconds",
                        "Release and notice the relaxation",
                        "Move up through each muscle group",
                        "End with your face and scalp"
                    ]
                }
            ],
            "depression": [
                {
                    "name": "Gratitude Practice",
                    "description": "Identify three things you're grateful for",
                    "duration": "5 minutes",
                    "type": "cognitive",
                    "instructions": [
                        "Think of three specific things from today",
                        "Write them down if possible",
                        "Reflect on why each matters to you",
                        "Notice the positive feelings that arise"
                    ]
                },
                {
                    "name": "Behavioral Activation",
                    "description": "Plan one small, achievable activity",
                    "duration": "Variable",
                    "type": "behavioral",
                    "instructions": [
                        "Choose something you used to enjoy",
                        "Make it small and manageable",
                        "Set a specific time to do it",
                        "Focus on the action, not the feeling"
                    ]
                }
            ],
            "anger": [
                {
                    "name": "STOP Technique",
                    "description": "Stop, Take a breath, Observe, Proceed mindfully",
                    "duration": "2-3 minutes",
                    "type": "mindfulness",
                    "instructions": [
                        "STOP what you're doing",
                        "TAKE a deep breath",
                        "OBSERVE your thoughts and feelings",
                        "PROCEED with intention"
                    ]
                }
            ],
            "neutral": [
                {
                    "name": "Mindful Check-in",
                    "description": "Brief awareness of current state",
                    "duration": "3 minutes",
                    "type": "mindfulness",
                    "instructions": [
                        "Notice your current emotional state",
                        "Observe without judgment",
                        "Acknowledge what you're feeling",
                        "Set an intention for the day"
                    ]
                }
            ]
        }
        
        return exercises.get(emotion.lower(), exercises["neutral"])

    async def generate_proactive_checkin(self, user_id: str) -> Dict:
        """Generate personalized proactive check-in based on user history"""
        try:
            context = await self.get_user_context(user_id, limit=5)
            
            # Analyze recent patterns
            recent_emotions = [conv.get("emotion", "neutral") for conv in context.get("recent_conversations", [])]
            
            if not recent_emotions:
                return {
                    "message": "Hi! I wanted to check in with you. How are you feeling today?",
                    "type": "general_checkin",
                    "suggested_topics": ["mood", "daily_activities", "goals"]
                }
            
            # Determine check-in type based on patterns
            if "sad" in recent_emotions or "depression" in recent_emotions:
                return {
                    "message": "I've noticed you've been going through a tough time lately. I'm here to listen and support you. What's on your mind today?",
                    "type": "supportive_checkin",
                    "suggested_topics": ["coping_strategies", "support_system", "small_wins"],
                    "recommended_exercises": await self.get_therapeutic_exercises(user_id, "depression")
                }
            
            elif "anxiety" in recent_emotions or "anxious" in recent_emotions:
                return {
                    "message": "I wanted to check in and see how you're managing your anxiety today. Remember, you have tools to help you through this.",
                    "type": "anxiety_checkin",
                    "suggested_topics": ["stress_levels", "breathing_exercises", "grounding_techniques"],
                    "recommended_exercises": await self.get_therapeutic_exercises(user_id, "anxiety")
                }
            
            else:
                return {
                    "message": "Hope you're having a good day! I wanted to check in and see how things are going for you.",
                    "type": "wellness_checkin",
                    "suggested_topics": ["mood", "achievements", "goals"],
                    "recommended_exercises": await self.get_therapeutic_exercises(user_id, "neutral")
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to generate proactive check-in: {e}")
            return {
                "message": "Hi! I wanted to check in with you. How are you feeling today?",
                "type": "general_checkin",
                "error": str(e)
            }

# Global instance
cognee_service = CogneeMemoryService()