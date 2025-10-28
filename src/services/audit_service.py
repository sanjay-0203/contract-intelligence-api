"""Audit service for detecting risky contract clauses."""
import re
from typing import List, Dict, Tuple
from sqlalchemy.orm import Session
from src.models.database import Document, DocumentChunk


class AuditService:
    """Service for detecting risky clauses in contracts."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def audit_contract(self, document_id: str, full_text: str) -> List[Dict]:
        """
        Audit contract for risky clauses.
        
        Returns list of findings with severity and evidence.
        """
        findings = []
        
        # Check for auto-renewal with short notice
        findings.extend(self._check_auto_renewal(full_text))
        
        # Check for unlimited liability
        findings.extend(self._check_unlimited_liability(full_text))
        
        # Check for broad indemnity
        findings.extend(self._check_broad_indemnity(full_text))
        
        # Check for unilateral termination rights
        findings.extend(self._check_unilateral_termination(full_text))
        
        # Check for assignment restrictions
        findings.extend(self._check_assignment_restrictions(full_text))
        
        # Check for perpetual confidentiality
        findings.extend(self._check_perpetual_confidentiality(full_text))
        
        return findings
    
    def _check_auto_renewal(self, text: str) -> List[Dict]:
        """Detect auto-renewal clauses with insufficient notice period."""
        findings = []
        
        # Pattern for auto-renewal with notice period
        patterns = [
            (r'auto(?:matically)?\s+renew(?:al|s|ed)?.*?(\d+)\s*day(?:s)?', 'days'),
            (r'renew(?:al|s|ed)?\s+(?:automatically|auto).*?(\d+)\s*day(?:s)?', 'days'),
            (r'auto(?:matic)?\s+renewal.*?notice.*?(\d+)\s*day(?:s)?', 'days'),
        ]
        
        for pattern, unit in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                days = int(match.group(1))
                evidence_start = match.start()
                evidence_end = min(match.end() + 100, len(text))
                evidence = text[match.start():evidence_end]
                
                if days < 30:
                    severity = "high" if days < 15 else "medium"
                    findings.append({
                        "risk_type": "auto_renewal_short_notice",
                        "severity": severity,
                        "title": f"Auto-renewal with {days}-day notice period",
                        "description": f"Contract automatically renews with only {days} days' notice, which may be insufficient to cancel before renewal.",
                        "evidence_text": evidence,
                        "char_start": evidence_start,
                        "char_end": evidence_end,
                        "detection_method": "rule_based",
                        "confidence_score": 0.9
                    })
        
        # Pattern for auto-renewal without clear notice period
        if re.search(r'auto(?:matically)?\s+renew(?:al|s)?', text, re.IGNORECASE):
            if not re.search(r'(\d+)\s*day(?:s)?\s*(?:notice|prior|advance)', text, re.IGNORECASE):
                match = re.search(r'auto(?:matically)?\s+renew(?:al|s)?[^.]{0,200}', text, re.IGNORECASE)
                if match:
                    findings.append({
                        "risk_type": "auto_renewal_unclear_notice",
                        "severity": "medium",
                        "title": "Auto-renewal clause without clear notice period",
                        "description": "Contract contains auto-renewal language but does not specify a clear notice period for cancellation.",
                        "evidence_text": match.group(0),
                        "char_start": match.start(),
                        "char_end": match.end(),
                        "detection_method": "rule_based",
                        "confidence_score": 0.8
                    })
        
        return findings
    
    def _check_unlimited_liability(self, text: str) -> List[Dict]:
        """Detect unlimited liability clauses."""
        findings = []
        
        # Check for explicit unlimited liability
        patterns = [
            r'unlimited\s+liability',
            r'no\s+(?:limit|cap)\s+(?:on|to)\s+liability',
            r'liability\s+shall\s+not\s+be\s+limited',
            r'without\s+(?:limit|limitation)\s+of\s+liability'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                evidence_start = max(0, match.start() - 50)
                evidence_end = min(match.end() + 100, len(text))
                evidence = text[evidence_start:evidence_end]
                
                findings.append({
                    "risk_type": "unlimited_liability",
                    "severity": "critical",
                    "title": "Unlimited liability clause detected",
                    "description": "Contract contains language indicating unlimited liability, which could expose the party to significant financial risk.",
                    "evidence_text": evidence,
                    "char_start": evidence_start,
                    "char_end": evidence_end,
                    "detection_method": "rule_based",
                    "confidence_score": 0.95
                })
        
        # Check for absence of liability cap in liability section
        if re.search(r'liabilit(?:y|ies)', text, re.IGNORECASE):
            if not re.search(r'(?:limited|capped|cap)\s+(?:to|at)\s+(?:\$|USD|EUR)?[\d,]+', text, re.IGNORECASE):
                findings.append({
                    "risk_type": "no_liability_cap",
                    "severity": "high",
                    "title": "No clear liability cap specified",
                    "description": "Contract mentions liability but does not specify a clear monetary cap or limitation.",
                    "evidence_text": "Liability section present but no cap found",
                    "char_start": None,
                    "char_end": None,
                    "detection_method": "rule_based",
                    "confidence_score": 0.7
                })
        
        return findings
    
    def _check_broad_indemnity(self, text: str) -> List[Dict]:
        """Detect overly broad indemnification clauses."""
        findings = []
        
        patterns = [
            r'indemnif(?:y|ication).*?(?:any|all).*?(?:claims?|losses?|damages?|liabilities)',
            r'hold\s+harmless.*?(?:any|all).*?(?:claims?|losses?)',
            r'indemnif(?:y|ication).*?(?:including|without\s+limitation)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                evidence_start = match.start()
                evidence_end = min(match.end() + 100, len(text))
                evidence = text[evidence_start:evidence_end]
                
                # Check if there are carve-outs or limitations
                has_limitation = re.search(r'except|excluding|other than', evidence, re.IGNORECASE)
                severity = "medium" if has_limitation else "high"
                
                findings.append({
                    "risk_type": "broad_indemnity",
                    "severity": severity,
                    "title": "Broad indemnification obligation",
                    "description": "Contract contains broad indemnification language that may expose party to extensive liability for third-party claims.",
                    "evidence_text": evidence,
                    "char_start": evidence_start,
                    "char_end": evidence_end,
                    "detection_method": "rule_based",
                    "confidence_score": 0.85
                })
        
        return findings
    
    def _check_unilateral_termination(self, text: str) -> List[Dict]:
        """Detect unilateral termination rights favoring one party."""
        findings = []
        
        patterns = [
            r'(?:may|shall|can)\s+terminate.*?(?:at\s+any\s+time|without\s+cause|for\s+any\s+reason)',
            r'terminate.*?(?:at\s+its\s+sole\s+discretion|in\s+its\s+sole\s+discretion)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                evidence_start = max(0, match.start() - 50)
                evidence_end = min(match.end() + 100, len(text))
                evidence = text[evidence_start:evidence_end]
                
                findings.append({
                    "risk_type": "unilateral_termination",
                    "severity": "medium",
                    "title": "Unilateral termination right",
                    "description": "Contract allows one party to terminate at will, which may create imbalance in contractual obligations.",
                    "evidence_text": evidence,
                    "char_start": evidence_start,
                    "char_end": evidence_end,
                    "detection_method": "rule_based",
                    "confidence_score": 0.8
                })
        
        return findings
    
    def _check_assignment_restrictions(self, text: str) -> List[Dict]:
        """Detect restrictive assignment clauses."""
        findings = []
        
        patterns = [
            r'(?:may|shall)\s+not\s+assign.*?without.*?(?:consent|approval)',
            r'assignment.*?prohibited.*?without.*?(?:consent|approval)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Check if consent can be unreasonably withheld
                evidence_start = max(0, match.start() - 50)
                evidence_end = min(match.end() + 200, len(text))
                evidence = text[evidence_start:evidence_end]
                
                unreasonable = not re.search(r'not\s+(?:be\s+)?unreasonably\s+withheld', evidence, re.IGNORECASE)
                severity = "medium" if unreasonable else "low"
                
                findings.append({
                    "risk_type": "assignment_restriction",
                    "severity": severity,
                    "title": "Restrictive assignment clause",
                    "description": "Contract restricts assignment rights, potentially limiting flexibility in business transactions.",
                    "evidence_text": evidence[:200],
                    "char_start": evidence_start,
                    "char_end": evidence_end,
                    "detection_method": "rule_based",
                    "confidence_score": 0.75
                })
        
        return findings
    
    def _check_perpetual_confidentiality(self, text: str) -> List[Dict]:
        """Detect perpetual confidentiality obligations."""
        findings = []
        
        patterns = [
            r'confidential(?:ity)?.*?(?:perpetual|indefinite|forever)',
            r'confidential(?:ity)?.*?(?:survive|continue).*?(?:indefinitely|termination)',
            r'confidential(?:ity)?.*?no\s+time\s+limit'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                evidence_start = match.start()
                evidence_end = min(match.end() + 100, len(text))
                evidence = text[evidence_start:evidence_end]
                
                findings.append({
                    "risk_type": "perpetual_confidentiality",
                    "severity": "medium",
                    "title": "Perpetual confidentiality obligation",
                    "description": "Contract requires confidentiality obligations to continue indefinitely, which may be impractical or overly burdensome.",
                    "evidence_text": evidence,
                    "char_start": evidence_start,
                    "char_end": evidence_end,
                    "detection_method": "rule_based",
                    "confidence_score": 0.8
                })
        
        return findings
