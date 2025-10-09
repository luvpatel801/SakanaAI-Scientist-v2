"""
Hallucination Detector
Detects and prevents hallucinations in generated content.
"""

import re
from typing import List, Dict, Optional, Tuple
import json


def detect_hallucinations(
    text: str,
    experimental_results: Dict[str, any],
    context: Optional[str] = None
) -> Dict[str, List[Dict[str, str]]]:
    """
    Detect potential hallucinations in generated text.
    
    Args:
        text: Generated text to check (e.g., paper section)
        experimental_results: Actual experimental results to verify against
        context: Additional context (e.g., literature, code)
    
    Returns:
        Dictionary categorizing different types of hallucinations
    """
    hallucinations = {
        "unsupported_claims": [],
        "contradictions": [],
        "impossible_values": [],
        "citation_issues": [],
        "logical_errors": [],
    }
    
    # 1. Check for unsupported numerical claims
    hallucinations["unsupported_claims"].extend(
        check_unsupported_numerical_claims(text, experimental_results)
    )
    
    # 2. Check for contradictions with results
    hallucinations["contradictions"].extend(
        check_contradictions_with_results(text, experimental_results)
    )
    
    # 3. Check for impossible values
    hallucinations["impossible_values"].extend(
        check_impossible_values(text)
    )
    
    # 4. Check citation patterns
    hallucinations["citation_issues"].extend(
        check_citation_patterns(text)
    )
    
    # 5. Check for logical errors
    hallucinations["logical_errors"].extend(
        check_logical_errors(text)
    )
    
    return hallucinations


def check_unsupported_numerical_claims(
    text: str,
    experimental_results: Dict[str, any]
) -> List[Dict[str, str]]:
    """Check for numerical claims not supported by experimental results."""
    issues = []
    
    # Extract numbers with context from text
    number_pattern = r'(\d+\.?\d*%?|\d+\.?\d*×)'
    numbers_in_text = re.finditer(number_pattern, text)
    
    for match in numbers_in_text:
        number_str = match.group(1)
        context_start = max(0, match.start() - 50)
        context_end = min(len(text), match.end() + 50)
        context = text[context_start:context_end]
        
        # Parse the number
        try:
            if '%' in number_str:
                claimed_value = float(number_str.replace('%', ''))
                is_percentage = True
            elif '×' in number_str:
                claimed_value = float(number_str.replace('×', ''))
                is_multiplier = True
            else:
                claimed_value = float(number_str)
                is_percentage = False
                is_multiplier = False
            
            # Check if this value appears in results (with tolerance)
            found_in_results = False
            tolerance = 0.01 if is_percentage else 0.001
            
            def check_value_in_dict(d, target, tol):
                if isinstance(d, dict):
                    for v in d.values():
                        if check_value_in_dict(v, target, tol):
                            return True
                elif isinstance(d, (list, tuple)):
                    for v in d:
                        if check_value_in_dict(v, target, tol):
                            return True
                elif isinstance(d, (int, float)):
                    if abs(d - target) < tol or abs(d * 100 - target) < 1.0:  # Also check percentage conversion
                        return True
                return False
            
            found_in_results = check_value_in_dict(experimental_results, claimed_value, tolerance)
            
            if not found_in_results and claimed_value > 1.0:  # Only flag significant values
                issues.append({
                    "value": number_str,
                    "context": context,
                    "issue": f"Numerical claim '{number_str}' not found in experimental results",
                    "type": "UnsupportedClaim"
                })
        
        except ValueError:
            pass  # Not a parseable number
    
    return issues


