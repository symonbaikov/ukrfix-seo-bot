"""
Small helpers to enrich generated HTML with CTA and internal links.
"""

from __future__ import annotations

from typing import List, Dict

CTA_TEXT = "Якщо вам потрібна допомога — звертайтеся в UkrFix. Знайдемо найкраще рішення 🚀"
CTA_BUTTON = '<a href="https://ukrfix.com/add-listing/" class="btn-submit">Подати оголошення на UkrFix безкоштовно</a>'

CTA_BLOCK = f"""
<div class="cta-block">
  <p>{CTA_TEXT}</p>
  {CTA_BUTTON}
</div>
""".strip()


def ensure_cta_block(content: str) -> str:
    """Append CTA block if it's missing."""
    lower_content = content.lower()
    if CTA_TEXT.lower() in lower_content or "add-listing" in lower_content:
        return content
    return f"{content.rstrip()}\n\n{CTA_BLOCK}\n"


def inject_internal_links(content: str, links: List[Dict[str, str]]) -> str:
    """Append internal links section when links are available."""
    if not links:
        return content

    if "internal-links" in content:
        return content

    items = "".join(
        f'<li><a href="{link["url"]}" target="_blank" rel="noopener">{link["title"]}</a></li>'
        for link in links
        if link.get("url")
    )
    if not items:
        return content

    block = f"""
<div class="internal-links">
  <h3>Читайте також:</h3>
  <ul>
    {items}
  </ul>
</div>
""".strip()

    # Place internal links before CTA block when possible
    cta_marker = '<div class="cta-block">'
    if cta_marker in content:
        parts = content.split(cta_marker, 1)
        return f"{parts[0].rstrip()}\n\n{block}\n\n{cta_marker}{parts[1]}"

    return f"{content.rstrip()}\n\n{block}\n"
