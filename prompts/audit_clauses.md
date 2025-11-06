# Audit Clauses Detection Prompt

## Purpose
This prompt is used to detect risky clauses in contracts using GPT-3.5-turbo.

## Prompt Template

```
Analyze this contract for risky clauses. Return as JSON array:
[
  {
    "finding_type": "type of risk",
    "severity": "critical|high|medium|low",
    "description": "explanation",
    "evidence_text": "exact quote from contract"
  }
]

Look for:
- Auto-renewal with less than 30 days notice
- Unlimited liability
- Broad indemnity clauses
- Unfavorable payment terms
- Restrictive termination clauses

Contract text:
{text}

Return ONLY valid JSON array, no markdown.
```

## Rationale

1. **Risk Categories**: Focuses on common contract risks that legal teams care about.
2. **Severity Levels**: Provides actionable priority (critical vs. low) for risk management.
3. **Evidence Extraction**: Including exact quotes enables verification and negotiation.
4. **Temperature 0.1**: Low temperature ensures consistent risk detection.
5. **Array Format**: Allows multiple findings per contract.

## Example Output

```json
[
  {
    "finding_type": "Unlimited Liability",
    "severity": "critical",
    "description": "Contract contains unlimited liability clause with no cap on damages",
    "evidence_text": "The parties agree to unlimited liability for all claims arising from this agreement"
  },
  {
    "finding_type": "Insufficient Auto-Renewal Notice",
    "severity": "high",
    "description": "Auto-renewal requires only 15 days notice, less than industry standard of 30 days",
    "evidence_text": "This agreement will automatically renew unless either party provides 15 days written notice"
  }
]
```

## Risk Severity Mapping

| Severity | Definition | Example |
| --- | --- | --- |
| **Critical** | Immediate legal/financial exposure | Unlimited liability, broad indemnity |
| **High** | Significant risk requiring negotiation | Auto-renewal <30 days, unfavorable payment terms |
| **Medium** | Should be reviewed and potentially negotiated | Restrictive termination, unclear jurisdiction |
| **Low** | Minor concern, typically acceptable | Standard confidentiality clause |

## Fallback Mechanism

When LLM is unavailable or disabled, the system falls back to the **Rule-Based Audit Engine** which uses regex patterns and keyword matching for deterministic risk detection. This ensures the audit endpoint always returns results, even without LLM access.

See `app/rule_engine.py` for the fallback implementation.
