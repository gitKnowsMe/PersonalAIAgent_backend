"""
Response filtering utilities to extract only requested information from context
"""

import re
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from difflib import SequenceMatcher


@dataclass
class ValidationResult:
    """Result of response validation"""
    is_valid: bool
    confidence: float
    issues: List[str]
    suggested_corrections: List[str]


class ResponseValidator:
    """Validates LLM responses against context to prevent hallucinations"""
    
    def __init__(self):
        self.min_confidence_threshold = 0.7
        self.entity_similarity_threshold = 0.8
    
    def validate_response(self, response: str, query: str, context_chunks: List[str]) -> ValidationResult:
        """
        Validate response against context to detect potential hallucinations
        
        Args:
            response: The LLM-generated response
            query: The original user query
            context_chunks: The context used for generation
            
        Returns:
            ValidationResult with validation details
        """
        issues = []
        suggested_corrections = []
        confidence_scores = []
        
        # Extract entities from query and response
        query_entities = self._extract_entities(query)
        response_entities = self._extract_entities(response)
        
        # Validate each response entity against context
        for entity in response_entities:
            entity_validation = self._validate_entity_in_context(entity, context_chunks)
            confidence_scores.append(entity_validation['confidence'])
            
            if not entity_validation['found']:
                issues.append(f"Entity '{entity}' not found in context")
                if entity_validation['similar_entities']:
                    suggested_corrections.extend(entity_validation['similar_entities'])
        
        # Check for numerical inconsistencies
        numerical_issues = self._validate_numerical_consistency(response, context_chunks)
        issues.extend(numerical_issues)
        
        # Check for temporal inconsistencies
        temporal_issues = self._validate_temporal_consistency(response, context_chunks)
        issues.extend(temporal_issues)
        
        # Calculate overall confidence
        overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        # Determine if response is valid
        is_valid = overall_confidence >= self.min_confidence_threshold and len(issues) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            confidence=overall_confidence,
            issues=issues,
            suggested_corrections=list(set(suggested_corrections))  # Remove duplicates
        )
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract named entities from text"""
        entities = []
        
        # Extract proper nouns (capitalized words)
        proper_nouns = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        entities.extend(proper_nouns)
        
        # Extract monetary amounts
        monetary_amounts = re.findall(r'\$\d+(?:,\d{3})*(?:\.\d{2})?', text)
        entities.extend(monetary_amounts)
        
        # Extract dates
        date_patterns = [
            r'\b\d{1,2}/\d{1,2}/\d{4}\b',  # MM/DD/YYYY
            r'\b\d{4}-\d{2}-\d{2}\b',      # YYYY-MM-DD
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b'
        ]
        for pattern in date_patterns:
            dates = re.findall(pattern, text)
            entities.extend(dates)
        
        # Extract payment methods and transaction types
        payment_terms = re.findall(r'\b(?:Zelle|Venmo|PayPal|Credit Card|Debit Card|Cash|Check)\b', text, re.IGNORECASE)
        entities.extend(payment_terms)
        
        return list(set(entities))  # Remove duplicates
    
    def _validate_entity_in_context(self, entity: str, context_chunks: List[str]) -> Dict[str, Any]:
        """Validate if an entity exists in the context"""
        context_text = ' '.join(context_chunks).lower()
        entity_lower = entity.lower()
        
        # Direct match
        if entity_lower in context_text:
            return {
                'found': True,
                'confidence': 1.0,
                'similar_entities': []
            }
        
        # Fuzzy matching for similar entities
        similar_entities = []
        best_similarity = 0.0
        
        # Split context into words and check for similar entities
        context_words = re.findall(r'\b\w+\b', context_text)
        
        for word in context_words:
            if len(word) > 3:  # Only check substantial words
                similarity = SequenceMatcher(None, entity_lower, word).ratio()
                if similarity > self.entity_similarity_threshold:
                    similar_entities.append(word)
                    best_similarity = max(best_similarity, similarity)
        
        return {
            'found': best_similarity > self.entity_similarity_threshold,
            'confidence': best_similarity,
            'similar_entities': similar_entities[:3]  # Limit to top 3
        }
    
    def _validate_numerical_consistency(self, response: str, context_chunks: List[str]) -> List[str]:
        """Validate numerical consistency between response and context"""
        issues = []
        
        # Extract amounts from response
        response_amounts = re.findall(r'\$\d+(?:,\d{3})*(?:\.\d{2})?', response)
        
        # Extract amounts from context
        context_text = ' '.join(context_chunks)
        context_amounts = re.findall(r'\$\d+(?:,\d{3})*(?:\.\d{2})?', context_text)
        
        # Check if response amounts exist in context
        for amount in response_amounts:
            if amount not in context_amounts:
                issues.append(f"Amount {amount} not found in context")
        
        return issues
    
    def _validate_temporal_consistency(self, response: str, context_chunks: List[str]) -> List[str]:
        """Validate temporal consistency between response and context"""
        issues = []
        
        # Extract dates from response
        response_dates = re.findall(r'\b\d{1,2}/\d{1,2}/\d{4}\b', response)
        
        # Extract dates from context
        context_text = ' '.join(context_chunks)
        context_dates = re.findall(r'\b\d{1,2}/\d{1,2}/\d{4}\b', context_text)
        
        # Check if response dates exist in context
        for date in response_dates:
            if date not in context_dates:
                issues.append(f"Date {date} not found in context")
        
        return issues


class FinancialResponseFilter:
    """Specialized filter for financial queries to prevent hallucination"""
    
    def __init__(self):
        self.validator = ResponseValidator()
    
    def filter_financial_response(self, query: str, response: str, context_chunks: List[str]) -> str:
        """
        Filter and validate financial responses to prevent hallucination
        
        Args:
            query: The user's query
            response: The LLM-generated response
            context_chunks: The context used for generation
            
        Returns:
            Filtered and validated response
        """
        # Always try to generate a more specific response using dynamic matching
        smart_response = self._generate_safe_financial_response(query, context_chunks, None)
        
        # If we got a specific smart response, use it
        if smart_response and not smart_response.startswith("I found some financial information"):
            return smart_response
        
        # Otherwise, validate the original response
        validation = self.validator.validate_response(response, query, context_chunks)
        
        if not validation.is_valid:
            # Generate a safer response based on validated context
            return self._generate_safe_financial_response(query, context_chunks, validation)
        
        return response
    
    def _generate_safe_financial_response(self, query: str, context_chunks: List[str], validation: Optional[ValidationResult]) -> str:
        """Generate a safe response when validation fails or to provide more specific answers"""
        query_lower = query.lower()
        
        # Extract specific financial information from context
        financial_data = self._extract_financial_data(context_chunks)

        # Check for location-specific queries (e.g., "Istanbul", "Turkey", etc.)
        location_patterns = {
            'istanbul': ['thy', 'turkish', 'turkey'],
            'turkey': ['thy', 'turkish'], 
            'london': ['british', 'ba', 'heathrow'],
            'paris': ['air france', 'af', 'cdg'],
            'new york': ['jfk', 'lga', 'newark'],
            'tokyo': ['jal', 'ana', 'narita']
        }
        
        for location, patterns in location_patterns.items():
            if location in query_lower:
                # Look for transactions related to this location
                location_amounts = []
                for chunk in context_chunks:
                    text = chunk if isinstance(chunk, str) else chunk.get('content', '')
                    text_lower = text.lower()
                    
                    # Check if any location-specific pattern matches
                    for pattern in patterns:
                        if pattern in text_lower:
                            # Extract amounts from this line
                            amounts = re.findall(r'\$\d+(?:,\d{3})*(?:\.\d{2})?', text)
                            if not amounts:
                                amounts = re.findall(r'\b\d+(?:,\d{3})*\.\d{2}\b', text)
                            for amt in amounts:
                                if not amt.startswith('$'):
                                    amt = f'${amt}'
                                location_amounts.append(amt)
                            break
                    
                    # Also check for foreign exchange fees which are travel-related
                    if 'foreign' in text_lower and 'exch' in text_lower:
                        amounts = re.findall(r'\$\d+(?:,\d{3})*(?:\.\d{2})?', text)
                        if not amounts:
                            amounts = re.findall(r'\b\d+(?:,\d{3})*\.\d{2}\b', text)
                        for amt in amounts:
                            if not amt.startswith('$'):
                                amt = f'${amt}'
                            location_amounts.append(amt)
                
                if location_amounts:
                    unique_amounts = list(dict.fromkeys(location_amounts))
                    if len(unique_amounts) == 1:
                        return f"You spent {unique_amounts[0]} related to {location.title()}."
                    return f"You spent these amounts related to {location.title()}: {', '.join(unique_amounts)}."

        # Dynamic transaction pattern matching - extract entities from query and find in context
        query_entities = self.validator._extract_entities(query)
        
        # Also extract potential keywords from the query, including proper name phrases
        query_words = re.findall(r'\b[a-zA-Z]+\b', query_lower)
        potential_keywords = [word for word in query_words if len(word) > 3 and word not in 
                            {'much', 'paid', 'send', 'sent', 'money', 'amount', 'cost', 'spent', 'with', 'from', 'this', 'that', 'what', 'when', 'where', 'have', 'does'}]
        
        # Extract multi-word names (e.g., "Baby Girl", "Andy Eckman") - case insensitive
        name_patterns = re.findall(r'\b([A-Za-z]+ [A-Za-z]+)\b', query)
        # Filter out common phrases that aren't names
        name_patterns = [name for name in name_patterns if name.lower() not in 
                        ['how much', 'did i', 'i send', 'i paid', 'much did', 'send to', 'paid for']]
        
        # Combine entities, keywords, and names for matching, prioritizing longer/more specific terms
        search_terms = list(set(query_entities + potential_keywords + name_patterns))
        # Sort by length descending to prefer longer, more specific matches
        search_terms.sort(key=len, reverse=True)
        
        # Check for specific payment method queries (Zelle, Venmo, etc.)
        payment_method = None
        if 'zelle' in query_lower:
            payment_method = 'zelle'
        elif 'venmo' in query_lower:
            payment_method = 'venmo'
        elif 'paypal' in query_lower:
            payment_method = 'paypal'
        
        if search_terms and ('how much' in query_lower or 'amount' in query_lower or 'paid' in query_lower or 'cost' in query_lower or 'sent' in query_lower):
            matched_amounts = []
            matched_service = None
            
            for chunk in context_chunks:
                text = chunk if isinstance(chunk, str) else chunk.get('content', '')
                text_lower = text.lower()
                
                # Check if any search term appears in this transaction (checking longest terms first)
                for term in search_terms:
                    term_lower = term.lower()
                    
                    # Direct match
                    if term_lower in text_lower:
                        # If payment method is specified, only match chunks that contain BOTH the person/entity AND the payment method
                        if payment_method:
                            if payment_method not in text_lower:
                                continue  # Skip this chunk if it doesn't contain the specified payment method
                        
                        # Extract amounts from this transaction line/chunk
                        amounts = re.findall(r'\$\d+(?:,\d{3})*(?:\.\d{2})?', text)
                        if not amounts:
                            amounts = re.findall(r'\b\d+(?:,\d{3})*\.\d{2}\b', text)
                        
                        # For better accuracy, only take the first amount from this specific chunk
                        # This prevents multiple unrelated amounts from being combined
                        if amounts:
                            amt = amounts[0]  # Take only the first amount from this chunk
                            if not amt.startswith('$'):
                                amt = f'${amt}'
                            matched_amounts.append(amt)
                        
                        # Use the first (longest) match found
                        if not matched_service:
                            matched_service = term
                        break
            
            if matched_amounts:
                unique_amounts = list(dict.fromkeys(matched_amounts))
                service_name = matched_service.title() if matched_service else 'the requested service'
                
                # Handle special cases for common query patterns
                if 'subscription' in query_lower and not matched_service:
                    service_name = 'subscription services'
                
                # Add payment method context if specified
                if payment_method:
                    service_name += f' via {payment_method.title()}'
                
                # For queries without payment method specification, if multiple amounts found,
                # return the most recent transaction (first in the list since chunks are sorted by relevance)
                if not payment_method and len(unique_amounts) > 1:
                    # For general queries, return the most recent/relevant transaction
                    if 'how much' in query_lower:
                        # Return the first (most recent/relevant) transaction
                        return f"You paid {unique_amounts[0]} to {service_name}."
                    else:
                        return f"You paid these amounts to {service_name}: {', '.join(unique_amounts)}."
                
                if len(unique_amounts) == 1:
                    return f"You paid {unique_amounts[0]} to {service_name}."
                return f"You paid these amounts to {service_name}: {', '.join(unique_amounts)}."


        # Build response based on what's actually in the context
        if 'how much' in query_lower or 'total' in query_lower:
            if financial_data['amounts']:
                amounts_str = ', '.join(financial_data['amounts'][:3])  # Limit to 3 amounts
                return f"Based on the available information, I found these amounts: {amounts_str}"
        
        elif 'when' in query_lower or 'date' in query_lower:
            if financial_data['dates']:
                dates_str = ', '.join(financial_data['dates'][:3])  # Limit to 3 dates
                return f"Based on the available information, I found these dates: {dates_str}"
        
        elif 'who' in query_lower or 'payee' in query_lower:
            if financial_data['payees']:
                payees_str = ', '.join(financial_data['payees'][:3])  # Limit to 3 payees
                return f"Based on the available information, I found these payees: {payees_str}"
        
        # Generic safe response
        return "I found some financial information in your documents, but I need to be more specific about what you're looking for. Could you clarify your question?"
    
    def _extract_financial_data(self, context_chunks: List[str]) -> Dict[str, List[str]]:
        """Extract structured financial data from context"""
        context_text = ' '.join(context_chunks)
        
        # Extract amounts
        amounts = re.findall(r'\$\d+(?:,\d{3})*(?:\.\d{2})?', context_text)
        
        # Extract dates
        dates = re.findall(r'\b\d{1,2}/\d{1,2}/\d{4}\b', context_text)
        
        # Extract payees (names after "To" or "From")
        payees = re.findall(r'(?:To|From)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', context_text)
        
        return {
            'amounts': amounts,
            'dates': dates,
            'payees': payees
        }


class EmailResponseFilter:
    """Filter email responses to extract only email content"""
    
    def filter_email_response(self, query: str, response: str, context_chunks: List[str]) -> Optional[str]:
        """
        Filter responses for email queries to only return email content
        
        Args:
            query: The user's query
            response: The LLM-generated response
            context_chunks: The context used for generation
            
        Returns:
            Filtered response with only email content, or None if no email content found
        """
        query_lower = query.lower()
        
        # Check if this is an email query
        if not any(keyword in query_lower for keyword in ['check email', 'check emails', 'email', 'invoice', 'receipt']):
            return None
            
        # Extract email content from context chunks
        email_chunks = []
        for chunk in context_chunks:
            text = chunk if isinstance(chunk, str) else chunk.get('content', '')
            if '[EMAIL' in text:
                email_chunks.append(text)
        
        if not email_chunks:
            return None
            
        # Look for specific company/service mentioned in query
        query_entities = self._extract_query_entities(query)
        
        if query_entities:
            # Find email chunks that mention the specific entities
            relevant_emails = []
            for chunk in email_chunks:
                for entity in query_entities:
                    if entity.lower() in chunk.lower():
                        relevant_emails.append(chunk)
                        break
            
            if relevant_emails:
                # Extract amounts from relevant emails
                amounts = self._extract_amounts_from_emails(relevant_emails)
                if amounts:
                    entity_name = query_entities[0].title()
                    if len(amounts) == 1:
                        return f"The {entity_name} invoice was {amounts[0]}."
                    else:
                        return f"The {entity_name} invoices were: {', '.join(amounts)}."
        
        # General email query - extract all amounts from email content
        all_amounts = self._extract_amounts_from_emails(email_chunks)
        if all_amounts:
            if len(all_amounts) == 1:
                return f"The invoice amount is {all_amounts[0]}."
            else:
                return f"The invoice amounts are: {', '.join(all_amounts)}."
        
        return None
    
    def _extract_query_entities(self, query: str) -> List[str]:
        """Extract company/service names from query"""
        query_lower = query.lower()
        
        # Common company names and their variations
        companies = {
            'apple': ['apple', 'icloud', 'app store', 'itunes'],
            'google': ['google', 'gmail', 'google play', 'youtube'],
            'amazon': ['amazon', 'aws', 'prime'],
            'microsoft': ['microsoft', 'office', 'outlook', 'azure'],
            'netflix': ['netflix'],
            'spotify': ['spotify'],
            'dropbox': ['dropbox'],
            'adobe': ['adobe', 'creative cloud']
        }
        
        found_entities = []
        for company, variants in companies.items():
            if any(variant in query_lower for variant in variants):
                found_entities.append(company)
        
        # Also look for capitalized words that might be company names
        words = query.split()
        for word in words:
            if word.istitle() and len(word) > 3:
                found_entities.append(word)
        
        return list(set(found_entities))
    
    def _extract_amounts_from_emails(self, email_chunks: List[str]) -> List[str]:
        """Extract monetary amounts from email content"""
        amounts = []
        for chunk in email_chunks:
            # Look for various amount formats
            import re
            patterns = [
                r'\$\d+(?:,\d{3})*(?:\.\d{2})?',  # $123.45
                r'USD\s*\d+(?:,\d{3})*(?:\.\d{2})?',  # USD 123.45
                r'Total:\s*\$\d+(?:,\d{3})*(?:\.\d{2})?',  # Total: $123.45
                r'Amount:\s*\$\d+(?:,\d{3})*(?:\.\d{2})?',  # Amount: $123.45
                r'Amount Due:\s*\$\d+(?:,\d{3})*(?:\.\d{2})?',  # Amount Due: $123.45
                r'\$\d+(?:\.\d{2})?',  # Simple $123.45
            ]
            
            for pattern in patterns:
                found = re.findall(pattern, chunk, re.IGNORECASE)
                for amount in found:
                    # Clean up the amount
                    clean_amount = re.sub(r'[^\d\.\$]', '', amount)
                    if clean_amount and not clean_amount.startswith('$'):
                        clean_amount = '$' + clean_amount
                    if clean_amount and clean_amount not in amounts:
                        amounts.append(clean_amount)
        
        return amounts


class VacationResponseFilter:
    """Filter vacation responses to return only requested information"""
    
    def filter_vacation_response(self, query: str, context_chunks: List[str]) -> str:
        """
        Filter vacation context to return only what's specifically asked for
        
        Args:
            query: The user's query
            context_chunks: List of context chunks from vector search
            
        Returns:
            Filtered response with only requested information
        """
        query_lower = query.lower()
        
        # Extract target year from query
        target_year = self._extract_year_from_query(query)
        
        # Find the relevant vacation entry
        vacation_data = self._extract_vacation_data(context_chunks, target_year)
        
        if not vacation_data:
            return None
        
        # Determine what information is requested
        requested_info = self._parse_query_intent(query_lower)
        
        # Build response based on requested information
        return self._build_filtered_response(vacation_data, requested_info)
    
    def _extract_year_from_query(self, query: str) -> str:
        """Extract year from query string"""
        year_match = re.search(r'\b(20[0-2]\d)\b', query)
        if year_match:
            return year_match.group(1)
        return None
    
    def _extract_vacation_data(self, context_chunks: List[str], target_year: str = None) -> Dict[str, Any]:
        """Extract structured vacation data from context chunks"""
        vacation_data = {}
        
        for chunk in context_chunks:
            # Extract destination and year from header pattern
            destination_patterns = [
                r'(\w+)\s*[-–]\s*([^(]+?)\s*\((\d{4})\)',  # "Thailand – Bangkok & Phuket (2023)"
                r'(\d+)\.\s*(\w+)\s*[-–]\s*([^(]+?)\s*\((\d{4})\)',  # "9. Thailand – Bangkok & Phuket (2023)"
            ]
            
            for pattern in destination_patterns:
                matches = re.findall(pattern, chunk, re.MULTILINE)
                for match in matches:
                    if len(match) == 3:  # First pattern
                        country, cities, year = match
                    else:  # Second pattern  
                        _, country, cities, year = match
                    
                    # If target year specified, only process that year
                    if target_year and year != target_year:
                        continue
                    
                    vacation_data['country'] = country.strip()
                    vacation_data['cities'] = cities.strip()
                    vacation_data['year'] = year
                    break
            
            if vacation_data:  # Found the target year, process its details
                # Extract rental car
                car_match = re.search(r'Rental Car:\s*(.+?)(?:\s*[-–]\s*\$(\d+))?', chunk)
                if car_match:
                    vacation_data['rental_car'] = car_match.group(1).strip()
                    if car_match.group(2):
                        vacation_data['car_cost'] = f"${car_match.group(2)}"
                
                # Extract total cost
                total_match = re.search(r'Total Cost:\s*\$([0-9,]+)', chunk)
                if total_match:
                    vacation_data['total_cost'] = f"${total_match.group(1)}"
                
                # Extract airline (but only if specifically asked)
                airline_match = re.search(r'Airline:\s*(.+)', chunk)
                if airline_match:
                    vacation_data['airline'] = airline_match.group(1).strip()
                
                # Extract hotel (but only if specifically asked)
                hotel_match = re.search(r'Hotel:\s*(.+?)(?:\s*[-–]\s*\$([0-9,]+))?', chunk)
                if hotel_match:
                    vacation_data['hotel'] = hotel_match.group(1).strip()
                    if hotel_match.group(2):
                        vacation_data['hotel_cost'] = f"${hotel_match.group(2)}"
        
        return vacation_data
    
    def _parse_query_intent(self, query_lower: str) -> List[str]:
        """Parse what information is being requested from the query"""
        requested = []
        
        if any(word in query_lower for word in ['where', 'destination', 'location']):
            requested.append('destination')
        
        if any(word in query_lower for word in ['car', 'rental', 'vehicle']):
            requested.append('car')
        
        if any(word in query_lower for word in ['cost', 'spend', 'spent', 'money', 'price', 'total']):
            requested.append('cost')
        
        if any(word in query_lower for word in ['airline', 'flight', 'flew']):
            requested.append('airline')
        
        if any(word in query_lower for word in ['hotel', 'stay', 'stayed']):
            requested.append('hotel')
        
        # If no specific information requested, default to destination only for "where" questions
        if not requested and 'where' in query_lower:
            requested.append('destination')
        
        return requested
    
    def _build_filtered_response(self, vacation_data: Dict[str, Any], requested_info: List[str]) -> str:
        """Build response with only the requested information"""
        response_parts = []
        
        for info_type in requested_info:
            if info_type == 'destination' and 'country' in vacation_data:
                if 'cities' in vacation_data:
                    response_parts.append(f"{vacation_data['country']} ({vacation_data['cities']})")
                else:
                    response_parts.append(vacation_data['country'])
            
            elif info_type == 'car' and 'rental_car' in vacation_data:
                car_info = vacation_data['rental_car']
                if 'car_cost' in vacation_data:
                    car_info += f" for {vacation_data['car_cost']}"
                response_parts.append(car_info)
            
            elif info_type == 'cost' and 'total_cost' in vacation_data:
                response_parts.append(vacation_data['total_cost'])
            
            elif info_type == 'airline' and 'airline' in vacation_data:
                response_parts.append(vacation_data['airline'])
            
            elif info_type == 'hotel' and 'hotel' in vacation_data:
                hotel_info = vacation_data['hotel']
                if 'hotel_cost' in vacation_data:
                    hotel_info += f" for {vacation_data['hotel_cost']}"
                response_parts.append(hotel_info)
        
        if not response_parts:
            return None
        
        # Format the response naturally
        if len(response_parts) == 1:
            return response_parts[0]
        elif len(response_parts) == 2:
            return f"{response_parts[0]} and {response_parts[1]}"
        else:
            return f"{', '.join(response_parts[:-1])}, and {response_parts[-1]}"


# Global instances
vacation_filter = VacationResponseFilter()
financial_filter = FinancialResponseFilter()
email_filter = EmailResponseFilter()
response_validator = ResponseValidator()