import sys, importlib, os
import warnings
import pdfplumber
import json
import re
from collections import defaultdict

def _is_footer_text(text, page_height):
    """Detect if text is likely footer content based on patterns and position."""
    if not text or not text.strip():
        return True  # Empty or whitespace-only text should be filtered out
    
    text = text.strip()
    
    # Common footer patterns
    footer_patterns = [
        r'Page\s+\d+\s+of\s+\d+',  # "Page X of Y"
        r'Page\s+\d+',              # "Page X"
        r'Page\s+\d+\s*/\s*\d+',    # "Page X/Y"
    ]
    
    # Check if text matches footer patterns
    for pattern in footer_patterns:
        if re.match(pattern, text, re.IGNORECASE):
            return True
    
    return False

def _filter_footer_lines(lines, page_height):
    """Filter out footer lines from the lines array."""
    filtered_lines = []
    for line in lines:
        # Check if this line is likely footer content
        if not _is_footer_text(line.get("text", ""), page_height):
            filtered_lines.append(line)
    return filtered_lines

def _filter_footer_text(text):
    """Filter out footer content from extracted text."""
    if not text:
        return text
    
    lines = text.split('\n')
    filtered_lines = []
    
    for line in lines:
        line = line.strip()
        if not _is_footer_text(line, None):  # We don't have page height here, so just check patterns
            filtered_lines.append(line)
    
    return '\n'.join(filtered_lines)

def _group_words_by_row(page):
    rows = defaultdict(list)
    for w in page.extract_words():
        rows[round(w["top"], 1)].append(w)
    return rows


def _rows_to_lines(rows):
    lines = []
    for top in sorted(rows):
        words = sorted(rows[top], key=lambda w: w["x0"])
        lines.append({"y": float(top), "text": " ".join(w["text"] for w in words)})
    return lines


def _extract_tables_on_page(page):
    tables = []
    for t in page.find_tables(table_settings={
        "vertical_strategy": "lines",
        "horizontal_strategy": "lines"
    }):
        x0, top, x1, bottom = t.bbox
        # Clip table bbox to page boundaries to avoid errors
        x0 = max(0, min(x0, page.width))
        x1 = max(0, min(x1, page.width))
        top = max(0, min(top, page.height))
        bottom = max(0, min(bottom, page.height))
        
        # Only add valid tables (with non-zero area)
        if x1 > x0 and bottom > top:
            tables.append({"bbox": (x0, top, x1, bottom), "data": t.extract()})
    return tables

def _build_page_entry(page, lines, tables):
    # Extract text excluding table regions to avoid duplication
    text = page.extract_text() or ""
    
    # If there are tables, filter out text from those regions
    if tables:
        # Create a filtered page by excluding table bboxes
        filtered_page = page
        for table in tables:
            try:
                # Crop out the table region
                filtered_page = filtered_page.outside_bbox(table["bbox"])
            except ValueError as e:
                # If bbox is still invalid, skip filtering for this table
                # This shouldn't happen after clipping, but safety first
                warnings.warn(f"Skipping table bbox filtering due to: {e}")
                continue
        text = filtered_page.extract_text() or ""
    
    # Filter out footer content from text
    text = _filter_footer_text(text)
    
    # Filter out footer lines from lines array
    filtered_lines = _filter_footer_lines(lines, page.height)
    
    return {
        "text": text,
        "lines": filtered_lines,
        "height": page.height,
        "tables": tables
    }

def extract_text_tables(pdf_path):
    """Return per-page text, line anchors (y), page height, and tables with bbox."""
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            rows = _group_words_by_row(page)
            lines = _rows_to_lines(rows)
            tables = _extract_tables_on_page(page)
            pages.append(_build_page_entry(page, lines, tables))
    return pages

def _stitch_full_text(pages_content):
    parts, offsets = [], []
    off = 0
    for p in pages_content:
        parts.append(p["text"])
        offsets.append(off)
        off += len(p["text"]) + 1  # newline between pages
    return "\n".join(parts), offsets

