"""Jinja2 prompt template reader for orchestration."""

from pathlib import Path
from typing import Any, Dict, Optional
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from src.adapters.orchestration.personas import AgentRole, get_persona


class PromptTemplateReader:
    """Loader and renderer for Jinja2 prompt templates."""

    def __init__(self, templates_dir: Optional[Path] = None):
        if templates_dir is None:
            current_file = Path(__file__).resolve()
            templates_dir = current_file.parent / "prompts"

        self.templates_dir = templates_dir

        if not self.templates_dir.exists():
            raise FileNotFoundError(f"Templates directory not found: {self.templates_dir}")

        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(self, template_name: str, context: Dict[str, Any]) -> str:
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
        except TemplateNotFound:
            raise FileNotFoundError(f"Template '{template_name}' not found in {self.templates_dir}")
        except Exception as e:
            raise RuntimeError(f"Error rendering template '{template_name}': {str(e)}")


def build_agent_prompt(
    role: AgentRole,
    ticker: str,
    user_thesis: Optional[str] = None,
    bull_case_output: Optional[str] = None,
    bear_case_output: Optional[str] = None,
    capital: Optional[float] = None,
    risk_tolerance: Optional[str] = None,
    current_price: Optional[float] = None,
    **extra_context
) -> str:
    """
    Build agent system prompt by rendering the appropriate Jinja2 template."""
    persona = get_persona(role)
    reader = PromptTemplateReader()

    context = {
        "name": persona.name,
        "title": persona.title,
        "voice": persona.voice,
        "ticker": ticker,
        "user_thesis": user_thesis,
        "bull_case_output": bull_case_output,
        "bear_case_output": bear_case_output,
        "capital": capital,
        "risk_tolerance": risk_tolerance,
        "current_price": current_price,
        "bull_analyst_name": "Chidi Okonkwo",
        "bear_analyst_name": "Amara Nwosu",
        **extra_context
    }

    return reader.render(persona.template_file, context)
