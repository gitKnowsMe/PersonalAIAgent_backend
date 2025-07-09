import os
import logging
import json
import hashlib
import time
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

from llama_cpp import Llama
from app.core.config import settings
from app.core.constants import LLM_CONTEXT_DEFAULT, LLM_MAX_TOKENS_DEFAULT
from app.services.ai_config_service import (
    get_ai_config_service, AIBehaviorMode,
    ResponseValidationLevel
)
from app.utils.response_filter import vacation_filter, financial_filter, response_validator

# Get the logger
logger = logging.getLogger("personal_ai_agent")

# Global LLM model instance
_llm_model = None
_current_model_path = None

# Response cache for identical queries
_response_cache = {}

# Available models
AVAILABLE_MODELS = {
    "mistral-7b": "mistral-7b-instruct-v0.1.Q4_K_M.gguf",
    "phi-2": "phi-2-instruct-Q4_K_M.gguf"
}

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

def get_llm(model_name: str = None):
    """
    Get the LLM model (lazy loading)
    
    Args:
        model_name: Name of the model to use (mistral-7b, phi-2) or None for default
    
    Returns:
        The LLM model
    """
    global _llm_model, _current_model_path
    
    # Determine model path
    if model_name:
        if model_name not in AVAILABLE_MODELS:
            raise ValueError(f"Model {model_name} not available. Choose from: {list(AVAILABLE_MODELS.keys())}")
        model_filename = AVAILABLE_MODELS[model_name]
        model_path = str(settings.BASE_DIR / "models" / model_filename)
    else:
        model_path = settings.LLM_MODEL_PATH
    
    # Check if we need to reload the model (different model or first load)
    if _llm_model is None or _current_model_path != model_path:
        try:
            # Reset if switching models
            if _llm_model is not None and _current_model_path != model_path:
                logger.info(f"Switching from {_current_model_path} to {model_path}")
                reset_llm()
            
            logger.info(f"Initializing LLM model: {model_name or 'default'}")
            
            # Check if model file exists
            if not os.path.exists(model_path):
                logger.error(f"LLM model file not found: {model_path}")
                raise FileNotFoundError(f"LLM model file not found: {model_path}")
            
            # Check if Metal acceleration is enabled
            use_metal = settings.USE_METAL
            metal_n_gpu_layers = settings.METAL_N_GPU_LAYERS
            
            logger.info(f"Loading LLM model from {model_path} (Metal: {use_metal}, GPU Layers: {metal_n_gpu_layers})")
            
            # Configure model parameters
            model_kwargs = {
                "verbose": False,  # Reduce verbose output
                "use_mlock": True,  # Use memory locking for better performance
                "use_mmap": True,   # Use memory mapping
                "n_threads": settings.LLM_THREADS,  # Set thread count
            }
            
            if use_metal:
                model_kwargs["n_gpu_layers"] = metal_n_gpu_layers
                logger.info(f"Using Metal acceleration with {metal_n_gpu_layers} GPU layers")
            
            # Initialize the model with error handling
            _llm_model = Llama(
                model_path=model_path,
                n_ctx=settings.LLM_CONTEXT_WINDOW,
                **model_kwargs
            )
            
            _current_model_path = model_path
            logger.info(f"LLM model {model_name or 'default'} initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing LLM model: {str(e)}")
            _llm_model = None  # Reset to None so it can be retried
            _current_model_path = None
            raise
    
    return _llm_model

def reset_llm():
    """
    Reset the LLM model (useful for recovery from errors)
    """
    global _llm_model, _current_model_path
    if _llm_model is not None:
        logger.info("Resetting LLM model")
        try:
            # Try to close the model gracefully if possible
            del _llm_model
        except Exception as e:
            logger.warning(f"Error during LLM model cleanup: {str(e)}")
        _llm_model = None
        _current_model_path = None

