"""HTML Parser for Baidu Baike lemma pages."""

from __future__ import annotations

import re
from bs4 import BeautifulSoup


def parse_baike_page(
    html: str,
    url: str,
    fallback_lemma: str,
    max_sections: int = 25,
) -> str:
    """
    Parse Baidu Baike HTML into structured, LLM-optimized Markdown.
    """
    if "百度安全验证" in html:
        return f"Error: Baidu security verification triggered for URL: {url}."

    soup = BeautifulSoup(html, "html.parser")

    # 1. Canonical Title
    h1 = soup.find("h1")
    title = h1.get_text(strip=True) if h1 else None
    if not title:
        title_tag = soup.find("title")
        if title_tag and title_tag.string:
            title = title_tag.string.replace("_百度百科", "").strip()
        else:
            title = fallback_lemma

    # 2. Check for Disambiguation / Polysemy links
    polysemy_notes: list[str] = []
    for poly in soup.select('[class*="polysemantText"], [class*="polysemy"] a'):
        text = poly.get_text(strip=True)
        if text and text not in polysemy_notes:
            polysemy_notes.append(text)

    # 3. Summary / Abstract
    summary_parts: list[str] = []
    summary_div = soup.select_one(
        '[class*="J-summary"], .lemma-summary, [class*="lemmaSummary"]'
    )
    if summary_div:
        for junk in summary_div.select(
            '[class*="lemma-subscribe"], [class*="edit-lemma"], [class*="audio-play"]'
        ):
            junk.decompose()
        clean_text = _clean_text(summary_div.get_text(separator="\n", strip=True))
        if clean_text:
            summary_parts.append(clean_text)
    else:
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            content_desc = str(meta_desc.get("content")).strip()
            if content_desc:
                summary_parts.append(content_desc)

    summary_text = "\n\n".join(summary_parts) if summary_parts else "暂无概述。"

    # 4. Infobox (Key-Value pairs)
    infobox_items: list[tuple[str, str]] = []
    # Try item wrappers first
    for wrapper in soup.select('[class*="itemWrapper"], .basic-info dl > div'):
        dt = wrapper.select_one('dt, [class*="itemName"], [class*="name"]')
        dd = wrapper.select_one('dd, [class*="itemValue"], [class*="value"]')
        if dt and dd:
            k = dt.get_text(strip=True).replace("\xa0", " ").strip()
            v = dd.get_text(strip=True).replace("\xa0", " ").strip()
            if k and v:
                infobox_items.append((k, v))

    # Fallback to direct dt/dd pairing
    if not infobox_items:
        dts = soup.select('[class*="basicInfo"] dt, .basic-info dt, [class*="itemName"]')
        dds = soup.select('[class*="basicInfo"] dd, .basic-info dd, [class*="itemValue"]')
        for dt, dd in zip(dts, dds):
            k = dt.get_text(strip=True).replace("\xa0", " ").strip()
            v = dd.get_text(strip=True).replace("\xa0", " ").strip()
            if k and v and (k, v) not in infobox_items:
                infobox_items.append((k, v))

    infobox_text = (
        "\n".join(f"- **{k}**: {v}" for k, v in infobox_items)
        if infobox_items
        else "无基本信息。"
    )

    # 5. Catalog / Table of Contents
    catalogs: list[str] = []
    for cat in soup.select('[class*="catalogText"], [class*="catalogList"] a, .lemma-catalog a'):
        c_text = cat.get_text(strip=True)
        if c_text and c_text not in catalogs and c_text != "目录":
            catalogs.append(c_text)

    catalog_text = (
        "\n".join(f"{i+1}. {c}" for i, c in enumerate(catalogs))
        if catalogs
        else ""
    )

    # 6. Main Body Headings & Paragraphs
    # Note: Use exact class match on div.J-lemma-content to avoid matching inner spans like J-lemma-content-lemma-text
    content_area = (
        soup.find("div", class_=lambda c: c and "J-lemma-content" in c.split())
        or soup.find(class_="main-content")
        or soup.find(class_="contentWrapper_ESwGG")
        or soup
    )

    body_blocks: list[str] = []
    sections_count = 0
    truncated = False

    for element in content_area.find_all(["h2", "h3", "h4", "div", "p"]):
        name = element.name
        classes = element.get("class", [])
        class_str = " ".join(classes) if isinstance(classes, list) else str(classes)

        # Skip infobox, catalog, summary, or editor UI elements
        if any(
            x in class_str
            for x in [
                "basicInfo",
                "basic-info",
                "catalog",
                "J-summary",
                "lemma-summary",
                "editLemma",
                "contentBottom",
                "lemma-subscribe",
            ]
        ):
            continue

        if name == "h2":
            h_text = _clean_heading(element.get_text(strip=True))
            if h_text and h_text != "目录" and not any(h_text in b for b in body_blocks[-2:]):
                sections_count += 1
                if sections_count > max_sections:
                    truncated = True
                    break
                body_blocks.append(f"\n## {h_text}\n")
        elif name == "h3":
            h_text = _clean_heading(element.get_text(strip=True))
            if h_text and not any(h_text in b for b in body_blocks[-2:]):
                body_blocks.append(f"\n### {h_text}\n")
        elif name == "h4":
            h_text = _clean_heading(element.get_text(strip=True))
            if h_text and not any(h_text in b for b in body_blocks[-2:]):
                body_blocks.append(f"\n#### {h_text}\n")
        elif name in ("p", "div") and any(
            k in class_str for k in ["para", "lemma-text", "content-lemma"]
        ):
            p_text = _clean_text(element.get_text(strip=True))
            # Require substantive length to filter out buttons/labels
            if p_text and len(p_text) >= 20:
                if not body_blocks or body_blocks[-1] != p_text:
                    body_blocks.append(p_text)

    # Assemble final markdown
    doc: list[str] = [
        f"# 百度百科: {title}",
        f"**来源链接**: {url}",
    ]

    if polysemy_notes:
        doc.append("\n> **同名/多义词提示**: " + " | ".join(polysemy_notes[:5]))

    doc.extend([
        "\n## 概述 (Summary)",
        summary_text,
        "\n## 基本信息 (Infobox)",
        infobox_text,
    ])

    if catalog_text:
        doc.extend([
            "\n## 目录 (Catalog)",
            catalog_text,
        ])

    doc.append("\n## 正文要点 (Body Content)")
    if body_blocks:
        doc.append("\n\n".join(body_blocks))
        if truncated:
            doc.append(
                f"\n> 提示: 该词条内容丰富，当前已显示前 {max_sections} 个主要章节。"
                "完整章节请参见上方 [目录] 索引。"
            )
    else:
        doc.append("未解析到正文详细段落。")

    return "\n\n".join(doc)


def _clean_heading(text: str) -> str:
    """Remove UI action buttons such as 播报, 编辑 from headings."""
    text = re.sub(r"\[\d+\]", "", text)
    text = text.replace("播报", "").replace("编辑", "").replace("锁定", "").strip()
    return text


def _clean_text(text: str) -> str:
    """Clean superscript references and excess whitespace."""
    text = re.sub(r"\[\d+(?:-\d+)?\]", "", text)
    text = re.sub(r"\n\s*\n", "\n\n", text)
    return text.strip()
