# Google Colab Execution Guide
## AI Scientist V2 - Rigorous Research Paper Generation

This guide provides step-by-step instructions for running the AI Scientist V2 system on Google Colab Pro to generate a high-quality research paper on **Retrieval-Augmented Multimodal Agentic Systems**.

---

## 📋 **Prerequisites**

✅ Google Colab Pro subscription (A100 GPU, High-RAM)  
✅ Google Drive with at least 20GB free space  
✅ OpenAI API key (for GPT-4o, o1-preview, o3-mini)  
✅ Claude API key (for Claude 3.5 Sonnet)  
✅ Semantic Scholar API key (for literature search)  

---

## 🎯 **Overview**

The process is divided into 3 sessions:

| Session | Duration | Purpose | Main Outputs |
|---------|----------|---------|--------------|
| **Session 1** | 2-3 hours | Ideation | 25 research ideas → Select top 1 |
| **Session 2** | 8-10 hours | Experiments | BFTS exploration, results, plots |
| **Session 3** | 3-4 hours | Writeup & Review | 8-page paper + reviews |

**Total Cost Estimate:** $35-45

---

## 🚀 **Session 1: Ideation**

### **Objective:** Generate 25 high-quality research ideas and select the best one

### **Setup (Run these cells first)**

```python
# Cell 1: Mount Google Drive
from google.colab import drive
drive.mount('/content/drive')

# Cell 2: Clone repository to Colab
!git clone -b research-paper-v1 https://github.com/YOUR_USERNAME/SakanaAI-Scientist-v2.git
%cd SakanaAI-Scientist-v2

# Cell 3: Install dependencies
!pip install -q -r requirements.txt
!pip install -q scipy psutil

# Cell 4: Set up API keys securely
import os
from getpass import getpass

# Prompt for API keys (they won't be saved in notebook)
OPENAI_API_KEY = getpass('Enter OpenAI API Key: ')
CLAUDE_API_KEY = getpass('Enter Claude API Key: ')
S2_API_KEY = getpass('Enter Semantic Scholar API Key: ')

os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY
os.environ['ANTHROPIC_API_KEY'] = CLAUDE_API_KEY
os.environ['S2_API_KEY'] = S2_API_KEY

print("✓ API keys configured")
```

### **Run Ideation**

```python
# Cell 5: Run ideation script
!python ai_scientist/perform_ideation_temp_free.py \
    --workshop-file "ai_scientist/ideas/rag_multimodal_agents.md" \
    --model o1-preview-2024-09-12 \
    --max-num-generations 25 \
    --num-reflections 7

print("✓ Ideation complete! Check ai_scientist/ideas/rag_multimodal_agents.json")
```

### **Review and Select Ideas**

```python
# Cell 6: Load and display generated ideas
import json

with open('ai_scientist/ideas/rag_multimodal_agents.json', 'r') as f:
    ideas = json.load(f)

print(f"Generated {len(ideas)} ideas:\n")
for i, idea in enumerate(ideas):
    print(f"{i+1}. {idea['Title']}")
    print(f"   Hypothesis: {idea['Short Hypothesis'][:100]}...")
    print(f"   Risk: {idea.get('Risk Factors and Limitations', ['N/A'])[0] if isinstance(idea.get('Risk Factors and Limitations'), list) else 'N/A'}")
    print()
```

### **Save Selected Idea Index**

```python
# Cell 7: Select your favorite idea
SELECTED_IDEA_INDEX = 0  # Change this to your choice (0-24)

# Save selection to Drive for next session
import json
selection_data = {
    'selected_index': SELECTED_IDEA_INDEX,
    'idea_name': ideas[SELECTED_IDEA_INDEX]['Name'],
    'idea_title': ideas[SELECTED_IDEA_INDEX]['Title'],
    'timestamp': datetime.now().isoformat()
}

with open('/content/drive/MyDrive/AI_Scientist_Checkpoints/selected_idea.json', 'w') as f:
    json.dump(selection_data, f, indent=2)

print(f"✓ Selected Idea #{SELECTED_IDEA_INDEX}: {ideas[SELECTED_IDEA_INDEX]['Title']}")
print("✓ Selection saved to Google Drive")
```

