# Querying Your Data

Learn how to effectively search and query your PDF documents and Gmail emails using natural language.

## Query Types

Personal AI Agent supports several types of queries, each optimized for different use cases:

### Simple Content Queries

Ask direct questions about your documents and emails:

```
"What is my current bank balance?"
"Find emails from Apple about receipts"
"What skills are mentioned on my resume?"
```

### Cross-Content Queries

Search across both PDFs and emails simultaneously:

```
"Find all information about Apple purchases"
"Show me everything related to Project Alpha"
"What do my documents say about machine learning?"
```

### Analytical Queries

Get insights and analysis from your data:

```
"Categorize my March expenses"
"Summarize the key findings in my research papers"
"What are the main topics in my business emails?"
```

### Temporal Queries

Search by time periods and dates:

```
"What were my expenses in Q1 2024?"
"Find emails from last week about meetings"
"Show me documents created after January 1st"
```

## Query Optimization

### Be Specific

**Good**: "Apple transactions over $100 in March 2024"
**Poor**: "Apple stuff"

**Good**: "Meeting notes from quarterly review with Sarah"
**Poor**: "meetings"

### Include Context

**Good**: "From my bank statement, find grocery expenses"
**Poor**: "groceries"

**Good**: "In my research papers, explain the methodology"
**Poor**: "methodology"

### Use Natural Language

The system understands conversational queries:

```
"How much did I spend on restaurants last month?"
"What did my manager say about the project timeline?"
"Can you explain the main conclusions from this research?"
```

## Content-Specific Strategies

### Financial Document Queries

Best for transaction analysis and expense tracking:

```
# Transaction searches
"Find all Amazon purchases in March"
"How much did I spend on groceries?"
"Show me all transactions over $500"

# Balance and account queries
"What was my balance on March 15th?"
"Find all overdraft fees"
"Show me all deposits this quarter"

# Expense analysis
"Categorize my spending by merchant"
"What percentage of my income went to dining?"
"Compare my Q1 and Q2 expenses"
```

### Email Queries

Optimized for communication and correspondence:

```
# Conversation searches
"Find the email thread about budget approval"
"What did John say about the deadline?"
"Show me all emails from customer support"

# Category-specific searches
"Find business emails about meetings"
"Show me all promotional emails from Amazon"
"Find transactional emails with receipts"

# Content searches
"Find emails containing project updates"
"Show me all emails with attachments"
"Find emails marked as important"
```

### Research Document Queries

Best for long-form content analysis:

```
# Content analysis
"Summarize the main findings"
"What methodology was used?"
"List the key recommendations"

# Deep understanding
"Explain the theoretical framework"
"What are the limitations mentioned?"
"How does this relate to previous work?"

# Structure queries
"What are the main sections?"
"Find the conclusion"
"Show me the abstract"
```

## Advanced Query Techniques

### Using Filters

Narrow your search with built-in filters:

```json
{
  "query": "Apple purchases",
  "content_types": ["pdf"],
  "document_types": ["financial"],
  "max_results": 10
}
```

### Combining Multiple Criteria

```
"Find Apple transactions over $100 from my bank statements in March 2024"
```

This query combines:
- Entity: Apple
- Amount: over $100
- Source: bank statements
- Time: March 2024

### Follow-up Questions

The system maintains context for follow-up queries:

```
User: "What were my Apple expenses in March?"
AI: "You spent $1,247.89 on Apple products in March..."

User: "What specific items did I buy?"
AI: "Based on the previous results, you purchased..."
```

## Query Response Structure

### Answer with Sources

Every response includes:

1. **Direct Answer**: Clear response to your question
2. **Source Citations**: References to specific documents/emails
3. **Confidence Indicators**: How certain the AI is about the answer
4. **Context**: Relevant surrounding information

Example response:
```
Based on your financial documents, you spent $1,247.89 on Apple products in March 2024.

Sources:
- Bank Statement March 2024 (Page 2): "03/15/2024 APPLE STORE $899.00"
- Email from Apple Store: "Your receipt for iPhone 15 Pro purchase"
- Credit Card Statement: "APPLE.COM/BILL $67.89"
```

### Understanding Confidence

- **High Confidence (90%+)**: Direct matches with clear source attribution
- **Medium Confidence (70-90%)**: Good matches with some interpretation
- **Low Confidence (<70%)**: Possible matches, verify sources carefully

## Common Query Patterns

### Financial Analysis

```
"How much did I spend on [category] in [time period]?"
"Find all transactions with [merchant/vendor]"
"What was my [account] balance on [date]?"
"Compare my spending between [period1] and [period2]"
```

### Email Communication

```
"Find emails about [topic] from [person/company]"
"What did [person] say about [subject]?"
"Show me all [category] emails from [time period]"
"Find the conversation thread about [topic]"
```

### Document Research

```
"Summarize [document/topic]"
"What does [document] say about [specific topic]?"
"Find [information type] in [document category]"
"Explain [concept] from my research papers"
```

### Cross-Content Analysis

```
"Find all information about [topic]"
"Show me everything related to [project/person/company]"
"Compare information about [topic] from different sources"
"What do my documents and emails say about [subject]?"
```

## Troubleshooting Queries

### No Results Found

**Try these approaches:**

1. **Broaden your search**: Use more general terms
2. **Check spelling**: Verify terminology matches source documents
3. **Simplify query**: Break complex questions into parts
4. **Verify content**: Ensure documents were processed successfully

### Poor Result Quality

**Improvement strategies:**

1. **Add context**: Include document type or source hints
2. **Be more specific**: Use exact terms from your documents
3. **Rephrase**: Try different ways of asking the same question
4. **Check sources**: Verify the cited sources are relevant

### Slow Response Times

**Optimization tips:**

1. **Use filters**: Limit search scope with content type filters
2. **Reduce result count**: Ask for fewer results initially
3. **Specific queries**: Avoid very broad search terms
4. **Check system resources**: Ensure adequate memory and CPU

## Best Practices

### Query Formulation

1. **Start specific**: Begin with detailed queries and broaden if needed
2. **Use your vocabulary**: Include terms you know appear in your documents
3. **Natural language**: Write queries as you would ask a person
4. **Context matters**: Include relevant background information

### Result Verification

1. **Check sources**: Always verify the cited sources
2. **Cross-reference**: Compare results with original documents
3. **Ask follow-ups**: Clarify unclear or incomplete answers
4. **Report issues**: Note any inaccurate or problematic responses

### Iterative Improvement

1. **Learn from results**: Note which query styles work best
2. **Refine techniques**: Develop personal query patterns
3. **Explore capabilities**: Try different types of questions
4. **Stay updated**: Learn about new features and improvements

## Example Query Session

Here's an example of an effective query session:

```
User: "Find my Apple expenses from March 2024"

AI: "I found $1,247.89 in Apple-related expenses from March 2024:
- iPhone 15 Pro: $899.00 (March 15)
- App Store purchases: $67.89 (various dates)
- Apple Music: $10.99 (March 1)
- Apple Care: $269.99 (March 20)

Sources: Bank Statement March 2024, Apple Store receipts via email"

User: "Which of these was the most expensive?"

AI: "The iPhone 15 Pro at $899.00 was the most expensive Apple purchase in March 2024."

User: "Show me the original receipt for the iPhone"

AI: "Here's the iPhone 15 Pro receipt from your email:
Subject: 'Your Receipt from Apple Store'
Date: March 15, 2024
Amount: $899.00
Payment method: Visa ending in 4532"
```

This demonstrates effective use of:
- Specific initial query
- Natural follow-up questions
- Context maintenance across the conversation
- Detailed source attribution