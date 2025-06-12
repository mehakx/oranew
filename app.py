import os
import json
import uuid
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Initialize the OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

# In-memory conversation store
conversations = {}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/classify", methods=["POST"])
def classify():
    data = request.get_json()
    text = data.get("text","").strip()
    if not text:
        return jsonify({"error":"No text"}), 400
    
    prompt = f"Classify the primary emotion in this text in one word (e.g. Happy, Sad, Angry, Neutral):\n\n\"{text}\""
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role":"user","content":prompt}],
        temperature=0.0,
        max_tokens=5
    )
    
    emotion = response.choices[0].message.content.strip().split()[0]
    return jsonify({"emotion": emotion})

@app.route("/respond", methods=["POST"])
def respond():
    data = request.get_json()
    emotion = data.get("emotion","Neutral")
    text = data.get("text","")
    
    prompt = (
      f"You are a compassionate assistant. The user is feeling {emotion}. "
      f"They said: \"{text}\". Reply in one or two sentences showing empathy."
    )
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role":"user","content":prompt}],
        temperature=0.7,
        max_tokens=60
    )
    
    reply = response.choices[0].message.content.strip()
    
    # new chat session
    chat_id = uuid.uuid4().hex
    conversations[chat_id] = [
      {"role":"system","content":"You are a compassionate assistant."},
      {"role":"assistant","content": reply}
    ]
    
    return jsonify({"message": reply, "chat_id": chat_id})

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    chat_id = data.get("chat_id")
    user_msg = data.get("message","").strip()
    
    if not chat_id or chat_id not in conversations:
        return jsonify({"error":"Invalid chat_id"}), 400
    
    conversations[chat_id].append({"role":"user","content":user_msg})
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=conversations[chat_id] + [{"role":"user","content":user_msg}],
        temperature=0.7,
        max_tokens=60
    )
    
    assistant_msg = response.choices[0].message.content.strip()
    conversations[chat_id].append({"role":"assistant","content":assistant_msg})
    
    return jsonify({"reply": assistant_msg})

if __name__ == "__main__":
    app.run(debug=True)