def clear_response_cache():
    """
    Clear the response cache
    """
    global _response_cache
    logger.info("Clearing response cache")
    _response_cache.clear()

def get_current_model_info():
    """
    Get information about the currently loaded model
    
    Returns:
        Dict with model info
    """
    global _current_model_path
    if _current_model_path:
        model_name = None
        for name, filename in AVAILABLE_MODELS.items():
            if filename in _current_model_path:
                model_name = name
                break
        
        return {
            "model_name": model_name or "unknown",
            "model_path": _current_model_path,
            "loaded": _llm_model is not None
        }
    return {"model_name": None, "model_path": None, "loaded": False}

def estimate_token_count(text: str) -> int:
    """
    Estimate token count for text (optimized for speed and accuracy)
    
    Args:
        text: The text to estimate tokens for
        
    Returns:
        Estimated token count
    """
    # More accurate estimation: ~1.3 tokens per word on average
    return max(1, int(len(text.split()) * 1.3))

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

FINANCIAL TRANSACTION KNOWLEDGE:
- THY = Turkish Airlines (Turkey/Istanbul)
- Foreign Exchange Rate Adjustment Fees are charges for international transactions
- Card purchases at international merchants may include location-specific spending
- When asked about spending in a specific location, look for:
  * Airlines from that country (e.g., THY for Turkey/Istanbul)
  * Foreign exchange fees related to transactions
  * Merchant names that might relate to the location

INSTRUCTIONS FOR YOUR RESPONSE:
- Answer the user's question based on the provided context information.
- Be CONCISE and DIRECT - provide only the essential information needed to answer the question.
- Focus ONLY on answering the specific question asked - do not provide extra context unless directly relevant.
- If the question asks for a specific amount, date, or fact, provide just that information.
- Do not include related information unless it directly answers the question.
- If the context doesn't contain the information needed to answer the question, say so clearly.
- Do not mention that your answer is based on the provided context.
- Use simple, clear language and avoid unnecessary details.

CRITICAL RULES:
- Never make up information that isn't in the context.
- Be as brief as possible while still being helpful.
- For financial questions, provide the specific amount and date if available.
- For location-specific spending questions, identify relevant transactions by merchant codes, airline codes, or foreign exchange fees.
- For factual questions, provide the direct answer without elaboration.
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
    
    # Define keywords directly since query classification is deprecated
    general_ai_keywords = [
        "how", "what", "why", "when", "where", "explain", "define", "tell me",
        "artificial intelligence", "machine learning", "programming", "code"
    ]
    personal_data_keywords = [
        "my", "i", "me", "personal", "document", "file", "upload", "search"
    ]
    
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
    service = get_ai_config_service()
    config = service.get_ai_config()
    
    if not response or len(response.strip()) < config.min_response_length:
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
    # Get system prompt from AI config service
    service = get_ai_config_service()
    
    if query_type == QueryType.GENERAL_KNOWLEDGE:
        base_prompt = service.get_system_prompt("general_knowledge")
    elif query_type == QueryType.PERSONAL_DATA:
        base_prompt = service.get_system_prompt("personal_data")
    else:
        base_prompt = service.get_system_prompt("default")

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
        logger.warning(f"LLM returned empty response: '{answer}' (length: {len(answer) if answer else 0})")
        # Handle empty or short responses
        if not answer:
            return "I couldn't generate a proper response to your question."
        else:
            return "The response seems incomplete. Please try rephrasing your question."
    
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

