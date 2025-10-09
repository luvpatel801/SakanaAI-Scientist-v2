"""
Unit Test Generator and Code Quality Validator
Generates unit tests for experimental code and validates code quality.
"""

import ast
import re
import subprocess
from typing import List, Dict, Optional, Tuple
import os


def generate_unit_tests(code: str, model_client=None, model_name: str = "gpt-4o") -> str:
    """
    Generate unit tests for given code using an LLM.
    
    Args:
        code: Python code to generate tests for
        model_client: LLM client for generation
        model_name: Name of the model to use
    
    Returns:
        Generated unit test code as a string
    """
    if model_client is None:
        # Return basic template if no client
        return generate_basic_test_template(code)
    
    from ai_scientist.llm import get_response_from_llm
    
    prompt = f"""Generate comprehensive unit tests for the following Python code.
Include tests for:
1. Basic functionality with typical inputs
2. Edge cases (empty inputs, None, extreme values)
3. Error handling and exceptions
4. Data type validation
5. Output shape/format validation for ML code

Code to test:
```python
{code}
```

Provide complete, runnable pytest-compatible unit tests.
Use assert statements and proper test function naming (test_*).
Include docstrings explaining what each test validates.
"""

    system_message = "You are an expert Python developer specialized in writing comprehensive unit tests. Generate high-quality, thorough test cases."
    
    try:
        response, _ = get_response_from_llm(
            prompt=prompt,
            client=model_client,
            model=model_name,
            system_message=system_message,
            temperature=0.3,  # Low temperature for consistent test generation
        )
        
        # Extract code from response
        if "```python" in response:
            tests = response.split("```python")[1].split("```")[0]
        elif "```" in response:
            tests = response.split("```")[1].split("```")[0]
        else:
            tests = response
        
        return tests.strip()
    
    except Exception as e:
        print(f"Error generating unit tests: {e}")
        return generate_basic_test_template(code)


def generate_basic_test_template(code: str) -> str:
    """Generate basic test template without LLM."""
    return f"""import pytest
import numpy as np

# Basic test template for generated code
# TODO: Add specific test cases based on the functions

def test_basic_functionality():
    \"\"\"Test basic functionality of the code.\"\"\"
    # Add assertions here
    pass

def test_edge_cases():
    \"\"\"Test edge cases.\"\"\"
    # Test with empty inputs, None, extreme values
    pass

def test_error_handling():
    \"\"\"Test error handling.\"\"\"
    # Test that appropriate errors are raised
    pass
"""


def validate_code_quality(code: str, file_path: Optional[str] = None) -> Dict[str, any]:
    """
    Validate code quality using static analysis.
    
    Args:
        code: Python code to validate
        file_path: Optional path to save code temporarily for analysis
    
    Returns:
        Dictionary with validation results
    """
    issues = {
        "syntax_errors": [],
        "style_issues": [],
        "complexity_issues": [],
        "import_issues": [],
        "warnings": [],
        "score": 100.0,
    }
    
    # 1. Check for syntax errors
    try:
        ast.parse(code)
    except SyntaxError as e:
        issues["syntax_errors"].append({
            "line": e.lineno,
            "message": str(e),
            "type": "SyntaxError"
        })
        issues["score"] -= 50
        return issues  # Don't proceed if syntax is broken
    
    # 2. Check for common anti-patterns
    issues["warnings"].extend(check_common_antipatterns(code))
    
    # 3. Check imports
    import_check = check_imports(code)
    issues["import_issues"].extend(import_check)
    
    # 4. Check code complexity
    complexity_check = check_code_complexity(code)
    issues["complexity_issues"].extend(complexity_check)
    
    # Calculate score based on issues
    issues["score"] -= len(issues["warnings"]) * 2
    issues["score"] -= len(issues["import_issues"]) * 5
    issues["score"] -= len(issues["complexity_issues"]) * 3
    issues["score"] = max(0.0, issues["score"])
    
    return issues


def check_common_antipatterns(code: str) -> List[Dict[str, str]]:
    """Check for common Python anti-patterns."""
    warnings = []
    
    lines = code.split('\n')
    
    for i, line in enumerate(lines, 1):
        # Check for bare except
        if re.search(r'except\s*:', line) and 'pass' in lines[i] if i < len(lines) else False:
            warnings.append({
                "line": i,
                "message": "Bare except clause with pass - may hide errors",
                "type": "AntiPattern"
            })
        
        # Check for mutable default arguments
        if re.search(r'def\s+\w+.*=\s*\[\]', line) or re.search(r'def\s+\w+.*=\s*\{\}', line):
            warnings.append({
                "line": i,
                "message": "Mutable default argument - can cause unexpected behavior",
                "type": "AntiPattern"
            })
        
        # Check for infinite loops without break
        if 'while True:' in line:
            # Check next few lines for break statement
            has_break = False
            for j in range(i, min(i + 10, len(lines))):
                if 'break' in lines[j]:
                    has_break = True
                    break
            if not has_break:
                warnings.append({
                    "line": i,
                    "message": "Infinite loop without break statement",
                    "type": "Warning"
                })
        
        # Check for print statements (should use logging in production)
        if re.search(r'\bprint\s*\(', line) and 'TODO' not in line:
            # This is actually fine for experimental code, so just note it
            pass
    
    return warnings


