"""
Validation Module for AI Scientist
Provides rigorous validation, statistical analysis, and error detection.
"""

from .statistical_analysis import (
    compute_confidence_intervals,
    perform_significance_testing,
    analyze_multi_seed_results,
    check_distribution_assumptions,
)

from .unit_test_generator import (
    generate_unit_tests,
    validate_code_quality,
    check_for_common_bugs,
)

from .hallucination_detector import (
    detect_hallucinations,
    verify_claims,
    check_citation_accuracy,
)

from .reproducibility_checker import (
    check_reproducibility,
    validate_random_seeds,
    verify_determinism,
)

__all__ = [
    "compute_confidence_intervals",
    "perform_significance_testing",
    "analyze_multi_seed_results",
    "check_distribution_assumptions",
    "generate_unit_tests",
    "validate_code_quality",
    "check_for_common_bugs",
    "detect_hallucinations",
    "verify_claims",
    "check_citation_accuracy",
    "check_reproducibility",
    "validate_random_seeds",
    "verify_determinism",
]

