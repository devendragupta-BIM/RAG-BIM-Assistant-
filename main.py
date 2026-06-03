from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os

load_dotenv()

def load_vectorstore():
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )
    vectorstore = Chroma(
        persist_directory="chroma_db",
        embedding_function=embeddings
    )
    return vectorstore

def ask_question(question, vectorstore):
    docs = vectorstore.similarity_search(question, k=4)
    
    context = "\n\n".join([doc.page_content for doc in docs])
    
    llm = ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model_name="llama-3.3-70b-versatile"
    )
    
    prompt = f"""You are an expert BIM engineer assistant. 
Answer the question based only on the context provided below.
If the answer is not in the context, say "I could not find this in the provided BIM documents."

Context:
{context}

Question: {question}

Answer:"""
    
    response = llm.invoke(prompt)
    return response.content

def main():
    print("Loading BIM knowledge base...")
    vectorstore = load_vectorstore()
    print("BIM Assistant is ready. Type your question below.")
    print("Type 'exit' to quit.")
    print("-" * 50)
    
    while True:
        question = input("\nYour Question: ")
        
        if question.lower() == "exit":
            print("Goodbye!")
            break
            
        if question.strip() == "":
            print("Please enter a valid question.")
            continue
        
        print("\nSearching BIM documents...")
        answer = ask_question(question, vectorstore)
        print(f"\nAnswer: {answer}")
        print("-" * 50)

if __name__ == "__main__":
    main()