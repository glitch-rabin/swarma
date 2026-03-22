"""Expert catalog -- composable reasoning frameworks from 30+ domain experts."""

from .catalog import Expert, ExpertCatalog
from .composer import compose_lens, compose_lenses, compose_prompt_section

__all__ = [
    "Expert",
    "ExpertCatalog",
    "compose_lens",
    "compose_lenses",
    "compose_prompt_section",
]
