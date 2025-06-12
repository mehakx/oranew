import os
import json
import asyncio
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from ..cognee_service import cognee_service
from ..therapeutic_service import therapeutic_service

enhanced_memory_bp = Blueprint('enhanced_memory', __name__)

@enhanced_memory_bp.route('/cognee/context', methods=['POST'])
def get_cognee_context():
    """Get user context from Cognee semantic memory"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        limit = data.get('limit', 10)
        
        if not user_id:
            return jsonify({'error': 'user_id is required'}), 400
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        context = loop.run_until_complete(
            cognee_service.get_user_context(user_id, limit)
        )
        
        loop.close()
        return jsonify(context)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@enhanced_memory_bp.route('/cognee/store', methods=['POST'])
def store_in_cognee():
    """Store conversation in Cognee semantic memory"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        conversation_data = data.get('conversation_data', {})
        
        if not user_id:
            return jsonify({'error': 'user_id is required'}), 400
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        success = loop.run_until_complete(
            cognee_service.store_conversation(user_id, conversation_data)
        )
        
        loop.close()
        
        return jsonify({
            'success': success,
            'user_id': user_id,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@enhanced_memory_bp.route('/therapeutic/insights', methods=['POST'])
def get_therapeutic_insights():
    """Get therapeutic insights for user"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'user_id is required'}), 400
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        insights = loop.run_until_complete(
            therapeutic_service.get_user_insights(user_id)
        )
        
        loop.close()
        return jsonify(insights)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@enhanced_memory_bp.route('/therapeutic/progress', methods=['POST'])
def analyze_therapeutic_progress():
    """Analyze user's therapeutic progress"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        timeframe_days = data.get('timeframe_days', 30)
        
        if not user_id:
            return jsonify({'error': 'user_id is required'}), 400
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        progress = loop.run_until_complete(
            therapeutic_service.analyze_user_progress(user_id, timeframe_days)
        )
        
        loop.close()
        return jsonify(progress)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@enhanced_memory_bp.route('/crisis/assess', methods=['POST'])
def assess_crisis():
    """Assess crisis risk in user message"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        user_id = data.get('user_id')
        
        if not message:
            return jsonify({'error': 'message is required'}), 400
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Get user context
        user_context = loop.run_until_complete(
            cognee_service.get_user_context(user_id or 'anonymous')
        )
        
        # Assess crisis
        crisis_assessment = loop.run_until_complete(
            cognee_service.detect_crisis_indicators(message, user_context)
        )
        
        loop.close()
        
        return jsonify({
            'crisis_assessment': crisis_assessment,
            'user_id': user_id,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@enhanced_memory_bp.route('/exercises/get', methods=['POST'])
def get_exercises():
    """Get therapeutic exercises for user"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        emotion = data.get('emotion', 'neutral')
        exercise_type = data.get('type', 'any')
        
        if not user_id:
            return jsonify({'error': 'user_id is required'}), 400
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        exercises = loop.run_until_complete(
            cognee_service.get_therapeutic_exercises(user_id, emotion)
        )
        
        # Filter by type if specified
        if exercise_type != 'any':
            exercises = [ex for ex in exercises if ex.get('type') == exercise_type]
        
        loop.close()
        
        return jsonify({
            'exercises': exercises,
            'user_id': user_id,
            'emotion': emotion,
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@enhanced_memory_bp.route('/checkin/generate', methods=['POST'])
def generate_checkin():
    """Generate proactive check-in for user"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'user_id is required'}), 400
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        checkin = loop.run_until_complete(
            cognee_service.generate_proactive_checkin(user_id)
        )
        
        loop.close()
        return jsonify(checkin)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@enhanced_memory_bp.route('/analytics/emotional-patterns', methods=['POST'])
def get_emotional_patterns():
    """Get detailed emotional patterns analysis"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        timeframe_days = data.get('timeframe_days', 30)
        
        if not user_id:
            return jsonify({'error': 'user_id is required'}), 400
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        context = loop.run_until_complete(
            cognee_service.get_user_context(user_id, limit=100)
        )
        
        emotional_patterns = context.get('emotional_patterns', {})
        
        # Enhanced analytics
        analytics = {
            'user_id': user_id,
            'timeframe_days': timeframe_days,
            'emotional_patterns': emotional_patterns,
            'insights': context.get('therapeutic_insights', []),
            'recommendations': [],
            'generated_at': datetime.now().isoformat()
        }
        
        # Generate recommendations based on patterns
        dominant_emotions = emotional_patterns.get('dominant_emotions', {})
        if dominant_emotions:
            if dominant_emotions.get('anxiety', 0) > 0.3:
                analytics['recommendations'].append({
                    'type': 'anxiety_management',
                    'priority': 'high',
                    'suggestion': 'Consider daily breathing exercises and mindfulness practice'
                })
            
            if dominant_emotions.get('sad', 0) > 0.3:
                analytics['recommendations'].append({
                    'type': 'mood_support',
                    'priority': 'high',
                    'suggestion': 'Engage in behavioral activation and social connection'
                })
        
        loop.close()
        return jsonify(analytics)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@enhanced_memory_bp.route('/health', methods=['GET'])
def health_check():
    """Health check for enhanced memory service"""
    return jsonify({
        'status': 'healthy',
        'service': 'Enhanced Memory API',
        'features': [
            'cognee_integration',
            'therapeutic_insights',
            'crisis_detection',
            'progress_tracking',
            'emotional_analytics'
        ],
        'timestamp': datetime.now().isoformat()
    })