def generate_prompt(query: str, context_chunks: List[str], first_person_mode: bool = False, model_name: str = None) -> str:
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
    max_context_chars = 2000  # Reduced from 6000 for more focused responses
    for i, chunk in enumerate(context_chunks):
        if len(formatted_context) >= max_context_chars:
            logger.info("Reached maximum context size, stopping additional chunks")
            break
        # Truncate individual chunk if it is extremely long
        safe_chunk = chunk[:600]  # Reduced from 2000 for more focused responses
        formatted_context += f"{safe_chunk}\n\n"
    
    # Create model-specific prompts
    if model_name == "phi-2":
        # Detect if this is a vacation query and apply specific rules
        is_vacation_query = any(keyword in query.lower() for keyword in ['vacation', 'travel', 'trip', 'holiday', 'went', 'visit'])
        
        vacation_rules = ""
        if is_vacation_query:
            vacation_rules = """
- IMPORTANT: Answer only what is specifically asked. If asked "where", give only the destination."""

        # Detect if this is a financial query
        is_financial_query = any(keyword in query.lower() for keyword in ['paid', 'sent', 'spent', 'cost', 'money', 'dollar', '$', 'payment', 'transaction', 'zelle', 'venmo', 'paypal'])
        
        financial_rules = ""
        if is_financial_query:
            financial_rules = """
- CRITICAL: For financial queries, only include amounts that EXACTLY match the merchant/person mentioned in the question
- Do NOT include amounts from other transactions that happen to be in the same text chunk
- If asked about payments to a specific person or merchant, only report amounts for that exact person/merchant
- If multiple transactions to the same person/merchant exist, list each one separately with dates if available"""

        # Phi-2 works better with structured but concise prompts
        prompt = f"""You are a helpful assistant. Answer the question using only the provided context.

CONTEXT:
{formatted_context}

QUESTION: {query}

INSTRUCTIONS:
- Use only information from the context above
- Give a direct, complete answer
- If the context doesn't contain the answer, say "I don't have that information"
- Be specific with numbers, dates, and amounts when available
- IMPORTANT: Look through ALL context chunks to find ALL relevant information
- Answer ONLY what is specifically asked - do not provide additional details unless requested{vacation_rules}{financial_rules}

ANSWER:"""
    else:
        # Detect if this is a financial query
        is_financial_query = any(keyword in query.lower() for keyword in ['paid', 'sent', 'spent', 'cost', 'money', 'dollar', '$', 'payment', 'transaction', 'zelle', 'venmo', 'paypal'])
        
        financial_instructions = ""
        if is_financial_query:
            financial_instructions = """
- CRITICAL: For financial queries, only include amounts that EXACTLY match the merchant/person mentioned in the question
- Do NOT include amounts from other transactions that happen to be in the same text chunk
- If asked about payments to a specific person or merchant, only report amounts for that exact person/merchant
- If multiple transactions to the same person/merchant exist, list each one separately with dates if available"""
        else:
            financial_instructions = """
- For financial questions asking "how much", add up all relevant amounts to give the total"""

        # Mistral-7B format (default) - Enhanced to handle aggregation
        prompt = f"""<s>[INST] {query}

Context:
{formatted_context}

Please provide a clear explanation based on the context above. 

IMPORTANT INSTRUCTIONS:
- Look through ALL the context information provided
- Be specific with numbers, dates, and amounts when available{financial_instructions}
[/INST]"""
    
    return prompt

