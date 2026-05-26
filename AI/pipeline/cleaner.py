import re


def clean_text(text: str) -> str:
    """
    Transformations applied:
    - Display math ($$...$$) fully removed — token-heavy, no retrieval value.
    - Inline math ($...$) replaced with <equation> — preserves sentence structure
      while avoiding LaTeX noise.
    - Footnotes (\\footnote{...}) fully removed — meta-commentary, not retrieval signal.
    - Runs of whitespace collapsed — artifact of the above removals.
    - Excessive blank lines collapsed to a maximum of one blank line.

    Applied symmetrically to both sides (corpus chunks and query documents)
    """
    text = re.sub(r'\$\$.*?\$\$', ' ', text, flags=re.DOTALL)

    text = re.sub(r'\$[^\$\n]{1,300}\$', ' <equation> ', text)

    text = re.sub(r'\\footnote\{[^{}]*(?:\{[^{}]*\}[^{}]*)?\}', ' ', text)

    # Collapse runs of spaces/tabs introduced by the removals above
    text = re.sub(r'[ \t]{2,}', ' ', text)

    # Collapse 3+ consecutive newlines to a single blank line
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()