from langchain_google_genai import ChatGoogleGenerativeAI
from .retrieval import retrieve_multiple_queries, get_retriever
from .config import gemini_api_key
from .query_expansion import expand_query
from typing import List, Dict, Optional, Tuple
from langchain_core.documents import Document
import time

# Set up the LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=gemini_api_key,
    temperature=0
)

def format_context(docs):
    """Format context from chunks into a prompt"""
    context_text = "\n\n".join([doc.page_content for doc in docs])
    return context_text

def generate_answer(
    query: str, 
    retriever=None, 
    expand: bool = True, 
    return_expanded: bool = False,
    k: int = 5,
    progress_callback=None
) -> str | Tuple[str, List[str]]:
    """
    Generate an answer using RAG pipeline
    
    Args:
        query: The user's question
        retriever: Optional retriever object (if None, will create one)
        expand: Whether to expand the query
        return_expanded: Whether to return expanded queries
        k: Number of documents to retrieve
        progress_callback: Optional callback for progress updates
    
    Returns:
        Either just the answer (str) or tuple of (answer, expanded_queries)
    """
    
    def update_progress(stage, progress, message, details=None):
        if progress_callback:
            progress_callback(stage, progress, message, details)
    
    # Step 1: Initialize retriever if not provided (with correct k value)
    if retriever is None:
        update_progress("initialization", 10, "Loading retriever...")
        retriever = get_retriever(k=k)
    else:
        # Update the retriever's k value if it's different
        retriever.search_kwargs = {"k": k}
    
    # Step 2: Query expansion (if enabled)
    expanded_queries = []
    if expand:
        update_progress("expansion", 20, "Expanding query...")
        try:
            expanded_queries = expand_query(query)
            update_progress("expansion", 30, f"Generated {len(expanded_queries)} query variations", 
                          {"expanded_queries": expanded_queries})
        except Exception as e:
            print(f"Warning: Query expansion failed: {e}")
            expanded_queries = []
    
    # Step 3: Retrieve relevant documents
    update_progress("retrieval", 40, "Retrieving relevant documents...")
    
    try:
        if expanded_queries:
            # Use original query + expanded queries
            all_queries = [query] + expanded_queries
            docs = retrieve_multiple_queries(all_queries, retriever)
        else:
            # Use only original query - use invoke instead of get_relevant_documents
            docs = retriever.invoke(query)
        
        update_progress("retrieval", 60, f"Retrieved {len(docs)} documents")
        
        if not docs:
            update_progress("retrieval", 70, "No relevant documents found")
            answer = "I couldn't find any relevant documents to answer your question. Please make sure documents are indexed."
            return (answer, expanded_queries) if return_expanded else answer
            
    except Exception as e:
        update_progress("retrieval", 60, f"Retrieval error: {str(e)}")
        answer = f"Error during document retrieval: {str(e)}"
        return (answer, expanded_queries) if return_expanded else answer
    
    # Step 4: Generate answer
    update_progress("generation", 70, "Generating answer...")
    
    try:
        # Format context from retrieved documents
        context = format_context(docs)
        
        # Create prompt
        prompt = f"""Use the following context to answer the question.

Context:
{context}

Question:
{query}

Answer (detailed and grounded in the context):
"""
        
        # Generate answer
        response = llm.invoke(prompt)
        answer = response.content.strip()
        
        update_progress("generation", 90, "Answer generated successfully")
        
    except Exception as e:
        update_progress("generation", 70, f"Generation error: {str(e)}")
        answer = f"Error during answer generation: {str(e)}"
    
    update_progress("completion", 100, "Query processing completed")
    
    # Return based on what's requested
    if return_expanded:
        return answer, expanded_queries
    else:
        return answer