def generate_response(query: str, context_chunks: List[Any], first_person_mode: bool = False, model_name: str = None) -> str:
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
        service = get_ai_config_service()
        ai_config = service.get_ai_config()
        
        # Limit context for more focused responses - take only the most relevant chunks
        limited_context = context_content[:3]  # Limit to 3 most relevant chunks maximum
        
        # Truncate context to fit within context window
        truncated_context = truncate_context_to_fit(query, limited_context, ai_config.max_tokens)
        
        # Determine actual model name if not provided
        if model_name is None:
            model_info = get_current_model_info()
            detected_model = model_info.get('model_name', 'unknown')
            model_name = detected_model if detected_model != 'unknown' else None
        
        # Generate the prompt
        prompt = generate_prompt(query, truncated_context, first_person_mode, model_name)
        
        # Log the prompt length and token estimate
        estimated_tokens = estimate_token_count(prompt)
        logger.info(f"Generated prompt with {len(prompt)} characters, estimated {estimated_tokens} tokens")
        
        # Validate that prompt + response fits within context window
        total_tokens_needed = estimated_tokens + ai_config.max_tokens
        if total_tokens_needed > settings.LLM_CONTEXT_WINDOW:
            logger.error(f"Total tokens needed ({total_tokens_needed}) exceeds context window ({settings.LLM_CONTEXT_WINDOW})")
            return "The question requires too much context to process. Please try a more specific question or upload fewer/shorter documents."
        
        # Initialize the LLM with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                llm = get_llm(model_name)
                
                # Generate the response
                logger.info(f"Generating response with LLM (attempt {attempt + 1}/{max_retries})")
                raw_response = llm(
                    prompt,
                    max_tokens=ai_config.max_tokens,
                    temperature=ai_config.temperature,
                    top_p=ai_config.top_p,
                    top_k=ai_config.top_k,
                    repeat_penalty=ai_config.repeat_penalty,
                    echo=False,  # Don't echo the prompt back
                    stop=["</s>"]  # Stop tokens
                )
                break  # Success, exit retry loop
                
            except (BrokenPipeError, OSError, IOError) as pipe_error:
                logger.warning(f"Pipe error on attempt {attempt + 1}: {str(pipe_error)}")
                if attempt < max_retries - 1:
                    # Reset the LLM and try again
                    reset_llm()
                    time.sleep(1)  # Brief pause before retry
                    continue
                else:
                    logger.error(f"All {max_retries} attempts failed with pipe errors")
                    return "I'm experiencing technical difficulties generating a response right now. Please try again in a moment."
            except Exception as llm_error:
                logger.error(f"LLM error on attempt {attempt + 1}: {str(llm_error)}")
                if attempt < max_retries - 1:
                    # Reset the LLM and try again for certain errors
                    if "broken pipe" in str(llm_error).lower() or "connection" in str(llm_error).lower():
                        reset_llm()
                        time.sleep(1)
                        continue
                raise  # Re-raise non-recoverable errors

        # Extract text from response depending on type
        if isinstance(raw_response, str):
            response_text = raw_response
        elif isinstance(raw_response, dict):
            # llama_cpp returns a dict with 'choices'
            response_text = raw_response.get("choices", [{}])[0].get("text", "")
        else:
            # Fallback to string representation
            response_text = str(raw_response)
        
        # Log raw response for debugging
        logger.info(f"Raw LLM response (length {len(response_text)}): '{response_text[:200]}...'")  # First 200 chars

        # Clean and validate LLM response
        cleaned_response = response_text.strip()
        cleaned_response = cleaned_response.replace("[INST]", "").replace("[/INST]", "").strip()
        cleaned_response = cleaned_response.replace("</s>", "").strip()
        
        # If LLM response is empty but we have context chunks, create a basic answer
        if not cleaned_response and context_chunks:
            logger.warning("LLM failed, creating basic answer from context chunks")
            
            # For financial queries asking "how much", try to aggregate all relevant chunks
            if any(phrase in query.lower() for phrase in ["how much", "total", "amount"]):
                relevant_chunks = []
                query_lower = query.lower()
                
                # Extract specific entity names from query (remove common/generic words)
                import re
                
                # Clean the query and extract meaningful terms
                cleaned_query = re.sub(r'[^\w\s]', ' ', query_lower)  # Remove punctuation
                words = cleaned_query.split()
                
                # Filter out common question words and generic financial terms
                stop_words = {"how", "much", "did", "invest", "with", "send", "sent", "pay", "paid", "spend", 
                            "money", "total", "amount", "from", "what", "when", "where", 
                            "will", "does", "have", "the", "and", "for", "via", "using",
                            "was", "is", "to", "on"}
                
                # Get specific entity names (proper nouns and specific terms)
                # Focus on people, companies, and payment methods, not action words
                entity_terms = [word for word in words if len(word) > 3 and word not in stop_words]
                
                # Find chunks that contain the specific entities mentioned in the query
                for chunk in context_chunks:
                    content = chunk.get('content', '') if isinstance(chunk, dict) else str(chunk)
                    content_lower = content.lower()
                    
                    # For specific person/entity combinations, require ALL terms to be present
                    # This handles cases like "Andy Eckman via Zelle" where we want ONLY
                    # chunks that contain both the person AND the payment method
                    if len(entity_terms) > 1:
                        # Check if ALL entity terms are present in the chunk
                        all_terms_present = all(term in content_lower for term in entity_terms)
                        if all_terms_present:
                            relevant_chunks.append(content.strip())
                    else:
                        # Single entity term - check for exact match or fuzzy match
                        contains_entity = False
                        for term in entity_terms:
                            if term in content_lower:
                                contains_entity = True
                                break
                            
                            # Dynamic fuzzy matching for abbreviations (no hard-coded thresholds)
                            # Check if any substantial part of the term appears in the content
                            if len(term) >= 4:  # Only for reasonable length terms
                                # Check multiple substring patterns dynamically
                                term_parts = []
                                
                                # Add prefix patterns of varying lengths
                                for i in range(3, min(len(term), 6)):
                                    term_parts.append(term[:i])
                                
                                # Add suffix patterns
                                if len(term) > 5:
                                    term_parts.append(term[-3:])
                                    term_parts.append(term[-4:])
                                
                                # Add consonant-based abbreviations (remove vowels)
                                consonants = ''.join([c for c in term if c not in 'aeiou'])
                                if len(consonants) >= 3:
                                    term_parts.append(consonants[:4])
                                
                                # Check if any pattern matches
                                for part in term_parts:
                                    if len(part) >= 3 and part in content_lower:
                                        contains_entity = True
                                        break
                                
                                if contains_entity:
                                    break
                        
                        if contains_entity:
                            relevant_chunks.append(content.strip())
                
                if len(relevant_chunks) > 1:
                    # Multiple relevant chunks - list them all
                    response_parts = ["Based on the available information:"]
                    for chunk_content in relevant_chunks[:3]:  # Limit to 3 most relevant chunks  
                        response_parts.append(chunk_content[:200])  # Limit each chunk length
                    cleaned_response = "\n".join(response_parts)
                else:
                    # Single chunk fallback
                    best_chunk = context_chunks[0]
                    content = best_chunk.get('content', '') if isinstance(best_chunk, dict) else str(best_chunk)
                    if content:
                        content_excerpt = content[:800]
                        cleaned_response = f"Based on the available information: {content_excerpt}"
            else:
                # Non-financial query - use original logic
                best_chunk = context_chunks[0]
                content = best_chunk.get('content', '') if isinstance(best_chunk, dict) else str(best_chunk)
                if content:
                    content_excerpt = content[:800]
                    if len(content) > 800:
                        content_excerpt += "..."
                    cleaned_response = f"Based on the available information: {content_excerpt}"
                else:
                    cleaned_response = "I couldn't find specific information to answer your question."
        
        # Check if the response is empty or too short
        if not cleaned_response or len(cleaned_response) < ai_config.min_response_length:
            logger.warning("LLM returned empty response")
            return "I couldn't find a good answer to your question in the provided documents. Please try rephrasing your question or upload more relevant documents."
        
        return cleaned_response
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        logger.exception("Full exception details:")
        return f"Error generating response: {str(e)}"

