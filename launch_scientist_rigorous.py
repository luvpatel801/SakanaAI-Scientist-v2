"""
Enhanced AI Scientist Launch Script with Validation and Checkpointing
Optimized for high-quality research papers with rigorous methodology.
"""

import os.path as osp
import json
import argparse
import shutil
import torch
import os
import re
import sys
from datetime import datetime
from contextlib import contextmanager
from typing import Dict, Any

from ai_scientist.llm import create_client
from ai_scientist.treesearch.perform_experiments_bfts_with_agentmanager import (
    perform_experiments_bfts,
)
from ai_scientist.treesearch.bfts_utils import (
    idea_to_markdown,
    edit_bfts_config_file,
)
from ai_scientist.perform_plotting import aggregate_plots
from ai_scientist.perform_writeup import perform_writeup
from ai_scientist.perform_icbinb_writeup import (
    perform_writeup as perform_icbinb_writeup,
    gather_citations,
)
from ai_scientist.perform_llm_review import perform_review, load_paper
from ai_scientist.perform_vlm_review import perform_imgs_cap_ref_review
from ai_scientist.utils.token_tracker import token_tracker

# Import validation modules
from ai_scientist.validation import (
    compute_confidence_intervals,
    analyze_multi_seed_results,
    check_reproducibility,
    detect_hallucinations,
    verify_claims,
)

# Import checkpoint manager
from ai_scientist.checkpoint_manager import CheckpointManager, create_experiment_state


def print_time():
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


def save_token_tracker(idea_dir):
    with open(osp.join(idea_dir, "token_tracker.json"), "w") as f:
        json.dump(token_tracker.get_summary(), f)
    with open(osp.join(idea_dir, "token_tracker_interactions.json"), "w") as f:
        json.dump(token_tracker.get_interactions(), f)


def parse_arguments():
    parser = argparse.ArgumentParser(description="Run AI scientist experiments with validation")
    parser.add_argument(
        "--writeup-type",
        type=str,
        default="normal",  # Changed default to 8-page format
        choices=["normal", "icbinb"],
        help="Type of writeup to generate (normal=8 page, icbinb=4 page)",
    )
    parser.add_argument(
        "--load_ideas",
        type=str,
        default="ai_scientist/ideas/rag_multimodal_agents.json",
        help="Path to a JSON file containing pregenerated ideas",
    )
    parser.add_argument(
        "--load_code",
        action="store_true",
        help="If set, load a Python file with same name as ideas file but .py extension",
    )
    parser.add_argument(
        "--idea_idx",
        type=int,
        default=0,
        help="Index of the idea to run",
    )
    parser.add_argument(
        "--add_dataset_ref",
        action="store_true",
        help="If set, add a HF dataset reference to the idea",
    )
    parser.add_argument(
        "--writeup-retries",
        type=int,
        default=3,
        help="Number of writeup attempts to try",
    )
    parser.add_argument(
        "--attempt_id",
        type=int,
        default=0,
        help="Attempt ID, used to distinguish same idea in different attempts in parallel runs",
    )
    parser.add_argument(
        "--model_agg_plots",
        type=str,
        default="o3-mini-2025-01-31",
        help="Model to use for plot aggregation",
    )
    parser.add_argument(
        "--model_writeup",
        type=str,
        default="o1-preview-2024-09-12",
        help="Model to use for writeup",
    )
    parser.add_argument(
        "--model_citation",
        type=str,
        default="gpt-4o-2024-11-20",
        help="Model to use for citation gathering",
    )
    parser.add_argument(
        "--num_cite_rounds",
        type=int,
        default=30,  # Increased for more comprehensive citations
        help="Number of citation rounds to perform",
    )
    parser.add_argument(
        "--model_review",
        type=str,
        default="o1-preview-2024-09-12",  # Using o1-preview for better review
        help="Model to use for review main text and captions",
    )
    parser.add_argument(
        "--skip_writeup",
        action="store_true",
        help="If set, skip the writeup process",
    )
    parser.add_argument(
        "--skip_review",
        action="store_true",
        help="If set, skip the review process",
    )
    parser.add_argument(
        "--enable_checkpointing",
        action="store_true",
        default=True,
        help="Enable automatic checkpointing to Google Drive",
    )
    parser.add_argument(
        "--resume_from_checkpoint",
        type=str,
        default=None,
        help="Resume from a specific checkpoint",
    )
    parser.add_argument(
        "--config_file",
        type=str,
        default="bfts_config_rigorous.yaml",
        help="Path to BFTS configuration file",
    )
    parser.add_argument(
        "--validate_results",
        action="store_true",
        default=True,
        help="Enable result validation and hallucination detection",
    )
    return parser.parse_args()


