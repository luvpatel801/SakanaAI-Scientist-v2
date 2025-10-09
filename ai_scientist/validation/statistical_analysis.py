"""
Statistical Analysis Module
Provides rigorous statistical analysis for multi-seed experiments.
"""

import numpy as np
from scipy import stats
from typing import List, Dict, Tuple, Optional
import json


def compute_confidence_intervals(
    values: List[float],
    confidence_level: float = 0.95
) -> Dict[str, float]:
    """
    Compute confidence intervals for a list of values.
    
    Args:
        values: List of numerical values (e.g., accuracies from multiple seeds)
        confidence_level: Confidence level (default: 0.95 for 95% CI)
    
    Returns:
        Dictionary with mean, std, ci_lower, ci_upper, margin_of_error
    """
    if not values or len(values) < 2:
        return {
            "mean": values[0] if values else 0.0,
            "std": 0.0,
            "ci_lower": values[0] if values else 0.0,
            "ci_upper": values[0] if values else 0.0,
            "margin_of_error": 0.0,
            "n_samples": len(values),
        }
    
    values_array = np.array(values)
    mean = np.mean(values_array)
    std = np.std(values_array, ddof=1)  # Sample standard deviation
    n = len(values_array)
    
    # Use t-distribution for small sample sizes
    df = n - 1
    t_critical = stats.t.ppf((1 + confidence_level) / 2, df)
    margin_of_error = t_critical * (std / np.sqrt(n))
    
    ci_lower = mean - margin_of_error
    ci_upper = mean + margin_of_error
    
    return {
        "mean": float(mean),
        "std": float(std),
        "ci_lower": float(ci_lower),
        "ci_upper": float(ci_upper),
        "margin_of_error": float(margin_of_error),
        "n_samples": int(n),
        "confidence_level": float(confidence_level),
    }


def perform_significance_testing(
    baseline_values: List[float],
    treatment_values: List[float],
    test_type: str = "t-test",
    alpha: float = 0.05
) -> Dict[str, any]:
    """
    Perform statistical significance testing between two sets of values.
    
    Args:
        baseline_values: Results from baseline/control condition
        treatment_values: Results from treatment/experimental condition
        test_type: Type of test ('t-test', 'mann-whitney', 'wilcoxon')
        alpha: Significance level (default: 0.05)
    
    Returns:
        Dictionary with test results including p-value, statistic, significant
    """
    if len(baseline_values) < 2 or len(treatment_values) < 2:
        return {
            "test_type": test_type,
            "error": "Insufficient samples for statistical testing",
            "significant": False,
        }
    
    baseline = np.array(baseline_values)
    treatment = np.array(treatment_values)
    
    try:
        if test_type == "t-test":
            # Two-sample t-test (unpaired)
            statistic, p_value = stats.ttest_ind(treatment, baseline)
            test_name = "Independent t-test"
        elif test_type == "paired-t-test":
            # Paired t-test
            if len(baseline) != len(treatment):
                return {
                    "test_type": test_type,
                    "error": "Paired test requires equal sample sizes",
                    "significant": False,
                }
            statistic, p_value = stats.ttest_rel(treatment, baseline)
            test_name = "Paired t-test"
        elif test_type == "mann-whitney":
            # Mann-Whitney U test (non-parametric)
            statistic, p_value = stats.mannwhitneyu(
                treatment, baseline, alternative='two-sided'
            )
            test_name = "Mann-Whitney U test"
        elif test_type == "wilcoxon":
            # Wilcoxon signed-rank test (paired, non-parametric)
            if len(baseline) != len(treatment):
                return {
                    "test_type": test_type,
                    "error": "Wilcoxon test requires equal sample sizes",
                    "significant": False,
                }
            statistic, p_value = stats.wilcoxon(treatment, baseline)
            test_name = "Wilcoxon signed-rank test"
        else:
            return {
                "test_type": test_type,
                "error": f"Unknown test type: {test_type}",
                "significant": False,
            }
        
        significant = p_value < alpha
        
        # Compute effect size (Cohen's d for t-tests)
        pooled_std = np.sqrt(
            ((len(treatment) - 1) * np.var(treatment, ddof=1) +
             (len(baseline) - 1) * np.var(baseline, ddof=1)) /
            (len(treatment) + len(baseline) - 2)
        )
        cohens_d = (np.mean(treatment) - np.mean(baseline)) / pooled_std if pooled_std > 0 else 0.0
        
        return {
            "test_type": test_name,
            "statistic": float(statistic),
            "p_value": float(p_value),
            "alpha": float(alpha),
            "significant": bool(significant),
            "cohens_d": float(cohens_d),
            "baseline_mean": float(np.mean(baseline)),
            "treatment_mean": float(np.mean(treatment)),
            "baseline_std": float(np.std(baseline, ddof=1)),
            "treatment_std": float(np.std(treatment, ddof=1)),
        }
    
    except Exception as e:
        return {
            "test_type": test_type,
            "error": str(e),
            "significant": False,
        }


