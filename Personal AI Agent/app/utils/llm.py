import os
import logging
import json
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

from llama_cpp import Llama
from app.core.config import settings
from app.core.constants import LLM_CONTEXT_DEFAULT, LLM_MAX_TOKENS_DEFAULT
from app.utils.ai_config import (
    get_ai_config, get_query_classification_keywords,
    get_response_template, get_system_prompt, AIBehaviorMode,
    ResponseValidationLevel, SYSTEM_PROMPTS
)

# Get the logger
logger = logging.getLogger("personal_ai_agent")

# Global LLM model instance
_llm_model = None

class QueryType(Enum):
    """Enum for different types of queries"""
    PERSONAL_DATA = "personal_data"  # User's personal information from documents
    GENERAL_KNOWLEDGE = "general_knowledge"  # General AI/tech questions
    MIXED = "mixed"  # Questions that could be both

class ResponseQuality(Enum):
    """Enum for response quality assessment"""
    GOOD = "good"
    EMPTY = "empty"
    HALLUCINATION = "hallucination"
    ERROR = "error"

def get_llm():
    """
    Get the LLM model (lazy loading)
    
    Returns:
        The LLM model
    """
    global _llm_model
    
    if _llm_model is None:
        try:
            logger.info("Initializing LLM model")
            
            # Load model configuration
            model_path = settings.LLM_MODEL_PATH
            
            # Check if Metal acceleration is enabled
            use_metal = settings.USE_METAL
            metal_n_gpu_layers = settings.METAL_N_GPU_LAYERS
            
            logger.info(f"Loading LLM model from {model_path} (Metal: {use_metal}, GPU Layers: {metal_n_gpu_layers})")
            
            # Configure model parameters
            model_kwargs = {}
            if use_metal:
                model_kwargs["n_gpu_layers"] = metal_n_gpu_layers
                logger.info(f"Using Metal acceleration with {metal_n_gpu_layers} GPU layers")
            
            # Initialize the model
            _llm_model = Llama(
                model_path=model_path,
                n_ctx=settings.LLM_CONTEXT_WINDOW,
                **model_kwargs
            )
            
            logger.info("LLM model initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing LLM model: {str(e)}")
            raise
    
    return _llm_model

def estimate_token_count(text: str) -> int:
    """
    Estimate token count for text (rough approximation: 1 token ≈ 4 characters)
    
    Args:
        text: The text to estimate tokens for
        
    Returns:
        Estimated token count
    """
    return len(text) // 4

def truncate_context_to_fit(query: str, context_content: List[str], max_response_tokens: int = None) -> List[str]:
    """
    Truncate context content to fit within the model's context window
    
    Args:
        query: The user's query
        context_content: List of context strings
        max_response_tokens: Maximum tokens to reserve for response
        
    Returns:
        Truncated context content that fits within context window
    """
    if max_response_tokens is None:
        max_response_tokens = settings.LLM_MAX_TOKENS
    
    # Reserve tokens for system prompt, query, and response
    base_prompt_template = """<s>[INST] You are a helpful AI assistant that answers questions based on provided context.

CONTEXT INFORMATION:
{context}

USER QUESTION:
{query}

INSTRUCTIONS FOR YOUR RESPONSE:
- Answer the user's question based on the provided context information.
- If the context doesn't contain the information needed to answer the question, say so clearly.
- Be concise and direct in your response.
- Focus only on answering the specific question asked.
- Do not mention that your answer is based on the provided context.
- Do not apologize or use phrases like "Based on the provided information".
- If you find relevant information in the context, provide a detailed and helpful answer.
- Use simple, clear language.

CRITICAL RULES:
- Never make up information that isn't in the context.
- Never say "I don't have information" if the information is actually in the context.
- If the context contains the answer, always provide it.
[/INST]"""
    
    # Estimate tokens for base prompt structure
    base_tokens = estimate_token_count(base_prompt_template.format(context="", query=query))
    
    # Calculate available tokens for context
    available_context_tokens = settings.LLM_CONTEXT_WINDOW - base_tokens - max_response_tokens
    available_context_tokens = max(100, available_context_tokens)  # Ensure minimum context
    
    logger.info(f"Context window: {settings.LLM_CONTEXT_WINDOW}, base tokens: {base_tokens}, "
                f"response tokens: {max_response_tokens}, available for context: {available_context_tokens}")
    
    # Truncate context to fit
    truncated_content = []
    current_tokens = 0
    
    for content in context_content:
        content_tokens = estimate_token_count(content)
        if current_tokens + content_tokens <= available_context_tokens:
            truncated_content.append(content)
            current_tokens += content_tokens
        else:
            # Try to fit a partial chunk
            remaining_tokens = available_context_tokens - current_tokens
            if remaining_tokens > 50:  # Only include if we have reasonable space
                chars_to_include = remaining_tokens * 4
                partial_content = content[:chars_to_include] + "..."
                truncated_content.append(partial_content)
            break
    
    if len(truncated_content) < len(context_content):
        logger.warning(f"Context truncated from {len(context_content)} to {len(truncated_content)} chunks "
                      f"to fit context window")
    
    return truncated_content

