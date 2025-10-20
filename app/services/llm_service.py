from typing import List, Dict
from openai import OpenAI
from anthropic import Anthropic
from tenacity import retry, stop_after_attempt, wait_exponential
from app.config import settings
from app.utils.logger import logger


class LLMService:
    """Handles interactions with LLM providers."""
    
    def __init__(self):
        self.provider = settings.llm_provider
        
        if self.provider == "openai":
            if not settings.openai_api_key:
                raise ValueError("OpenAI API key not configured")
            self.client = OpenAI(api_key=settings.openai_api_key)
        elif self.provider == "anthropic":
            if not settings.anthropic_api_key:
                raise ValueError("Anthropic API key not configured")
            self.client = Anthropic(api_key=settings.anthropic_api_key)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
        
        logger.info("llm_service_initialized", provider=self.provider)
    
    def _build_context(self, query: str, search_results: List[Dict]) -> str:
        """Build context from search results."""
        context_parts = ["Here is the relevant context from the documents:\n"]
        
        for i, result in enumerate(search_results, 1):
            context_parts.append(f"\n--- Document Chunk {i} ---")
            context_parts.append(result['text'])
            
            # Add metadata if available
            metadata = result.get('metadata', {})
            if 'filename' in metadata:
                context_parts.append(f"(Source: {metadata['filename']})")
        
        context = "\n".join(context_parts)
        return context
    
    def _build_prompt(self, query: str, context: str) -> str:
        """Build the final prompt for the LLM."""
        prompt = f"""You are a helpful assistant that answers questions based on the provided context.

{context}

Question: {query}

Instructions:
- Answer the question based on the context provided above
- If the context doesn't contain enough information to answer the question, say so
- Be concise and accurate
- Cite specific parts of the context when possible

Answer:"""
        return prompt
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def generate_answer(
        self, 
        query: str, 
        search_results: List[Dict]
    ) -> Dict[str, str]:
        """Generate answer using LLM based on query and context."""
        try:
            context = self._build_context(query, search_results)
            
            if self.provider == "openai":
                answer = self._generate_openai(query, context)
            else:
                answer = self._generate_anthropic(query, context)
            
            logger.info("answer_generated", query=query[:50])
            
            return {
                "answer": answer,
                "context": context,
                "num_sources": len(search_results)
            }
            
        except Exception as e:
            logger.error("answer_generation_failed", error=str(e))
            raise
    
    def _generate_openai(self, query: str, context: str) -> str:
        """Generate answer using OpenAI."""
        prompt = self._build_prompt(query, context)
        
        response = self.client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions based on provided context."},
                {"role": "user", "content": prompt}
            ],
            temperature=settings.llm_temperature,
            max_tokens=settings.max_tokens
        )
        
        return response.choices[0].message.content
    
    def _generate_anthropic(self, query: str, context: str) -> str:
        """Generate answer using Anthropic."""
        prompt = self._build_prompt(query, context)
        
        response = self.client.messages.create(
            model=settings.llm_model,
            max_tokens=settings.max_tokens,
            temperature=settings.llm_temperature,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.content[0].text


llm_service = LLMService()