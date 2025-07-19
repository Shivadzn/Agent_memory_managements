from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.docstore.document import Document
import os

class KnowledgeBase:
    def __init__(self, persist_path="persistence/faiss_index"):
        self.embedding = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.persist_path = persist_path
        index_file = os.path.join(persist_path, "index.faiss")
        if os.path.exists(index_file):
            self.db = FAISS.load_local(persist_path, self.embedding, allow_dangerous_deserialization=True)
        else:
            self.db = FAISS.from_texts(["placeholder"], self.embedding)
    
    def query(self, query_text):
        return self.db.similarity_search(query_text, k=3)
    
    def update_knowledge(self, new_texts: list[str]):
        docs = [Document(page_content=text) for text in new_texts]
        self.db.add_documents(docs)
        self.db.save_local(self.persist_path)