"""
LangChain compatibility layer for imports across different versions.
Handles differences between LangChain 0.1.x and 0.2+ / 1.0+
"""

from typing import Callable, Any

# Document import (moved to langchain_core in newer versions)
try:
    from langchain_core.documents import Document
except ImportError:
    try:
        from langchain.schema import Document
    except ImportError as e:
        raise ImportError(
            "Cannot import Document. Install: pip install langchain-core or langchain"
        ) from e

# Text splitter imports (moved to separate package in newer versions)
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    try:
        from langchain.text_splitters import RecursiveCharacterTextSplitter
    except ImportError:
        try:
            from langchain.text_splitter import RecursiveCharacterTextSplitter
        except ImportError as e:
            raise ImportError(
                "Cannot import RecursiveCharacterTextSplitter. "
                "Install: pip install langchain-text-splitters or langchain"
            ) from e

# Prompts import (moved to langchain_core in newer versions)
try:
    from langchain_core.prompts import ChatPromptTemplate
except ImportError:
    try:
        from langchain.prompts import ChatPromptTemplate
    except ImportError as e:
        raise ImportError(
            "Cannot import ChatPromptTemplate. Install: pip install langchain-core"
        ) from e

# Chains imports (restructured in newer versions)
# In LangChain 1.0+, chains are built via composition using Runnable
def create_stuff_documents_chain(
    llm: Any, prompt: Any, document_variable_name: str = "documents"
) -> Callable:
    """
    Create a chain that stuff documents into a prompt and call the LLM.
    Works with LangChain 1.0+ using Runnable composition.
    Note: Modern LangChain uses direct composition instead of legacy chains.
    """
    # Use manual chain composition (standard approach in LangChain 1.0+)
    from langchain_core.runnables import RunnableLambda
    
    def format_and_invoke(input_data):
        """Format documents and invoke LLM through prompt."""
        # Extract documents from input
        docs = input_data.get(document_variable_name, [])
        query = input_data.get("input", "")
        
        # Format documents
        if not docs:
            formatted_docs = ""
        else:
            formatted_list = []
            for doc in docs:
                if hasattr(doc, "page_content"):
                    formatted_list.append(doc.page_content)
                else:
                    formatted_list.append(str(doc))
            formatted_docs = "\n\n".join(formatted_list)
        
        # Create prompt input dict
        prompt_input = {
            "documents": formatted_docs,
            "input": query
        }
        
        # Format and invoke
        prompt_msg = prompt.format_prompt(**prompt_input)
        response = llm.invoke(prompt_msg)
        
        # Extract text from response
        if hasattr(response, 'content'):
            return response.content
        return str(response)
    
    # Build and return the chain
    chain = RunnableLambda(format_and_invoke)
    return chain

def create_retrieval_chain(
    retriever: Any, combine_docs_chain: Any
) -> Callable:
    """
    Create a retrieval chain that retrieves documents and passes them to combine chain.
    Works with LangChain 1.0+.
    """
    try:
        # Try newer LangChain approach
        from langchain.chains.retrieval import create_retrieval_chain as _create_retrieval
        return _create_retrieval(retriever=retriever, combine_docs_chain=combine_docs_chain)
    except (ImportError, AttributeError):
        try:
            # Fallback: manual composition using Runnable
            from langchain_core.runnables import RunnablePassthrough
            from langchain_core.runnables.utils import Input, Output
            
            # Build retrieval chain manually
            def retrieve_docs(input_dict):
                query = input_dict.get("input") or input_dict.get("query", "")
                docs = retriever.invoke(query)
                input_dict["documents"] = docs
                return input_dict
            
            chain = (
                RunnablePassthrough()
                .assign(documents=lambda x: retriever.invoke(x.get("input", "")))
                | combine_docs_chain
            )
            return chain
        except Exception as e:
            raise ImportError(
                f"Cannot build retrieval chain. Error: {e}"
            ) from e

__all__ = [
    "Document",
    "RecursiveCharacterTextSplitter",
    "ChatPromptTemplate",
    "create_stuff_documents_chain",
    "create_retrieval_chain",
]
