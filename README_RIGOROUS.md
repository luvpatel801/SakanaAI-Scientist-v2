# AI Scientist V2 - Rigorous Research Paper Generation
## `research-paper-v1` Branch

This branch contains enhanced configurations and validation modules for generating **high-quality, rigorous research papers** suitable for top-tier ML conferences. It includes comprehensive statistical analysis, hallucination detection, reproducibility checks, and Google Colab Pro integration.

---

## 🎯 **What's New in This Branch**

### **1. Enhanced Validation Framework** (`ai_scientist/validation/`)

#### **Statistical Analysis** (`statistical_analysis.py`)
- Confidence interval computation (95% CI with t-distribution)
- Statistical significance testing (t-test, Mann-Whitney, Wilcoxon)
- Multi-seed result analysis with error bars
- Distribution assumption checking (normality tests, outlier detection)
- Effect size computation (Cohen's d)

#### **Unit Test Generation** (`unit_test_generator.py`)
- Automated unit test generation using LLMs
- Code quality validation (syntax, style, complexity)
- Anti-pattern detection (mutable defaults, bare except clauses)
- Import validation and missing dependency detection
- Common bug pattern checking (data leakage, numerical stability)

#### **Hallucination Detection** (`hallucination_detector.py`)
- Unsupported numerical claim detection
- Contradiction checking against experimental results
- Impossible value detection (percentages > 100%, perfect scores)
- Citation accuracy verification
- Logical inconsistency detection

#### **Reproducibility Checks** (`reproducibility_checker.py`)
- Random seed validation across libraries (numpy, torch, tensorflow)
- Deterministic operation verification
- Multi-run consistency checking
- Environment documentation generation

### **2. Checkpoint Manager** (`ai_scientist/checkpoint_manager.py`)

- Automatic checkpointing to Google Drive every 30 minutes
- Session recovery for Colab timeouts
- Experiment state preservation (progress, results, config)
- Artifact backup (logs, plots, models)
- Checkpoint history management (keeps last 10)

### **3. Enhanced Launch Script** (`launch_scientist_rigorous.py`)

- Integrated validation at each stage
- Automatic checkpoint creation
- Statistical analysis of multi-seed results
- Comprehensive error handling
- Progress tracking and stage-by-stage execution

### **4. Rigorous BFTS Configuration** (`bfts_config_rigorous.yaml`)

```yaml
agent:
  num_workers: 4  # Parallel exploration paths
  num_seeds: 5    # Statistical rigor (increased from 3)
  stages:
    stage1_max_iters: 30  # Thorough initial exploration
    stage2_max_iters: 20  # Extended refinement
    stage3_max_iters: 20  # Further refinement
    stage4_max_iters: 25  # Final optimization
  search:
    max_debug_depth: 5   # More thorough debugging
    debug_prob: 0.7      # Higher debugging probability
```

### **5. Research Topic: RAG + Multimodal Agents**

Pre-configured research topic focusing on:
- Retrieval-augmented generation for multimodal systems
- Agentic reasoning with vision-language models
- Real-world task performance
- Failure mode analysis
- Robustness and hallucination reduction

### **6. Google Colab Pro Optimization**

- Complete execution guide (`COLAB_EXECUTION_GUIDE.md`)
- 3-session workflow (Ideation → Experiments → Writeup)
- Google Drive integration for checkpointing
- Session recovery mechanisms
- Memory and resource management

---

## 🚀 **Quick Start**

### **For Google Colab Pro (Recommended)**

1. **Read the Colab Execution Guide:**
   ```
   Open COLAB_EXECUTION_GUIDE.md and follow the 3-session workflow
   ```

2. **Required API Keys:**
   - OpenAI API key (for GPT-4o, o1-preview, o3-mini)
   - Claude API key (for Claude 3.5 Sonnet)
   - Semantic Scholar API key (optional but recommended)

3. **Estimated Cost:** $35-45 per paper

4. **Total Time:** 13-17 hours across 3 sessions

### **For Local Execution**

```bash
# 1. Clone repository
git clone -b research-paper-v1 https://github.com/YOUR_USERNAME/SakanaAI-Scientist-v2.git
cd SakanaAI-Scientist-v2

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set environment variables
export OPENAI_API_KEY="your-key-here"
export ANTHROPIC_API_KEY="your-key-here"
export S2_API_KEY="your-key-here"

# 4. Run ideation (2-3 hours)
python ai_scientist/perform_ideation_temp_free.py \
    --workshop-file "ai_scientist/ideas/rag_multimodal_agents.md" \
    --model o1-preview-2024-09-12 \
    --max-num-generations 25 \
    --num-reflections 7

# 5. Review ideas and select your favorite (idea_idx)

# 6. Run experiments (8-10 hours)
python launch_scientist_rigorous.py \
    --load_ideas "ai_scientist/ideas/rag_multimodal_agents.json" \
    --idea_idx 0 \
    --load_code \
    --add_dataset_ref \
    --config_file "bfts_config_rigorous.yaml" \
    --writeup-type normal \
    --model_writeup o1-preview-2024-09-12 \
    --model_citation gpt-4o-2024-11-20 \
    --model_review o1-preview-2024-09-12 \
    --model_agg_plots o3-mini-2025-01-31 \
    --num_cite_rounds 30 \
    --enable_checkpointing \
    --validate_results

# 7. Find your paper in experiments/TIMESTAMP_IDEANAME/
```

---

## 📊 **Model Selection Rationale**

| Stage | Model | Why This Model? | Cost/1M Tokens |
|-------|-------|-----------------|----------------|
| **Ideation** | o1-preview | Best reasoning for novel ideas | $15-60 |
| **Code Generation** | Claude 3.5 Sonnet | Superior coding ability | $3-15 |
| **Code Feedback** | GPT-4o | Fast, reliable error analysis | $2.50-10 |
| **Plot Analysis** | o3-mini | Cost-effective reasoning | $1.10-4.40 |
| **Writeup** | o1-preview | Best long-form reasoning | $15-60 |
| **Citations** | GPT-4o | Fast, good enough quality | $2.50-10 |
| **Review** | o1-preview | Critical analysis capability | $15-60 |

---

## 📁 **New File Structure**

```
SakanaAI-Scientist-v2/
├── ai_scientist/
│   ├── validation/                    # NEW: Validation framework
│   │   ├── __init__.py
│   │   ├── statistical_analysis.py
│   │   ├── unit_test_generator.py
│   │   ├── hallucination_detector.py
│   │   └── reproducibility_checker.py
│   ├── checkpoint_manager.py          # NEW: Checkpoint management
│   ├── ideas/
│   │   └── rag_multimodal_agents.md  # NEW: Research topic
│   └── ...
├── launch_scientist_rigorous.py       # NEW: Enhanced launch script
├── bfts_config_rigorous.yaml          # NEW: Rigorous configuration
├── COLAB_EXECUTION_GUIDE.md           # NEW: Colab instructions
├── README_RIGOROUS.md                 # NEW: This file
└── requirements.txt                   # UPDATED: Added scipy, psutil
```

---

## ✅ **Quality Guarantees**

This branch implements the following quality measures:

### **Statistical Rigor**
- ✅ 5 random seeds per experiment (increased from 3)
- ✅ 95% confidence intervals on all metrics
- ✅ Statistical significance testing (p-values)
- ✅ Effect size reporting (Cohen's d)
- ✅ Distribution assumption validation

### **Reproducibility**
- ✅ All random seeds documented and fixed
- ✅ Deterministic operations enforced
- ✅ Complete dependency tracking
- ✅ Environment documentation
- ✅ Code quality validation

### **Hallucination Prevention**
- ✅ Numerical claims verified against results
- ✅ Contradictions detected and flagged
- ✅ Citation accuracy checked
- ✅ Impossible values detected
- ✅ Logical consistency verified

### **Experimental Thoroughness**
- ✅ Extended BFTS exploration (95 total iterations vs 62)
- ✅ Deeper debugging (5 levels vs 3)
- ✅ Higher debugging probability (70% vs 50%)
- ✅ More comprehensive citations (30 rounds vs 20)
- ✅ 8-page format for depth (vs 4-page)

---

## 🔧 **Configuration Details**

### **BFTS Parameters**

| Parameter | Original | Rigorous | Rationale |
|-----------|----------|----------|-----------|
| `num_seeds` | 3 | 5 | Better statistical confidence |
| `stage1_max_iters` | 20 | 30 | More thorough initial exploration |
| `stage2_max_iters` | 12 | 20 | Extended refinement |
| `stage3_max_iters` | 12 | 20 | Further refinement |
| `stage4_max_iters` | 18 | 25 | Comprehensive final optimization |
| `max_debug_depth` | 3 | 5 | More thorough error resolution |
| `debug_prob` | 0.5 | 0.7 | Higher debugging frequency |
| **Total Iterations** | **62** | **95** | **53% more exploration** |

### **Ideation Parameters**

| Parameter | Original | Rigorous | Rationale |
|-----------|----------|----------|-----------|
| `max-num-generations` | 20 | 25 | More candidate ideas |
| `num-reflections` | 5 | 7 | More refinement rounds |

---

## 💰 **Cost Breakdown**

### **Detailed Cost Estimate**

| Component | Details | Model | Est. Cost |
|-----------|---------|-------|-----------|
| **Ideation** | 25 ideas × 7 reflections | o1-preview | $12-15 |
| **Literature Search** | ~500 API calls | Semantic Scholar | Free |
| **Code Generation** | 95 iterations × 4 workers | Claude 3.5 | $15-20 |
| **Code Feedback** | ~200 evaluations | GPT-4o | $3-5 |
| **Plot Aggregation** | ~10 plots | o3-mini | $0.50-1 |
| **Citation Gathering** | 30 rounds | GPT-4o | $1-2 |
| **Paper Writing** | 8 pages + reflections | o1-preview | $8-12 |
| **Paper Review** | Text + figures | o1-preview | $3-5 |
| **TOTAL** | | | **$42.50-60** |

**Budget Target:** $40-45 (achievable by running only top 1 idea)

---

## 🐛 **Troubleshooting**

### **Common Issues**

#### **1. Colab Session Timeout**
```python
# Solution: Resume from checkpoint
!python launch_scientist_rigorous.py \
    --resume_from_checkpoint "checkpoint_name" \
    ...other args...
```

#### **2. Out of Memory**
```python
# Solution: Clear cache and restart
import torch
torch.cuda.empty_cache()
# Then restart runtime
```

#### **3. API Rate Limits**
```
Error: Rate limit exceeded

Solution: 
- OpenAI o1-preview: 10,000 TPM limit
- Claude: 40,000 TPM limit
- Wait 60 seconds and retry
- Checkpointing will save progress
```

#### **4. Validation Fails**
```
Validation FAILED: Insufficient seeds

Solution:
- Check experiment_results/ directory
- Verify all seed runs completed
- Re-run with --validate_results flag
```

---

## 📈 **Expected Outputs**

After successful completion, your experiment directory will contain:

```
experiments/2025-01-09_12-34-56_YOUR_IDEA_attempt_0/
├── idea.json                      # Idea details
├── idea.md                        # Idea markdown
├── validation_report.json         # Validation results
├── token_tracker.json             # API usage stats
├── final_paper.pdf                # Generated paper (8 pages)
├── review_text.txt                # Critical review
├── review_img_cap_ref.json        # Figure/caption review
├── logs/                          # Experiment logs
│   └── 0-run/
│       ├── unified_tree_viz.html  # Tree visualization
│       └── experiment_results/     # Raw results
├── plots/                         # Generated plots
└── latex/                         # LaTeX source
```

---

## 📚 **Additional Resources**

- **Original AI Scientist V2 Paper:** https://pub.sakana.ai/ai-scientist-v2/paper
- **AIDE Framework (underlying tree search):** https://github.com/WecoAI/aideml
- **Semantic Scholar API:** https://www.semanticscholar.org/product/api

---

## 🤝 **Contributing**

This branch focuses on research quality and rigor. Contributions welcome for:

- Additional validation checks
- New statistical analysis methods
- Enhanced hallucination detection
- Better reproducibility tools
- Improved checkpoint mechanisms

---

## 📝 **License**

Same as main repository (see LICENSE file).

---

## ⚠️ **Important Notes**

1. **Cost Management:** Monitor token usage in `token_tracker.json` to stay within budget
2. **Time Commitment:** Full pipeline takes 13-17 hours - plan accordingly
3. **GPU Requirements:** A100 GPU recommended for Colab (included in Pro)
4. **Checkpointing:** Always enable checkpointing for long runs
5. **Validation:** Review validation reports before finalizing paper
6. **Human Review:** Always perform final human review before submission

---

## 🎓 **Citation**

If you use this rigorous configuration in your research:

```bibtex
@misc{aiscientist_v2_rigorous,
  title={AI Scientist V2: Rigorous Configuration for High-Quality Research},
  author={Based on work by Yamada, Yutaro and Lange, Robert Tjarko and Lu, Cong and others},
  year={2025},
  note={research-paper-v1 branch with enhanced validation and quality controls}
}
```

---

**Happy researching! May your papers be accepted and your ideas be novel! 🚀📄✨**

