# AI Scientist-v2 Experiment Writing Workflow Documentation

## Overview

The AI Scientist-v2 is a sophisticated system that automates scientific research through agentic tree search, experiment execution, and paper generation. This document provides a comprehensive understanding of how experiment writing works in this system.

## Architecture Overview

The system follows a multi-phase approach:
1. **Ideation** → 2. **Experiment Execution** → 3. **Paper Generation** → 4. **Review**

## Phase 1: Ideation

### Purpose
Generate structured research ideas with hypotheses, experiments, and related work analysis.

### Key Files
- `ai_scientist/perform_ideation_temp_free.py`: Main ideation script
- `ai_scientist/ideas/`: Directory containing research topic descriptions and generated ideas

### Process
1. Create a markdown file describing the research area (e.g., `my_research_topic.md`)
2. Run ideation script:
   ```bash
   python ai_scientist/perform_ideation_temp_free.py \
    --workshop-file "ai_scientist/ideas/my_research_topic.md" \
    --model gpt-4o-2024-05-13 \
    --max-num-generations 20 \
    --num-reflections 5
   ```
3. Output: JSON file with structured research ideas

## Phase 2: Experiment Execution

### Main Orchestrator
`launch_scientist_bfts.py` - The central script that coordinates the entire experiment pipeline.

### Configuration
`bfts_config.yaml` - Controls all experiment parameters:
- **Agent settings**: Number of workers, stages, iterations
- **Model configurations**: Different models for coding, feedback, VLM analysis
- **Search parameters**: Debug depth, debug probability, number of drafts

### Tree Search Architecture

#### Core Components
1. **AgentManager** (`ai_scientist/treesearch/agent_manager.py`)
   - Coordinates multi-stage experiments
   - Manages stage transitions and progression
   - Handles sub-stage creation and completion

2. **ParallelAgent** (`ai_scientist/treesearch/parallel_agent.py`)
   - Executes experiments in parallel
   - Processes nodes through tree search
   - Handles multi-seed evaluation and plot aggregation

3. **Journal** (`ai_scientist/treesearch/journal.py`)
   - Tracks all experimental nodes and results
   - Manages node relationships and metrics
   - Provides best node selection logic

#### Node Structure
Each experimental attempt is represented as a `Node` containing:
- **Code & Planning**: `code`, `plan`, `overall_plan`
- **Execution Info**: `exec_time`, `exc_type`, `term_out`
- **Evaluation**: `metric`, `analysis`, `is_buggy`
- **Plotting**: `plot_code`, `plot_data`, `plots_generated`
- **VLM Feedback**: `plot_analyses`, `vlm_feedback_summary`

### Four-Stage Experiment Process

#### Stage 1: Initial Implementation (`initial_implementation`)
- **Goal**: Get basic working implementation
- **Focus**: Functional correctness, simple dataset
- **Completion**: When at least one working implementation is found
- **Code Integration**: Can use provided code as starting point

#### Stage 2: Baseline Tuning (`baseline_tuning`)
- **Goal**: Optimize hyperparameters (learning rate, epochs, batch size)
- **Constraint**: Cannot change model architecture from Stage 1
- **Dataset Requirement**: Test on TWO additional HuggingFace datasets
- **Completion**: Stable convergence, tested on multiple datasets

#### Stage 3: Creative Research (`creative_research`)
- **Goal**: Explore novel improvements and insights
- **Focus**: Creative approaches, new experiments
- **Dataset Requirement**: Use THREE HuggingFace datasets total
- **Completion**: Novel insights, sufficient experimental depth

#### Stage 4: Ablation Studies (`ablation_studies`)
- **Goal**: Systematic component analysis
- **Focus**: Understand contribution of each part
- **Dataset Requirement**: Use same datasets from Stage 3
- **Completion**: Comprehensive ablation analysis

### Stage Management

#### Sub-Stage Creation
- Each main stage can have multiple sub-stages
- Sub-stages are dynamically created based on progress
- LLM evaluates completion and generates next sub-stage goals

#### Stage Progression Logic
1. **Completion Check**: Evaluate if current stage goals are met
2. **Multi-Seed Evaluation**: Run best implementation with multiple seeds
3. **Plot Aggregation**: Generate comprehensive visualizations
4. **Transition**: Move to next stage or create new sub-stage

### Experiment Execution Flow

```
1. Load research idea from JSON
2. Create timestamped experiment directory
3. Convert idea to markdown format
4. Load and integrate any provided code
5. Configure BFTS parameters
6. Execute tree search through all stages:
   - Stage 1: Initial implementation
   - Stage 2: Baseline tuning
   - Stage 3: Creative research
   - Stage 4: Ablation studies
7. Aggregate plots and results
8. Save experiment data and token usage
```

## Phase 3: Paper Generation

### Two Writeup Types
1. **Normal Writeup** (`perform_writeup.py`): 8-page conference paper
2. **ICBINB Writeup** (`perform_icbinb_writeup.py`): 4-page workshop paper

