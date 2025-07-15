# Document and Email Classification

Understanding how Personal AI Agent automatically categorizes your content for optimal processing and search.

## Overview

Personal AI Agent uses intelligent classification to optimize how your content is processed, stored, and searched. This automatic categorization ensures that each type of content receives the most appropriate handling for maximum accuracy and relevance.

## Document Classification

### Classification Process

When you upload a PDF, the system analyzes:

1. **Content Patterns**: Keywords, formatting, structure
2. **Document Metadata**: Page count, creation date, file properties
3. **Text Analysis**: Language patterns, terminology, data types
4. **Structure Recognition**: Headers, tables, formatting styles

### Document Categories

#### Financial Documents

**Automatic Detection Criteria:**
- Transaction patterns and monetary amounts
- Banking terminology (account, balance, deposit, withdrawal)
- Date-amount pairs in tabular format
- Financial institution headers and footers
- Tax and accounting terminology

**Examples:**
- Bank statements
- Credit card statements
- Investment reports
- Tax documents
- Invoices and receipts
- Financial summaries

**Processing Optimizations:**
- **Small Chunks (500 characters)**: Precise transaction matching
- **Minimal Overlap (50 characters)**: Avoid duplicate transactions
- **Pattern Recognition**: Enhanced for monetary amounts and dates
- **Structured Data**: Optimized for tabular information

**Best Query Types:**
```
"How much did I spend on groceries in March?"
"Find all Apple transactions over $100"
"What was my account balance on March 15th?"
"Show me all overdraft fees"
```

#### Long-form Documents

**Automatic Detection Criteria:**
- Document length (20+ pages)
- Academic or research structure
- Complex formatting with sections and subsections
- Bibliography or reference sections
- Abstract or executive summary presence

**Examples:**
- Research papers and studies
- Technical reports
- Legal contracts
- Policy documents
- Thesis and dissertations
- Comprehensive analyses

**Processing Optimizations:**
- **Large Chunks (1500 characters)**: Comprehensive context preservation
- **Significant Overlap (300 characters)**: Maintain narrative flow
- **Deep Analysis**: Enhanced semantic understanding
- **Structure Awareness**: Section and hierarchy recognition

**Best Query Types:**
```
"Summarize the key findings of this research"
"What methodology was used in this study?"
"Explain the main conclusions"
"What are the recommendations in this report?"
```

#### Generic Documents

**Default Classification For:**
- Short documents (under 20 pages)
- Mixed content that doesn't fit other categories
- Personal documents (resumes, letters)
- General business documents
- Reference materials

**Examples:**
- Resumes and CVs
- Personal correspondence
- Product manuals
- Meeting notes
- Project plans
- Miscellaneous reports

**Processing Optimizations:**
- **Balanced Chunks (1000 characters)**: Good for varied content
- **Moderate Overlap (200 characters)**: Context preservation
- **Flexible Processing**: Adapts to content structure
- **General Purpose**: Works well for diverse queries

**Best Query Types:**
```
"What skills are mentioned on this resume?"
"Find contact information in these documents"
"Summarize the main points"
"What experience is listed?"
```

### Classification Confidence

Each document receives a confidence score:

- **High Confidence (85%+)**: Clear category indicators
- **Medium Confidence (65-85%)**: Some category features present
- **Low Confidence (<65%)**: Ambiguous or mixed content

**Note**: Classification affects optimization but doesn't prevent functionality. All documents work with all query types, though some may be more efficient than others.

## Email Classification

### Classification Process

Emails are classified by analyzing:

1. **Subject Line Patterns**: Keywords and formatting
2. **Sender Information**: Domain, sender reputation, frequency
3. **Content Analysis**: Message body, tone, terminology
4. **Metadata**: Labels, threading, importance markers
5. **Recipient Context**: To/CC/BCC patterns

### Email Categories

#### Business Emails

**Automatic Detection Criteria:**
- Work-related keywords (meeting, project, deadline, client)
- Professional email domains (@company.com)
- Calendar invitations and meeting requests
- Corporate terminology and formal language
- Work schedule and business hour timing

**Examples:**
- Meeting invitations and calendar events
- Project updates and status reports
- Team communications and announcements
- Client correspondence
- Work-related notifications

**Processing Optimizations:**
- **Professional Context**: Work-focused keyword recognition
- **Thread Awareness**: Full conversation context
- **Temporal Patterns**: Business hour weighting
- **Hierarchy Recognition**: Manager/team relationships

**Best Query Types:**
```
"Find emails about the quarterly review meeting"
"What did my manager say about the project timeline?"
"Show me all team communications from last week"
"Find client emails about budget approval"
```

#### Personal Emails

**Automatic Detection Criteria:**
- Personal relationships (family, friends)
- Informal language and casual tone
- Personal domains (@gmail.com, @yahoo.com)
- Social and family-related content
- Personal event and activity references

**Examples:**
- Family communications
- Friend correspondence
- Personal invitations
- Social updates
- Private conversations

**Processing Optimizations:**
- **Relationship Context**: Personal name recognition
- **Informal Language**: Casual conversation patterns
- **Social Patterns**: Personal event recognition
- **Emotional Context**: Tone and sentiment awareness

**Best Query Types:**
```
"Find emails from my family about vacation plans"
"What did Sarah say about the birthday party?"
"Show me personal emails from last month"
"Find conversations about weekend activities"
```

#### Promotional Emails

**Automatic Detection Criteria:**
- Marketing language (sale, deal, offer, discount)
- Newsletter formats and structures
- Promotional sender patterns
- Unsubscribe links and marketing footers
- Product announcements and campaigns