def check_contradictions_with_results(
    text: str,
    experimental_results: Dict[str, any]
) -> List[Dict[str, str]]:
    """Check for statements contradicting experimental results."""
    issues = []
    
    # Common comparative phrases
    comparative_patterns = [
        (r'outperforms?|better than|superior to|improves? over', 'positive'),
        (r'underperforms?|worse than|inferior to|degraded', 'negative'),
        (r'achieves?|reaches?|obtains?', 'neutral'),
    ]
    
    for pattern, sentiment in comparative_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            context_start = max(0, match.start() - 100)
            context_end = min(len(text), match.end() + 100)
            context = text[context_start:context_end]
            
            # Check if we have baseline comparisons in results
            has_baseline = 'baseline' in str(experimental_results).lower()
            if not has_baseline and 'better' in match.group(0).lower():
                issues.append({
                    "claim": match.group(0),
                    "context": context,
                    "issue": "Comparative claim without baseline results",
                    "type": "Contradiction"
                })
    
    return issues


def check_impossible_values(text: str) -> List[Dict[str, str]]:
    """Check for statistically impossible or suspicious values."""
    issues = []
    
    # Check for suspiciously perfect values
    perfect_patterns = [
        (r'accuracy:?\s*100%', "Perfect 100% accuracy is suspicious"),
        (r'error:?\s*0\.0+\b', "Zero error is suspicious"),
        (r'p\s*[=<]\s*0\.0+\b', "p-value of exactly 0 is suspicious (report as p < 0.001)"),
        (r'(?:accuracy|precision|recall|f1).*1\.0+\b', "Perfect score (1.0) is suspicious"),
    ]
    
    for pattern, message in perfect_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            context_start = max(0, match.start() - 50)
            context_end = min(len(text), match.end() + 50)
            context = text[context_start:context_end]
            
            issues.append({
                "value": match.group(0),
                "context": context,
                "issue": message,
                "type": "ImpossibleValue"
            })
    
    # Check for values out of valid ranges
    percentage_pattern = r'(\d+\.?\d*)%'
    for match in re.finditer(percentage_pattern, text):
        try:
            value = float(match.group(1))
            if value > 100:
                context_start = max(0, match.start() - 50)
                context_end = min(len(text), match.end() + 50)
                context = text[context_start:context_end]
                
                issues.append({
                    "value": match.group(0),
                    "context": context,
                    "issue": f"Percentage value > 100% ({value}%)",
                    "type": "ImpossibleValue"
                })
        except ValueError:
            pass
    
    return issues


def check_citation_patterns(text: str) -> List[Dict[str, str]]:
    """Check for citation-related issues."""
    issues = []
    
    # Check for unsupported claims that should have citations
    claim_patterns = [
        r'previous work has shown',
        r'it is well[- ]known',
        r'studies have demonstrated',
        r'research indicates',
        r'according to',
    ]
    
    for pattern in claim_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            # Check if there's a citation nearby (within 100 characters)
            context_start = max(0, match.start() - 20)
            context_end = min(len(text), match.end() + 100)
            context = text[context_start:context_end]
            
            # Look for citation patterns: \cite{}, [1], (Author et al., Year)
            has_citation = bool(
                re.search(r'\\cite\{[^}]+\}', context) or
                re.search(r'\[\d+\]', context) or
                re.search(r'\([A-Z][a-z]+\s+et al\.,\s+\d{4}\)', context)
            )
            
            if not has_citation:
                issues.append({
                    "claim": match.group(0),
                    "context": context,
                    "issue": "Claim about prior work without citation",
                    "type": "MissingCitation"
                })
    
    # Check for potential citation format errors
    cite_patterns = [
        (r'\[\d+,\s*\d+\]', "Multiple citations should be separate: [1], [2] not [1, 2]"),
        (r'\\cite\{[^}]*,\s*[^}]*,\s*[^}]*,\s*[^}]*,\s*[^}]*,\s*[^}]*\}', "Too many citations in one \\cite{} - consider breaking up"),
    ]
    
    for pattern, message in cite_patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            issues.append({
                "citation": match.group(0),
                "issue": message,
                "type": "CitationFormat"
            })
    
    return issues