### Writeup Process
1. **Citation Gathering**: Collect relevant academic citations
2. **Paper Generation**: Generate LaTeX paper using experiment results
3. **Multiple Attempts**: Retry mechanism for failed writeups
4. **Reflection Iterations**: Improve paper through multiple reflection cycles

### Paper Structure
- **Title**: Catchy and informative
- **Abstract**: TL;DR of the paper
- **Introduction**: Extended abstract with context
- **Related Work**: Academic siblings and comparisons
- **Background**: Foundational concepts
- **Method**: Proposed approach and hypotheses
- **Experimental Setup**: Data, environment, baselines
- **Experiments**: Results and analysis
- **Conclusion**: Summary and future directions
- **Appendix**: Supplementary material

## Phase 4: Review Process

### Components
1. **LLM Review** (`perform_llm_review.py`): Text-based paper review
2. **VLM Review** (`perform_vlm_review.py`): Image, caption, and reference review

### Review Outputs
- `review_text.txt`: Comprehensive text review
- `review_img_cap_ref.json`: Visual and reference analysis

## Key Configuration Parameters

### Agent Configuration (`bfts_config.yaml`)
```yaml
agent:
  type: parallel
  num_workers: 4  # Parallel exploration paths
  steps: 5        # Max nodes per stage
  stages:
    stage1_max_iters: 20
    stage2_max_iters: 12
    stage3_max_iters: 12
    stage4_max_iters: 18
  multi_seed_eval:
    num_seeds: 3  # Should match num_workers if < 3
  search:
    max_debug_depth: 3
    debug_prob: 0.5
    num_drafts: 3
```

### Model Configuration
- **Coding**: `anthropic.claude-3-5-sonnet-20241022-v2:0`
- **Feedback**: `gpt-4o-2024-11-20`
- **VLM**: `gpt-4o-2024-11-20`
- **Writeup**: `o1-preview-2024-09-12`
- **Citation**: `gpt-4o-2024-11-20`
- **Review**: `gpt-4o-2024-11-20`

## File Structure and Outputs

### Experiment Directory Structure
```
experiments/
└── {timestamp}_{idea_name}_attempt_{id}/
    ├── idea.md                    # Research idea in markdown
    ├── idea.json                   # Raw idea JSON
    ├── logs/0-run/                 # Tree search logs
    │   ├── experiment_results/     # Individual experiment results
    │   └── unified_tree_viz.html   # Tree visualization
    ├── experiment_results/         # Copied experiment results
    ├── figures/                    # Generated plots
    ├── {idea_name}.pdf             # Generated paper
    ├── review_text.txt             # Paper review
    ├── review_img_cap_ref.json     # VLM review
    └── token_tracker.json          # Token usage tracking
```

## Usage Examples

### Complete Pipeline
```bash
python launch_scientist_bfts.py \
 --load_ideas "ai_scientist/ideas/my_research_topic.json" \
 --load_code \
 --add_dataset_ref \
 --model_writeup o1-preview-2024-09-12 \
 --model_citation gpt-4o-2024-11-20 \
 --model_review gpt-4o-2024-11-20 \
 --model_agg_plots o3-mini-2025-01-31 \
 --num_cite_rounds 20
```

### Ideation Only
```bash
python ai_scientist/perform_ideation_temp_free.py \
 --workshop-file "ai_scientist/ideas/my_research_topic.md" \
 --model gpt-4o-2024-05-13 \
 --max-num-generations 20 \
 --num-reflections 5
```

## Success Metrics and Completion Criteria

### Stage Completion
- **Stage 1**: At least one working implementation
- **Stage 2**: Stable convergence, multiple datasets tested
- **Stage 3**: Novel insights, sufficient experimental depth
- **Stage 4**: Comprehensive ablation analysis

### Overall Success
- Successful completion of all 4 stages
- Generated paper with proper LaTeX compilation
- Comprehensive review and analysis
- Token usage tracking and cost monitoring

## Troubleshooting

### Common Issues
1. **No PDF Generated**: Check model performance and idea complexity
2. **Failed Experiments**: Increase max iterations or reduce complexity
3. **Token Costs**: Monitor usage via `token_tracker.json`

### Cost Estimates
- **Ideation**: ~$2-5 (depending on generations/reflections)
- **Experiments**: ~$15-20 (using Claude 3.5 Sonnet)
- **Writing**: ~$5 (using default models)

## Best Practices

1. **Start Simple**: Begin with basic research ideas
2. **Monitor Progress**: Check tree visualization regularly
3. **Resource Management**: Use appropriate model configurations
4. **Iterative Improvement**: Use reflection cycles for better results
5. **Documentation**: Keep track of experimental decisions and outcomes

---

This documentation provides a comprehensive understanding of the AI Scientist-v2 experiment writing workflow. The system's strength lies in its systematic approach to scientific research automation, combining tree search, parallel execution, and intelligent stage management to produce high-quality research papers.
