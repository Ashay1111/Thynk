"""Command-line interface for PsyRAG"""
from .core import PsyRAGCore

def print_progress(stage, progress, message, details=None):
    print(f"[{progress:3.0f}%] {stage.upper()}: {message}")
    if details and 'expanded_queries' in details:
        for i, q in enumerate(details['expanded_queries'], 1):
            print(f"  {i}. {q}")

def main():
    print("🧠 PsyRAG - Psychology RAG System")
    print("=" * 50)
    
    try:
        psyrag = PsyRAGCore()
        print("Loading retriever...")
        psyrag.initialize_retriever()
        print("✅ Retriever loaded successfully!")
        
        while True:
            query = input("\nAsk a question (or 'quit' to exit): ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
                
            if not query:
                continue
            
            try:
                answer, expanded = psyrag.process_query(
                    query, 
                    expand=True, 
                    progress_callback=print_progress
                )
                
                print("\n" + "=" * 50)
                print("🧠 PsyRAG ANSWER:")
                print("=" * 50)
                print(answer)
                print("=" * 50)
                
            except Exception as e:
                print(f"Error: {e}")
                
    except Exception as e:
        print(f"Failed to initialize: {e}")

if __name__ == "__main__":
    main()