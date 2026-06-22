import json
import os
from typing import List, Dict, Set

_CONFIG = os.path.join(os.path.dirname(__file__), '..', 'config', 'mappings.json')


def load_all() -> List[Dict]:
    with open(_CONFIG, encoding='utf-8') as f:
        return json.load(f)


def load_for_slot(slot: str) -> List[Dict]:
    """Return active mappings whose refresh_time matches the given slot (e.g. '09:30')."""
    return [
        m for m in load_all()
        if m.get('active', True) and m.get('refresh_time', '') == slot
    ]


def all_slots() -> Set[str]:
    """All unique refresh_time values from active mappings."""
    return {
        m['refresh_time']
        for m in load_all()
        if m.get('active', True) and m.get('refresh_time')
    }