def classify_query_type(query: str) -> Tuple[QueryType, float]:
    """
    Classify the query type and return confidence score
    
    Args:
        query: The user's query
        
    Returns:
        Tuple of (QueryType, confidence_score)
    """
    query_lower = query.lower()
    
    # Get keywords from configuration
    keywords = get_query_classification_keywords()
    general_ai_keywords = keywords["general_ai_keywords"]
    personal_data_keywords = keywords["personal_data_keywords"]
    
    # Count keyword matches
    general_matches = sum(1 for keyword in general_ai_keywords if keyword in query_lower)
    personal_matches = sum(1 for keyword in personal_data_keywords if keyword in query_lower)
    
    # Calculate confidence based on keyword density
    total_words = len(query_lower.split())
    general_confidence = min(general_matches / max(total_words, 1), 1.0)
    personal_confidence = min(personal_matches / max(total_words, 1), 1.0)
    
    # Determine query type
    if general_confidence > personal_confidence and general_confidence > 0.1:
        return QueryType.GENERAL_KNOWLEDGE, general_confidence
    elif personal_confidence > 0.1:
        return QueryType.PERSONAL_DATA, personal_confidence
    else:
        return QueryType.MIXED, 0.5

def assess_response_quality(response: str, query: str, context_chunks: List[Any]) -> ResponseQuality:
    """
    Assess the quality of a generated response
    
    Args:
        response: The generated response
        query: The original query
        context_chunks: The context used for generation
        
    Returns:
        ResponseQuality enum value
    """
    config = get_ai_config()
    
    if not response or len(response.strip()) < config["min_response_length"]:
        return ResponseQuality.EMPTY
    
    response_lower = response.lower()
    
    # Check for hallucination indicators (general AI knowledge in personal queries)
    query_type, _ = classify_query_type(query)
    
    if query_type == QueryType.PERSONAL_DATA:
        # Check if response contains general AI knowledge instead of personal data
        ai_knowledge_indicators = config["hallucination_indicators"]
        
        if any(indicator in response_lower for indicator in ai_knowledge_indicators):
            return ResponseQuality.HALLUCINATION
    
    # Check for error indicators
    error_indicators = config["error_indicators"]
    
    if any(indicator in response_lower for indicator in error_indicators):
        return ResponseQuality.ERROR
    
    return ResponseQuality.GOOD

def create_system_prompt(query_type: QueryType, is_first_person: bool = False) -> str:
    """
    Create a system prompt based on query type
    
    Args:
        query_type: The type of query being processed
        is_first_person: Whether to use first person mode
        
    Returns:
        The system prompt string
    """
    # Get base prompt from configuration
    base_prompt = SYSTEM_PROMPTS["base"]

    if query_type == QueryType.GENERAL_KNOWLEDGE:
        base_prompt += SYSTEM_PROMPTS["general_knowledge"]
    elif query_type == QueryType.PERSONAL_DATA:
        base_prompt += SYSTEM_PROMPTS["personal_data"]

    if is_first_person:
        base_prompt += """

RESPONSE FORMAT: The user is asking about their own information, so phrase your response using SECOND-PERSON pronouns (you, your).
For example, say "You went to Thailand in 2023" instead of "I went to Thailand in 2023"."""

    return base_prompt

