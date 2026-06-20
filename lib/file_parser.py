"""
file_parser.py - PDF/TXT/MD ファイルパーサー + セクション分割
"""
import re
from typing import Optional


def extract_text(uploaded_file) -> str:
    """アップロードされたファイルからテキストを抽出する"""
    name = uploaded_file.name.lower()

    if name.endswith(".pdf"):
        return _parse_pdf(uploaded_file)
    elif name.endswith(".md") or name.endswith(".txt"):
        return _parse_text(uploaded_file)
    else:
        raise ValueError(f"Unsupported file type: {name}")


def _parse_pdf(uploaded_file) -> str:
    """PDFからテキストを抽出"""
    from pypdf import PdfReader

    reader = PdfReader(uploaded_file)
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            pages.append(f"--- Page {i + 1} ---\n{text}")
    return "\n\n".join(pages)


def _parse_text(uploaded_file) -> str:
    """TXT/MDファイルを読み込み"""
    raw = uploaded_file.read()
    # Try UTF-8 first, fallback to shift-jis for Japanese texts
    for encoding in ["utf-8", "utf-8-sig", "shift_jis", "euc-jp", "cp932"]:
        try:
            return raw.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", errors="replace")


def split_sections(text: str) -> list[dict]:
    """
    テキストをセクション（章・節）に分割する。
    Markdownの見出し構造（#, ##, ###）を検出して分割。
    見出しがなければ一定行数で分割。

    Returns:
        list of {"title": str, "content": str, "level": int}
    """
    lines = text.split("\n")

    # Markdownの見出しパターン
    heading_pattern = re.compile(r"^(#{1,4})\s+(.+)$")
    # プレーンテキストの章見出しパターン（CHAPTER, BOOK, 第X章 等）
    plain_heading = re.compile(
        r"^(?:CHAPTER|BOOK|PART|SECTION|第[一二三四五六七八九十百千\d]+[章編節部篇])\s*",
        re.IGNORECASE,
    )

    # まずMarkdown見出しがあるか確認
    has_md_headings = any(heading_pattern.match(line) for line in lines)

    sections = []
    current_title = "Introduction"
    current_level = 1
    current_lines = []

    for line in lines:
        md_match = heading_pattern.match(line)

        if md_match:
            # Markdown見出しで分割
            if current_lines:
                content = "\n".join(current_lines).strip()
                if content:
                    sections.append(
                        {
                            "title": current_title,
                            "content": content,
                            "level": current_level,
                        }
                    )
            current_level = len(md_match.group(1))
            current_title = md_match.group(2).strip()
            current_lines = []
        elif (
            not has_md_headings
            and plain_heading.match(line.strip())
            and len(line.strip()) > 5
        ):
            # MD見出しがないファイルでのみプレーンテキスト見出しを使う
            if current_lines:
                content = "\n".join(current_lines).strip()
                if content:
                    sections.append(
                        {
                            "title": current_title,
                            "content": content,
                            "level": current_level,
                        }
                    )
            current_title = line.strip()
            current_level = 2
            current_lines = []
        else:
            current_lines.append(line)

    # 最後のセクションを追加
    if current_lines:
        content = "\n".join(current_lines).strip()
        if content:
            sections.append(
                {
                    "title": current_title,
                    "content": content,
                    "level": current_level,
                }
            )

    # セクションが見つからなかった場合、一定行数で分割
    if len(sections) <= 1 and len(text) > 3000:
        return _split_by_lines(text, chunk_size=200)

    return sections


def _split_by_lines(text: str, chunk_size: int = 200) -> list[dict]:
    """見出しがない場合、一定行数で分割"""
    lines = text.split("\n")
    sections = []
    for i in range(0, len(lines), chunk_size):
        chunk = lines[i : i + chunk_size]
        content = "\n".join(chunk).strip()
        if content:
            section_num = (i // chunk_size) + 1
            sections.append(
                {
                    "title": f"Section {section_num}",
                    "content": content,
                    "level": 2,
                }
            )
    return sections


def truncate_for_ai(text: str, max_chars: int = 15000) -> str:
    """AI送信用にテキストを切り詰める（トークン制限対策）"""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n... [truncated for AI processing] ..."
