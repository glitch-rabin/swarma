"""Expert composer -- turns selected experts into agent prompt sections.

Pick 2-3 experts from the catalog and the composer generates:
1. Operating beliefs -> system prompt foundations
2. Key questions -> reasoning instructions
3. Biases -> awareness / self-correction prompts
4. Limitations -> quality gates (when to flag uncertainty)
5. Frameworks -> structured reasoning steps

The composed output is injected into Agent.build_system_prompt() as
the "Reasoning Lenses" section.
"""

from .catalog import Expert


def compose_lens(expert: Expert, include_frameworks: bool = False) -> dict:
    """Compose a single expert into a lens dict for the agent.

    Returns a dict that can be stored in agent config or injected
    into the system prompt.
    """
    sections = []

    # Core thesis
    if expert.core_thesis:
        sections.append(f"**Core principle:** {expert.core_thesis}")

    # Operating beliefs -> reasoning foundations
    if expert.operating_beliefs:
        beliefs = "\n".join(f"- {b}" for b in expert.operating_beliefs)
        sections.append(f"**Operating beliefs:**\n{beliefs}")

    # Key questions -> decision checklist
    if expert.key_questions:
        questions = "\n".join(f"- {q}" for q in expert.key_questions)
        sections.append(f"**Key questions to ask:**\n{questions}")

    # Biases -> self-awareness
    if expert.biases:
        biases = "\n".join(f"- {b}" for b in expert.biases)
        sections.append(f"**Known biases (compensate for these):**\n{biases}")

    # Limitations -> quality gates
    if expert.limitations:
        limits = "\n".join(f"- {l}" for l in expert.limitations)
        sections.append(f"**Limitations (flag when these apply):**\n{limits}")

    # Frameworks -> structured reasoning (optional, can be verbose)
    if include_frameworks and expert.frameworks:
        for fw in expert.frameworks[:3]:  # cap at 3 to manage token count
            fw_name = fw.get("name", "Framework")
            fw_purpose = fw.get("purpose", "")
            mechanics = fw.get("mechanics", {})
            desc = mechanics.get("description", "")

            fw_section = f"**Framework: {fw_name}**"
            if fw_purpose:
                fw_section += f"\nPurpose: {fw_purpose}"
            if desc:
                fw_section += f"\n{desc}"
            sections.append(fw_section)

    return {
        "expert": expert.name,
        "domain": expert.domain,
        "expert_id": expert.id,
        "instruction": "\n\n".join(sections),
    }


def compose_lenses(
    experts: list[Expert],
    include_frameworks: bool = False,
) -> list[dict]:
    """Compose multiple experts into lens dicts."""
    return [compose_lens(e, include_frameworks) for e in experts]


def compose_prompt_section(
    experts: list[Expert],
    include_frameworks: bool = False,
) -> str:
    """Compose experts into a ready-to-inject prompt section.

    This is the markdown that goes directly into the system prompt
    under "## Reasoning Lenses".
    """
    if not experts:
        return ""

    parts = []
    for expert in experts:
        lens = compose_lens(expert, include_frameworks)
        parts.append(f"### {lens['expert']} ({lens['domain']})")
        parts.append(lens["instruction"])

    return "\n\n".join(parts)