def _qa_pattern():
    return re.compile(
        r"(Question\s*\d+\..*?)(?:\n| )Answer:\s*(.*?)(?=(?:\n?Question\s*\d+\.|$))",
        re.DOTALL
    )

def _qa_matches_to_results(matches):
    return [{
        "question": m.group(1).strip(),
        "answer": [{"type": "text", "content": m.group(2).strip()}]
    } for m in matches]

def _is_question_line(ln):
    return re.match(r"\s*Question\s*\d+\.", ln["text"] or "") is not None

def _is_answer_line(ln):
    return re.match(r"\s*Answer:\s*", ln["text"] or "") is not None

def _collect_line_anchors(pages_content):
    q_anchors, a_anchors = [], []  # tuples of (page_idx, y)
    for pi, page in enumerate(pages_content):
        for ln in page["lines"]:
            if _is_question_line(ln):
                q_anchors.append((pi, ln["y"]))
            if _is_answer_line(ln):
                a_anchors.append((pi, ln["y"]))
    q_anchors.sort(key=lambda t: (t[0], t[1]))
    a_anchors.sort(key=lambda t: (t[0], t[1]))
    return q_anchors, a_anchors


def _compute_answer_spans(a_anchors, q_anchors, pages_content, results_len):
    """Return list of (start_page, start_y, end_page, end_y) aligned to results."""
    n = min(len(a_anchors), results_len)
    spans = []
    qj = 0
    last_end = (len(pages_content) - 1, pages_content[-1]["height"] + 5.0)

    for i in range(n):
        ap, ay = a_anchors[i]
        # advance to first question strictly below (ap, ay)
        while qj < len(q_anchors) and (
            q_anchors[qj][0] < ap or (q_anchors[qj][0] == ap and q_anchors[qj][1] <= ay + 0.1)
        ):
            qj += 1
        ep, ey = q_anchors[qj] if qj < len(q_anchors) else last_end
        spans.append((ap, ay, ep, ey))
    return spans

def _pos_le(p1, y1, p2, y2):
    return (p1 < p2) or (p1 == p2 and y1 <= y2)

def _pos_ge(p1, y1, p2, y2):
    return (p1 > p2) or (p1 == p2 and y1 >= y2)

def _attach_tables_to_spans(results, pages_content, spans):
    if not spans:
        return
    n = min(len(spans), len(results))
    for pi, page in enumerate(pages_content):
        for t in page["tables"]:
            _, top, _, bottom = t["bbox"]
            yc = 0.5 * (top + bottom)
            target = None
            # primary: containing span
            for idx in range(n):
                sp, sy, ep, ey = spans[idx]
                if _pos_ge(pi, yc, sp, sy) and _pos_le(pi, yc, ep, ey):
                    target = idx
                    break
            # fallback: last span that started before this table
            if target is None and n > 0:
                latest = None
                for idx in range(n):
                    sp, sy, _, _ = spans[idx]
                    if _pos_le(sp, sy, pi, yc):
                        latest = idx
                target = latest
            if target is not None:
                results[target]["answer"].append({"type": "table", "content": t["data"]})

def split_into_qas(pages_content):
    """Global Q&A parse (handles page spill) + attach tables to the correct answer via (page,y) spans."""
    # 1) Global Q&A from stitched text
    full_text, page_offsets = _stitch_full_text(pages_content)  # offsets kept to preserve original logic footprint
    qa_pat = _qa_pattern()
    qa_matches = list(qa_pat.finditer(full_text))
    results = _qa_matches_to_results(qa_matches)

    # 2) Build ordered anchors from page lines
    q_anchors, a_anchors = _collect_line_anchors(pages_content)

    # 3) Compute cross-page answer spans
    spans = _compute_answer_spans(a_anchors, q_anchors, pages_content, len(results))

    # 4) Attach tables by locating table center inside spans
    _attach_tables_to_spans(results, pages_content, spans)

    return results