# HANDLES MEMORY, CONTEXT, AND SESSION
# dependencies or libs

from langchain.memory import ConversationBufferMemory
from langchain.schema import messages_to_dict, messages_from_dict
import sqlite3
import json
from typing import Dict

class SessionManager:
    def __init__(self, db_path = "sessions/session_db.sqlite"):

        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS session_memory (session_id TEXT PRIMARY KEY, memory_json TEXT)"
        )

    def save_memory(self, session_id: str, memory: ConversationBufferMemory):

        serialized = json.dumps(messages_to_dict(memory.chat_memory.messages))
        self.cursor.execute("REPLACE INTO session_memory (session_id, memory_json) VALUES (?, ?)", (session_id, serialized))
        self.conn.commit()

    def load_memory(self, session_id: str) -> ConversationBufferMemory:
        self.cursor.execute("SELECT memory_json FROM session_memory WHERE session_id = ?", (session_id,))
        result = self.cursor.fetchone()
        memory = ConversationBufferMemory(memory_key="chat_history", input_key="question")
        if result:
            memory.chat_memory.messages = messages_from_dict(json.loads(result[0]))
        return memory