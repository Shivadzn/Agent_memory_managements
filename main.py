from langchain.chains import ConversationalRetrievalChain
from memory_manager import SessionManager
from knowledge_base import KnowledgeBase
from langchain.llms.base import LLM
from typing import Optional, List, Any
from groq import Groq
from dotenv import load_dotenv
import os

# Load environment variables from .env file
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

class GroqLLM(LLM):
    model: str = "gemma2-9b-it"
    temperature: float = 0.0
    api_key: Optional[str] = None

    def __init__(self, model: str = "gemma2-9b-it", temperature: float = 0.0, api_key: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.model = model
        self.temperature = temperature
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        object.__setattr__(self, "client", Groq(api_key=self.api_key))

    @property
    def _llm_type(self) -> str:
        return "groq"

    def _call(self, prompt: str, stop: Optional[List[str]] = None, **kwargs: Any) -> str:
        messages = [{"role": "user", "content": prompt}]
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature
        )
        return response.choices[0].message.content

# Step 1: Load or create memory
session_id = "user_123"
session_mgr = SessionManager()
memory = session_mgr.load_memory(session_id)

# Step 2: Load knowledge base
kb = KnowledgeBase()

# Step 3: Combine retriever with LLM
retriever = kb.db.as_retriever()
llm = GroqLLM(model="gemma2-9b-it", temperature=0)
qa_chain = ConversationalRetrievalChain.from_llm(llm, retriever=retriever)

# Step 4: Ask questions and update session
chat_history = []
while True:
    query = input("You: ")
    if query.lower() == "exit":
        break

    result = qa_chain.invoke({"question": query, "chat_history": chat_history})
    answer = result["answer"] if isinstance(result, dict) and "answer" in result else result
    print("Bot:", answer)

    chat_history.append((query, answer))
    session_mgr.save_memory(session_id, memory)
