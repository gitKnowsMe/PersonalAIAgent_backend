"""
Unit tests for the document classifier
"""

try:
    import pytest
except ImportError:
    pytest = None
    
from app.utils.document_classifier import detect_document_type, get_document_type_metadata


class TestDocumentClassifier:
    """Test cases for document type classification"""

    def test_financial_document_by_filename(self):
        """Test financial classification based on filename patterns"""
        # Test various financial filename patterns
        test_cases = [
            ("bank_statement_june.pdf", "Generic content here"),
            ("invoice_123.txt", "Some regular text"),
            ("transactions_2024.csv", "Date,Amount\n01/01/2024,$100.00"),
            ("receipt_restaurant.pdf", "Thank you for your purchase"),
            ("billing_statement.docx", "Account summary")
        ]
        
        for filename, content in test_cases:
            result = detect_document_type(content, filename)
            assert result == "financial", f"Failed to classify {filename} as financial"

    def test_financial_document_by_content(self):
        """Test financial classification based on content patterns"""
        # Test content with multiple financial phrases
        financial_content = """
        Account Number: 1234567890
        Available Balance: $2,543.67
        Transaction Date: 01/15/2024
        
        Posted Transactions:
        01/14/2024  DEBIT CARD PURCHASE  -$45.67  GROCERY STORE
        01/13/2024  CREDIT DEPOSIT       +$1,200.00  PAYROLL
        01/12/2024  PAYMENT              -$125.00  REFERENCE NUMBER: 789456123
        01/11/2024  DEBIT               -$25.00  ATM WITHDRAWAL
        """
        
        result = detect_document_type(financial_content, "document.txt")
        assert result == "financial"

    def test_financial_document_by_transaction_patterns(self):
        """Test financial classification based on transaction patterns"""
        # Content with date + dollar patterns
        transaction_content = """
        Monthly Statement
        
        12/01/2023  $1,234.56  Deposit
        12/02/2023  -$45.67   Coffee Shop
        12/03/2023  -$89.12   Gas Station
        12/04/2023  -$156.78  Grocery Store
        12/05/2023  $2,000.00 Salary
        12/06/2023  -$67.89   Restaurant
        12/07/2023  -$23.45   Parking
        12/08/2023  -$134.56  Utility Bill
        """
        
        result = detect_document_type(transaction_content, "statement.pdf")
        assert result == "financial"

    def test_long_form_document(self):
        """Test long-form classification for academic/technical documents"""
        # Create a long document with multiple clear paragraphs
        section_template = """
Section {i}

This is a detailed analysis of topic {i}. The content provides comprehensive coverage of the subject matter with extensive explanations and detailed examples. This section contains multiple sentences that form coherent paragraphs discussing various aspects of the topic.

The methodology employed in this section follows established academic standards. Research findings indicate significant correlations between variables examined in the study. Data analysis reveals patterns that support the hypothesis presented in earlier sections.

Further investigation shows that these patterns hold across different sample groups. Statistical significance was achieved at p < 0.05 for all major findings. The implications of these results extend beyond the immediate scope of this research.

"""
        
        # Generate enough content to exceed 5000 tokens with clear paragraph structure
        long_content = "".join(section_template.format(i=i) for i in range(1, 28))
        
        result = detect_document_type(long_content, "research_paper.pdf")
        assert result == "long_form", f"Expected 'long_form', got '{result}' for content with {len(long_content)} chars"

    def test_generic_document_resume(self):
        """Test generic classification for resume/CV documents"""
        resume_content = """
        John Doe
        Software Engineer
        john.doe@email.com | (555) 123-4567
        
        EXPERIENCE
        
        Senior Software Engineer | TechCorp | 2020-Present
        • Led development of microservices architecture
        • Implemented CI/CD pipelines using Jenkins and Docker
        • Mentored junior developers
        
        Software Engineer | StartupXYZ | 2018-2020
        • Developed React frontend applications
        • Built RESTful APIs using Node.js
        • Collaborated with cross-functional teams
        
        EDUCATION
        
        B.S. Computer Science | University of Technology | 2018
        
        SKILLS
        
        Languages: Python, JavaScript, Java, Go
        Frameworks: React, Node.js, Django, Spring Boot
        Tools: Docker, Kubernetes, Jenkins, Git
        """
        
        result = detect_document_type(resume_content, "john_doe_resume.pdf")
        assert result == "generic"

    def test_generic_document_notes(self):
        """Test generic classification for personal notes"""
        notes_content = """
        Meeting Notes - Project Planning
        Date: March 15, 2024
        
        Attendees: Alice, Bob, Carol, Dave
        
        Action Items:
        - Alice: Complete API design by Friday
        - Bob: Set up development environment
        - Carol: Research third-party integrations
        - Dave: Create project timeline
        
        Next Steps:
        - Review API design next week
        - Begin development phase
        - Schedule client demo for month-end
        
        Questions:
        - What's the budget for external tools?
        - Do we need additional team members?
        - When is the final deadline?
        """
        
        result = detect_document_type(notes_content, "meeting_notes.txt")
        assert result == "generic"

    def test_edge_cases(self):
        """Test edge cases and error handling"""
        # Empty content
        result = detect_document_type("", "empty.txt")
        assert result == "generic"
        
        # Very short content
        result = detect_document_type("Hello world", "short.txt")
        assert result == "generic"
        
        # Content with some financial terms but not enough
        partial_financial = "I need to pay my credit card bill of $100.50 next week."
        result = detect_document_type(partial_financial, "reminder.txt")
        assert result == "generic"

    def test_get_document_type_metadata(self):
        """Test metadata retrieval for different document types"""
        # Test financial metadata
        financial_meta = get_document_type_metadata("financial")
        assert financial_meta["recommended_chunk_size"] == 200
        assert financial_meta["recommended_overlap"] == 20
        assert financial_meta["processing_priority"] == "structured"
        
        # Test long_form metadata
        long_form_meta = get_document_type_metadata("long_form")
        assert long_form_meta["recommended_chunk_size"] == 600
        assert long_form_meta["recommended_overlap"] == 100
        assert long_form_meta["processing_priority"] == "semantic"
        
        # Test generic metadata
        generic_meta = get_document_type_metadata("generic")
        assert generic_meta["recommended_chunk_size"] == 400
        assert generic_meta["recommended_overlap"] == 80
        assert generic_meta["processing_priority"] == "balanced"
        
        # Test invalid type (should return generic)
        invalid_meta = get_document_type_metadata("invalid_type")
        assert invalid_meta == generic_meta

    def test_financial_vs_long_form_distinction(self):
        """Test that financial documents aren't misclassified as long_form"""
        # Long financial document (like a detailed bank statement)
        long_financial_content = """
        BANK STATEMENT
        Account Number: 1234567890
        Statement Period: January 1 - January 31, 2024
        
        Beginning Balance: $5,432.10
        """ + "\n".join([
            f"01/{i:02d}/2024  TRANSACTION_{i:03d}  ${(i*12.34):.2f}  MERCHANT_{i}"
            for i in range(1, 100)  # 99 transactions
        ]) + """
        
        Ending Balance: $8,765.43
        
        FEES AND CHARGES:
        Monthly Maintenance Fee: $12.00
        ATM Fee: $3.50
        Overdraft Fee: $35.00
        
        INTEREST EARNED:
        Savings Interest: $0.45
        """
        
        result = detect_document_type(long_financial_content, "bank_statement.pdf")
        assert result == "financial", "Long financial document should still be classified as financial"

    def test_structured_vs_narrative_content(self):
        """Test distinction between structured and narrative content"""
        # Structured content (should be financial or generic, not long_form)
        structured_content = """
        PRODUCT CATALOG
        
        Item ID | Description | Price | Quantity
        --------|-------------|-------|----------
        001     | Widget A    | $12.99| 100
        002     | Widget B    | $15.99| 75
        003     | Widget C    | $8.99 | 200
        004     | Widget D    | $22.99| 50
        """ + "\n".join([
            f"{i:03d}     | Product {i}  | ${(i*3.99):.2f}| {i*10}"
            for i in range(5, 100)
        ])
        
        result = detect_document_type(structured_content, "catalog.csv")
        # Should not be long_form despite length due to structured format
        assert result != "long_form"


