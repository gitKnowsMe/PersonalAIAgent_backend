import os
import logging
import json
from typing import List, Dict, Any, Optional

from llama_cpp import Llama
from app.core.config import settings

# Get the logger
logger = logging.getLogger("personal_ai_agent")

# Global LLM model instance
_llm_model = None

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
            }
            
            # Add Metal acceleration if enabled with optimized parameters
            if settings.USE_METAL:
                print(f"DEBUG: Enabling Metal acceleration with {settings.METAL_N_GPU_LAYERS} GPU layers")
                logger.info(f"DEBUG: Enabling Metal acceleration with {settings.METAL_N_GPU_LAYERS} GPU layers")
                model_params["n_gpu_layers"] = settings.METAL_N_GPU_LAYERS
                # Using only parameters supported by this version of llama_cpp
                model_params["offload_kqv"] = True  # Offload key/query/value matrices to GPU
                
            # Log the model parameters
            print(f"DEBUG: Model parameters: {model_params}")
            logger.info(f"DEBUG: Model parameters: {model_params}")
                
            # Load the model with configured parameters
            _llm_model = Llama(**model_params)
            
            logger.info("LLM model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading LLM model: {str(e)}")
            raise
    
    return _llm_model

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
    # Check query type to determine how to filter context
    query_lower = query.lower()
    is_skills_query = any(keyword in query_lower for keyword in ["skill", "skills", "resume", "cv", "what can i do", "what am i good at"])
    is_expense_query = any(keyword in query_lower for keyword in ["expense", "money", "spend", "spent", "cost", "budget"])
    is_vacation_query = any(keyword in query_lower for keyword in ["vacation", "travel", "trip", "holiday"])
    
    # Filter context chunks based on query type
    filtered_chunks = []
    if is_skills_query:
        # For skills queries, only include chunks related to skills/resume
        for chunk in context_chunks:
            content = ""
            if hasattr(chunk, 'page_content'):
                content = chunk.page_content.lower()
            elif isinstance(chunk, dict) and "content" in chunk:
                content = chunk["content"].lower()
                
            # Check if this chunk contains skills-related content
            if any(keyword in content for keyword in ["skill", "technical", "programming", "framework", "education", "experience", "qualification"]):
                filtered_chunks.append(chunk)
        
        # If no skills chunks found, use all chunks
        if not filtered_chunks:
            filtered_chunks = context_chunks
    else:
        # For other queries, use all chunks
        filtered_chunks = context_chunks
    
    # Log the context chunks being used
    logger.info(f"Using {len(filtered_chunks)} chunks for context with question: '{query}'")
    
    # Extract content from chunks and prepare for prompt
    context_content = ""
    for i, chunk in enumerate(filtered_chunks):
        # Check if this is a langchain Document object
        if hasattr(chunk, 'page_content') and hasattr(chunk, 'metadata'):
            # Handle langchain Document object
            content = chunk.page_content
            metadata = chunk.metadata
            namespace = metadata.get("namespace", "unknown")
            content_preview = content[:100] + "..." if content else ""
            
            # Add chunk content to context with source information
            if content:
                # Add source information to help LLM understand where information is coming from
                source_info = f"[SOURCE {i+1}]: "
                if "title" in metadata:
                    source_info += f"Title: {metadata['title']} | "
                if "source" in metadata:
                    source_info += f"Source: {metadata['source']} | "
                if "file_path" in metadata:
                    source_info += f"Source: {metadata['file_path']} | "
                
                context_content += f"{source_info}\n{content}\n\n"
        else:
            # Handle dictionary-like object
            namespace = chunk.get("namespace", "unknown")
            content = chunk.get("content", "")
            content_preview = content[:100] + "..." if content else ""
            
            # Add chunk content to context with source information
            if content:
                # Add source information to help LLM understand where information is coming from
                source_info = f"[SOURCE {i+1}]: "
                if "metadata" in chunk and chunk["metadata"]:
                    if "title" in chunk["metadata"]:
                        source_info += f"Title: {chunk['metadata']['title']} | "
                    if "source" in chunk["metadata"]:
                        source_info += f"Source: {chunk['metadata']['source']} | "
                
                context_content += f"{source_info}\n{content}\n\n"
        
        logger.info(f"Chunk {i+1} (from {namespace}): {content_preview}")
    
    # Log the first 500 characters of context for debugging
    logger.info(f"Context content (first 500 chars): {context_content[:500]}")
    
    # Check if the query contains first-person references
    has_first_person = any(word in query.lower() for word in ["i ", "my ", "me ", "mine ", "i've ", "i'm ", "i'll ", "i'd "])
    
    # Determine if we should use first-person mode
    use_first_person = first_person_mode or has_first_person
    
    # Analyze if this is a multi-part question
    is_multi_part = "?" in query and query.count("?") > 1
    
    # Split multi-part questions for analysis
    query_parts = []
    if is_multi_part:
        # Split by question mark but keep the question mark with each part
        parts = query.split("?")
        for i in range(len(parts) - 1):  # Skip the last part if it's empty
            if parts[i].strip():
                query_parts.append(parts[i].strip() + "?")
    
    # Identify question types using keywords
    vacation_keywords = ['vacation', 'travel', 'trip', 'holiday', 'went', 'go', 'visit', 'thailand', '2023', 'resort', 'beach', 'tour', 'destination', 'flight', 'hotel', 'stay']
    skills_keywords = ['technical', 'skill', 'resume', 'cv', 'qualification', 'experience', 'job', 'programming', 'developer', 'software', 'engineer', 'coding', 'framework', 'language', 'technology', 'proficiency']
    expense_keywords = ['money', 'spend', 'spent', 'expense', 'cost', 'budget', 'march', 'dollar', '$', 'january', 'february', 'april', 'purchase', 'transaction', 'bill', 'receipt', 'price', 'payment', 'finance']
    
    query_lower = query.lower()
    is_vacation_query = any(keyword in query_lower for keyword in vacation_keywords)
    is_skills_query = any(keyword in query_lower for keyword in skills_keywords)
    is_expense_query = any(keyword in query_lower for keyword in expense_keywords)
    
    # Create system message with instructions - streamlined for better performance
    system_message = """You are a helpful assistant that STRICTLY answers based ONLY on the provided context. 

CRITICAL RULES:
1. NEVER make up information that is not explicitly stated in the context
2. Use EXACT numbers, dates, and amounts from the context
3. If information is missing or unclear, say "I don't have that specific information in the provided context"
4. When providing financial amounts, use the EXACT dollar figures from the context
5. For dates and timeframes, use only what is explicitly mentioned

Format responses clearly and be specific with dates, numbers and facts."""

    if use_first_person:
        system_message += """

IMPORTANT: The user is asking about their own information, so phrase your response using SECOND-PERSON pronouns (you, your).
For example, say "You went to Thailand in 2023" instead of "I went to Thailand in 2023".
Always use "You" instead of "I" when referring to the user's personal information.
"""

    if is_multi_part:
        system_message += f"""

IMPORTANT: This is a multi-part question with {len(query_parts)} parts. Make sure to address EACH part separately and completely.
For clarity, structure your response with separate sections for each part of the question:

"""
        for i, part in enumerate(query_parts):
            system_message += f"PART {i+1}: {part}\n"
        
        system_message += """
For each part, if the context doesn't contain relevant information, clearly state that.
"""

    # Add specific instructions based on question type
    if is_vacation_query:
        system_message += """

VACATION INFORMATION RULES:
- Look ONLY for exact vacation details in the context
- Use EXACT destination names, years, and costs as written
- If a specific year is mentioned in the question (like 2023), ONLY provide information about vacations from that EXACT year
- If you find "Thailand 2023" with "$5000", use those exact details
- DO NOT combine information from different trips or years
- If context shows multiple trips, clearly specify which trip each detail belongs to
Only include information that is explicitly and clearly mentioned in the context.
"""

    if is_skills_query:
        system_message += """

TECHNICAL SKILLS RULES:
- List ONLY skills explicitly mentioned in the context
- Include specific programming languages, tools, frameworks as written
- Do NOT infer skills that aren't directly stated
- Focus ONLY on professional and technical information
- If context mentions "8 years experience" use that exact phrase
- Separate clearly between technical skills and work experience
Only list skills and qualifications that are explicitly mentioned in the context.
"""

    if is_expense_query:
        system_message += """

EXPENSE INFORMATION RULES - CRITICAL FOR ACCURACY:
- Find the EXACT month and year mentioned in the query (e.g., "March 2023")
- Look for that EXACT combination in the context
- Use the EXACT "Total Spent:" amount shown for that specific month/year
- DO NOT use amounts from other months or years
- If context shows "March 2023... Total Spent: $2650" then answer is $2650
- DO NOT round, estimate, or modify the amounts
- If the exact month/year combination is not found, say so clearly

EXAMPLE: If asked about "March 2023" and context shows:
"March 2023
...
Total Spent: $2650"

Then answer: "Your total expenses for March 2023 were $2650."

NEVER combine expenses from different months or use approximate amounts.
"""

    # Create the full prompt with better structure to reduce hallucination
    prompt = f"""<s>[INST] {system_message}

CONTEXT INFORMATION:
{context_content}

USER QUESTION: {query}

INSTRUCTIONS FOR YOUR RESPONSE:
1. Read the context carefully and find information that directly answers the question
2. Use EXACT phrases, numbers, and dates from the context
3. If the exact information requested is not in the context, state this clearly
4. Do not make assumptions or combine information from different sections

Please provide your answer based strictly on the context above: [/INST]"""

    try:
        # Get the LLM model
        model = get_llm_model()
        
        # Check if prompt might exceed context window
        # Estimate tokens (rough approximation: 4 chars per token)
        estimated_tokens = len(prompt) / 4
        
        # For Mistral-7B model with 4096 context window, be conservative
        max_context = settings.LLM_CONTEXT_WINDOW - 1024  # Leave room for response
        
        # If prompt is too long, truncate context
        if estimated_tokens > max_context:
            logger.warning(f"Prompt too long (est. {estimated_tokens} tokens), truncating context")
            
            # Calculate how much to keep (in characters)
            keep_chars = int(max_context * 3) - len(system_message) - len(query) - 300
            
            # Make sure we keep some context
            if keep_chars < 500:
                keep_chars = 500
            
            # Truncate the context from the beginning, keeping the most recent parts
            if len(context_content) > keep_chars:
                context_content = "..." + context_content[-keep_chars:]
            
            # Rebuild the prompt
            prompt = f"""<s>[INST] {system_message}

Context:
{context_content}

User Question: {query} [/INST]"""
        
        # Log the actual prompt being sent
        logger.info(f"Sending prompt to LLM (length: {len(prompt)} chars)")
        
        # Generate response with appropriate parameters for Mistral
        response = model(
            prompt,
            max_tokens=512,  # Reasonable response length
            temperature=0.05,  # Very low temperature for more deterministic responses
            top_p=0.9,
            top_k=40,
            repeat_penalty=1.1,
            stop=["</s>", "[INST]", "[/INST]", "USER QUESTION:", "CONTEXT INFORMATION:"]  # Mistral-specific stop tokens
        )
        
        # Extract the response text
        if isinstance(response, dict) and 'choices' in response:
            answer = response['choices'][0]['text'].strip()
        elif isinstance(response, str):
            answer = response.strip()
        else:
            answer = str(response).strip()
        
        # Clean up the response more thoroughly
        answer = answer.replace("[INST]", "").replace("[/INST]", "").strip()
        answer = answer.replace("</s>", "").strip()
        
        # Remove any repeated instruction text that might leak through
        if "CONTEXT INFORMATION:" in answer:
            answer = answer.split("CONTEXT INFORMATION:")[0].strip()
        if "USER QUESTION:" in answer:
            answer = answer.split("USER QUESTION:")[0].strip()
        if "INSTRUCTIONS FOR YOUR RESPONSE:" in answer:
            answer = answer.split("INSTRUCTIONS FOR YOUR RESPONSE:")[0].strip()
        
        # Clean up any leading/trailing whitespace and newlines
        answer = answer.strip()
        
        # Log the response
        logger.info(f"LLM response generated (length: {len(answer)} chars): {answer[:100]}...")
        
        if not answer or len(answer.strip()) < 5:
            logger.warning("LLM returned empty or very short response")
            return "I apologize, but I'm having trouble generating a complete response. Please try rephrasing your question or asking about a specific aspect of the topic."
        
        return answer
        
    except Exception as e:
        error_msg = f"Error generating response: {str(e)}"
        logger.error(error_msg)
        return f"I apologize, but I encountered an error while processing your request: {str(e)}"

_answer_cache = {}

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
        # Clear cache periodically to ensure fresh responses
        if len(_answer_cache) > 50:
            _answer_cache.clear()
            logger.info("Cleared answer cache for fresh responses")
        
        # Create a cache key from the query and context fingerprints
        context_fingerprint = "_".join([str(hash(c.get("content", "")[:50] if hasattr(c, "get") else c.page_content[:50])) for c in context_chunks[:2]])
        cache_key = f"{query}_{context_fingerprint}"
        
        # For now, skip caching to ensure accuracy - we can re-enable later if needed
        # if cache_key in _answer_cache:
        #     logger.info("Using cached response for similar query")
        #     return _answer_cache[cache_key]
        
        # Check if the query contains first-person references
        first_person_mode = any(word in query.lower() for word in ["i ", "my ", "me ", "mine ", "i've ", "i'm ", "i'll ", "i'd "])
        
        # Generate response
        response = generate_response(query, context_chunks, first_person_mode)
        
        # Cache the response (disabled for now to ensure accuracy)
        # _answer_cache[cache_key] = response
        
        return response
    except Exception as e:
        logger.error(f"Error generating answer: {str(e)}")
        return "Sorry, I encountered an error while generating an answer." 