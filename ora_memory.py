# Lightweight Semantic Memory Module for Ora

import os
import json
import numpy as np
import sqlite3
from datetime import datetime
import logging
from typing import List, Dict, Any, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import sentence-transformers, fall back to OpenAI if not available
try:
    from sentence_transformers import SentenceTransformer
    USING_LOCAL_EMBEDDINGS = True
    logger.info("Using sentence-transformers for embeddings")
except ImportError:
    USING_LOCAL_EMBEDDINGS = False
    import openai
    logger.info("Using OpenAI for embeddings")

class OraMemory:
    """Lightweight semantic memory system for Ora therapeutic AI"""
    
    def __init__(self, db_path: str = "ora_memory.db", embedding_dim: int = 384):
        """Initialize the memory system
        
        Args:
            db_path: Path to SQLite database
            embedding_dim: Dimension of embeddings (384 for MiniLM)
        """
        self.db_path = db_path
        self.embedding_dim = embedding_dim
        
        # Initialize embedding model if available locally
        if USING_LOCAL_EMBEDDINGS:
            try:
                self.model = SentenceTransformer('all-MiniLM-L6-v2')  # Small, fast model (384 dimensions)
            except Exception as e:
                logger.error(f"Error loading embedding model: {e}")
                self.model = None
        else:
            # Will use OpenAI for embeddings
            openai.api_key = os.getenv("OPENAI_API_KEY")
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize the SQLite database with tables for memory storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            name TEXT,
            preferences TEXT,
            created_at DATETIME,
            last_active DATETIME
        )
        ''')
        
        # Create conversations table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            message TEXT,
            response TEXT,
            emotion TEXT,
            timestamp DATETIME,
            crisis_level INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        # Create embeddings table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS embeddings (
            id TEXT PRIMARY KEY,
            conversation_id TEXT,
            embedding BLOB,
            FOREIGN KEY (conversation_id) REFERENCES conversations (id)
        )
        ''')
        
        # Create therapeutic_insights table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS therapeutic_insights (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            insight_type TEXT,
            insight_content TEXT,
            timestamp DATETIME,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def _get_embedding(self, text: str) -> np.ndarray:
        """Get embedding vector for text
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as numpy array
        """
        if USING_LOCAL_EMBEDDINGS and self.model:
            try:
                return self.model.encode(text)
            except Exception as e:
                logger.error(f"Error generating local embedding: {e}")
                # Fall back to zeros if error
                return np.zeros(self.embedding_dim)
        else:
            # Use OpenAI for embeddings
            try:
                response = openai.Embedding.create(
                    input=text,
                    model="text-embedding-ada-002"
                )
                return np.array(response['data'][0]['embedding'])
            except Exception as e:
                logger.error(f"Error generating OpenAI embedding: {e}")
                # Fall back to zeros if error
                return np.zeros(self.embedding_dim)
    
    def store_user(self, user_id: str, name: Optional[str] = None, preferences: Optional[Dict] = None):
        """Store user information
        
        Args:
            user_id: Unique user identifier
            name: User's name
            preferences: User preferences as dictionary
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now()
        
        # Check if user exists
        cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        if cursor.fetchone():
            # Update existing user
            cursor.execute(
                "UPDATE users SET last_active = ? WHERE user_id = ?",
                (now, user_id)
            )
            if name:
                cursor.execute(
                    "UPDATE users SET name = ? WHERE user_id = ?",
                    (name, user_id)
                )
            if preferences:
                cursor.execute(
                    "UPDATE users SET preferences = ? WHERE user_id = ?",
                    (json.dumps(preferences), user_id)
                )
        else:
            # Create new user
            cursor.execute(
                "INSERT INTO users (user_id, name, preferences, created_at, last_active) VALUES (?, ?, ?, ?, ?)",
                (user_id, name or "", json.dumps(preferences or {}), now, now)
            )
        
        conn.commit()
        conn.close()
    
    def store_conversation(self, 
                          user_id: str, 
                          conversation_id: str,
                          message: str, 
                          response: str, 
                          emotion: str = "neutral",
                          crisis_level: int = 0):
        """Store conversation with embedding
        
        Args:
            user_id: User identifier
            conversation_id: Unique conversation identifier
            message: User message
            response: AI response
            emotion: Detected emotion
            crisis_level: Crisis level (0-3)
        """
        # Ensure user exists
        self.store_user(user_id)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now()
        
        # Store conversation
        cursor.execute(
            "INSERT INTO conversations (id, user_id, message, response, emotion, timestamp, crisis_level) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (conversation_id, user_id, message, response, emotion, now, crisis_level)
        )
        
        # Generate and store embedding for combined message and response
        combined_text = f"User: {message}\nAI: {response}"
        embedding = self._get_embedding(combined_text)
        
        # Convert numpy array to bytes for storage
        embedding_bytes = embedding.tobytes()
        
        cursor.execute(
            "INSERT INTO embeddings (id, conversation_id, embedding) VALUES (?, ?, ?)",
            (conversation_id, conversation_id, embedding_bytes)
        )
        
        conn.commit()
        conn.close()
    
    def search_semantic_memory(self, user_id: str, query: str, limit: int = 5) -> List[Dict]:
        """Search for semantically similar conversations
        
        Args:
            user_id: User identifier
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of conversation dictionaries
        """
        # Generate embedding for query
        query_embedding = self._get_embedding(query)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all embeddings for user
        cursor.execute("""
            SELECT e.conversation_id, e.embedding, c.message, c.response, c.emotion, c.timestamp
            FROM embeddings e
            JOIN conversations c ON e.conversation_id = c.id
            WHERE c.user_id = ?
        """, (user_id,))
        
        results = []
        for row in cursor.fetchall():
            conversation_id, embedding_bytes, message, response, emotion, timestamp = row
            
            # Convert bytes back to numpy array
            embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
            
            # Calculate cosine similarity
            similarity = np.dot(query_embedding, embedding) / (np.linalg.norm(query_embedding) * np.linalg.norm(embedding))
            
            results.append({
                "conversation_id": conversation_id,
                "message": message,
                "response": response,
                "emotion": emotion,
                "timestamp": timestamp,
                "similarity": float(similarity)
            })
        
        conn.close()
        
        # Sort by similarity (highest first) and limit results
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:limit]
    
    def get_user_context(self, user_id: str, query: Optional[str] = None) -> str:
        """Get user context for therapeutic response
        
        Args:
            user_id: User identifier
            query: Optional query to find relevant context
            
        Returns:
            Context string for therapeutic response
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        context_parts = []
        
        # Get user information
        cursor.execute("SELECT name, preferences FROM users WHERE user_id = ?", (user_id,))
        user_row = cursor.fetchone()
        if user_row:
            name, preferences_json = user_row
            if name:
                context_parts.append(f"User name: {name}")
            
            try:
                preferences = json.loads(preferences_json)
                if preferences:
                    context_parts.append("User preferences: " + ", ".join(f"{k}: {v}" for k, v in preferences.items()))
            except:
                pass
        
        # Get recent emotions
        cursor.execute("""
            SELECT emotion, COUNT(*) as count
            FROM conversations
            WHERE user_id = ?
            GROUP BY emotion
            ORDER BY count DESC
            LIMIT 3
        """, (user_id,))
        
        emotions = cursor.fetchall()
        if emotions:
            emotion_str = ", ".join(f"{emotion}" for emotion, _ in emotions)
            context_parts.append(f"Common emotions: {emotion_str}")
        
        # Get semantically relevant conversations if query provided
        if query:
            relevant_convos = self.search_semantic_memory(user_id, query, limit=3)
            if relevant_convos:
                context_parts.append("Relevant past conversations:")
                for i, convo in enumerate(relevant_convos):
                    context_parts.append(f"  {i+1}. User: {convo['message']}")
                    context_parts.append(f"     AI: {convo['response']}")
        
        # Get therapeutic insights
        cursor.execute("""
            SELECT insight_content
            FROM therapeutic_insights
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT 2
        """, (user_id,))
        
        insights = cursor.fetchall()
        if insights:
            context_parts.append("Therapeutic insights:")
            for insight in insights:
                context_parts.append(f"  - {insight[0]}")
        
        conn.close()
        
        # Combine all context parts
        if context_parts:
            return "\n".join(context_parts)
        else:
            return "No previous context available."
    
    def store_therapeutic_insight(self, user_id: str, insight_type: str, insight_content: str):
        """Store therapeutic insight for user
        
        Args:
            user_id: User identifier
            insight_type: Type of insight (pattern, recommendation, etc.)
            insight_content: Content of insight
        """
        import uuid
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        insight_id = str(uuid.uuid4())
        now = datetime.now()
        
        cursor.execute(
            "INSERT INTO therapeutic_insights (id, user_id, insight_type, insight_content, timestamp) VALUES (?, ?, ?, ?, ?)",
            (insight_id, user_id, insight_type, insight_content, now)
        )
        
        conn.commit()
        conn.close()
    
    def generate_user_insights(self, user_id: str, openai_client) -> List[str]:
        """Generate therapeutic insights based on user conversations
        
        Args:
            user_id: User identifier
            openai_client: OpenAI client for generating insights
            
        Returns:
            List of insight strings
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get recent conversations
        cursor.execute("""
            SELECT message, response, emotion
            FROM conversations
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT 10
        """, (user_id,))
        
        conversations = cursor.fetchall()
        conn.close()
        
        if not conversations:
            return []
        
        # Format conversations for analysis
        conversation_text = ""
        for i, (message, response, emotion) in enumerate(conversations):
            conversation_text += f"Conversation {i+1}:\n"
            conversation_text += f"User ({emotion}): {message}\n"
            conversation_text += f"AI: {response}\n\n"
        
        # Generate insights using OpenAI
        try:
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a therapeutic AI assistant. Based on the conversation history, identify 2-3 key insights about the user's emotional patterns, potential therapeutic needs, or behavioral trends. Format each insight as a separate point."},
                    {"role": "user", "content": conversation_text}
                ],
                max_tokens=200
            )
            
            insights_text = response.choices[0].message.content.strip()
            
            # Parse insights (assuming they're in a list format)
            insights = []
            for line in insights_text.split('\n'):
                line = line.strip()
                if line and (line.startswith('-') or line.startswith('•') or line.startswith('*') or 
                            (line[0].isdigit() and line[1:3] in ['. ', ') '])):
                    # Remove leading marker and whitespace
                    insight = line.lstrip('-•*0123456789.) ').strip()
                    insights.append(insight)
            
            # Store insights
            for insight in insights:
                self.store_therapeutic_insight(user_id, "pattern", insight)
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return []