### **My Recommendation**

```python
# Cell 8: AI Scientist's recommendation (optional)
# Based on the criteria: novelty, feasibility, impact, and clarity

def score_idea(idea):
    """Simple scoring function"""
    score = 0
    # Prefer ideas with clear experiments
    if 'Experiments' in idea and len(idea['Experiments']) >= 5:
        score += 2
    # Prefer ideas with comprehensive related work
    if 'Related Work' in idea and len(idea['Related Work']) > 200:
        score += 2
    # Prefer ideas with manageable risk
    risks = idea.get('Risk Factors and Limitations', [])
    if isinstance(risks, list) and len(risks) <= 5:
        score += 1
    # Prefer ideas mentioning specific benchmarks or datasets
    if 'dataset' in str(idea).lower() or 'benchmark' in str(idea).lower():
        score += 1
    return score

scored_ideas = [(i, score_idea(idea), idea['Title']) for i, idea in enumerate(ideas)]
scored_ideas.sort(key=lambda x: x[1], reverse=True)

print("My Top 3 Recommendations:\n")
for rank, (idx, score, title) in enumerate(scored_ideas[:3], 1):
    print(f"{rank}. Idea #{idx} (Score: {score}/6)")
    print(f"   {title}\n")
```

---

## 🧪 **Session 2: Experiments**

### **Objective:** Run rigorous experiments with 5 seeds, generate results

### **Setup**

```python
# Cell 1: Mount Drive and navigate to repo
from google.colab import drive
drive.mount('/content/drive')

%cd /content
!git clone -b research-paper-v1 https://github.com/YOUR_USERNAME/SakanaAI-Scientist-v2.git
%cd SakanaAI-Scientist-v2

# Cell 2: Install dependencies
!pip install -q -r requirements.txt
!pip install -q scipy psutil

# Cell 3: Set up API keys
import os
from getpass import getpass

OPENAI_API_KEY = getpass('Enter OpenAI API Key: ')
CLAUDE_API_KEY = getpass('Enter Claude API Key: ')
S2_API_KEY = getpass('Enter Semantic Scholar API Key: ')

os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY
os.environ['ANTHROPIC_API_KEY'] = CLAUDE_API_KEY
os.environ['S2_API_KEY'] = S2_API_KEY

# Cell 4: Load selected idea from Session 1
import json

with open('/content/drive/MyDrive/AI_Scientist_Checkpoints/selected_idea.json', 'r') as f:
    selection = json.load(f)

IDEA_INDEX = selection['selected_index']
print(f"✓ Running experiments for Idea #{IDEA_INDEX}: {selection['idea_title']}")
```

### **Run Experiments**

```python
# Cell 5: Run experiments with rigorous configuration
# This will take 8-10 hours - monitor progress
!python launch_scientist_rigorous.py \
    --load_ideas "ai_scientist/ideas/rag_multimodal_agents.json" \
    --idea_idx {IDEA_INDEX} \
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
    --validate_results \
    --skip_writeup

print("✓ Experiments complete!")
```

### **Monitor Progress**

```python
# Cell 6: Check checkpoint status (run this periodically)
from ai_scientist.checkpoint_manager import CheckpointManager
import glob

# Find latest experiment directory
exp_dirs = glob.glob('experiments/*_attempt_0')
if exp_dirs:
    latest_exp = sorted(exp_dirs)[-1]
    print(f"Latest experiment: {latest_exp}")
    
    # Check for results
    if os.path.exists(f"{latest_exp}/experiment_results"):
        print("✓ Experiment results generated")
    
    if os.path.exists(f"{latest_exp}/validation_report.json"):
        with open(f"{latest_exp}/validation_report.json", 'r') as f:
            report = json.load(f)
        print(f"✓ Validation: {'PASSED' if report['passed'] else 'FAILED'}")
else:
    print("No experiments found yet")
```

### **Backup Results to Drive**

