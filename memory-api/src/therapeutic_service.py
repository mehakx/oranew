import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import openai
from dataclasses import dataclass, asdict
import logging
from .cognee_service import cognee_service, TherapeuticInsight

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ProgressMetric:
    metric_name: str
    current_value: float
    previous_value: float
    change_percentage: float
    trend: str  # "improving", "stable", "declining"
    timestamp: datetime

@dataclass
class TherapeuticSession:
    session_id: str
    user_id: str
    start_time: datetime
    end_time: Optional[datetime]
    session_type: str
    techniques_used: List[str]
    outcomes: Dict[str, Any]
    notes: str

class TherapeuticService:
    def __init__(self):
        """Initialize therapeutic service with OpenAI integration"""
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.crisis_hotlines = {
            "US": "988",
            "UK": "116 123",
            "Canada": "1-833-456-4566",
            "Australia": "13 11 14"
        }

    async def analyze_user_progress(self, user_id: str, timeframe_days: int = 30) -> Dict:
        """Analyze user's therapeutic progress over specified timeframe"""
        try:
            # Get user context from Cognee
            context = await cognee_service.get_user_context(user_id, limit=50)
            
            progress_analysis = {
                "user_id": user_id,
                "analysis_period": f"{timeframe_days} days",
                "overall_progress": "stable",
                "key_metrics": [],
                "insights": [],
                "recommendations": [],
                "next_steps": []
            }
            
            # Analyze emotional patterns
            emotional_patterns = context.get("emotional_patterns", {})
            dominant_emotions = emotional_patterns.get("dominant_emotions", {})
            
            # Calculate progress metrics
            if dominant_emotions:
                positive_emotions = sum(dominant_emotions.get(emotion, 0) for emotion in ["happy", "joy", "excited", "calm"])
                negative_emotions = sum(dominant_emotions.get(emotion, 0) for emotion in ["sad", "angry", "anxious", "fear"])
                
                progress_analysis["key_metrics"].append(ProgressMetric(
                    metric_name="Emotional Balance",
                    current_value=positive_emotions,
                    previous_value=negative_emotions,
                    change_percentage=((positive_emotions - negative_emotions) / max(negative_emotions, 0.1)) * 100,
                    trend="improving" if positive_emotions > negative_emotions else "needs_attention",
                    timestamp=datetime.now()
                ))
            
            # Generate insights
            insights = context.get("therapeutic_insights", [])
            progress_analysis["insights"] = [asdict(insight) for insight in insights]
            
            # Generate recommendations
            progress_analysis["recommendations"] = await self._generate_progress_recommendations(context)
            
            return progress_analysis
            
        except Exception as e:
            logger.error(f"❌ Failed to analyze user progress: {e}")
            return {"error": str(e)}

    async def _generate_progress_recommendations(self, user_context: Dict) -> List[str]:
        """Generate personalized recommendations based on user progress"""
        recommendations = []
        
        emotional_patterns = user_context.get("emotional_patterns", {})
        dominant_emotions = emotional_patterns.get("dominant_emotions", {})
        
        # Analyze dominant emotions and provide recommendations
        if dominant_emotions.get("anxiety", 0) > 0.3:
            recommendations.extend([
                "Consider incorporating daily breathing exercises",
                "Practice grounding techniques when feeling overwhelmed",
                "Maintain a regular sleep schedule to reduce anxiety"
            ])
        
        if dominant_emotions.get("sad", 0) > 0.3 or dominant_emotions.get("depression", 0) > 0.3:
            recommendations.extend([
                "Engage in behavioral activation - plan one enjoyable activity daily",
                "Practice gratitude journaling",
                "Consider reaching out to your support network"
            ])
        
        if dominant_emotions.get("angry", 0) > 0.2:
            recommendations.extend([
                "Use the STOP technique when feeling angry",
                "Practice progressive muscle relaxation",
                "Identify and address anger triggers"
            ])
        
        # General wellness recommendations
        recommendations.extend([
            "Continue regular check-ins to monitor emotional well-being",
            "Celebrate small wins and progress made",
            "Consider professional therapy if patterns persist"
        ])
        
        return recommendations

    async def generate_therapeutic_response(self, user_message: str, user_context: Dict, emotion: str) -> Dict:
        """Generate therapeutic response using OpenAI with context awareness"""
        try:
            # Detect crisis indicators
            crisis_assessment = await cognee_service.detect_crisis_indicators(user_message, user_context)
            
            # If high crisis risk, prioritize safety
            if crisis_assessment["risk_level"] == "high":
                return await self._generate_crisis_response(user_message, crisis_assessment)
            
            # Build therapeutic prompt with context
            therapeutic_prompt = self._build_therapeutic_prompt(user_message, user_context, emotion)
            
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": therapeutic_prompt["system_message"]
                    },
                    {
                        "role": "user",
                        "content": user_message
                    }
                ],
                temperature=0.7,
                max_tokens=300
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Get relevant therapeutic exercises
            exercises = await cognee_service.get_therapeutic_exercises(user_context["user_id"], emotion)
            
            return {
                "response": ai_response,
                "therapeutic_context": {
                    "emotion_detected": emotion,
                    "crisis_risk": crisis_assessment["risk_level"],
                    "recommended_exercises": exercises[:2],  # Top 2 exercises
                    "session_type": "supportive_therapy"
                },
                "follow_up_suggestions": self._get_follow_up_suggestions(emotion),
                "crisis_assessment": crisis_assessment
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to generate therapeutic response: {e}")
            return {
                "response": "I'm here to support you. Could you tell me more about how you're feeling right now?",
                "error": str(e)
            }

    def _build_therapeutic_prompt(self, user_message: str, user_context: Dict, emotion: str) -> Dict:
        """Build therapeutic prompt with user context and emotional awareness"""
        
        # Get recent conversation patterns
        recent_conversations = user_context.get("recent_conversations", [])
        emotional_patterns = user_context.get("emotional_patterns", {})
        
        context_summary = ""
        if recent_conversations:
            recent_emotions = [conv.get("emotion", "neutral") for conv in recent_conversations[-3:]]
            context_summary = f"Recent emotional patterns: {', '.join(recent_emotions)}. "
        
        if emotional_patterns.get("dominant_emotions"):
            dominant = max(emotional_patterns["dominant_emotions"].items(), key=lambda x: x[1])
            context_summary += f"User's most common emotion: {dominant[0]}. "
        
        system_message = f"""You are ORA, a compassionate AI therapeutic companion trained in evidence-based therapeutic techniques including CBT, mindfulness, and supportive therapy.

Current context: {context_summary}
User's current emotion: {emotion}

Guidelines:
1. Show empathy and validate the user's feelings
2. Use therapeutic techniques appropriate for their emotional state
3. Ask open-ended questions to encourage reflection
4. Provide practical coping strategies when appropriate
5. Maintain professional boundaries while being warm and supportive
6. If you detect crisis indicators, prioritize safety and provide resources
7. Encourage professional help when needed
8. Keep responses concise but meaningful (2-3 sentences)

Respond therapeutically to the user's message, considering their emotional state and conversation history."""

        return {
            "system_message": system_message,
            "context_summary": context_summary
        }

    async def _generate_crisis_response(self, user_message: str, crisis_assessment: Dict) -> Dict:
        """Generate immediate crisis intervention response"""
        
        crisis_response = {
            "response": "I'm really concerned about you right now, and I want you to know that you're not alone. Your life has value, and there are people who want to help.",
            "immediate_actions": [
                "Please reach out to a crisis counselor immediately",
                "Contact emergency services if you're in immediate danger",
                "Reach out to a trusted friend or family member"
            ],
            "crisis_resources": {
                "national_suicide_prevention_lifeline": "988",
                "crisis_text_line": "Text HOME to 741741",
                "international_hotlines": self.crisis_hotlines
            },
            "safety_plan": [
                "Remove any means of self-harm from your immediate area",
                "Stay with someone you trust",
                "Go to your nearest emergency room if needed",
                "Call 911 if you're in immediate danger"
            ],
            "therapeutic_context": {
                "session_type": "crisis_intervention",
                "priority": "immediate_safety",
                "follow_up_required": True
            }
        }
        
        return crisis_response

    def _get_follow_up_suggestions(self, emotion: str) -> List[str]:
        """Get follow-up conversation suggestions based on emotion"""
        suggestions = {
            "anxiety": [
                "Would you like to try a breathing exercise together?",
                "What situations tend to trigger your anxiety?",
                "How has your sleep been lately?"
            ],
            "sad": [
                "What's been weighing on your mind?",
                "Can you think of one small thing that brought you joy recently?",
                "How is your support system right now?"
            ],
            "angry": [
                "What triggered these feelings of anger?",
                "How do you usually cope when you feel this way?",
                "Would you like to explore what's underneath the anger?"
            ],
            "happy": [
                "That's wonderful to hear! What contributed to these positive feelings?",
                "How can we help you maintain this positive state?",
                "What would you like to focus on today?"
            ],
            "neutral": [
                "How are you feeling overall today?",
                "What's been on your mind lately?",
                "Is there anything specific you'd like to talk about?"
            ]
        }
        
        return suggestions.get(emotion.lower(), suggestions["neutral"])

    async def schedule_proactive_checkin(self, user_id: str, checkin_type: str = "wellness") -> Dict:
        """Schedule a proactive check-in for the user"""
        try:
            checkin_data = await cognee_service.generate_proactive_checkin(user_id)
            
            # Store the scheduled check-in
            checkin_record = {
                "user_id": user_id,
                "checkin_type": checkin_type,
                "scheduled_time": datetime.now().isoformat(),
                "message": checkin_data.get("message"),
                "suggested_topics": checkin_data.get("suggested_topics", []),
                "status": "scheduled"
            }
            
            # In a real implementation, you'd store this in a database
            # and have a background task system to send the check-ins
            
            return {
                "success": True,
                "checkin_id": f"checkin_{user_id}_{datetime.now().timestamp()}",
                "scheduled_for": "next_appropriate_time",
                "checkin_data": checkin_data
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to schedule proactive check-in: {e}")
            return {"success": False, "error": str(e)}

    async def get_user_insights(self, user_id: str) -> Dict:
        """Get comprehensive user insights for therapeutic purposes"""
        try:
            # Get user context from Cognee
            context = await cognee_service.get_user_context(user_id)
            
            # Analyze progress
            progress = await self.analyze_user_progress(user_id)
            
            insights = {
                "user_id": user_id,
                "generated_at": datetime.now().isoformat(),
                "emotional_profile": context.get("emotional_patterns", {}),
                "therapeutic_insights": context.get("therapeutic_insights", []),
                "progress_analysis": progress,
                "risk_assessment": {
                    "current_risk_level": "low",  # This would be calculated based on recent conversations
                    "protective_factors": [],
                    "risk_factors": []
                },
                "recommendations": {
                    "immediate": [],
                    "short_term": [],
                    "long_term": []
                }
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"❌ Failed to get user insights: {e}")
            return {"error": str(e)}

# Global instance
therapeutic_service = TherapeuticService()