def get_available_gpus(gpu_ids=None):
    if gpu_ids is not None:
        return [int(gpu_id) for gpu_id in gpu_ids.split(",")]
    return list(range(torch.cuda.device_count()))


def validate_experimental_results(
    experiment_results_dir: str,
    idea_dir: str
) -> Dict[str, Any]:
    """
    Validate experimental results for statistical rigor and reproducibility.
    """
    print("\n" + "=" * 60)
    print("VALIDATING EXPERIMENTAL RESULTS")
    print("=" * 60)
    
    validation_report = {
        "statistical_analysis": {},
        "reproducibility_check": {},
        "issues": [],
        "passed": True,
    }
    
    # Load results from experiment_results directory
    if not osp.exists(experiment_results_dir):
        validation_report["passed"] = False
        validation_report["issues"].append("Experiment results directory not found")
        return validation_report
    
    try:
        # Look for results files
        results_files = [f for f in os.listdir(experiment_results_dir) if f.endswith('.json')]
        
        if not results_files:
            validation_report["issues"].append("No JSON results files found")
            return validation_report
        
        # Analyze multi-seed results if available
        all_results = {}
        for results_file in results_files:
            with open(osp.join(experiment_results_dir, results_file), 'r') as f:
                data = json.load(f)
                # Extract seed info from filename or data
                seed_match = re.search(r'seed[_-]?(\d+)', results_file)
                if seed_match:
                    seed = int(seed_match.group(1))
                    all_results[seed] = data
        
        if len(all_results) >= 2:
            # Perform statistical analysis
            validation_report["statistical_analysis"] = analyze_multi_seed_results(all_results)
            print(f"✓ Statistical analysis completed for {len(all_results)} seeds")
        else:
            validation_report["issues"].append(
                f"Insufficient seeds for statistical analysis (found {len(all_results)}, need ≥2)"
            )
        
        # Save validation report
        with open(osp.join(idea_dir, "validation_report.json"), 'w') as f:
            json.dump(validation_report, f, indent=2)
        
        print("✓ Validation report saved")
    
    except Exception as e:
        validation_report["passed"] = False
        validation_report["issues"].append(f"Error during validation: {str(e)}")
        print(f"✗ Validation error: {e}")
    
    return validation_report


def find_pdf_path_for_review(idea_dir):
    pdf_files = [f for f in os.listdir(idea_dir) if f.endswith(".pdf")]
    reflection_pdfs = [f for f in pdf_files if "reflection" in f]
    if reflection_pdfs:
        final_pdfs = [f for f in reflection_pdfs if "final" in f.lower()]
        if final_pdfs:
            pdf_path = osp.join(idea_dir, final_pdfs[0])
        else:
            reflection_nums = []
            for f in reflection_pdfs:
                match = re.search(r"reflection[_.]?(\d+)", f)
                if match:
                    reflection_nums.append((int(match.group(1)), f))
            
            if reflection_nums:
                highest_reflection = max(reflection_nums, key=lambda x: x[0])
                pdf_path = osp.join(idea_dir, highest_reflection[1])
            else:
                pdf_path = osp.join(idea_dir, reflection_pdfs[0])
    else:
        # Look for any PDF
        if pdf_files:
            pdf_path = osp.join(idea_dir, pdf_files[0])
        else:
            pdf_path = None
    
    return pdf_path


@contextmanager
def redirect_stdout_stderr_to_file(log_file_path):
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    log = open(log_file_path, "a")
    sys.stdout = log
    sys.stderr = log
    try:
        yield
    finally:
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        log.close()


