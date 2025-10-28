# Risk Audit Rules

## Purpose
Document the rule-based risk detection logic for contract auditing.

## Overview

The audit service uses deterministic regex patterns to detect known risky clauses. This approach provides:
- **Consistency**: Same input always produces same findings
- **Explainability**: Clear rules, not black-box AI
- **Speed**: Faster than LLM-based detection
- **Reliability**: Works without external API dependencies

## Risk Categories

### 1. Auto-Renewal with Short Notice

**Risk**: Contract automatically renews with insufficient time to cancel

**Detection Rules**:
```regex
auto(?:matically)?\s+renew(?:al|s|ed)?.*?(\d+)\s*day(?:s)?
renew(?:al|s|ed)?\s+(?:automatically|auto).*?(\d+)\s*day(?:s)?
auto(?:matic)?\s+renewal.*?notice.*?(\d+)\s*day(?:s)?
```

**Severity Logic**:
- **High**: Notice period < 15 days
- **Medium**: Notice period 15-29 days
- **Low**: Notice period 30+ days (not flagged)

**Example Detection**:
```
"...automatically renew for successive one-year terms unless either party
provides written notice of non-renewal at least 15 days prior..."
```
→ **High severity**: 15-day notice insufficient for most businesses

**Confidence**: 0.9 (high confidence in pattern matching)

### 2. Unlimited Liability

**Risk**: No cap on financial exposure for claims

**Detection Rules**:
```regex
unlimited\s+liability
no\s+(?:limit|cap)\s+(?:on|to)\s+liability
liability\s+shall\s+not\s+be\s+limited
without\s+(?:limit|limitation)\s+of\s+liability
```

**Severity**: **Critical** (always)

**Example Detection**:
```
"The liability of the service provider under this agreement shall be
unlimited and not subject to any cap or limitation."
```
→ **Critical severity**: Unbounded financial risk

**Confidence**: 0.95 (very high confidence - explicit language)

**Additional Check**:
If contract mentions liability but no cap pattern found:
- Severity: **High**
- Description: "No clear liability cap specified"
- Confidence: 0.7 (lower - absence-based detection)

### 3. Broad Indemnification

**Risk**: Overly broad obligations to defend/compensate other party

**Detection Rules**:
```regex
indemnif(?:y|ication).*?(?:any|all).*?(?:claims?|losses?|damages?|liabilities)
hold\s+harmless.*?(?:any|all).*?(?:claims?|losses?)
indemnif(?:y|ication).*?(?:including|without\s+limitation)
```

**Severity Logic**:
- **High**: Broad language without carveouts
- **Medium**: Broad language with some limitations ("except", "excluding")

**Example Detection**:
```
"Customer shall indemnify and hold harmless Provider from any and all
claims, losses, damages, and liabilities, including without limitation
attorney fees and costs."
```
→ **High severity**: "any and all" + "without limitation" = very broad

**Confidence**: 0.85

### 4. Unilateral Termination

**Risk**: One party can terminate at will, creating imbalance

**Detection Rules**:
```regex
(?:may|shall|can)\s+terminate.*?(?:at\s+any\s+time|without\s+cause|for\s+any\s+reason)
terminate.*?(?:at\s+its\s+sole\s+discretion|in\s+its\s+sole\s+discretion)
```

**Severity**: **Medium** (unless paired with penalty clauses)

**Example Detection**:
```
"Provider may terminate this Agreement at any time for any reason upon
written notice to Customer."
```
→ **Medium severity**: Imbalanced termination rights

**Confidence**: 0.8

### 5. Assignment Restrictions

**Risk**: Inability to assign contract limits business flexibility

**Detection Rules**:
```regex
(?:may|shall)\s+not\s+assign.*?without.*?(?:consent|approval)
assignment.*?prohibited.*?without.*?(?:consent|approval)
```

**Severity Logic**:
- **Medium**: Consent required + no "not unreasonably withheld" language
- **Low**: Consent required but "not unreasonably withheld" present

**Example Detection**:
```
"Neither party may assign this Agreement without the prior written consent
of the other party."
```
→ **Medium severity** (if no unreasonableness standard)
→ **Low severity** (if includes "not unreasonably withheld")

**Confidence**: 0.75

### 6. Perpetual Confidentiality

**Risk**: Indefinite confidentiality obligations may be impractical

**Detection Rules**:
```regex
confidential(?:ity)?.*?(?:perpetual|indefinite|forever)
confidential(?:ity)?.*?(?:survive|continue).*?(?:indefinitely|termination)
confidential(?:ity)?.*?no\s+time\s+limit
```

**Severity**: **Medium**

**Example Detection**:
```
"The confidentiality obligations shall survive termination of this Agreement
and continue indefinitely."
```
→ **Medium severity**: Perpetual obligation is burdensome

**Confidence**: 0.8

## Evidence Extraction

For each finding, extract:
- **evidence_text**: Actual clause text (up to 200 chars)
- **char_start**: Character position in document
- **char_end**: End position
- **page_number**: Page where clause appears (if available)

This enables:
- Precise citation
- UI highlighting
- User verification

## False Positive Mitigation

### Context Analysis
Some rules check surrounding context:
- Broad indemnity: Look for "except", "excluding" to reduce severity
- Assignment: Check for "not unreasonably withheld"

### Confidence Scoring
Lower confidence when:
- Pattern is ambiguous
- Detection based on absence (no cap found)
- Limited context available

## Limitations

### What Rules Cannot Detect
1. **Subtle Unfairness**: Clause that's technically legal but imbalanced
2. **Industry-Specific Risks**: Without domain knowledge
3. **Cross-Clause Interactions**: How multiple clauses combine
4. **Jurisdictional Nuances**: What's risky in one state may be normal in another

### Future LLM Enhancement
Rules could be augmented with LLM analysis:
- LLM reviews findings to reduce false positives
- LLM detects risks beyond rule coverage
- Hybrid approach: Rules + LLM verification

## Customization

Rules can be customized per client:
- Adjust severity thresholds (e.g., 45 days for auto-renewal)
- Add industry-specific rules
- Disable rules for certain contract types

Configuration could be database-driven for flexibility.

## Testing

Each rule should have:
1. **Positive tests**: Known risky clauses that should trigger
2. **Negative tests**: Safe clauses that should not trigger
3. **Edge cases**: Borderline language

See `tests/unit/test_audit_service.py` for examples.

## Performance

Rule-based detection is fast:
- ~50ms for typical contract (5000 words)
- Linear with document size
- No API calls required
- Can run offline

Compare to LLM-based:
- ~3-5 seconds
- API latency dependent
- Higher cost
- But more comprehensive

## Version History

- **v1.0**: Initial 6 rule categories
- **Future**: Add categories based on user feedback and legal research
