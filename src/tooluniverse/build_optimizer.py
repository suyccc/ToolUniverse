"""Build optimization utilities for ToolUniverse tools."""

import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Set, Tuple


def calculate_tool_hash(tool_config: Dict[str, Any]) -> str:
    """Calculate a hash for tool configuration to detect changes."""
    # Create a normalized version of the config for hashing
    normalized_config = {}
    for key, value in sorted(tool_config.items()):
        if key not in ["timestamp", "last_updated", "created_at"]:
            normalized_config[key] = value

    config_str = json.dumps(normalized_config, sort_keys=True, separators=(",", ":"))
    return hashlib.md5(config_str.encode("utf-8")).hexdigest()


def load_metadata(metadata_file: Path) -> Dict[str, str]:
    """Load tool metadata from file."""
    if not metadata_file.exists():
        return {}

    try:
        with open(metadata_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_metadata(metadata: Dict[str, str], metadata_file: Path) -> None:
    """Save tool metadata to file."""
    metadata_file.parent.mkdir(parents=True, exist_ok=True)
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, sort_keys=True)


def cleanup_orphaned_files(tools_dir: Path, current_tool_names: Set[str]) -> int:
    """Remove files for tools that no longer exist."""
    if not tools_dir.exists():
        return 0

    cleaned_count = 0
    keep_files = {"__init__", "_shared_client", "__pycache__"}

    for file_path in tools_dir.iterdir():
        if (
            file_path.is_file()
            and file_path.suffix == ".py"
            and file_path.stem not in keep_files
            and file_path.stem not in current_tool_names
        ):
            print(f"🗑️  Removing orphaned tool file: {file_path.name}")
            file_path.unlink()
            cleaned_count += 1

    return cleaned_count


def get_changed_tools(
    current_tools: Dict[str, Any], metadata_file: Path
) -> Tuple[list, list, list]:
    """Get lists of new, changed, and unchanged tools."""
    old_metadata = load_metadata(metadata_file)
    new_metadata = {}
    new_tools = []
    changed_tools = []
    unchanged_tools = []

    for tool_name, tool_config in current_tools.items():
        current_hash = calculate_tool_hash(tool_config)
        new_metadata[tool_name] = current_hash

        old_hash = old_metadata.get(tool_name)
        if old_hash is None:
            new_tools.append(tool_name)
        elif old_hash != current_hash:
            changed_tools.append(tool_name)
        else:
            unchanged_tools.append(tool_name)

    # Save updated metadata
    save_metadata(new_metadata, metadata_file)

    return new_tools, changed_tools, unchanged_tools
