import re
from pathlib import Path

import pandas as pd

HEAD = re.compile(r"^\s*(\d+)\.\s+(.+?)\s*$")
FOOTER = re.compile(r"^(Page \d+|.+ \(v\d+\))$")


def _is_heading(line, expected):
    """A heading looks like '3. Refund Timeline', numbered in sequence, short, no trailing punctuation."""
    m = HEAD.match(line)
    if not m or int(m.group(1)) != expected:
        return None
    if len(line) > 90 or line.strip().endswith((".", ",", ":", ";")):
        return None
    return m.group(2)


def _split_lines(page_lines):
    """page_lines: list of (page, line). Returns sections: {section, page, text}."""
    secs, cur_h, cur, start, expected = [], None, [], None, 1
    for page, line in page_lines:
        h = _is_heading(line, expected)
        if h:
            if cur_h or "".join(cur).strip():
                secs.append({"section": cur_h or "Overview", "page": start, "text": "\n".join(cur).strip()})
            cur_h, cur, start, expected = h, [], page, expected + 1
        else:
            if start is None:
                start = page
            cur.append(line)
    if cur_h or "".join(cur).strip():
        secs.append({"section": cur_h or "Overview", "page": start, "text": "\n".join(cur).strip()})
    return [s for s in secs if s["text"]]


def load_txt(p):
    text = Path(p).read_text(encoding="utf-8")
    return _split_lines([(None, ln) for ln in text.splitlines()])


def load_pdf(p):
    from pypdf import PdfReader
    page_lines = []
    for pn, page in enumerate(PdfReader(str(p)).pages, 1):
        for line in (page.extract_text() or "").splitlines():
            line = line.strip()
            if line and not FOOTER.match(line):
                page_lines.append((pn, line))
    return _split_lines(page_lines)


def load_docx(p):
    from docx import Document
    secs, cur_h, cur = [], None, []
    for para in Document(str(p)).paragraphs:
        style = para.style.name
        if style.startswith("Heading 2"):
            if cur_h or "".join(cur).strip():
                secs.append({"section": cur_h or "Overview", "page": None, "text": "\n".join(cur).strip()})
            cur_h = re.sub(r"^\d+\.\s*", "", para.text).strip()
            cur = []
        elif style == "Title":
            continue
        else:
            cur.append(para.text)
    if cur_h or "".join(cur).strip():
        secs.append({"section": cur_h or "Overview", "page": None, "text": "\n".join(cur).strip()})
    return [s for s in secs if s["text"]]


LABEL_COLS = ["question", "scenario", "item", "region", "partner", "trigger", "template_id"]



def _rows_to_sections(df):
    """Each spreadsheet row becomes one searchable section."""
    cols = list(df.columns)
    label_col = next((c for c in LABEL_COLS if c in cols), cols[0])
    secs = []

    for i, row in df.iterrows():
        text = "; ".join(
            f"{c}: {row[c]}" for c in cols if pd.notna(row[c])
        )

        # Add natural-language descriptions for product data.
        item = row.get("item")

        if pd.notna(item):
            item = str(item).strip()

            warranty = row.get("warranty_months")
            return_days = row.get("return_window_days")

            if pd.notna(warranty):
                text += (
                    f"\n{item} has a warranty period of "
                    f"{warranty} months."
                )

            if pd.notna(return_days):
                text += (
                    f"\n{item} can be returned within "
                    f"{return_days} days."
                )

        secs.append({
            "section": str(row[label_col]),
            "page": int(i) + 1,
            "text": text
        })

    return secs



def load_csv(p):
    return _rows_to_sections(pd.read_csv(p))


def load_xlsx(p):
    secs = []
    for name, df in pd.read_excel(p, sheet_name=None).items():
        if name.lower() == "about":
            continue
        secs += _rows_to_sections(df)
    return secs


LOADERS = {".txt": load_txt, ".pdf": load_pdf, ".docx": load_docx, ".csv": load_csv, ".xlsx": load_xlsx}


def load_file(path):
    return LOADERS[Path(path).suffix.lower()](path)