def analyze_multi_seed_results(
    results_dict: Dict[int, Dict[str, float]],
    metrics: Optional[List[str]] = None
) -> Dict[str, Dict[str, float]]:
    """
    Analyze results from multiple random seeds.
    
    Args:
        results_dict: Dictionary mapping seed -> {metric: value}
        metrics: List of metrics to analyze (default: all metrics found)
    
    Returns:
        Dictionary mapping metric -> statistical summary
    """
    if not results_dict:
        return {}
    
    # Collect all metrics if not specified
    if metrics is None:
        metrics = set()
        for seed_results in results_dict.values():
            metrics.update(seed_results.keys())
        metrics = list(metrics)
    
    analysis = {}
    
    for metric in metrics:
        values = []
        for seed, seed_results in results_dict.items():
            if metric in seed_results:
                values.append(seed_results[metric])
        
        if values:
            ci_results = compute_confidence_intervals(values)
            analysis[metric] = ci_results
    
    return analysis


def check_distribution_assumptions(
    values: List[float],
    alpha: float = 0.05
) -> Dict[str, any]:
    """
    Check assumptions for parametric statistical tests.
    
    Args:
        values: List of numerical values
        alpha: Significance level for tests
    
    Returns:
        Dictionary with normality test results and recommendations
    """
    if len(values) < 3:
        return {
            "error": "Insufficient samples for distribution checks",
            "recommend_parametric": False,
        }
    
    values_array = np.array(values)
    
    # Shapiro-Wilk test for normality
    if len(values) <= 5000:  # Shapiro-Wilk works best for smaller samples
        shapiro_stat, shapiro_p = stats.shapiro(values_array)
        is_normal = shapiro_p > alpha
    else:
        # Use Kolmogorov-Smirnov test for larger samples
        ks_stat, ks_p = stats.kstest(values_array, 'norm')
        is_normal = ks_p > alpha
        shapiro_stat, shapiro_p = None, None
    
    # Check for outliers using IQR method
    q1 = np.percentile(values_array, 25)
    q3 = np.percentile(values_array, 75)
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    outliers = values_array[(values_array < lower_bound) | (values_array > upper_bound)]
    
    return {
        "n_samples": len(values),
        "is_normal": bool(is_normal),
        "shapiro_statistic": float(shapiro_stat) if shapiro_stat is not None else None,
        "shapiro_p_value": float(shapiro_p) if shapiro_p is not None else None,
        "n_outliers": int(len(outliers)),
        "outlier_values": outliers.tolist() if len(outliers) > 0 else [],
        "recommend_parametric": bool(is_normal and len(outliers) == 0),
        "recommendation": (
            "Use parametric tests (t-test)" if is_normal and len(outliers) == 0
            else "Use non-parametric tests (Mann-Whitney, Wilcoxon)"
        ),
    }


def generate_statistical_summary(
    results_dict: Dict[int, Dict[str, float]],
    baseline_results: Optional[Dict[int, Dict[str, float]]] = None,
    metrics: Optional[List[str]] = None,
    output_file: Optional[str] = None
) -> Dict[str, any]:
    """
    Generate comprehensive statistical summary for experimental results.
    
    Args:
        results_dict: Dictionary mapping seed -> {metric: value}
        baseline_results: Optional baseline results for comparison
        metrics: List of metrics to analyze
        output_file: Optional file to save results as JSON
    
    Returns:
        Complete statistical analysis dictionary
    """
    summary = {
        "multi_seed_analysis": analyze_multi_seed_results(results_dict, metrics),
        "distribution_checks": {},
        "significance_tests": {},
    }
    
    # Get metrics
    if metrics is None:
        metrics = set()
        for seed_results in results_dict.values():
            metrics.update(seed_results.keys())
        metrics = list(metrics)
    
    # Check distribution assumptions for each metric
    for metric in metrics:
        values = [
            seed_results[metric]
            for seed_results in results_dict.values()
            if metric in seed_results
        ]
        if values:
            summary["distribution_checks"][metric] = check_distribution_assumptions(values)
    
    # Perform significance tests if baseline is provided
    if baseline_results is not None:
        for metric in metrics:
            baseline_values = [
                seed_results[metric]
                for seed_results in baseline_results.values()
                if metric in seed_results
            ]
            treatment_values = [
                seed_results[metric]
                for seed_results in results_dict.values()
                if metric in seed_results
            ]
            
            if baseline_values and treatment_values:
                # Choose test based on distribution
                dist_check = summary["distribution_checks"].get(metric, {})
                test_type = "t-test" if dist_check.get("recommend_parametric", False) else "mann-whitney"
                
                summary["significance_tests"][metric] = perform_significance_testing(
                    baseline_values, treatment_values, test_type=test_type
                )
    
    # Save to file if specified
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(summary, f, indent=2)
    
    return summary