def validate_and_clean_response(response: str, query: str, context_chunks: List[Any]) -> str:
    """
    Validate and clean the LLM response
    
    Args:
        response: The raw LLM response
        query: The original query
        context_chunks: The context used for generation
        
    Returns:
        The cleaned and validated response
    """
    # Basic cleaning
    answer = response.strip()
    answer = answer.replace("[INST]", "").replace("[/INST]", "").strip()
    answer = answer.replace("</s>", "").strip()
    
    # Remove any repeated instruction text that might leak through
    cleanup_phrases = [
        "CONTEXT INFORMATION:",
        "USER QUESTION:",
        "INSTRUCTIONS FOR YOUR RESPONSE:",
        "CRITICAL RULES:",
        "IMPORTANT:"
    ]
    
    for phrase in cleanup_phrases:
        if phrase in answer:
            answer = answer.split(phrase)[0].strip()
    
    # If response is empty after cleaning, return a helpful message
    if not answer or len(answer.strip()) < 10:
        logger.warning("LLM returned empty response")
        query_type, _ = classify_query_type(query)
        
        if query_type == QueryType.PERSONAL_DATA:
            return "I found some information in your documents but need to process it differently. Could you try rephrasing your question to be more specific about what you're looking for?"
        else:
            return "I understand your question about " + query.lower().replace("?", "").strip() + ". Let me try to explain based on the available information. " + get_response_template("error_fallback", "generation")
    
    # Assess response quality
    quality = assess_response_quality(answer, query, context_chunks)
    
    if quality == ResponseQuality.EMPTY:
        return "I found relevant information but need to process it differently. Could you try asking about a specific aspect of your question?"
    
    elif quality == ResponseQuality.HALLUCINATION:
        query_type, _ = classify_query_type(query)
        if query_type == QueryType.PERSONAL_DATA:
            return "I found some personal information in your documents but need to understand your question better. Could you be more specific about what you're looking for?"
        else:
            return "I have some information that might help answer your question about " + query.lower().replace("?", "").strip() + ". Could you clarify which aspect you're most interested in?"
    
    elif quality == ResponseQuality.ERROR:
        return "I found some relevant information but encountered an issue processing it. Could you try rephrasing your question to focus on a specific aspect?"
    
    return answer

def generate_prompt(query: str, context_chunks: List[str], first_person_mode: bool = False) -> str:
    """
    Generate a prompt for the LLM
    
    Args:
        query: The user's query
        context_chunks: The context chunks to use for answering
        first_person_mode: Whether to respond in first person (as if AI is the user)
        
    Returns:
        The generated prompt
    """
    # Build the context string while keeping track of length to avoid exceeding the model context window
    formatted_context = ""
    max_context_chars = 6000  # ~1.5k tokens, leave room for instructions and answer
    for i, chunk in enumerate(context_chunks):
        if len(formatted_context) >= max_context_chars:
            logger.info("Reached maximum context size, stopping additional chunks")
            break
        # Truncate individual chunk if it is extremely long
        safe_chunk = chunk[:2000]  # cap each chunk to 2k characters
        formatted_context += f"CHUNK {i+1}:\n{safe_chunk}\n\n"
    
    # Create the prompt
    prompt = f"""[INST]
CONTEXT INFORMATION:
{formatted_context}

USER QUESTION:
{query}

INSTRUCTIONS FOR YOUR RESPONSE:
- Answer the user's question based on the provided context information.
- If the context doesn't contain the information needed to answer the question, say so clearly.
- Be concise and direct in your response.
- Focus only on answering the specific question asked.
- Do not mention that your answer is based on the provided context.
- Do not apologize or use phrases like "Based on the provided information".
- If you find relevant information in the context, provide a detailed and helpful answer.
- Use simple, clear language.
{'- Respond in first person, as if you are the user.' if first_person_mode else ''}

CRITICAL RULES:
- Never make up information that isn't in the context.
- Never say "I don't have information" if the information is actually in the context.
- If the context contains the answer, always provide it.
[/INST]"""
    
    return prompt