```python
# Cell 7: Copy results to Google Drive
import shutil

exp_dirs = glob.glob('experiments/*_attempt_0')
if exp_dirs:
    latest_exp = sorted(exp_dirs)[-1]
    exp_name = os.path.basename(latest_exp)
    
    backup_dir = f'/content/drive/MyDrive/AI_Scientist_Checkpoints/{exp_name}'
    os.makedirs(backup_dir, exist_ok=True)
    
    # Copy key files
    for file in ['idea.json', 'validation_report.json', 'token_tracker.json']:
        src = f'{latest_exp}/{file}'
        if os.path.exists(src):
            shutil.copy2(src, backup_dir)
    
    # Copy experiment results if they exist
    if os.path.exists(f'{latest_exp}/experiment_results'):
        shutil.copytree(
            f'{latest_exp}/experiment_results',
            f'{backup_dir}/experiment_results',
            dirs_exist_ok=True
        )
    
    print(f"✓ Backup saved to: {backup_dir}")
```

---

## 📝 **Session 3: Writeup & Review**

### **Objective:** Generate 8-page paper and perform critical review

### **Setup**

```python
# Cell 1: Mount Drive and navigate to repo
from google.colab import drive
drive.mount('/content/drive')

%cd /content
!git clone -b research-paper-v1 https://github.com/YOUR_USERNAME/SakanaAI-Scientist-v2.git
%cd SakanaAI-Scientist-v2

# Cell 2: Install dependencies + LaTeX
!pip install -q -r requirements.txt
!pip install -q scipy psutil
!apt-get install -y texlive-full  # This takes ~10 minutes

# Cell 3: Set up API keys
import os
from getpass import getpass

OPENAI_API_KEY = getpass('Enter OpenAI API Key: ')
CLAUDE_API_KEY = getpass('Enter Claude API Key: ')
S2_API_KEY = getpass('Enter Semantic Scholar API Key: ')

os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY
os.environ['ANTHROPIC_API_KEY'] = CLAUDE_API_KEY
os.environ['S2_API_KEY'] = S2_API_KEY
```

### **Restore Experiment Results**

```python
# Cell 4: Copy experiment results from Drive back to Colab
import shutil
import glob

# Find backed up experiment
backup_dirs = glob.glob('/content/drive/MyDrive/AI_Scientist_Checkpoints/*_attempt_0')
if backup_dirs:
    latest_backup = sorted(backup_dirs)[-1]
    exp_name = os.path.basename(latest_backup)
    
    # Recreate experiment directory in Colab
    local_exp_dir = f'experiments/{exp_name}'
    os.makedirs(local_exp_dir, exist_ok=True)
    
    # Copy files
    for item in os.listdir(latest_backup):
        src = os.path.join(latest_backup, item)
        dst = os.path.join(local_exp_dir, item)
        if os.path.isfile(src):
            shutil.copy2(src, dst)
        elif os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
    
    print(f"✓ Experiment restored to: {local_exp_dir}")
    EXP_DIR = local_exp_dir
else:
    print("✗ No backup found!")
```

### **Run Writeup**

```python
# Cell 5: Generate paper writeup
from ai_scientist.perform_writeup import perform_writeup
from ai_scientist.perform_icbinb_writeup import gather_citations

# Gather citations
print("Gathering citations...")
citations_text = gather_citations(
    EXP_DIR,
    num_cite_rounds=30,
    small_model="gpt-4o-2024-11-20",
)

# Generate paper
print("Generating paper (this may take 20-30 minutes)...")
writeup_success = perform_writeup(
    base_folder=EXP_DIR,
    big_model="o1-preview-2024-09-12",
    page_limit=8,
    citations_text=citations_text,
)

if writeup_success:
    print("✓ Paper generated successfully!")
else:
    print("✗ Paper generation failed - check logs")
```

### **Review Paper**

