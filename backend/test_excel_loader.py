
from pathlib import Path
from app.rag.loaders import load_xlsx

files = list(Path("../data/documents").glob("warranty_matrix.xlsx"))

if not files:
    print("warranty_matrix.xlsx not found!")
else:
    sections = load_xlsx(files[0])

    for section in sections:
        if "Product X" in section["text"]:
            print("Section:", section["section"])
            print("\nGenerated text:")
            print(section["text"])
            break
