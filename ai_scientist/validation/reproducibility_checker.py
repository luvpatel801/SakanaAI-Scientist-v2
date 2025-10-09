"""
Reproducibility Checker
Validates reproducibility aspects of experiments.
"""

import re
import ast
from typing import Dict, List, Optional, Tuple
import hashlib


def check_reproducibility(
    code: str,
    config: Optional[Dict] = None,
    results: Optional[Dict] = None
) -> Dict[str, any]:
    """
    Check reproducibility aspects of experimental code.
    
    Args:
        code: Python code to check
        config: Configuration dictionary
        results: Experimental results
    
    Returns:
        Reproducibility report
    """
    report = {
        "has_random_seeds": False,
        "seeds_fixed": [],
        "deterministic_operations": True,
        "issues": [],
        "recommendations": [],
        "score": 0.0,
    }
    
    # Check for random seed setting
    seed_check = validate_random_seeds(code)
    report["has_random_seeds"] = seed_check["seeds_set"]
    report["seeds_fixed"] = seed_check["seed_values"]
    report["issues"].extend(seed_check["issues"])
    
    # Check for deterministic operations
    determinism_check = verify_determinism(code)
    report["deterministic_operations"] = determinism_check["is_deterministic"]
    report["issues"].extend(determinism_check["issues"])
    report["recommendations"].extend(determinism_check["recommendations"])
    
    # Calculate reproducibility score
    score = 100.0
    if not report["has_random_seeds"]:
        score -= 30
    if not report["deterministic_operations"]:
        score -= 20
    score -= len(report["issues"]) * 5
    report["score"] = max(0.0, score)
    
    return report


def validate_random_seeds(code: str) -> Dict[str, any]:
    """
    Validate that random seeds are properly set.
    
    Returns:
        Dictionary with seed validation results
    """
    result = {
        "seeds_set": False,
        "seed_values": [],
        "issues": [],
    }
    
    lines = code.split('\n')
    
    # Patterns for seed setting
    seed_patterns = [
        (r'random\.seed\((\d+)\)', 'python_random'),
        (r'np\.random\.seed\((\d+)\)', 'numpy'),
        (r'torch\.manual_seed\((\d+)\)', 'torch'),
        (r'torch\.cuda\.manual_seed\((\d+)\)', 'torch_cuda'),
        (r'torch\.cuda\.manual_seed_all\((\d+)\)', 'torch_cuda_all'),
        (r'tf\.random\.set_seed\((\d+)\)', 'tensorflow'),
        (r'random_state\s*=\s*(\d+)', 'sklearn'),
        (r'seed\s*=\s*(\d+)', 'generic'),
    ]
    
    seeds_found = {lib: [] for _, lib in seed_patterns}
    
    for line in lines:
        for pattern, library in seed_patterns:
            match = re.search(pattern, line)
            if match:
                try:
                    seed_value = int(match.group(1))
                    seeds_found[library].append(seed_value)
                except (ValueError, IndexError):
                    pass
    
    # Check if seeds are set
    result["seeds_set"] = any(len(seeds) > 0 for seeds in seeds_found.values())
    result["seed_values"] = seeds_found
    
    # Check for missing seed settings
    if 'random.' in code and not seeds_found['python_random']:
        result["issues"].append("Using random module but no random.seed() found")
    
    if 'np.random' in code and not seeds_found['numpy']:
        result["issues"].append("Using numpy.random but no np.random.seed() found")
    
    if 'torch' in code and not seeds_found['torch']:
        result["issues"].append("Using torch but no torch.manual_seed() found")
    
    if 'torch.cuda' in code and not (seeds_found['torch_cuda'] or seeds_found['torch_cuda_all']):
        result["issues"].append("Using torch.cuda but no CUDA seed set")
    
    if 'tensorflow' in code or 'import tf' in code:
        if not seeds_found['tensorflow']:
            result["issues"].append("Using TensorFlow but no tf.random.set_seed() found")
    
    return result


def verify_determinism(code: str) -> Dict[str, any]:
    """
    Verify that code uses deterministic operations.
    
    Returns:
        Dictionary with determinism check results
    """
    result = {
        "is_deterministic": True,
        "issues": [],
        "recommendations": [],
    }
    
    lines = code.split('\n')
    
    # Check for non-deterministic operations
    non_deterministic_patterns = [
        (r'shuffle.*(?!random_state)', "shuffle without random_state parameter"),
        (r'DataLoader.*shuffle\s*=\s*True(?!.*worker_init_fn)', "DataLoader shuffle without worker_init_fn"),
        (r'nn\.Dropout\(', "Dropout layer (non-deterministic in eval mode)"),
        (r'cudnn\.benchmark\s*=\s*True', "cuDNN benchmark mode is non-deterministic"),
        (r'(?<!set_)deterministic\s*=\s*False', "Deterministic mode disabled"),
    ]
    
    for i, line in enumerate(lines, 1):
        for pattern, issue in non_deterministic_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                result["is_deterministic"] = False
                result["issues"].append(f"Line {i}: {issue}")
    
    # Check for determinism enforcement
    good_patterns = [
        r'cudnn\.deterministic\s*=\s*True',
        r'cudnn\.benchmark\s*=\s*False',
        r'worker_init_fn',
        r'set_deterministic',
    ]
    
    has_determinism_enforcement = any(
        any(re.search(pattern, line) for pattern in good_patterns)
        for line in lines
    )
    
    if 'torch' in code and not has_determinism_enforcement:
        result["recommendations"].append(
            "Consider adding torch.backends.cudnn.deterministic = True for reproducibility"
        )
        result["recommendations"].append(
            "Consider adding torch.backends.cudnn.benchmark = False"
        )
    
    # Check for proper DataLoader configuration
    if 'DataLoader' in code:
        if 'worker_init_fn' not in code:
            result["recommendations"].append(
                "Consider adding worker_init_fn to DataLoader for reproducible multi-process data loading"
            )
    
    return result


