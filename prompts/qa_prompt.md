# Question Answering Prompt

## Purpose
Answer user questions about uploaded contracts with accuracy and proper citations.

## System Message
```
You are a legal document analyst. Answer questions accurately based on the provided contract text. Include specific details and quote relevant passages when possible.
```

## User Prompt Template

```
Answer the following question based on the provided contract excerpts. If the answer cannot be found in the context, say "I cannot find this information in the provided contracts."

Context:
{context_chunks}

Question: {question}

Answer:
```

## Model Configuration
- **Model**: gpt-4-turbo-preview
- **Temperature**: 0.2 (low creativity, high accuracy)
- **Max Tokens**: 1000
- **Streaming**: Optional (SSE endpoint available)

## Design Rationale

### RAG Architecture
1. **Question Embedding**: Convert question to 1536-dim vector
2. **Similarity Search**: Find top-5 most relevant chunks
3. **Context Assembly**: Combine chunks into prompt
4. **Answer Generation**: LLM generates grounded answer
5. **Citation Mapping**: Return source chunks as citations

### Temperature Setting
- **0.2**: Slightly higher than extraction for natural language
- **Trade-off**: Some creativity for readable answers
- **Rationale**: Legal accuracy more important than eloquence

### Context Management
- **Chunk Selection**: Top-5 by cosine similarity
- **Token Limit**: Context truncated to 6000 tokens
- **Order**: Chunks presented in relevance order, not document order

### Fallback Response
When no answer found in context:
```
"I cannot find this information in the provided contracts."
```

**Rationale**:
- Prevents hallucination
- Explicitly states limitation
- Prompts user to rephrase or check different documents

## Example Interactions

### Example 1: Direct Factual Question

**Question**: "What is the liability cap in this contract?"

**Context** (chunk from contract):
```
Section 8. Limitation of Liability. In no event shall either party's total liability under this Agreement exceed the amount of $500,000 USD. This limitation applies to all claims in aggregate, regardless of the form of action.
```

**Answer**:
```
The liability cap in this contract is $500,000 USD. This limitation applies to all claims in aggregate, regardless of the form of action. (Section 8)
```

**Citations**:
- Document ID, Page 4, chars 2150-2350

### Example 2: Interpretive Question

**Question**: "Can either party terminate this agreement early?"

**Context**:
```
Either party may terminate this Agreement upon sixty (60) days prior written notice to the other party. Upon termination, all obligations cease except those that expressly survive termination.
```

**Answer**:
```
Yes, either party can terminate this agreement early by providing sixty (60) days prior written notice to the other party. After termination, all obligations cease except for those that are explicitly stated to survive termination.
```

### Example 3: Question Not in Context

**Question**: "What insurance requirements are specified?"

**Context**: (No insurance information in top-5 chunks)

**Answer**:
```
I cannot find this information in the provided contracts.
```

### Example 4: Comparative Question

**Question**: "How does the payment terms in Contract A compare to Contract B?"

**Context**: (Chunks from both contracts)

**Answer**:
```
Contract A requires payment within Net 30 days from invoice date, while Contract B specifies payment due upon receipt. Contract A also includes a 1.5% late fee after 30 days, which is not mentioned in Contract B.
```

## Prompt Engineering Techniques

### 1. Context-First Approach
- Present context before question
- Helps model ground answer in provided text
- Reduces hallucination risk

### 2. Explicit Instruction
- "Answer based on provided excerpts"
- "If cannot find, say so explicitly"
- Sets clear expectations for model

### 3. Citation Encouragement
- "Quote relevant passages when possible"
- Increases answer verifiability
- Improves user trust

### 4. Professional Tone
- "Legal document analyst" persona
- Formal, precise language
- Appropriate for legal domain

## Common Question Types

### Factual Extraction
- "What is the term length?"
- "Who are the parties?"
- "What is the effective date?"

**Strategy**: Direct extraction from context

### Clause Interpretation
- "Can the contract auto-renew?"
- "What happens if one party breaches?"

**Strategy**: Summarize and explain clause

### Comparison
- "How do termination clauses differ between documents?"

**Strategy**: Extract and contrast relevant sections

### Risk Assessment
- "What are the risks in this indemnity clause?"

**Strategy**: Identify concerning language and explain implications

## Limitations

### 1. Context Window
- Limited to top-5 chunks (configurable)
- May miss relevant info in other chunks
- **Mitigation**: User can refine question or increase max_citations

### 2. No Legal Advice
- Provides information, not legal counsel
- Cannot advise on contract negotiation
- **Disclaimer**: Add to API docs and responses

### 3. Cross-Document Reasoning
- Limited ability to synthesize across many documents
- Best for focused queries
- **Future**: Implement multi-hop reasoning

### 4. Temporal Understanding
- May struggle with timeline questions
- "What happens 6 months after termination?"
- **Future**: Enhanced temporal reasoning

## Streaming Support

For long answers, streaming endpoint available:

```
GET /ask/stream?question=...&document_ids=...
```

**Benefits**:
- Real-time feedback
- Perceived faster response
- Better UX for complex questions

**Implementation**:
- Server-Sent Events (SSE)
- Token-by-token streaming
- Final "[DONE]" signal

## Evaluation Metrics

### Answer Quality
- **Relevance**: Does answer address question?
- **Accuracy**: Is information correct?
- **Completeness**: Are all aspects covered?
- **Citation Quality**: Are sources properly identified?

### Performance
- **Response Time**: Target <3s for typical question
- **Token Efficiency**: Minimize tokens while maintaining quality

## Improvement Opportunities

### Short-term
- [ ] Citation formatting (quotes, page numbers)
- [ ] Multi-document synthesis
- [ ] Follow-up question support

### Medium-term
- [ ] Confidence scoring
- [ ] Explanation of reasoning
- [ ] Clause highlighting in UI

### Long-term
- [ ] Interactive clarification
- [ ] Suggested follow-up questions
- [ ] Visual answer presentation (tables, charts)

## Fallback Behavior

When LLM unavailable:
- Return error: "Q&A service temporarily unavailable"
- **Future**: Keyword-based search fallback

## Version History

- **v1.0**: Initial RAG implementation with top-5 retrieval
- **Future**: Adaptive retrieval based on question complexity
