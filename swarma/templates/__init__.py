"""swarma.templates -- pre-built team configurations.

Templates are YAML configs for common swarm patterns. Users pick a template,
customize it, and start running cycles immediately.

Usage:
    swarma team create --template content    # create team from template
    swarma team templates                     # list available templates
"""

import importlib.resources
from pathlib import Path
from typing import Optional

import yaml


TEMPLATES_DIR = Path(__file__).parent


def list_templates() -> list[dict]:
    """List all available templates with metadata."""
    templates = []
    for path in sorted(TEMPLATES_DIR.glob("*.yaml")):
        try:
            with open(path) as f:
                data = yaml.safe_load(f)
            templates.append({
                "id": path.stem,
                "name": data.get("name", path.stem),
                "description": data.get("description", ""),
                "agents": len(data.get("agents", {})),
                "flow": data.get("flow", ""),
            })
        except Exception:
            pass
    return templates


def get_template(template_id: str) -> Optional[dict]:
    """Load a template by ID."""
    path = TEMPLATES_DIR / f"{template_id}.yaml"
    if not path.exists():
        return None
    with open(path) as f:
        return yaml.safe_load(f)


def render_template(template_id: str, overrides: Optional[dict] = None) -> dict:
    """Load template and apply overrides."""
    data = get_template(template_id)
    if not data:
        raise ValueError(f"Template '{template_id}' not found")

    if overrides:
        # Shallow merge at top level
        for key, value in overrides.items():
            if isinstance(value, dict) and isinstance(data.get(key), dict):
                data[key].update(value)
            else:
                data[key] = value

    return data