def generate_reproducibility_report(
    code: str,
    config: Dict,
    results: Dict,
    output_file: Optional[str] = None
) -> str:
    """
    Generate a comprehensive reproducibility report.
    
    Args:
        code: Experimental code
        config: Configuration used
        results: Results obtained
        output_file: Optional file to save report
    
    Returns:
        Report as formatted string
    """
    check_result = check_reproducibility(code, config, results)
    
    report_lines = [
        "=" * 60,
        "REPRODUCIBILITY REPORT",
        "=" * 60,
        "",
        f"Overall Score: {check_result['score']:.1f}/100",
        "",
        "RANDOM SEEDS:",
        f"  Seeds Set: {'Yes' if check_result['has_random_seeds'] else 'No'}",
    ]
    
    if check_result['seeds_fixed']:
        report_lines.append("  Seed Values:")
        for lib, seeds in check_result['seeds_fixed'].items():
            if seeds:
                report_lines.append(f"    - {lib}: {seeds}")
    
    report_lines.extend([
        "",
        f"DETERMINISTIC OPERATIONS: {'Yes' if check_result['deterministic_operations'] else 'No'}",
        "",
    ])
    
    if check_result['issues']:
        report_lines.append("ISSUES FOUND:")
        for issue in check_result['issues']:
            report_lines.append(f"  - {issue}")
        report_lines.append("")
    
    if check_result['recommendations']:
        report_lines.append("RECOMMENDATIONS:")
        for rec in check_result['recommendations']:
            report_lines.append(f"  - {rec}")
        report_lines.append("")
    
    # Add configuration info
    report_lines.extend([
        "CONFIGURATION:",
        f"  Config Hash: {hashlib.md5(str(config).encode()).hexdigest()[:8]}",
        "",
    ])
    
    # Add environment recommendations
    report_lines.extend([
        "ENVIRONMENT RECOMMENDATIONS:",
        "  1. Document all package versions (pip freeze > requirements.txt)",
        "  2. Use virtual environment or Docker for isolation",
        "  3. Document hardware specifications (GPU model, CUDA version)",
        "  4. Include random seeds in config file",
        "  5. Save and version control the exact code used",
        "",
        "=" * 60,
    ])
    
    report_text = "\n".join(report_lines)
    
    if output_file:
        with open(output_file, 'w') as f:
            f.write(report_text)
    
    return report_text


def create_reproducibility_checklist() -> List[str]:
    """
    Create a checklist for reproducibility.
    
    Returns:
        List of checklist items
    """
    checklist = [
        "✓ Set random seeds for all random number generators",
        "✓ Use deterministic algorithms where possible",
        "✓ Document all hyperparameters in config file",
        "✓ Save exact package versions (requirements.txt)",
        "✓ Document hardware specifications",
        "✓ Use version control for code",
        "✓ Save model checkpoints with seed info",
        "✓ Document data preprocessing steps",
        "✓ Include data splits or how they were created",
        "✓ Test reproducibility on different machines",
        "✓ Provide environment setup instructions",
        "✓ Include example runs with expected outputs",
    ]
    return checklist


def verify_multi_run_consistency(
    results_list: List[Dict[str, float]],
    tolerance: float = 0.01
) -> Dict[str, any]:
    """
    Verify consistency across multiple runs with same seed.
    
    Args:
        results_list: List of result dictionaries from multiple runs
        tolerance: Maximum allowed difference between runs
    
    Returns:
        Consistency report
    """
    if len(results_list) < 2:
        return {
            "consistent": True,
            "message": "Need at least 2 runs to check consistency",
        }
    
    # Extract all metric names
    metrics = set()
    for results in results_list:
        metrics.update(results.keys())
    
    consistency_report = {
        "consistent": True,
        "metrics": {},
        "max_difference": 0.0,
    }
    
    for metric in metrics:
        values = [r[metric] for r in results_list if metric in r]
        
        if len(values) >= 2:
            max_val = max(values)
            min_val = min(values)
            diff = max_val - min_val
            
            is_consistent = diff <= tolerance
            consistency_report["metrics"][metric] = {
                "consistent": is_consistent,
                "difference": diff,
                "tolerance": tolerance,
                "values": values,
            }
            
            if not is_consistent:
                consistency_report["consistent"] = False
            
            consistency_report["max_difference"] = max(
                consistency_report["max_difference"], diff
            )
    
    return consistency_report

