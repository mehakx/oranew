# Enhanced ORA - Therapeutic AI Companion

🧠 **Advanced emotional AI with therapeutic capabilities, semantic memory, and crisis intervention**

## 🌟 New Features (v2.0)

### Therapeutic AI Capabilities
- ✅ **Crisis Detection & Intervention** - Real-time risk assessment with immediate support
- ✅ **Evidence-Based Therapeutic Techniques** - CBT, mindfulness, and grounding exercises
- ✅ **Progress Tracking** - Emotional analytics and improvement metrics
- ✅ **Proactive Check-ins** - Personalized wellness monitoring
- ✅ **User Insights** - Behavioral pattern recognition and recommendations

### Enhanced Memory System
- ✅ **Cognee Integration** - Semantic memory for contextual understanding
- ✅ **Conversation Persistence** - Long-term memory with emotional context
- ✅ **Pattern Recognition** - Identifies emotional trends and triggers
- ✅ **Therapeutic Context** - Maintains therapeutic relationship continuity

### Crisis Support Features
- ✅ **Risk Level Assessment** - Automatic detection of crisis indicators
- ✅ **Emergency Resources** - Crisis hotlines and immediate intervention
- ✅ **Safety Planning** - Personalized crisis response protocols
- ✅ **Follow-up Monitoring** - Continuous support after crisis events

## 🚀 Quick Start

### Prerequisites
```bash
pip install -r requirements.txt
```

### Environment Setup
```bash
# Create .env file with:
OPENAI_API_KEY=your_openai_api_key_here
```

### Run Enhanced ORA
```bash
# Start the enhanced therapeutic AI
python enhanced_app.py

# Or run the original app (backward compatible)
python app.py

# Start memory API service
cd memory-api
python src/main.py
```

## 📊 API Endpoints

### Original Endpoints (Preserved)
- `POST /classify` - Emotion classification
- `POST /respond` - Generate AI response
- `POST /chat` - Continue conversation

### New Therapeutic Endpoints
- `GET /insights/<user_id>` - User patterns and insights
- `GET /progress/<user_id>` - Emotional progress tracking
- `POST /therapeutic_exercise` - Evidence-based exercises
- `GET /proactive_checkin/<user_id>` - Personalized check-ins
- `POST /crisis_assessment` - Crisis risk evaluation

### Enhanced Memory Endpoints
- `GET /memory/context/<user_id>` - Semantic memory context
- `POST /memory/store` - Store conversation with context
- `POST /api/enhanced/cognee/context` - Cognee semantic search
- `POST /api/enhanced/therapeutic/insights` - Therapeutic analysis

## 🧠 Cognee Integration

### Semantic Memory Features
```python
# Store conversation with therapeutic context
await cognee_service.store_conversation(user_id, {
    "user_message": "I'm feeling anxious",
    "ai_response": "I understand you're feeling anxious...",
    "emotion": "anxiety",
    "therapeutic_context": {...},
    "crisis_indicators": []
})

# Retrieve contextual memory
context = await cognee_service.get_user_context(user_id)
```

### Therapeutic Insights
```python
# Generate therapeutic insights
insights = await therapeutic_service.get_user_insights(user_id)

# Analyze progress
progress = await therapeutic_service.analyze_user_progress(user_id, 30)
```

## 🏥 Crisis Detection

### Automatic Risk Assessment
- **High Risk**: Immediate intervention with crisis resources
- **Medium Risk**: Enhanced support and monitoring
- **Low Risk**: Standard therapeutic support

### Crisis Response Protocol
1. **Immediate Safety Assessment**
2. **Crisis Resource Provision**
3. **Professional Help Encouragement**
4. **Follow-up Scheduling**

## 📈 Progress Tracking

### Emotional Analytics
- Dominant emotion patterns
- Emotional volatility metrics
- Improvement trends
- Trigger identification

### Therapeutic Metrics
- Coping strategy effectiveness
- Session outcomes
- Behavioral activation progress
- Crisis frequency reduction

