"""
Checkpoint Manager for Google Colab
Handles saving and restoring experiment state to/from Google Drive.
"""

import os
import json
import pickle
import shutil
from datetime import datetime
from typing import Dict, Optional, Any, List
from pathlib import Path
import time


class CheckpointManager:
    """Manages checkpoints for long-running experiments on Google Colab."""
    
    def __init__(
        self,
        experiment_name: str,
        drive_root: str = "/content/drive/MyDrive",
        checkpoint_folder: str = "AI_Scientist_Checkpoints",
        max_checkpoints: int = 10,
        save_interval_minutes: int = 30,
    ):
        """
        Initialize checkpoint manager.
        
        Args:
            experiment_name: Name of the experiment
            drive_root: Root path to Google Drive
            checkpoint_folder: Folder name for checkpoints
            max_checkpoints: Maximum number of checkpoints to keep
            save_interval_minutes: Minimum time between auto-saves
        """
        self.experiment_name = experiment_name
        self.drive_root = Path(drive_root)
        self.checkpoint_dir = self.drive_root / checkpoint_folder / experiment_name
        self.max_checkpoints = max_checkpoints
        self.save_interval_minutes = save_interval_minutes
        self.last_save_time = 0
        
        # Create checkpoint directory if it doesn't exist
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"Checkpoint Manager initialized: {self.checkpoint_dir}")
    
    def save_checkpoint(
        self,
        state: Dict[str, Any],
        checkpoint_name: Optional[str] = None,
        force: bool = False,
    ) -> str:
        """
        Save a checkpoint to Google Drive.
        
        Args:
            state: Dictionary containing state to save
            checkpoint_name: Optional custom name for checkpoint
            force: Force save even if interval hasn't elapsed
        
        Returns:
            Path to saved checkpoint
        """
        # Check if enough time has elapsed since last save
        current_time = time.time()
        time_since_last_save = (current_time - self.last_save_time) / 60  # minutes
        
        if not force and time_since_last_save < self.save_interval_minutes:
            print(f"Skipping save - only {time_since_last_save:.1f} minutes since last save")
            return None
        
        # Generate checkpoint name
        if checkpoint_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            checkpoint_name = f"checkpoint_{timestamp}"
        
        checkpoint_path = self.checkpoint_dir / checkpoint_name
        checkpoint_path.mkdir(parents=True, exist_ok=True)
        
        try:
            # Save state as JSON (for human readability)
            state_copy = self._prepare_state_for_json(state)
            with open(checkpoint_path / "state.json", 'w') as f:
                json.dump(state_copy, f, indent=2)
            
            # Save full state as pickle (for complete restoration)
            with open(checkpoint_path / "state.pkl", 'wb') as f:
                pickle.dump(state, f)
            
            # Save timestamp
            with open(checkpoint_path / "timestamp.txt", 'w') as f:
                f.write(datetime.now().isoformat())
            
            # Save metadata
            metadata = {
                "experiment_name": self.experiment_name,
                "checkpoint_name": checkpoint_name,
                "timestamp": datetime.now().isoformat(),
                "keys": list(state.keys()),
            }
            with open(checkpoint_path / "metadata.json", 'w') as f:
                json.dump(metadata, f, indent=2)
            
            self.last_save_time = current_time
            print(f"✓ Checkpoint saved: {checkpoint_path}")
            
            # Clean up old checkpoints
            self._cleanup_old_checkpoints()
            
            return str(checkpoint_path)
        
        except Exception as e:
            print(f"✗ Error saving checkpoint: {e}")
            return None
    
    def load_checkpoint(
        self,
        checkpoint_name: Optional[str] = None,
        use_latest: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """
        Load a checkpoint from Google Drive.
        
        Args:
            checkpoint_name: Specific checkpoint to load
            use_latest: If True, load the most recent checkpoint
        
        Returns:
            Loaded state dictionary or None if not found
        """
        if checkpoint_name is None and use_latest:
            checkpoint_name = self._get_latest_checkpoint()
        
        if checkpoint_name is None:
            print("No checkpoint found to load")
            return None
        
        checkpoint_path = self.checkpoint_dir / checkpoint_name
        
        if not checkpoint_path.exists():
            print(f"Checkpoint not found: {checkpoint_path}")
            return None
        
        try:
            # Try loading from pickle first (complete state)
            pkl_path = checkpoint_path / "state.pkl"
            if pkl_path.exists():
                with open(pkl_path, 'rb') as f:
                    state = pickle.load(f)
                print(f"✓ Checkpoint loaded: {checkpoint_path}")
                return state
            
            # Fallback to JSON (may not have full state)
            json_path = checkpoint_path / "state.json"
            if json_path.exists():
                with open(json_path, 'r') as f:
                    state = json.load(f)
                print(f"✓ Checkpoint loaded (JSON): {checkpoint_path}")
                return state
            
            print(f"No valid checkpoint files found in {checkpoint_path}")
            return None
        
        except Exception as e:
            print(f"✗ Error loading checkpoint: {e}")
            return None
    
    def list_checkpoints(self) -> List[Dict[str, str]]:
        """
        List all available checkpoints.
        
        Returns:
            List of checkpoint metadata dictionaries
        """
        checkpoints = []
        
        if not self.checkpoint_dir.exists():
            return checkpoints
        
        for item in self.checkpoint_dir.iterdir():
            if item.is_dir():
                metadata_path = item / "metadata.json"
                if metadata_path.exists():
                    try:
                        with open(metadata_path, 'r') as f:
                            metadata = json.load(f)
                        checkpoints.append(metadata)
                    except Exception as e:
                        print(f"Error reading metadata for {item.name}: {e}")
        
        # Sort by timestamp (newest first)
        checkpoints.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return checkpoints
    
    def delete_checkpoint(self, checkpoint_name: str) -> bool:
        """Delete a specific checkpoint."""
        checkpoint_path = self.checkpoint_dir / checkpoint_name
        
        if not checkpoint_path.exists():
            print(f"Checkpoint not found: {checkpoint_name}")
            return False
        
        try:
            shutil.rmtree(checkpoint_path)
            print(f"✓ Checkpoint deleted: {checkpoint_name}")
            return True
        except Exception as e:
            print(f"✗ Error deleting checkpoint: {e}")
            return False
    
    def _get_latest_checkpoint(self) -> Optional[str]:
        """Get the name of the most recent checkpoint."""
        checkpoints = self.list_checkpoints()
        return checkpoints[0]["checkpoint_name"] if checkpoints else None
    
    def _cleanup_old_checkpoints(self):
        """Remove old checkpoints beyond max_checkpoints limit."""
        checkpoints = self.list_checkpoints()
        
        if len(checkpoints) > self.max_checkpoints:
            # Delete oldest checkpoints
            for checkpoint in checkpoints[self.max_checkpoints:]:
                self.delete_checkpoint(checkpoint["checkpoint_name"])
    
    def _prepare_state_for_json(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare state dictionary for JSON serialization."""
        import numpy as np
        
        def convert_value(v):
            if isinstance(v, (np.integer, np.floating)):
                return float(v)
            elif isinstance(v, np.ndarray):
                return v.tolist()
            elif isinstance(v, dict):
                return {k: convert_value(val) for k, val in v.items()}
            elif isinstance(v, (list, tuple)):
                return [convert_value(item) for item in v]
            elif hasattr(v, '__dict__'):
                return str(v)  # Convert complex objects to string
            else:
                return v
        
        return {k: convert_value(v) for k, v in state.items()}
    
    def save_artifacts(
        self,
        artifacts_dict: Dict[str, str],
        checkpoint_name: Optional[str] = None,
    ) -> bool:
        """
        Save artifact files (logs, plots, results) to checkpoint.
        
        Args:
            artifacts_dict: Dictionary mapping artifact names to file paths
            checkpoint_name: Checkpoint to save artifacts to (default: latest)
        
        Returns:
            True if successful
        """
        if checkpoint_name is None:
            checkpoint_name = self._get_latest_checkpoint()
        
        if checkpoint_name is None:
            print("No checkpoint to save artifacts to")
            return False
        
        checkpoint_path = self.checkpoint_dir / checkpoint_name
        artifacts_dir = checkpoint_path / "artifacts"
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            for name, file_path in artifacts_dict.items():
                if os.path.exists(file_path):
                    if os.path.isfile(file_path):
                        shutil.copy2(file_path, artifacts_dir / name)
                    elif os.path.isdir(file_path):
                        shutil.copytree(
                            file_path,
                            artifacts_dir / name,
                            dirs_exist_ok=True
                        )
            
            print(f"✓ Artifacts saved to {artifacts_dir}")
            return True
        
        except Exception as e:
            print(f"✗ Error saving artifacts: {e}")
            return False
    
    def get_checkpoint_summary(self) -> str:
        """Get a human-readable summary of checkpoints."""
        checkpoints = self.list_checkpoints()
        
        if not checkpoints:
            return "No checkpoints found."
        
        summary_lines = [
            f"Checkpoint Summary for {self.experiment_name}:",
            f"Location: {self.checkpoint_dir}",
            f"Total checkpoints: {len(checkpoints)}",
            "",
            "Recent checkpoints:",
        ]
        
        for i, cp in enumerate(checkpoints[:5], 1):
            timestamp = cp.get('timestamp', 'Unknown')
            name = cp.get('checkpoint_name', 'Unknown')
            summary_lines.append(f"  {i}. {name} - {timestamp}")
        
        return "\n".join(summary_lines)


def create_experiment_state(
    stage: str,
    progress: float,
    results: Dict[str, Any],
    config: Dict[str, Any],
    **kwargs
) -> Dict[str, Any]:
    """
    Create a standardized experiment state dictionary for checkpointing.
    
    Args:
        stage: Current stage of experiment (e.g., 'ideation', 'training', 'writeup')
        progress: Progress percentage (0-100)
        results: Current results
        config: Configuration dictionary
        **kwargs: Additional state information
    
    Returns:
        State dictionary ready for checkpointing
    """
    state = {
        "stage": stage,
        "progress": progress,
        "timestamp": datetime.now().isoformat(),
        "results": results,
        "config": config,
    }
    state.update(kwargs)
    return state


def setup_colab_checkpointing(
    experiment_name: str,
    mount_drive: bool = True,
) -> CheckpointManager:
    """
    Set up checkpointing for Google Colab environment.
    
    Args:
        experiment_name: Name of the experiment
        mount_drive: Whether to mount Google Drive
    
    Returns:
        Initialized CheckpointManager
    """
    if mount_drive:
        try:
            from google.colab import drive
            drive.mount('/content/drive')
            print("✓ Google Drive mounted")
        except ImportError:
            print("Not running in Colab - skipping drive mount")
        except Exception as e:
            print(f"Error mounting drive: {e}")
    
    manager = CheckpointManager(experiment_name)
    print(manager.get_checkpoint_summary())
    
    return manager

