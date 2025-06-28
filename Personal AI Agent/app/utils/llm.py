import os
import logging
import json
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

from llama_cpp import Llama
from app.core.config import settings
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

def get_llm_model():
    """Get the LLM model instance (lazy loading)"""
    global _llm_model
    
    if _llm_model is None:
        try:
            # Check if model exists
            if not os.path.exists(settings.LLM_MODEL_PATH):
                raise FileNotFoundError(f"LLM model not found at {settings.LLM_MODEL_PATH}")
                
            # Load the model
            logger.info(f"Loading LLM model from {settings.LLM_MODEL_PATH}")
            
            # Configure model parameters
            model_params = {
                "model_path": settings.LLM_MODEL_PATH,
                "n_ctx": settings.LLM_CONTEXT_WINDOW,
                "n_threads": settings.LLM_THREADS,
                "verbose": False,  # Reduce noise in logs
            }
            
            # Add Metal acceleration if enabled with optimized parameters
            if settings.USE_METAL:
                logger.info(f"Enabling Metal acceleration with {settings.METAL_N_GPU_LAYERS} GPU layers")
                model_params["n_gpu_layers"] = settings.METAL_N_GPU_LAYERS
                model_params["offload_kqv"] = True  # Offload key/query/value matrices to GPU
                
            logger.info(f"Model parameters: {model_params}")
                
            # Load the model with configured parameters
            _llm_model = Llama(**model_params)
            
            logger.info("LLM model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading LLM model: {str(e)}")
            raise
    
    return _llm_model

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
    
    # Assess response quality
    quality = assess_response_quality(answer, query, context_chunks)
    
    if quality == ResponseQuality.EMPTY:
        logger.warning("LLM returned empty response")
        return get_response_template("error_fallback", "generation")
    
    elif quality == ResponseQuality.HALLUCINATION:
        query_type, _ = classify_query_type(query)
        if query_type == QueryType.PERSONAL_DATA:
            logger.warning("Detected hallucination in personal data query")
            return get_response_template("hallucination_detected", "personal_query")
        else:
            logger.warning("Detected general knowledge response for document-specific query")
            return get_response_template("hallucination_detected", "general_query")
    
    elif quality == ResponseQuality.ERROR:
        logger.warning("Response contains error indicators")
        return get_response_template("error_fallback", "processing")
    
    # Additional validation: Check if response is too generic for a personal query
    query_type, confidence = classify_query_type(query)
    if query_type == QueryType.PERSONAL_DATA and confidence > 0.7:
        # Check if response mentions "you" or personal references
        if not any(pronoun in answer.lower() for pronoun in ["you", "your", "you're", "you've"]):
            # Check if there's actual personal data in the context
            has_personal_context = False
            for chunk in context_chunks:
                content = ""
                if hasattr(chunk, 'page_content'):
                    content = chunk.page_content.lower()
                elif isinstance(chunk, dict) and "content" in chunk:
                    content = chunk["content"].lower()
                
                if any(keyword in content for keyword in ["eugene", "expense", "$", "skill", "experience", "vacation"]):
                    has_personal_context = True
                    break
            
            if not has_personal_context:
                return get_response_template("no_context_found", "general")
    
    return answer

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
        # Classify query type
        query_type, confidence = classify_query_type(query)
        logger.info(f"Query classified as {query_type.value} with confidence {confidence:.2f}")
        
        # Check if the query contains first-person references
        has_first_person = any(word in query.lower() for word in ["i ", "my ", "me ", "mine ", "i've ", "i'm ", "i'll ", "i'd "])
        use_first_person = first_person_mode or has_first_person
        
        # Create system prompt based on query type
        system_message = create_system_prompt(query_type, use_first_person)
        
        # Process context chunks
        context_content = ""
        for i, chunk in enumerate(context_chunks):
            # Extract content based on chunk type
            if hasattr(chunk, 'page_content') and hasattr(chunk, 'metadata'):
                content = chunk.page_content
                metadata = chunk.metadata
            else:
                content = chunk.get("content", "")
                metadata = chunk.get("metadata", {})
            
            if content:
                source_info = f"[SOURCE {i+1}]: "
                if metadata:
                    if "title" in metadata:
                        source_info += f"Title: {metadata['title']} | "
                    if "source" in metadata:
                        source_info += f"Source: {metadata['source']} | "
                
                context_content += f"{source_info}\n{content}\n\n"
        
        # Log context usage
        logger.info(f"Using {len(context_chunks)} chunks for {query_type.value} query")
        logger.info(f"Context content length: {len(context_content)} chars")
        
        # Create the full prompt
        prompt = f"""<s>[INST] {system_message}

CONTEXT INFORMATION:
{context_content}

USER QUESTION: {query}

Please provide your answer based strictly on the context above: [/INST]"""

        # Check prompt length and truncate if necessary
        estimated_tokens = len(prompt) / 4
        max_context = settings.LLM_CONTEXT_WINDOW - 1024
        
        if estimated_tokens > max_context:
            logger.warning(f"Prompt too long (est. {estimated_tokens} tokens), truncating context")
            keep_chars = int(max_context * 3) - len(system_message) - len(query) - 300
            keep_chars = max(keep_chars, 500)
            
            if len(context_content) > keep_chars:
                context_content = "..." + context_content[-keep_chars:]
            
            prompt = f"""<s>[INST] {system_message}

Context:
{context_content}

User Question: {query} [/INST]"""
        
        # Get the LLM model
        model = get_llm_model()
        
        # Get LLM parameters from configuration
        config = get_ai_config()
        
        # Generate response with configured parameters
        response = model(
            prompt,
            max_tokens=config["max_tokens"],
            temperature=config["temperature"],
            top_p=config["top_p"],
            top_k=config["top_k"],
            repeat_penalty=config["repeat_penalty"],
            stop=["</s>", "[INST]", "[/INST]", "USER QUESTION:", "CONTEXT INFORMATION:"]
        )
        
        # Extract response text
        if isinstance(response, dict) and 'choices' in response:
            raw_answer = response['choices'][0]['text'].strip()
        elif isinstance(response, str):
            raw_answer = response.strip()
        else:
            raw_answer = str(response).strip()
        
        # Validate and clean the response
        final_answer = validate_and_clean_response(raw_answer, query, context_chunks)
        
        logger.info(f"Generated response (length: {len(final_answer)} chars): {final_answer[:100]}...")
        
        return final_answer
        
    except Exception as e:
        error_msg = f"Error generating response: {str(e)}"
        logger.error(error_msg)
        return f"I apologize, but I encountered an error while processing your request. Please try again with a different question."

# Remove the global cache as it can cause inconsistent responses
async def generate_answer(query: str, context_chunks: List[Dict[Any, Any]]) -> str:
    """
    Generate an answer to a query using the provided context chunks
    
    Args:
        query: The user's query
        context_chunks: List of context chunks to use for answering
        
    Returns:
        The generated answer
    """
    try:
        # Check if the query contains first-person references
        first_person_mode = any(word in query.lower() for word in ["i ", "my ", "me ", "mine ", "i've ", "i'm ", "i'll ", "i'd "])
        
        # Generate response
        response = generate_response(query, context_chunks, first_person_mode)
        
        return response
    except Exception as e:
        logger.error(f"Error generating answer: {str(e)}")
        return "I apologize, but I encountered an error while generating an answer. Please try again." 