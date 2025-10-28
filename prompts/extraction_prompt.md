# Extraction Prompt

## Purpose
Extract structured contract fields from legal documents with high accuracy and consistency.

## System Message
```
You are a legal document analysis expert. Extract structured information from contracts accurately.
```

## User Prompt Template

```
Extract the following fields from this contract. Return valid JSON only.

Contract text:
{contract_text}

Extract these fields (set to null if not found):
- parties: array of party names (organizations/individuals)
- effective_date: date when contract becomes effective
- term: contract duration/term length
- governing_law: jurisdiction/governing law
- payment_terms: payment conditions and schedule
- termination: termination conditions
- auto_renewal: auto-renewal clause details
- confidentiality: confidentiality provisions
- indemnity: indemnification provisions
- liability_cap_amount: liability cap amount (number only)
- liability_cap_currency: currency for liability cap (USD, EUR, etc.)
- signatories: array of objects with "name" and "title" fields

Return JSON in this exact format:
{
  "parties": ["Party A", "Party B"],
  "effective_date": "date string or null",
  "term": "term description or null",
  "governing_law": "jurisdiction or null",
  "payment_terms": "terms or null",
  "termination": "conditions or null",
  "auto_renewal": "clause or null",
  "confidentiality": "provisions or null",
  "indemnity": "provisions or null",
  "liability_cap_amount": number or null,
  "liability_cap_currency": "currency or null",
  "signatories": [{"name": "John Doe", "title": "CEO"}] or null
}
```

## Model Configuration
- **Model**: gpt-4-turbo-preview
- **Temperature**: 0.1 (deterministic for consistency)
- **Max Tokens**: 2000
- **Response Format**: JSON object mode

## Design Rationale

### Field Selection
The 12 fields were chosen based on:
1. **Universal Applicability**: Present in most contract types
2. **Legal Significance**: Important for risk assessment
3. **Structured Data**: Amenable to automated extraction
4. **User Value**: Frequently queried by legal professionals

### Temperature Setting
- **Low (0.1)**: Ensures consistent extraction across similar documents
- **Trade-off**: May be overly conservative; temperature 0.3-0.5 could add useful flexibility
- **Rationale**: Legal accuracy prioritized over creative interpretation

### JSON Mode
- **Benefit**: Guaranteed valid JSON response
- **Alternative**: Could use function calling for stronger typing
- **Choice**: JSON mode simpler and sufficient for current needs

### Handling Missing Fields
- **Approach**: Return null for missing fields
- **Alternative**: Omit missing fields entirely
- **Rationale**: Explicit null indicates "searched but not found" vs "not searched"

### Token Management
- **Truncation**: Contract text truncated to 6000 tokens if needed
- **Trade-off**: May miss information in very long contracts
- **Mitigation**: Future enhancement to process multiple chunks and merge results

## Example Outputs

### Well-Structured Contract
```json
{
  "parties": ["Acme Corporation", "Beta Services LLC"],
  "effective_date": "January 15, 2024",
  "term": "24 months from effective date",
  "governing_law": "State of California",
  "payment_terms": "Net 30 days from invoice date",
  "termination": "Either party may terminate with 60 days written notice",
  "auto_renewal": "Automatically renews for successive 12-month terms unless either party provides 30 days notice",
  "confidentiality": "5 years from disclosure date",
  "indemnity": "Each party indemnifies the other for third-party claims arising from its breach",
  "liability_cap_amount": 500000,
  "liability_cap_currency": "USD",
  "signatories": [
    {"name": "Jane Smith", "title": "Chief Executive Officer"},
    {"name": "Robert Johnson", "title": "President"}
  ]
}
```

### Poorly-Structured Contract (Many Nulls)
```json
{
  "parties": ["Company A", "Company B"],
  "effective_date": null,
  "term": null,
  "governing_law": "Delaware",
  "payment_terms": null,
  "termination": "At-will",
  "auto_renewal": null,
  "confidentiality": null,
  "indemnity": null,
  "liability_cap_amount": null,
  "liability_cap_currency": null,
  "signatories": null
}
```

## Common Extraction Challenges

### 1. Multiple Date Formats
- "January 1, 2024"
- "01/01/2024"
- "1st day of January, 2024"
- **Solution**: LLM normalizes to readable format

### 2. Implicit Party Names
- "The Company" vs actual company name
- **Solution**: Extract actual names from preamble/signatures

### 3. Complex Term Descriptions
- "Initial term of 12 months plus renewal terms of 6 months each"
- **Solution**: Extract full description, not just numbers

### 4. Liability Cap Variations
- Percentage of fees vs fixed amount
- Multiple caps for different claim types
- **Solution**: Extract primary/largest cap

## Improvement Opportunities

### Short-term
- [ ] Few-shot examples for better accuracy
- [ ] Field-specific validation rules
- [ ] Confidence scoring per field

### Medium-term
- [ ] Multi-chunk processing for long documents
- [ ] Cross-reference validation (date consistency)
- [ ] Entity linking (resolve pronoun references)

### Long-term
- [ ] Fine-tuned model on legal contracts
- [ ] Active learning from user corrections
- [ ] Hierarchical field extraction (nested structures)

## Evaluation Metrics

### Accuracy
- **Field Recall**: % of present fields correctly extracted
- **Field Precision**: % of extracted fields that are correct
- **Exact Match**: % of documents with all fields correct

### Performance
- **Average Time**: Typical extraction time
- **Token Usage**: Average tokens consumed per extraction

### Cost
- **Per Extraction**: ~$0.03 at current GPT-4 pricing
- **Optimization**: Consider GPT-3.5 for simpler contracts

## Fallback Behavior

When LLM unavailable, rule-based extraction attempts:
- **Effective Date**: Regex for date patterns near "effective date"
- **Governing Law**: "governed by laws of X"
- **Term**: "term of X years/months"
- **Confidence**: Lower (0.6) due to limited coverage

## Version History

- **v1.0**: Initial implementation with 12 fields
- **Future**: Add custom field support based on user feedback