```python
# Cell 6: Perform comprehensive review
from ai_scientist.perform_llm_review import perform_review, load_paper
from ai_scientist.perform_vlm_review import perform_imgs_cap_ref_review
from ai_scientist.llm import create_client
import glob
import json

# Find generated PDF
pdf_files = glob.glob(f'{EXP_DIR}/*.pdf')
if pdf_files:
    pdf_path = sorted(pdf_files)[-1]
    print(f"Reviewing: {pdf_path}")
    
    # Load paper
    paper_content = load_paper(pdf_path)
    
    # Create client for o1-preview
    client, client_model = create_client("o1-preview-2024-09-12")
    
    # Perform text review
    review_text = perform_review(paper_content, client_model, client)
    
    # Perform image/caption review
    review_img_cap_ref = perform_imgs_cap_ref_review(client, client_model, pdf_path)
    
    # Save reviews
    with open(f'{EXP_DIR}/review_text.txt', 'w') as f:
        f.write(json.dumps(review_text, indent=4))
    
    with open(f'{EXP_DIR}/review_img_cap_ref.json', 'w') as f:
        json.dump(review_img_cap_ref, f, indent=4)
    
    print("✓ Review complete!")
else:
    print("✗ No PDF found!")
```

### **Download Final Paper**

```python
# Cell 7: Copy final paper to Drive and download
import shutil

# Copy to Drive
drive_paper_dir = '/content/drive/MyDrive/AI_Scientist_Papers'
os.makedirs(drive_paper_dir, exist_ok=True)

pdf_files = glob.glob(f'{EXP_DIR}/*.pdf')
if pdf_files:
    final_pdf = sorted(pdf_files)[-1]
    pdf_name = os.path.basename(final_pdf)
    
    shutil.copy2(final_pdf, f'{drive_paper_dir}/{pdf_name}')
    
    # Also copy reviews
    if os.path.exists(f'{EXP_DIR}/review_text.txt'):
        shutil.copy2(f'{EXP_DIR}/review_text.txt', drive_paper_dir)
    
    print(f"✓ Paper saved to Drive: {drive_paper_dir}/{pdf_name}")
    
    # Download to local machine
    from google.colab import files
    files.download(final_pdf)
else:
    print("✗ No PDF to download!")
```

---

## 🔍 **Troubleshooting**

### **Session Timeout**
- Google Colab Pro sessions can timeout after 12-24 hours
- Use checkpointing to resume: `--resume_from_checkpoint "checkpoint_name"`
- Always backup to Google Drive after each major stage

### **Out of Memory**
- Restart runtime: Runtime → Restart runtime
- Clear variables: `%reset -f`
- Ensure A100 GPU is selected in Runtime → Change runtime type

### **API Rate Limits**
- OpenAI: 10,000 TPM for o1-preview
- Claude: 40,000 TPM
- Semantic Scholar: 1 req/sec (already handled)

### **LaTeX Compilation Errors**
- Install full texlive: `!apt-get install -y texlive-full`
- Check logs in `{EXP_DIR}/latex/` folder
- Common issue: Missing packages - install with `tlmgr`

---

## 📊 **Expected Costs**

| Component | Model | Est. Cost |
|-----------|-------|-----------|
| Ideation (25 ideas, 7 reflections) | o1-preview | $12-15 |
| Experiments (BFTS, 5 seeds) | Claude 3.5 + GPT-4o | $20-25 |
| Citations | GPT-4o | $1-2 |
| Writeup | o1-preview | $8-12 |
| Review | o1-preview | $3-5 |
| **TOTAL** | | **$44-59** |

---

## ✅ **Quality Checklist**

Before submitting your paper, verify:

- [ ] All experiments run with 5 seeds
- [ ] Statistical analysis with confidence intervals included
- [ ] Validation report shows "PASSED"
- [ ] Paper is within 8 pages (excluding references)
- [ ] All figures have error bars
- [ ] Citations are properly formatted
- [ ] Review report addresses no major issues
- [ ] Reproducibility section includes all details
- [ ] Code and data availability statement included
- [ ] Ablation studies documented

---

## 📧 **Support**

If you encounter issues:
1. Check the validation report for specific errors
2. Review checkpoint files in Google Drive
3. Check token usage in `token_tracker.json`
4. Review experiment logs in `{EXP_DIR}/logs/`

Good luck with your research paper! 🚀

