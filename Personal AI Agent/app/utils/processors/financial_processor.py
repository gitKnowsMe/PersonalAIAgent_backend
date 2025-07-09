"""
Specialized processor for financial documents (bank statements, transactions)
Optimized for transaction-level chunking - 1 transaction per chunk for optimal retrieval
"""

import re
import logging
from typing import List, Dict, Any
from langchain_core.documents import Document as LangchainDocument

from app.utils.processors.base_processor import BaseDocumentProcessor

logger = logging.getLogger("personal_ai_agent")


class FinancialDocumentProcessor(BaseDocumentProcessor):
    """
    Specialized processor for financial documents like bank statements.
    Uses adaptive chunking: 1 transaction per chunk for precise retrieval.
    """
    
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        # Initialize parent but we'll override the chunking strategy
        super().__init__(chunk_size, chunk_overlap)
    
    async def extract_content(self, file_path: str) -> str:
        """
        This method is not used directly since we're using this processor
        only for chunking, but required by abstract base class
        """
        raise NotImplementedError("FinancialDocumentProcessor is used only for chunking")
    
    def extract_format_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        This method is not used directly since we're using this processor
        only for chunking, but required by abstract base class
        """
        return {}
    
    def create_chunks(self, content: str, base_metadata: Dict[str, any]) -> List[LangchainDocument]:
        """
        Create adaptive chunks for financial documents: 1 transaction per chunk
        
        Args:
            content: Financial document content (bank statement, etc.)
            base_metadata: Base metadata to add to all chunks
            
        Returns:
            List of LangchainDocument chunks, one per transaction
        """
        try:
            logger.info("Creating adaptive transaction-level chunks for financial document")
            
            # Split content into lines
            lines = content.split('\n')
            
            # Enhanced transaction patterns - more specific and comprehensive
            transaction_patterns = [
                # Date patterns with amounts
                r'\d{1,2}/\d{1,2}\s+.*?\$?\d+\.\d{2}',  # MM/DD format
                r'\d{1,2}-\d{1,2}\s+.*?\$?\d+\.\d{2}',  # MM-DD format
                # Transaction types with amounts
                r'(card purchase|debit|credit|payment|deposit|withdrawal|transfer|zelle|ach|wire|direct dep).*?\$?\d+\.\d{2}',
                # Amount patterns (including negative)
                r'[-$]?\$?\d+\.\d{2}\s*(debit|credit|payment|deposit|withdrawal)',
                # Specific financial institution patterns
                r'(card \d{4}|ppd id|ctx id).*?\$?\d+\.\d{2}',
            ]
            
            chunks = []
            chunk_index = 0
            current_context = []  # Keep account info and statement details
            
            for line_num, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                
                # Check if this line contains a transaction
                is_transaction = self._is_transaction_line(line, transaction_patterns)
                
                if is_transaction:
                    # This is a transaction line - create a chunk for it
                    transaction_chunk = self._create_transaction_chunk(
                        line, current_context, chunk_index, base_metadata
                    )
                    if transaction_chunk:
                        chunks.append(transaction_chunk)
                        chunk_index += 1
                    
                    # Keep this line as context for next transaction
                    current_context = [line]
                else:
                    # This is contextual information (headers, balances, etc.)
                    # Keep it as context but also create a chunk if it's important
                    if self._is_important_context(line):
                        context_chunk = self._create_context_chunk(
                            line, chunk_index, base_metadata
                        )
                        if context_chunk:
                            chunks.append(context_chunk)
                            chunk_index += 1
                    
                    # Add to context for transactions (keep last 3 lines)
                    current_context.append(line)
                    if len(current_context) > 3:
                        current_context.pop(0)
            
            # Update total chunks count in all chunks
            for chunk in chunks:
                chunk.metadata["total_chunks"] = len(chunks)
            
            logger.info(f"Created {len(chunks)} adaptive chunks for financial document")
            return chunks
            
        except Exception as e:
            logger.error(f"Error creating adaptive financial chunks: {str(e)}")
            # Fallback to standard chunking if adaptive fails
            return super().create_chunks(content, base_metadata)
    
    def _create_transaction_chunk(self, transaction_line: str, context: List[str], 
                                 index: int, base_metadata: Dict[str, any]) -> LangchainDocument:
        """
        Create a chunk for a single transaction with enhanced searchable content
        
        Args:
            transaction_line: The transaction line
            context: Contextual lines (account info, headers, etc.)
            index: Chunk index
            base_metadata: Base metadata
            
        Returns:
            LangchainDocument for the transaction
        """
        # Extract transaction metadata first
        transaction_metadata = self._extract_transaction_metadata(transaction_line)
        
        # Build enhanced chunk content with searchable information
        chunk_lines = []
        
        # Add relevant context (account info, statement period, etc.)
        for ctx_line in context[-2:]:  # Last 2 context lines
            if ctx_line and not ctx_line == transaction_line:
                chunk_lines.append(ctx_line)
        
        # Add the transaction itself
        chunk_lines.append(transaction_line)
        
        # Add structured information for better search
        if transaction_metadata.get("payee"):
            chunk_lines.append(f"Merchant/Payee: {transaction_metadata['payee']}")
        
        if transaction_metadata.get("amount"):
            chunk_lines.append(f"Amount: ${transaction_metadata['amount']:.2f}")
        
        if transaction_metadata.get("transaction_type"):
            chunk_lines.append(f"Transaction Type: {transaction_metadata['transaction_type']}")
        
        if transaction_metadata.get("location"):
            chunk_lines.append(f"Location: {transaction_metadata['location']}")
        
        if transaction_metadata.get("payment_method"):
            chunk_lines.append(f"Payment Method: {transaction_metadata['payment_method']}")
        
        chunk_content = '\n'.join(chunk_lines)
        
        # Combine metadata
        chunk_metadata = base_metadata.copy()
        chunk_metadata.update({
            "chunk_index": index,
            "chunk_type": "transaction",
            "chunk_length": len(chunk_content),
            "chunking_strategy": "adaptive_transaction_level",
            **transaction_metadata
        })
        
        return LangchainDocument(
            page_content=chunk_content,
            metadata=chunk_metadata
        )
    
    def _create_context_chunk(self, context_line: str, index: int, 
                             base_metadata: Dict[str, any]) -> LangchainDocument:
        """
        Create a chunk for important contextual information
        
        Args:
            context_line: Important context line (balance, account info, etc.)
            index: Chunk index
            base_metadata: Base metadata
            
        Returns:
            LangchainDocument for the context
        """
        chunk_metadata = base_metadata.copy()
        chunk_metadata.update({
            "chunk_index": index,
            "chunk_type": "context",
            "chunk_length": len(context_line),
            "chunking_strategy": "adaptive_context"
        })
        
        return LangchainDocument(
            page_content=context_line,
            metadata=chunk_metadata
        )
    
    def _is_important_context(self, line: str) -> bool:
        """
        Determine if a line contains important contextual information
        
        Args:
            line: Text line to check
            
        Returns:
            True if the line contains important context
        """
        important_patterns = [
            r'balance.*?\$\d+\.\d{2}',  # Balance information
            r'account.*?number',        # Account numbers
            r'statement.*?period',      # Statement periods
            r'total.*?\$\d+\.\d{2}',   # Totals
            r'beginning.*?balance',     # Beginning balance
            r'ending.*?balance',        # Ending balance
        ]
        
        line_lower = line.lower()
        return any(re.search(pattern, line_lower) for pattern in important_patterns)
    
    def _is_transaction_line(self, line: str, patterns: List[str]) -> bool:
        """
        Enhanced transaction detection with multiple validation criteria
        
        Args:
            line: Text line to check
            patterns: List of regex patterns to match
            
        Returns:
            True if the line represents a transaction
        """
        line_lower = line.lower()
        
        # Check basic patterns first
        pattern_match = any(re.search(pattern, line_lower) for pattern in patterns)
        
        # Additional validation criteria
        has_amount = re.search(r'\$?\d+\.\d{2}', line)
        has_date = re.search(r'\d{1,2}/\d{1,2}', line)
        has_transaction_indicator = any(indicator in line_lower for indicator in [
            'card purchase', 'zelle', 'direct dep', 'payment', 'deposit', 'withdrawal', 
            'transfer', 'ach', 'wire', 'debit', 'credit'
        ])
        
        # A line is a transaction if it has amount AND (date OR transaction indicator)
        # Skip complex pattern matching for now
        return has_amount and (has_date or has_transaction_indicator)
    
    def _extract_transaction_metadata(self, transaction_line: str) -> Dict[str, Any]:
        """
        Enhanced metadata extraction from transaction lines
        
        Args:
            transaction_line: The transaction text
            
        Returns:
            Dictionary with comprehensive extracted metadata
        """
        metadata = {}
        line_lower = transaction_line.lower()
        
        # Extract amount (handle negative amounts and different formats)
        amount_patterns = [
            r'\$(\d+\.\d{2})',  # $123.45
            r'(\d+\.\d{2})\s*$',  # 123.45 at end
            r'-(\d+\.\d{2})',  # -123.45
            r'(\d+\.\d{2})(?=\s|$)',  # 123.45 followed by space or end
        ]
        
        for pattern in amount_patterns:
            amount_match = re.search(pattern, transaction_line)
            if amount_match:
                metadata["amount"] = float(amount_match.group(1))
                break
        
        # Extract date with multiple formats
        date_patterns = [
            r'(\d{1,2}/\d{1,2})',  # MM/DD
            r'(\d{1,2}-\d{1,2})',  # MM-DD
            r'(\d{1,2}/\d{1,2}/\d{2,4})',  # MM/DD/YYYY
        ]
        
        for pattern in date_patterns:
            date_match = re.search(pattern, transaction_line)
            if date_match:
                metadata["transaction_date"] = date_match.group(1)
                break
        
        # Enhanced transaction type detection
        transaction_types = {
            'card purchase': ['card purchase', 'card purchase with pin'],
            'zelle': ['zelle payment', 'zelle'],
            'direct_deposit': ['direct dep', 'direct-pay'],
            'payment': ['payment to', 'payment from'],
            'withdrawal': ['withdrawal', 'atm'],
            'deposit': ['deposit'],
            'transfer': ['transfer'],
            'ach': ['ach'],
            'wire': ['wire'],
            'debit': ['debit'],
            'credit': ['credit']
        }
        
        for trans_type, keywords in transaction_types.items():
            if any(keyword in line_lower for keyword in keywords):
                metadata["transaction_type"] = trans_type
                break
        
        # Enhanced merchant/payee extraction
        payee_patterns = [
            r'zelle payment (?:to|from) ([^\d]+?)(?:\s+\w{10,}|\s+\$|$)',  # Zelle payments
            r'payment (?:to|from) ([^\d]+?)(?:\s+\w{10,}|\s+\$|$)',  # General payments
            r'card purchase (?:with pin )?\d{1,2}/\d{1,2} ([^\d]+?)(?:\s+card|\s+\$|$)',  # Card purchases
            r'direct dep ([^\d]+?)(?:\s+ppd|\s+\$|$)',  # Direct deposits
            r'([a-zA-Z][a-zA-Z0-9\s*]+?)(?:\s+\$\d+|\s+card|\s+\d{4}|\s+ppd|\s+ctx)',  # General merchant
        ]
        
        for pattern in payee_patterns:
            payee_match = re.search(pattern, line_lower)
            if payee_match:
                payee = payee_match.group(1).strip()
                # Clean up payee name
                payee = re.sub(r'\s+', ' ', payee)  # Normalize spaces
                payee = re.sub(r'[*]+', '', payee)  # Remove asterisks
                if len(payee) > 2:  # Only keep meaningful payees
                    metadata["payee"] = payee
                    break
        
        # Extract location information
        location_patterns = [
            r'([a-zA-Z]+\s+[a-zA-Z]{2})\s+card',  # City State format
            r'([a-zA-Z]+)\s+[a-zA-Z]{2}\s+card',  # City format
            r'/\s*([a-zA-Z]+)\s*card',  # Location after slash
        ]
        
        for pattern in location_patterns:
            location_match = re.search(pattern, transaction_line)
            if location_match:
                location = location_match.group(1).strip()
                if len(location) > 2:
                    metadata["location"] = location
                    break
        
        # Extract payment method
        payment_methods = {
            'card': ['card \d{4}', 'card purchase'],
            'zelle': ['zelle'],
            'ach': ['ach', 'ppd id'],
            'wire': ['wire'],
            'direct_deposit': ['direct dep']
        }
        
        for method, keywords in payment_methods.items():
            if any(re.search(keyword, line_lower) for keyword in keywords):
                metadata["payment_method"] = method
                break
        
        # Enhanced search keywords for better retrieval
        keywords = []
        
        # Add payee words
        if "payee" in metadata:
            payee_words = metadata["payee"].split()
            keywords.extend([word.lower() for word in payee_words if len(word) > 2])
        
        # Add transaction type
        if "transaction_type" in metadata:
            keywords.append(metadata["transaction_type"])
        
        # Add location
        if "location" in metadata:
            keywords.append(metadata["location"].lower())
        
        # Add payment method
        if "payment_method" in metadata:
            keywords.append(metadata["payment_method"])
        
        # Add amount range for filtering
        if "amount" in metadata:
            amount = metadata["amount"]
            if amount < 50:
                keywords.append("small_amount")
            elif amount > 500:
                keywords.append("large_amount")
        
        if keywords:
            metadata["search_keywords"] = keywords
        
        return metadata