# Extract Fields Prompt

## Purpose
This prompt is used to extract structured fields from contract text using GPT-3.5-turbo.

## Prompt Template

```
Extract the following fields from the contract text. Return as JSON:
{
  "parties": ["list of parties"],
  "effective_date": "date or null",
  "term": "duration or null",
  "governing_law": "jurisdiction or null",
  "payment_terms": "payment terms or null",
  "termination": "termination clause or null",
  "auto_renewal": true/false or null,
  "confidentiality": "summary or null",
  "indemnity": "summary or null",
  "liability_cap": {"amount": number, "currency": "USD"} or null,
  "signatories": [{"name": "name", "title": "title"}]
}

Contract text:
{text}

Return ONLY valid JSON, no markdown or extra text.
```

## Rationale

1. **Structured Output**: Using JSON schema ensures consistent, parseable output that maps directly to our database schema.
2. **Temperature 0.1**: Low temperature ensures deterministic, focused extraction without creative elaboration.
3. **Token Limit**: 1000 tokens is sufficient for most contract field extractions.
4. **Text Limit**: First 4000 characters prevents token overflow while capturing key contract sections.
5. **Null Handling**: Allows graceful handling of missing fields rather than forcing defaults.

## Example Output

```json
{
  "parties": ["Acme Corp", "Widget Inc"],
  "effective_date": "2024-01-01",
  "term": "2 years",
  "governing_law": "New York",
  "payment_terms": "Net 30",
  "termination": "Either party may terminate with 30 days notice",
  "auto_renewal": true,
  "confidentiality": "Both parties agree to maintain confidentiality of proprietary information",
  "indemnity": "Each party indemnifies the other against third-party claims",
  "liability_cap": {"amount": 100000, "currency": "USD"},
  "signatories": [
    {"name": "John Doe", "title": "CEO"},
    {"name": "Jane Smith", "title": "CFO"}
  ]
}
```

## Edge Cases Handled

- **Missing Fields**: Returns `null` for fields not found in contract
- **Multiple Parties**: Returns array of all identified parties
- **Complex Dates**: Attempts to normalize to ISO format
- **Currency Amounts**: Extracts both amount and currency code
- **Nested Structures**: Properly handles signatories as array of objects