## 🧘 Therapeutic Exercises

### Evidence-Based Interventions
- **Breathing Exercises**: 4-7-8 technique, box breathing
- **Mindfulness**: Body scans, present moment awareness
- **Cognitive**: Thought challenging, gratitude practice
- **Behavioral**: Activity scheduling, exposure exercises

### Personalized Recommendations
- Emotion-specific exercises
- User preference learning
- Progress-based adaptation
- Crisis-appropriate interventions

## 🎯 Admin Panel

Access the enhanced admin panel at `/enhanced_admin.html`:

### Features
- **User Management**: View all therapeutic users
- **Crisis Monitoring**: Real-time crisis alerts
- **Progress Visualization**: User improvement metrics
- **Therapeutic Insights**: AI-generated recommendations
- **Exercise Tracking**: Intervention effectiveness

## 🔧 Technical Architecture

### Core Components
1. **Enhanced App** (`enhanced_app.py`) - Main therapeutic AI application
2. **Cognee Service** - Semantic memory management
3. **Therapeutic Service** - Evidence-based interventions
4. **Crisis Detection** - Risk assessment and intervention
5. **Progress Analytics** - Outcome measurement

### Database Schema
- **Users**: Enhanced with therapeutic profiles
- **Conversations**: Emotional and therapeutic context
- **Therapeutic Sessions**: Intervention tracking
- **Progress Metrics**: Outcome measurements
- **Crisis Interventions**: Safety event logging

## 🔒 Privacy & Security

### Data Protection
- Encrypted conversation storage
- Anonymized analytics
- HIPAA-compliant design patterns
- Secure crisis intervention protocols

### Ethical AI
- Transparent therapeutic recommendations
- Human oversight requirements
- Professional referral protocols
- Bias monitoring and mitigation

## 🌐 Deployment

### Production Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY=your_key

# Run with gunicorn
gunicorn enhanced_app:app --bind 0.0.0.0:$PORT
```

### Docker Deployment
```dockerfile
FROM python:3.9-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["python", "enhanced_app.py"]
```

## 📚 Documentation

### Therapeutic AI Guidelines
- Evidence-based intervention protocols
- Crisis response procedures
- Progress measurement standards
- Ethical AI practices

### API Documentation
- Endpoint specifications
- Request/response formats
- Authentication requirements
- Rate limiting policies

## 🤝 Contributing

### Development Guidelines
1. Follow therapeutic AI best practices
2. Maintain backward compatibility
3. Include comprehensive testing
4. Document therapeutic interventions

### Testing
```bash
# Run therapeutic AI tests
python -m pytest tests/therapeutic/

# Test crisis detection
python -m pytest tests/crisis/

# Validate memory integration
python -m pytest tests/memory/
```

## 📞 Crisis Resources

### Emergency Contacts
- **US**: 988 (Suicide & Crisis Lifeline)
- **UK**: 116 123 (Samaritans)
- **Canada**: 1-833-456-4566
- **Australia**: 13 11 14 (Lifeline)

### Professional Support
- Encourage professional therapy
- Provide therapist directories
- Support treatment compliance
- Monitor therapeutic progress

## 🔄 Migration from v1.0

### Backward Compatibility
- All original endpoints preserved
- Existing conversations maintained
- Gradual feature adoption
- Zero-downtime deployment

### Enhanced Features
- Automatic emotion classification upgrade
- Semantic memory integration
- Therapeutic context addition
- Crisis detection activation

## 📊 Analytics & Monitoring

### Therapeutic Metrics
- User engagement rates
- Crisis intervention effectiveness
- Progress improvement percentages
- Exercise completion rates

### System Health
- API response times
- Memory system performance
- Crisis detection accuracy
- User satisfaction scores

---

**Enhanced ORA v2.0** - Bringing therapeutic AI capabilities to emotional support, with advanced memory, crisis intervention, and evidence-based therapeutic techniques.

For support: [GitHub Issues](https://github.com/mehakx/oraemotion/issues)