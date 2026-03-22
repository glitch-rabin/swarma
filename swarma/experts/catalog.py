"""Expert catalog -- load and query the expert reasoning framework library.

Each expert JSON file contains structured knowledge:
- operating_beliefs -> system prompt foundations
- key_questions -> decision rules / reasoning instructions
- biases -> awareness of blind spots
- limitations -> quality gates (when NOT to apply)
- frameworks -> specific reasoning frameworks with mechanics

The catalog loads these from a directory and makes them queryable
by ID, name, or domain.
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class Expert:
    """A loaded expert with all their reasoning frameworks."""
    id: int  # numeric ID from filename (01, 02, etc.)
    slug: str  # filename stem (e.g. "01-alex-hormozi-offer-engineering")
    name: str
    domain: str
    core_thesis: str
    key_questions: list[str] = field(default_factory=list)
    operating_beliefs: list[str] = field(default_factory=list)
    biases: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    frameworks: list[dict] = field(default_factory=list)
    raw: dict = field(default_factory=dict)

    @classmethod
    def from_file(cls, path: Path) -> "Expert":
        """Load an expert from a JSON file."""
        with open(path) as f:
            data = json.load(f)

        expert_data = data.get("expert", data)

        # Extract numeric ID from filename (e.g. "01-alex-hormozi..." -> 1)
        stem = path.stem
        try:
            expert_id = int(stem.split("-")[0])
        except (ValueError, IndexError):
            expert_id = 0

        return cls(
            id=expert_id,
            slug=stem,
            name=expert_data.get("name", stem),
            domain=expert_data.get("domain", ""),
            core_thesis=expert_data.get("core_thesis", ""),
            key_questions=expert_data.get("key_questions", []),
            operating_beliefs=expert_data.get("operating_beliefs", []),
            biases=expert_data.get("biases", []),
            limitations=expert_data.get("limitations", []),
            frameworks=data.get("frameworks", []),
            raw=data,
        )


class ExpertCatalog:
    """Loads and queries the expert library.

    Can load from:
    1. A directory of JSON files (the 43-experts library)
    2. The built-in catalog bundled with swarma
    3. A custom path specified in config.yaml
    """

    def __init__(self):
        self._experts: dict[int, Expert] = {}
        self._by_slug: dict[str, Expert] = {}

    def load_directory(self, path: str):
        """Load all expert JSON files from a directory."""
        dir_path = Path(path)
        if not dir_path.exists():
            logger.warning("expert catalog path not found: %s", path)
            return

        for f in sorted(dir_path.glob("*.json")):
            try:
                expert = Expert.from_file(f)
                self._experts[expert.id] = expert
                self._by_slug[expert.slug] = expert
                logger.debug("loaded expert: %d - %s", expert.id, expert.name)
            except Exception as e:
                logger.warning("failed to load expert from %s: %s", f.name, e)

        logger.info("loaded %d experts from %s", len(self._experts), path)

    def get(self, expert_id: int) -> Optional[Expert]:
        """Get expert by numeric ID."""
        return self._experts.get(expert_id)

    def get_by_slug(self, slug: str) -> Optional[Expert]:
        """Get expert by filename slug."""
        return self._by_slug.get(slug)

    def search(self, query: str) -> list[Expert]:
        """Search experts by name or domain (case-insensitive)."""
        q = query.lower()
        return [
            e for e in self._experts.values()
            if q in e.name.lower() or q in e.domain.lower() or q in e.core_thesis.lower()
        ]

    def list_all(self) -> list[Expert]:
        """List all loaded experts, sorted by ID."""
        return sorted(self._experts.values(), key=lambda e: e.id)

    @property
    def count(self) -> int:
        return len(self._experts)

    def get_multiple(self, expert_ids: list[int]) -> list[Expert]:
        """Get multiple experts by ID. Skips missing ones."""
        experts = []
        for eid in expert_ids:
            e = self._experts.get(eid)
            if e:
                experts.append(e)
            else:
                logger.warning("expert ID %d not found in catalog", eid)
        return experts