def check_logical_errors(text: str) -> List[Dict[str, str]]:
    """Check for logical errors and inconsistencies."""
    issues = []
    
    # Check for contradictory statements
    contradictory_pairs = [
        (r'increase', r'decrease', 100),
        (r'improve', r'degrade', 100),
        (r'higher', r'lower', 100),
        (r'faster', r'slower', 100),
    ]
    
    for word1, word2, max_distance in contradictory_pairs:
        pattern1 = re.compile(word1, re.IGNORECASE)
        pattern2 = re.compile(word2, re.IGNORECASE)
        
        matches1 = list(pattern1.finditer(text))
        matches2 = list(pattern2.finditer(text))
        
        for m1 in matches1:
            for m2 in matches2:
                if abs(m1.start() - m2.start()) < max_distance:
                    context_start = max(0, min(m1.start(), m2.start()) - 50)
                    context_end = min(len(text), max(m1.end(), m2.end()) + 50)
                    context = text[context_start:context_end]
                    
                    issues.append({
                        "context": context,
                        "issue": f"Potentially contradictory terms '{word1}' and '{word2}' in close proximity",
                        "type": "LogicalInconsistency"
                    })
    
    return issues


def verify_claims(
    text: str,
    experimental_results: Dict[str, any],
    severity_threshold: str = "medium"
) -> Tuple[bool, Dict[str, any]]:
    """
    Verify all claims in text against experimental results.
    
    Args:
        text: Text to verify
        experimental_results: Experimental results to check against
        severity_threshold: 'low', 'medium', or 'high'
    
    Returns:
        Tuple of (passed, verification_report)
    """
    hallucinations = detect_hallucinations(text, experimental_results)
    
    # Count issues by severity
    high_severity = len(hallucinations["contradictions"]) + len(hallucinations["impossible_values"])
    medium_severity = len(hallucinations["unsupported_claims"]) + len(hallucinations["citation_issues"])
    low_severity = len(hallucinations["logical_errors"])
    
    total_issues = high_severity + medium_severity + low_severity
    
    # Determine if passed based on threshold
    if severity_threshold == "high":
        passed = high_severity == 0
    elif severity_threshold == "medium":
        passed = high_severity == 0 and medium_severity < 3
    else:  # low
        passed = total_issues < 5
    
    report = {
        "passed": passed,
        "total_issues": total_issues,
        "high_severity": high_severity,
        "medium_severity": medium_severity,
        "low_severity": low_severity,
        "hallucinations": hallucinations,
        "recommendation": (
            "Text verification passed" if passed
            else f"Found {total_issues} potential issues - review and fix before proceeding"
        )
    }
    
    return passed, report


def check_citation_accuracy(
    text: str,
    citation_database: Optional[Dict[str, Dict[str, str]]] = None
) -> Dict[str, List[str]]:
    """
    Check citation accuracy against a database.
    
    Args:
        text: Text containing citations
        citation_database: Dictionary mapping citation keys to metadata
    
    Returns:
        Dictionary with citation accuracy issues
    """
    issues = {
        "missing_citations": [],
        "malformed_citations": [],
        "duplicate_citations": [],
    }
    
    # Extract all citations
    cite_pattern = r'\\cite\{([^}]+)\}'
    citations = re.findall(cite_pattern, text)
    
    all_cited_keys = []
    for cite in citations:
        keys = [k.strip() for k in cite.split(',')]
        all_cited_keys.extend(keys)
    
    # Check for duplicates
    seen = set()
    for key in all_cited_keys:
        if key in seen:
            issues["duplicate_citations"].append(key)
        seen.add(key)
    
    # Check against database if provided
    if citation_database:
        for key in set(all_cited_keys):
            if key not in citation_database:
                issues["missing_citations"].append(key)
    
    # Check for malformed citation keys
    for key in all_cited_keys:
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', key):
            issues["malformed_citations"].append(key)
    
    return issues