if __name__ == "__main__":
    if pytest:
        pytest.main([__file__])
    else:
        # Run tests manually if pytest is not available
        test_class = TestDocumentClassifier()
        
        print("Running document classifier tests...")
        
        try:
            test_class.test_financial_document_by_filename()
            print("✓ test_financial_document_by_filename")
        except Exception as e:
            print(f"✗ test_financial_document_by_filename: {e}")
        
        try:
            test_class.test_financial_document_by_content()
            print("✓ test_financial_document_by_content")
        except Exception as e:
            print(f"✗ test_financial_document_by_content: {e}")
        
        try:
            test_class.test_long_form_document()
            print("✓ test_long_form_document")
        except Exception as e:
            print(f"✗ test_long_form_document: {e}")
        
        try:
            test_class.test_generic_document_resume()
            print("✓ test_generic_document_resume")
        except Exception as e:
            print(f"✗ test_generic_document_resume: {e}")
        
        try:
            test_class.test_edge_cases()
            print("✓ test_edge_cases")
        except Exception as e:
            print(f"✗ test_edge_cases: {e}")
        
        try:
            test_class.test_get_document_type_metadata()
            print("✓ test_get_document_type_metadata")
        except Exception as e:
            print(f"✗ test_get_document_type_metadata: {e}")
        
        print("Tests completed!")