# Remove the global cache as it can cause inconsistent responses
async def generate_answer(query: str, context_chunks: List[Dict[Any, Any]]) -> tuple[str, bool]:
    """
    Generate an answer to a query using the LLM and context chunks
    
    Args:
        query: The user's query
        context_chunks: The context chunks to use for generating the answer
        
    Returns:
        Tuple of (generated answer, from_cache)
    """
    try:
        logger.info(f"Generating answer for query: '{query}' with {len(context_chunks)} context chunks")
        
        # Check if caching is enabled
        service = get_ai_config_service()
        ai_config = service.get_ai_config()
        if getattr(ai_config, "enable_response_caching", False):
            # Create cache key from query and context chunks
            context_text = " ".join([chunk.get('content', '') for chunk in context_chunks])
            cache_key = hashlib.md5(f"{query.lower().strip()}|{context_text}".encode()).hexdigest()
            
            # Check if we have a cached response
            if cache_key in _response_cache:
                logger.info(f"Returning cached response for query: '{query}'")
                return _response_cache[cache_key], True
        
        # Check if we have any context chunks
        if not context_chunks:
            logger.warning("No context chunks provided for query")
            return "I don't have enough information to answer that question. Please upload relevant documents first or try a different question.", False
        
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
            
            # Add chunk to context without debug logging
            
            # Add content to context
            if content:
                context_content.append(content)
        
        # Generate response with error handling
        logger.info(f"Generating response with {len(context_content)} content chunks")
        try:
            response = generate_response(query, context_content)
        except (BrokenPipeError, OSError, IOError) as pipe_error:
            logger.error(f"Broken pipe error during response generation: {str(pipe_error)}")
            return "I'm experiencing technical difficulties right now. Please try your question again in a moment.", False
        except Exception as gen_error:
            logger.error(f"Error during response generation: {str(gen_error)}")
            if "broken pipe" in str(gen_error).lower():
                return "I'm experiencing technical difficulties right now. Please try your question again in a moment.", False
            raise  # Re-raise other errors
        
        # Apply response filtering and validation
        
        # Apply financial response filtering for financial queries
        if any(keyword in query.lower() for keyword in ['money', 'spend', 'spent', 'expense', 'cost', 'dollar', '$', 'payment', 'paid', 'pay', 'finance', 'subscription', 'purchase']):
            logger.info(f"Applying financial filter to query: '{query}' with response: '{response[:100]}...'")
            try:
                filtered_response = financial_filter.filter_financial_response(query, response, context_content)
                logger.info(f"Financial filter returned: '{filtered_response[:100]}...'")
                if filtered_response != response:
                    logger.info(f"Applied financial filter: '{response}' -> '{filtered_response}'")
                    response = filtered_response
                else:
                    logger.info("Financial filter returned same response, no change made")
            except Exception as e:
                logger.error(f"Error in financial filter: {e}")
                import traceback
                logger.error(traceback.format_exc())
        
        # Apply vacation response filtering for vacation queries
        elif any(keyword in query.lower() for keyword in ['vacation', 'travel', 'trip', 'holiday', 'went', 'visit']):
            filtered_response = vacation_filter.filter_vacation_response(query, context_content)
            if filtered_response:
                logger.info(f"Applied vacation filter: '{response}' -> '{filtered_response}'")
                response = filtered_response
        
        # Apply general response validation for all queries
        validation_result = response_validator.validate_response(response, query, context_content)
        if not validation_result.is_valid and validation_result.confidence < 0.5:
            # Generate a safer response when confidence is very low
            response = "I found some relevant information in your documents, but I need to be more specific about what you're looking for. Could you clarify your question?"
        
        # Check if response is empty
        if not response or len(response.strip()) < 10:
            logger.warning("LLM returned empty response")
            return "I couldn't find a good answer to your question in the provided documents. Please try rephrasing your question or upload more relevant documents.", False
        
        # Cache the response if caching is enabled
        if getattr(ai_config, "enable_response_caching", False) and 'cache_key' in locals():
            _response_cache[cache_key] = response
            logger.info(f"Cached response for query: '{query}'")
        
        logger.info(f"Generated response of length {len(response)} chars")
        return response, False
    except Exception as e:
        logger.error(f"Error generating answer: {str(e)}")
        logger.exception("Full exception details:")
        return f"Error generating response: {str(e)}", False