def generate_response(query: str, context_chunks: List[Any], first_person_mode: bool = False) -> str:
    """
    Generate a response to a query using the local LLM
    
    Args:
        query: The user's query
        context_chunks: List of context chunks to use for answering
        first_person_mode: Whether to respond in first person (as if AI is the user)
        
    Returns:
        The generated response
    """
    try:
        # Extract content from chunks if they are dictionaries
        context_content = []
        for chunk in context_chunks:
            if isinstance(chunk, dict):
                content = chunk.get('content', '')
                if content:
                    context_content.append(content)
            elif hasattr(chunk, 'page_content'):
                context_content.append(chunk.page_content)
            else:
                context_content.append(str(chunk))
        
        # Get AI config to know max_tokens
        ai_config = get_ai_config()
        
        # Truncate context to fit within context window
        truncated_context = truncate_context_to_fit(query, context_content, ai_config["max_tokens"])
        
        # Generate the prompt
        prompt = generate_prompt(query, truncated_context, first_person_mode)
        
        # Log the prompt length and token estimate
        estimated_tokens = estimate_token_count(prompt)
        logger.info(f"Generated prompt with {len(prompt)} characters, estimated {estimated_tokens} tokens")
        
        # Validate that prompt + response fits within context window
        total_tokens_needed = estimated_tokens + ai_config["max_tokens"]
        if total_tokens_needed > settings.LLM_CONTEXT_WINDOW:
            logger.error(f"Total tokens needed ({total_tokens_needed}) exceeds context window ({settings.LLM_CONTEXT_WINDOW})")
            return "The question requires too much context to process. Please try a more specific question or upload fewer/shorter documents."
        
        # Initialize the LLM
        llm = get_llm()
        
        # Generate the response
        logger.info("Generating response with LLM")
        raw_response = llm(
            prompt,
            max_tokens=ai_config["max_tokens"],
            temperature=ai_config["temperature"],
            top_p=ai_config["top_p"],
            top_k=ai_config["top_k"],
            repeat_penalty=ai_config["repeat_penalty"]
        )

        # Extract text from response depending on type
        if isinstance(raw_response, str):
            response_text = raw_response
        elif isinstance(raw_response, dict):
            # llama_cpp returns a dict with 'choices'
            response_text = raw_response.get("choices", [{}])[0].get("text", "")
        else:
            # Fallback to string representation
            response_text = str(raw_response)

        # Clean and validate the response
        cleaned_response = validate_and_clean_response(response_text, query, context_chunks)
        
        # Check if the response is empty or too short
        if not cleaned_response or len(cleaned_response) < ai_config["min_response_length"]:
            logger.warning("LLM returned empty response")
            return "I couldn't find a good answer to your question in the provided documents. Please try rephrasing your question or upload more relevant documents."
        
        return cleaned_response
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        logger.exception("Full exception details:")
        return f"Error generating response: {str(e)}"

# Remove the global cache as it can cause inconsistent responses
async def generate_answer(query: str, context_chunks: List[Dict[Any, Any]]) -> str:
    """
    Generate an answer to a query using the LLM and context chunks
    
    Args:
        query: The user's query
        context_chunks: The context chunks to use for generating the answer
        
    Returns:
        The generated answer
    """
    try:
        logger.info(f"Generating answer for query: '{query}' with {len(context_chunks)} context chunks")
        
        # Check if we have any context chunks
        if not context_chunks:
            logger.warning("No context chunks provided for query")
            return "I don't have enough information to answer that question. Please upload relevant documents first or try a different question."
        
        # Log the scores of the context chunks
        scores = [chunk.get('score', 0) for chunk in context_chunks]
        logger.info(f"Context chunk scores: {[round(score, 2) for score in scores]}")
        
        # Extract content from chunks
        context_content = []
        for i, chunk in enumerate(context_chunks):
            # Get content and metadata
            content = chunk.get('content', '')
            metadata = chunk.get('metadata', {})
            score = chunk.get('score', 0)
            
            # Log chunk details
            logger.debug(f"Chunk {i+1} - Score: {score:.2f}, Source: {metadata.get('source', 'unknown')}, Length: {len(content)} chars")
            
            # Add content to context
            if content:
                context_content.append(content)
        
        # Generate response
        logger.info(f"Generating response with {len(context_content)} content chunks")
        response = generate_response(query, context_content)
        
        # Check if response is empty
        if not response or len(response.strip()) < 10:
            logger.warning("LLM returned empty response")
            return "I couldn't find a good answer to your question in the provided documents. Please try rephrasing your question or upload more relevant documents."
        
        logger.info(f"Generated response of length {len(response)} chars")
        return response
    except Exception as e:
        logger.error(f"Error generating answer: {str(e)}")
        logger.exception("Full exception details:")
        return f"Error generating response: {str(e)}" 