**Examples:**
- Marketing emails and advertisements
- Newsletter subscriptions
- Product announcements
- Sales notifications
- Promotional campaigns

**Processing Optimizations:**
- **Marketing Keywords**: Deal and promotion recognition
- **Brand Recognition**: Company and product identification
- **Offer Extraction**: Price and discount detection
- **Content Filtering**: Focus on relevant promotional content

**Best Query Types:**
```
"Find deals from Amazon last month"
"Show me all newsletter emails"
"What promotions did I receive from Apple?"
"Find discount offers over 50%"
```

#### Transactional Emails

**Automatic Detection Criteria:**
- Transaction confirmations and receipts
- Account notifications and updates
- Service confirmations
- Payment and billing information
- Order and shipping notifications

**Examples:**
- Purchase receipts
- Account statements
- Service confirmations
- Booking confirmations
- Payment notifications

**Processing Optimizations:**
- **Transaction Data**: Amount and date extraction
- **Service Recognition**: Vendor and service identification
- **Account Context**: User account pattern recognition
- **Financial Integration**: Links to financial document data

**Best Query Types:**
```
"Find my receipt from Apple Store"
"Show me all Uber receipts from March"
"What subscriptions renewed this month?"
"Find all purchase confirmations over $100"
```

#### Support Emails

**Automatic Detection Criteria:**
- Customer service interactions
- Technical support conversations
- Help desk communications
- Ticket numbers and case references
- Problem resolution language

**Examples:**
- Customer service responses
- Technical support tickets
- Help desk communications
- Product support
- Account assistance

**Processing Optimizations:**
- **Issue Tracking**: Problem and solution identification
- **Support Context**: Ticket and case recognition
- **Resolution Patterns**: Problem-solution pairing
- **Service Quality**: Response time and satisfaction tracking

**Best Query Types:**
```
"Find my support conversation about billing issues"
"What did customer service say about my refund?"
"Show me all technical support tickets"
"Find the resolution to my account problem"
```

## Classification Benefits

### Processing Optimization

**Document-Specific Benefits:**
- **Financial**: Optimized for precise transaction matching
- **Long-form**: Enhanced for comprehensive understanding
- **Generic**: Balanced for flexible content types

**Email-Specific Benefits:**
- **Business**: Work context and professional terminology
- **Personal**: Relationship and social context
- **Promotional**: Marketing and offer recognition
- **Transactional**: Purchase and service data
- **Support**: Problem-solution tracking

### Search Enhancement

**Improved Relevance:**
- Category-specific keyword weighting
- Context-aware result ranking
- Optimized chunking for query types
- Enhanced source attribution

**Performance Benefits:**
- Faster search within categories
- Reduced false positives
- More accurate semantic matching
- Better cross-content queries

## Working with Classification

### Understanding Results

When viewing classification results:

```json
{
  "document_type": "financial",
  "confidence": 0.92,
  "processing_metadata": {
    "chunk_size": 500,
    "overlap": 50,
    "optimization": "transaction_focused"
  }
}
```

**Key Information:**
- **Type**: The assigned category
- **Confidence**: How certain the system is
- **Optimization**: Processing strategy used

### Classification Accuracy

**High Accuracy Categories:**
- Financial documents with clear transaction patterns
- Business emails with professional formatting
- Promotional emails with marketing language

**Moderate Accuracy Categories:**
- Mixed-content documents
- Personal emails with varied topics
- Generic documents with diverse content

**Note**: Lower accuracy doesn't mean poor functionality. The system is designed to work effectively regardless of classification confidence.

### Manual Verification

While classification is automatic, you can verify accuracy:

1. **Check Processing Details**: Review document metadata
2. **Test Queries**: Try category-specific query patterns
3. **Compare Results**: Note if results match expectations
4. **Monitor Performance**: Observe search quality over time

## Best Practices

### Document Upload

1. **Use Descriptive Filenames**: Help with context recognition
2. **Single Category Per File**: Avoid mixed-content documents when possible
3. **Clear Structure**: Well-formatted documents classify better
4. **Verify Processing**: Check that classification makes sense

### Email Management

1. **Regular Sync**: Keep email classification current
2. **Category Awareness**: Understand your email patterns
3. **Query Adaptation**: Use category-appropriate query styles
4. **Performance Monitoring**: Note search quality across categories

### Query Optimization

1. **Category-Specific Queries**: Use optimized patterns for each type
2. **Cross-Category Search**: Leverage unified search when appropriate
3. **Result Verification**: Check that sources match expectations
4. **Iterative Improvement**: Refine query techniques based on results

## Troubleshooting Classification

### Incorrect Classification

**Common Causes:**
- Mixed content in single document
- Ambiguous formatting or structure
- Unusual document types
- Poor text extraction quality

**Solutions:**
- Classification doesn't prevent functionality
- Try different query approaches
- Focus on content rather than category
- Report patterns for future improvement

### Low Confidence Scores

**Understanding Low Confidence:**
- Document has mixed characteristics
- Unusual formatting or structure
- Limited content for analysis
- Borderline between categories

**Working with Low Confidence:**
- System still processes effectively
- May use generic processing approach
- All query types remain available
- Performance usually unaffected

### Category Mismatch

**When Classification Seems Wrong:**
- Remember it's optimization, not limitation
- All categories support all query types
- Focus on query techniques rather than classification
- System learns and improves over time

The classification system is designed to enhance your experience while maintaining full functionality regardless of category assignment.