"""Core PsyRAG functionality shared between CLI and API"""
from typing import Optional, Tuple, List, Callable
from .retrieval import get_retriever
from .generation import generate_answer

class PsyRAGCore:
    def __init__(self, k: int = 5):
        self.retriever = None
        self.k = k
    
    def initialize_retriever(self, k: Optional[int] = None):
        """Initialize or update retriever"""
        if k is not None:
            self.k = k
        self.retriever = get_retriever(k=self.k)
    
    def process_query(
        self, 
        query: str, 
        expand: bool = True, 
        k: Optional[int] = None,
        progress_callback: Optional[Callable] = None
    ) -> Tuple[str, List[str]]:
        """Process a query and return answer with expanded queries"""
        if k is not None and k != self.k:
            self.k = k
            self.retriever = None  # Force re-initialization
        
        if self.retriever is None:
            self.initialize_retriever()
        
        return generate_answer(
            query=query,
            retriever=self.retriever,
            expand=expand,
            return_expanded=True,
            k=self.k,
            progress_callback=progress_callback
        )