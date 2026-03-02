from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_community.vectorstores.faiss import FAISS
import os

class StorylineRecall:
    @staticmethod
    def build_vectorstore(
        data: list[dict], 
        field: str = "description", 
        model_name: str = "./.storyline/models/all-MiniLM-L6-v2", 
        device: str = "cpu"
    ):
        """
        Build a FAISS vectorstore using a local HuggingFace embedding model.

        Args:
            data: list of dicts
            field: which text field to embed
            model_name: HuggingFace model identifier
            device: "cpu" or "cuda" if available

        Returns:
            FAISS vectorstore
        """
        if not os.path.exists(model_name):
            model_name = "sentence-transformers/all-MiniLM-L6-v2"

        # Create embeddings using HF model
        embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={"device": device}
        )

        # Construct LangChain Documents
        docs = []
        for item in data:
            text = item.get(field, "")
            if text:
                docs.append(Document(page_content=text, metadata=item))

        if not docs:
            print(f"[RECALL - Build vectorstore] Cannot find field: {field}, return None.")
            return None
        # Build FAISS
        vectorstore = FAISS.from_documents(docs, embeddings)
        return vectorstore

    @staticmethod
    def query_top_n(vectorstore, query: str, n: int = 32):
        """
        Query the vectorstore and return top-N original dicts.

        Args:
            vectorstore: FAISS
            query: query string
            n: number of results

        Returns:
            list of original dict entries
        """
        results = vectorstore.similarity_search(query, k=n)
        return [doc.metadata for doc in results]