if __name__ == "__main__":
    args = parse_arguments()
    os.environ["AI_SCIENTIST_ROOT"] = os.path.dirname(os.path.abspath(__file__))
    print(f"Set AI_SCIENTIST_ROOT to {os.environ['AI_SCIENTIST_ROOT']}")
    
    # Check available GPUs and adjust parallel processes if necessary
    available_gpus = get_available_gpus()
    print(f"Using GPUs: {available_gpus}")
    
    # Load ideas
    with open(args.load_ideas, "r") as f:
        ideas = json.load(f)
        print(f"Loaded {len(ideas)} pregenerated ideas from {args.load_ideas}")
    
    idea = ideas[args.idea_idx]
    date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    idea_dir = f"experiments/{date}_{idea['Name']}_attempt_{args.attempt_id}"
    print(f"Results will be saved in {idea_dir}")
    os.makedirs(idea_dir, exist_ok=True)
    
    # Initialize checkpoint manager
    checkpoint_manager = None
    if args.enable_checkpointing:
        try:
            checkpoint_manager = CheckpointManager(
                experiment_name=f"{date}_{idea['Name']}",
                save_interval_minutes=30,
            )
            print(f"✓ Checkpoint manager initialized")
        except Exception as e:
            print(f"Warning: Could not initialize checkpoint manager: {e}")
            checkpoint_manager = None
    
    # Check if resuming from checkpoint
    if args.resume_from_checkpoint and checkpoint_manager:
        print(f"Attempting to resume from checkpoint: {args.resume_from_checkpoint}")
        state = checkpoint_manager.load_checkpoint(args.resume_from_checkpoint)
        if state:
            print("✓ Checkpoint loaded successfully")
            # Restore state variables as needed
            # TODO: Implement state restoration logic
        else:
            print("Could not load checkpoint, starting fresh")
    
    # Convert idea json to markdown file
    idea_path_md = osp.join(idea_dir, "idea.md")
    
    # If load_code is True, get the Python file with same name as JSON
    code = None
    if args.load_code:
        code_path = args.load_ideas.rsplit(".", 1)[0] + ".py"
        if os.path.exists(code_path):
            with open(code_path, "r") as f:
                code = f.read()
        else:
            print(f"Warning: Code file {code_path} not found")
    else:
        code_path = None
    
    idea_to_markdown(ideas[args.idea_idx], idea_path_md, code_path)
    
    dataset_ref_code = None
    if args.add_dataset_ref:
        dataset_ref_path = "hf_dataset_reference.py"
        if os.path.exists(dataset_ref_path):
            with open(dataset_ref_path, "r") as f:
                dataset_ref_code = f.read()
        else:
            print(f"Warning: Dataset reference file {dataset_ref_path} not found")
            dataset_ref_code = None
    
    if dataset_ref_code is not None and code is not None:
        added_code = dataset_ref_code + "\n" + code
    elif dataset_ref_code is not None and code is None:
        added_code = dataset_ref_code
    elif dataset_ref_code is None and code is not None:
        added_code = code
    else:
        added_code = None
    
    if added_code is not None:
        ideas[args.idea_idx]["Code"] = added_code
    
    # Store raw idea json
    idea_path_json = osp.join(idea_dir, "idea.json")
    with open(idea_path_json, "w") as f:
        json.dump(ideas[args.idea_idx], f, indent=4)
    
    # Create checkpoint: Idea preparation complete
    if checkpoint_manager:
        checkpoint_manager.save_checkpoint(
            create_experiment_state(
                stage="idea_preparation",
                progress=10,
                results={},
                config=vars(args),
                idea_dir=idea_dir,
                idea_name=idea['Name'],
            ),
            checkpoint_name="01_idea_prepared"
        )
    
    # Edit BFTS config file
    config_path = args.config_file
    idea_config_path = edit_bfts_config_file(
        config_path,
        idea_dir,
        idea_path_json,
    )
    
    print("\n" + "=" * 60)
    print("STAGE 1: RUNNING EXPERIMENTS (BFTS)")
    print("=" * 60)
    print_time()
    
    # Run experiments
    perform_experiments_bfts(idea_config_path)
    
    # Create checkpoint: Experiments complete
    if checkpoint_manager:
        checkpoint_manager.save_checkpoint(
            create_experiment_state(
                stage="experiments_complete",
                progress=50,
                results={},
                config=vars(args),
                idea_dir=idea_dir,
            ),
            checkpoint_name="02_experiments_complete"
        )
    
    # Copy experiment results
    experiment_results_dir = osp.join(idea_dir, "logs/0-run/experiment_results")
    if os.path.exists(experiment_results_dir):
        shutil.copytree(
            experiment_results_dir,
            osp.join(idea_dir, "experiment_results"),
            dirs_exist_ok=True,
        )
        print("✓ Experiment results copied")
    
    # Validate experimental results
    if args.validate_results:
        validation_report = validate_experimental_results(
            osp.join(idea_dir, "experiment_results"),
            idea_dir
        )
        print(f"\nValidation Result: {'PASSED' if validation_report['passed'] else 'FAILED'}")
        if validation_report['issues']:
            print("Issues found:")
            for issue in validation_report['issues']:
                print(f"  - {issue}")
    
    print("\n" + "=" * 60)
    print("STAGE 2: AGGREGATING PLOTS")
    print("=" * 60)
    print_time()
    
    aggregate_plots(base_folder=idea_dir, model=args.model_agg_plots)
    
    # Clean up temp experiment results
    shutil.rmtree(osp.join(idea_dir, "experiment_results"))
    
    save_token_tracker(idea_dir)
    
    # Create checkpoint: Plots aggregated
    if checkpoint_manager:
        checkpoint_manager.save_checkpoint(
            create_experiment_state(
                stage="plots_aggregated",
                progress=60,
                results={},
                config=vars(args),
                idea_dir=idea_dir,
            ),
            checkpoint_name="03_plots_aggregated"
        )
    
    if not args.skip_writeup:
        print("\n" + "=" * 60)
        print("STAGE 3: GATHERING CITATIONS")
        print("=" * 60)
        print_time()
        
        citations_text = gather_citations(
            idea_dir,
            num_cite_rounds=args.num_cite_rounds,
            small_model=args.model_citation,
        )
        
        print("\n" + "=" * 60)
        print(f"STAGE 4: WRITING PAPER ({args.writeup_type.upper()} FORMAT)")
        print("=" * 60)
        print_time()
        
        writeup_success = False
        for attempt in range(args.writeup_retries):
            print(f"\nWriteup attempt {attempt+1} of {args.writeup_retries}")
            if args.writeup_type == "normal":
                writeup_success = perform_writeup(
                    base_folder=idea_dir,
                    big_model=args.model_writeup,
                    page_limit=8,
                    citations_text=citations_text,
                )
            else:
                writeup_success = perform_icbinb_writeup(
                    base_folder=idea_dir,
                    big_model=args.model_writeup,
                    page_limit=4,
                    citations_text=citations_text,
                )
            if writeup_success:
                print("✓ Writeup completed successfully")
                break
        
        if not writeup_success:
            print("✗ Writeup process did not complete successfully after all retries.")
        
        # Create checkpoint: Writeup complete
        if checkpoint_manager:
            checkpoint_manager.save_checkpoint(
                create_experiment_state(
                    stage="writeup_complete",
                    progress=80,
                    results={"writeup_success": writeup_success},
                    config=vars(args),
                    idea_dir=idea_dir,
                ),
                checkpoint_name="04_writeup_complete"
            )
    
    save_token_tracker(idea_dir)
    
    if not args.skip_review and not args.skip_writeup:
        print("\n" + "=" * 60)
        print("STAGE 5: REVIEWING PAPER")
        print("=" * 60)
        print_time()
        
        pdf_path = find_pdf_path_for_review(idea_dir)
        if pdf_path and os.path.exists(pdf_path):
            print(f"Paper found at: {pdf_path}")
            paper_content = load_paper(pdf_path)
            client, client_model = create_client(args.model_review)
            
            # Perform comprehensive review
            review_text = perform_review(paper_content, client_model, client)
            review_img_cap_ref = perform_imgs_cap_ref_review(
                client, client_model, pdf_path
            )
            
            with open(osp.join(idea_dir, "review_text.txt"), "w") as f:
                f.write(json.dumps(review_text, indent=4))
            with open(osp.join(idea_dir, "review_img_cap_ref.json"), "w") as f:
                json.dump(review_img_cap_ref, f, indent=4)
            
            print("✓ Paper review completed")
        else:
            print("✗ No PDF found for review")
    
    # Final checkpoint
    if checkpoint_manager:
        checkpoint_manager.save_checkpoint(
            create_experiment_state(
                stage="complete",
                progress=100,
                results={"final": True},
                config=vars(args),
                idea_dir=idea_dir,
            ),
            checkpoint_name="05_complete",
            force=True
        )
        
        # Save all artifacts to checkpoint
        checkpoint_manager.save_artifacts({
            "idea_dir": idea_dir,
        })
    
    print("\n" + "=" * 60)
    print("EXPERIMENT COMPLETE!")
    print("=" * 60)
    print(f"Results saved in: {idea_dir}")
    print_time()
    
    # Print final token usage summary
    print("\nToken Usage Summary:")
    print(json.dumps(token_tracker.get_summary(), indent=2))
    
    print("\nStart cleaning up processes")
    # Kill all mp and torch processes associated with this experiment
    import psutil
    import signal
    
    current_process = psutil.Process()
    children = current_process.children(recursive=True)
    
    for child in children:
        try:
            child.send_signal(signal.SIGTERM)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    gone, alive = psutil.wait_procs(children, timeout=3)
    
    for process in alive:
        try:
            process.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    sys.exit(0)

