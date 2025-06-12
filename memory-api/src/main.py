import os
import sys
import sqlite3
from datetime import datetime
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, request, jsonify
from src.routes.memory import memory_bp
from src.routes.enhanced_memory import enhanced_memory_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'ora-memory-secret-key-2024'

# Register memory routes
app.register_blueprint(memory_bp, url_prefix='/api/memory')
app.register_blueprint(enhanced_memory_bp, url_prefix='/api/enhanced')

# Initialize SQLite database
def init_db():
    """Initialize SQLite database with required tables"""
    db_path = os.path.join(os.path.dirname(__file__), 'ora_memory.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            name TEXT,
            personality_type TEXT,
            communication_style TEXT,
            first_visit TIMESTAMP,
            last_visit TIMESTAMP,
            onboarding_complete BOOLEAN DEFAULT 0,
            preferences TEXT,
            total_conversations INTEGER DEFAULT 0,
            therapeutic_profile TEXT,
            crisis_history TEXT,
            progress_metrics TEXT
        )
    ''')
    
    # Conversations table (enhanced)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            timestamp TIMESTAMP,
            user_message TEXT,
            ora_response TEXT,
            emotion TEXT,
            emotion_intensity REAL,
            topic TEXT,
            session_id TEXT,
            therapeutic_context TEXT,
            crisis_indicators TEXT,
            intervention_applied BOOLEAN DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    
    # User insights table (enhanced)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_insights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            insight_type TEXT,
            insight_value TEXT,
            confidence_score REAL,
            created_at TIMESTAMP,
            therapeutic_relevance TEXT,
            action_taken TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    
    # Therapeutic sessions table (new)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS therapeutic_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            session_id TEXT,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            session_type TEXT,
            techniques_used TEXT,
            outcomes TEXT,
            notes TEXT,
            crisis_level TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    
    # Progress tracking table (new)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS progress_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            metric_name TEXT,
            metric_value REAL,
            measurement_date TIMESTAMP,
            trend TEXT,
            notes TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    
    # Crisis interventions table (new)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS crisis_interventions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            intervention_time TIMESTAMP,
            risk_level TEXT,
            indicators TEXT,
            actions_taken TEXT,
            outcome TEXT,
            follow_up_required BOOLEAN DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"✅ Enhanced database initialized at: {db_path}")

# Health check endpoint
@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'Enhanced ORA Memory API',
        'version': '2.0.0',
        'features': [
            'cognee_integration',
            'therapeutic_ai',
            'crisis_detection',
            'progress_tracking',
            'semantic_memory'
        ],
        'timestamp': datetime.now().isoformat()
    })

# Root endpoint
@app.route('/')
def root():
    return jsonify({
        'message': 'Enhanced ORA Memory API is running! 🧠✨',
        'endpoints': {
            'health': '/health',
            'admin_panel': '/admin',
            'legacy_memory': '/api/memory/*',
            'enhanced_memory': '/api/enhanced/*',
            'cognee_context': '/api/enhanced/cognee/context',
            'therapeutic_insights': '/api/enhanced/therapeutic/insights',
            'crisis_assessment': '/api/enhanced/crisis/assess',
            'progress_tracking': '/api/enhanced/therapeutic/progress'
        },
        'documentation': 'Enhanced with Cognee semantic memory and therapeutic AI capabilities'
    })

# Admin panel route
@app.route('/admin')
def admin_panel():
    """Serve the enhanced admin panel HTML"""
    return app.send_static_file('admin.html')

if __name__ == '__main__':
    # Initialize database on startup
    init_db()
    
    print("🚀 Starting Enhanced ORA Memory API...")
    print("📊 Database: SQLite + Cognee")
    print("🧠 Memory: Semantic + Therapeutic")
    print("🏥 Crisis Detection: Enabled")
    print("📈 Progress Tracking: Active")
    print("🔗 Ready for therapeutic AI integration!")
    print("🎯 Admin Panel: Available at /admin")
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)