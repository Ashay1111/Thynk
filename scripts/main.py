from .retrieval import get_retriever
from .generation import generate_answer_cli

def main():
    """Main CLI interface for PsyRAG"""
    print("🧠 PsyRAG - Psychology RAG System")
    print("=" * 50)
    
    try:
        # Initialize retriever
        print("Loading retriever...")
        retriever = get_retriever()
        print("✅ Retriever loaded successfully!")
        
        # Interactive query loop
        while True:
            print("\n" + "-" * 50)
            query = input("Ask a question about psychology, cognition, or behavior (or 'quit' to exit): ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
                
            if not query:
                print("Please enter a valid question.")
                continue
            
            print(f"\n🔍 Processing query: {query}")
            print("-" * 50)
            
            try:
                answer = generate_answer_cli(query, retriever=retriever, expand=True, verbose=True)
                print("\n" + "=" * 50)
                print("🧠 PsyRAG ANSWER:")
                print("=" * 50)
                print(answer)
                print("=" * 50)
                
            except Exception as e:
                print(f"❌ Error processing query: {e}")
                print("Make sure documents are indexed and the system is properly configured.")
                
    except Exception as e:
        print(f"❌ Failed to initialize PsyRAG: {e}")
        print("Make sure you have:")
        print("1. Indexed some documents")
        print("2. Set up your environment variables (GEMINI_API_KEY)")
        print("3. Have the FAISS index files in the correct location")

if __name__ == "__main__":
    main()