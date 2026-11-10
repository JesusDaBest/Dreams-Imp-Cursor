"""Writable application state, separate from the portable program files."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATE = Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'Dreams Imp'
STATE.mkdir(parents=True, exist_ok=True)
REQUEST = STATE / 'expression.request'
READY = STATE / 'cursor-ready.json'
ERROR = STATE / 'last-error.txt'

def write_json(path, value):
    import json
    temporary = path.with_suffix(f'.{os.getpid()}.tmp')
    temporary.write_text(json.dumps(value, indent=2), encoding='utf-8')
    temporary.replace(path)
