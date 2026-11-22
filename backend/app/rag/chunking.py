from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core import config


def make_splitter(size=None, overlap=None):
    return RecursiveCharacterTextSplitter(
        chunk_size=size or config.CHUNK_SIZE,
        chunk_overlap=overlap if overlap is not None else config.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""])


def chunk_sections(sections, doc_id, size=None, overlap=None):
    """Metadata-based chunking: one parent per section.
    Recursive chunking: each parent is split into small child chunks."""
    splitter = make_splitter(size, overlap)
    parents, children = [], []
    for i, s in enumerate(sections):
        pid = f"d{doc_id}-p{i}"
        parents.append({"id": pid, "section": s["section"], "page": s["page"], "text": s["text"]})
        for j, piece in enumerate(splitter.split_text(s["text"])):
            children.append({"id": f"{pid}-c{j}", "parent_id": pid, "section": s["section"],
                             "page": s["page"], "text": piece})
    return parents, children