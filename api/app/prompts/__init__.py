"""Prompt templates, ported from the n8n prototype and parameterised.

Templates use `string.Template` rather than `str.format` because the prompts
contain literal JSON braces, which `format` would try to interpret.
"""

from functools import lru_cache
from pathlib import Path
from string import Template

_DIR = Path(__file__).parent


@lru_cache
def _template(name: str) -> Template:
    return Template((_DIR / f"{name}.md").read_text(encoding="utf-8"))


def render(name: str, **values: str) -> str:
    """Render a prompt template, raising if a placeholder was left unfilled."""
    return _template(name).substitute(**values)
