"""
File I/O utilities for timeline scripts
"""

import json
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import sys

# Import parser factory from research-server
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'research-server' / 'server'))
try:
    from parsers.factory import EventParserFactory
    _parser_factory = EventParserFactory()
except ImportError:
    _parser_factory = None
    print("Warning: Could not import EventParserFactory. JSON/Markdown parsing may be limited.", file=sys.stderr)


def load_yaml_file(filepath: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a YAML file and return its contents.
    
    Args:
        filepath: Path to the YAML file
        
    Returns:
        Dictionary containing the YAML data
        
    Raises:
        FileNotFoundError: If file doesn't exist
        yaml.YAMLError: If YAML is invalid
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        try:
            return yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Invalid YAML in {filepath}: {e}")


def save_yaml_file(filepath: Union[str, Path], data: Dict[str, Any]) -> None:
    """
    Save data to a YAML file.
    
    Args:
        filepath: Path to save the YAML file
        data: Dictionary to save as YAML
    """
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def load_json_file(filepath: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a JSON file and return its contents.
    
    Args:
        filepath: Path to the JSON file
        
    Returns:
        Dictionary containing the JSON data
        
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If JSON is invalid
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json_file(filepath: Union[str, Path], data: Dict[str, Any], indent: int = 2) -> None:
    """
    Save data to a JSON file.
    
    Args:
        filepath: Path to save the JSON file
        data: Dictionary to save as JSON
        indent: Number of spaces for indentation
    """
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False, default=str)


def get_event_files(events_dir: Union[str, Path] = "timeline_data/events") -> List[Path]:
    """
    Get all event files from the events directory.

    Supports multiple formats: JSON (.json), Markdown (.md), and YAML (.yaml, .yml).

    Args:
        events_dir: Path to the events directory

    Returns:
        List of Path objects for each event file
    """
    events_dir = Path(events_dir)
    if not events_dir.exists():
        print(f"Warning: Events directory not found: {events_dir}", file=sys.stderr)
        return []

    # Get event files in all supported formats, excluding hidden files and README
    event_files = []
    for pattern in ['*.json', '*.md', '*.yaml', '*.yml']:
        files = [
            f for f in events_dir.glob(pattern)
            if not f.name.startswith('.') and f.name.upper() != 'README.MD'
        ]
        event_files.extend(files)

    return sorted(event_files)


def load_event(filepath: Union[str, Path]) -> Optional[Dict[str, Any]]:
    """
    Load a single event file with error handling.

    Supports JSON, Markdown, and YAML formats using the parser factory.

    Args:
        filepath: Path to the event file

    Returns:
        Dictionary containing event data, or None if loading fails
    """
    filepath = Path(filepath)

    try:
        # Try using parser factory for JSON and Markdown files
        if _parser_factory and filepath.suffix.lower() in ['.json', '.md']:
            data = _parser_factory.parse_event(filepath)
        # Fall back to YAML for .yaml/.yml files
        elif filepath.suffix.lower() in ['.yaml', '.yml']:
            data = load_yaml_file(filepath)
        else:
            print(f"Unsupported file format: {filepath.suffix}", file=sys.stderr)
            return None

        # Add metadata
        data['_file'] = filepath.name

        # Convert date objects to strings for consistency
        if 'date' in data and hasattr(data['date'], 'isoformat'):
            data['date'] = data['date'].isoformat()

        return data
    except Exception as e:
        print(f"Error loading {filepath}: {e}", file=sys.stderr)
        return None


def save_event(filepath: Union[str, Path], data: Dict[str, Any]) -> bool:
    """
    Save an event file with error handling.
    
    Args:
        filepath: Path to save the event file
        data: Event data to save
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Remove internal metadata before saving
        save_data = data.copy()
        for key in ['_file', '_id_hash', '_errors']:
            save_data.pop(key, None)
        
        save_yaml_file(filepath, save_data)
        return True
    except Exception as e:
        print(f"Error saving {filepath}: {e}", file=sys.stderr)
        return False


def ensure_dir(dirpath: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        dirpath: Path to the directory
        
    Returns:
        Path object for the directory
    """
    dirpath = Path(dirpath)
    dirpath.mkdir(parents=True, exist_ok=True)
    return dirpath


def load_all_events(events_dir: Union[str, Path] = "timeline_data/events") -> List[Dict[str, Any]]:
    """
    Load all events from the events directory.
    
    Args:
        events_dir: Path to the events directory
        
    Returns:
        List of event dictionaries
    """
    events = []
    for filepath in get_event_files(events_dir):
        event = load_event(filepath)
        if event:
            events.append(event)
    return events