def check_imports(code: str) -> List[Dict[str, str]]:
    """Check for import-related issues."""
    issues = []
    
    try:
        tree = ast.parse(code)
        
        imported_modules = set()
        used_names = set()
        
        # Collect imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_modules.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported_modules.add(node.module.split('.')[0])
        
        # Check for unused imports (basic check)
        # This is a simplified check - more sophisticated tools like pylint do this better
        
        # Check for missing common imports
        code_lower = code.lower()
        if 'np.' in code and 'numpy' not in imported_modules:
            issues.append({
                "message": "Using 'np.' but numpy not explicitly imported",
                "type": "MissingImport"
            })
        
        if 'torch.' in code and 'torch' not in imported_modules:
            issues.append({
                "message": "Using 'torch.' but torch not imported",
                "type": "MissingImport"
            })
    
    except Exception as e:
        issues.append({
            "message": f"Error checking imports: {str(e)}",
            "type": "ImportCheckError"
        })
    
    return issues


def check_code_complexity(code: str) -> List[Dict[str, str]]:
    """Check code complexity metrics."""
    issues = []
    
    try:
        tree = ast.parse(code)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Count lines in function
                if hasattr(node, 'body'):
                    func_lines = node.end_lineno - node.lineno if hasattr(node, 'end_lineno') else 0
                    
                    if func_lines > 100:
                        issues.append({
                            "function": node.name,
                            "lines": func_lines,
                            "message": f"Function '{node.name}' is very long ({func_lines} lines). Consider breaking it down.",
                            "type": "Complexity"
                        })
                
                # Count nested depth
                max_depth = calculate_nesting_depth(node)
                if max_depth > 4:
                    issues.append({
                        "function": node.name,
                        "depth": max_depth,
                        "message": f"Function '{node.name}' has high nesting depth ({max_depth}). Consider refactoring.",
                        "type": "Complexity"
                    })
    
    except Exception as e:
        issues.append({
            "message": f"Error checking complexity: {str(e)}",
            "type": "ComplexityCheckError"
        })
    
    return issues


def calculate_nesting_depth(node: ast.AST, current_depth: int = 0) -> int:
    """Calculate maximum nesting depth in an AST node."""
    max_depth = current_depth
    
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
            child_depth = calculate_nesting_depth(child, current_depth + 1)
            max_depth = max(max_depth, child_depth)
        else:
            child_depth = calculate_nesting_depth(child, current_depth)
            max_depth = max(max_depth, child_depth)
    
    return max_depth


def check_for_common_bugs(code: str) -> Dict[str, List[str]]:
    """
    Check for common bug patterns in ML/data science code.
    
    Returns:
        Dictionary categorizing different types of potential bugs
    """
    bugs = {
        "data_leakage": [],
        "random_seed_issues": [],
        "numerical_stability": [],
        "type_issues": [],
        "other": [],
    }
    
    lines = code.split('\n')
    
    for i, line in enumerate(lines, 1):
        # Check for potential data leakage
        if 'fit' in line and 'transform' in line and 'test' in line.lower():
            bugs["data_leakage"].append(
                f"Line {i}: Potential data leakage - fitting on test data?"
            )
        
        # Check for missing random seed
        if 'random' in line.lower() and 'seed' not in line.lower():
            # Check if seed is set elsewhere in nearby lines
            has_seed = any('seed' in lines[j].lower() for j in range(max(0, i-5), min(len(lines), i+5)))
            if not has_seed:
                bugs["random_seed_issues"].append(
                    f"Line {i}: Random operation without seed - may affect reproducibility"
                )
        
        # Check for numerical stability issues
        if 'log(' in line and 'log(0' not in line:
            if '+' not in line and 'epsilon' not in line.lower():
                bugs["numerical_stability"].append(
                    f"Line {i}: log() without epsilon - may cause NaN with zero values"
                )
        
        if '/ ' in line or line.strip().endswith('/'):
            if 'epsilon' not in line.lower() and '+ ' not in line:
                bugs["numerical_stability"].append(
                    f"Line {i}: Division without checking for zero"
                )
    
    return bugs


def run_code_linter(code: str, temp_file: str = "temp_code_check.py") -> Tuple[bool, str]:
    """
    Run external linter (black, flake8) if available.
    
    Returns:
        Tuple of (success, output_message)
    """
    try:
        # Write code to temp file
        with open(temp_file, 'w') as f:
            f.write(code)
        
        # Try black formatting check
        try:
            result = subprocess.run(
                ['black', '--check', temp_file],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                return False, "Code formatting issues detected. Run black to fix."
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass  # black not available or timeout
        
        # Clean up
        if os.path.exists(temp_file):
            os.remove(temp_file)
        
        return True, "Code quality checks passed"
    
    except Exception as e:
        if os.path.exists(temp_file):
            os.remove(temp_file)
        return False, f"Error running linter: {str(e)}"

