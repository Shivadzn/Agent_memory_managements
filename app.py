import streamlit as st
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.chains import ConversationalRetrievalChain
from memory_manager import SessionManager
from knowledge_base import KnowledgeBase
import re

# Load environment variables
load_dotenv()

groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    st.error("GROQ_API_KEY is not set. Please add it to your .env file.")
    st.stop()

# App title
st.set_page_config(page_title="Agentic Memory Chat", layout="wide")
st.title("Agentic AI Memory Chat")

# Session ID selection
session_id = st.text_input("🔑 Session ID", value="default_user")

# Load session memory
session_mgr = SessionManager()
memory = session_mgr.load_memory(session_id)

# Load Knowledge Base
kb = KnowledgeBase()

# Load LLM + RAG Chain
retriever = kb.db.as_retriever()
llm = ChatGroq(api_key=groq_api_key, model="gemma2-9b-it")
qa_chain = ConversationalRetrievalChain.from_llm(llm, retriever=retriever)

# Initialize chat_history in Streamlit session state
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

# System prompt to guide the LLM
system_prompt = (
    "You are a helpful Python assistant. "
    "If the user's question is about programming, answer it directly with code and explanation, "
    "even if no context is provided. "
    "If the question is about something else, use the context if available."
)

# Chat input
query = st.text_input("🗣️ Ask something...", key="input_query")

# Knowledge base upload
with st.expander("📚 Upload New Knowledge"):
    new_text = st.text_area("Add new knowledge:")
    if st.button("Update Knowledge Base"):
        if new_text:
            kb.update_knowledge([new_text])
            st.success("✅ Knowledge updated!")
            st.session_state["chat_history"] = []  # Clear chat history after knowledge update
            st.info("Chat history cleared. Please ask your next question.")

# Run Chat
if query:
    with st.spinner("Thinking..."):
        # Retrieve relevant documents
        docs = kb.db.similarity_search_with_score(query, k=1)
        threshold = 0.85
        stopwords = {"is", "in", "the", "a", "an", "and", "or", "to", "of", "with", "for", "on", "at", "by", "from", "as", "that", "this", "it", "be", "are", "was", "were", "has", "have", "had", "but", "not", "do", "does", "did", "so", "if", "then", "than", "which", "who", "whom", "whose", "can", "will", "would", "should", "could", "may", "might", "must"}
        def significant_keywords(text):
            return [word for word in re.findall(r'\w+', text.lower()) if word not in stopwords and len(word) > 2]
        query_keywords = significant_keywords(query)
        context_words = docs[0][0].page_content.lower() if docs else ""
        keyword_matches = sum(1 for word in query_keywords if word in context_words)
        if docs and docs[0][1] > threshold and keyword_matches >= 2:
            context = docs[0][0].page_content
            prompt = f"{system_prompt}\n\nContext: {context}\n\nQuestion: {query}"
        else:
            prompt = f"{system_prompt}\n\n{query}"
        response = qa_chain.invoke({"question": prompt, "chat_history": st.session_state["chat_history"]})
        st.markdown(f"**🤖 Answer:** {response['answer'] if isinstance(response, dict) and 'answer' in response else response}")
        st.session_state["chat_history"].append((query, response['answer'] if isinstance(response, dict) and 'answer' in response else response))

# Chat history display
if st.session_state["chat_history"]:
    st.markdown("### 🕒 Conversation History")
    for q, a in st.session_state["chat_history"]:
        st.markdown(f"**You:** {q}")
        st.markdown(f"**Bot:** {a}")
