import sys

import pandas as pd

from app.core import config
from app.db.models import SessionLocal, Document, ParentChunk
from app.rag import vectorstore
from app.services.ingestion import ingest_file


def reset():
    s = SessionLocal()
    s.query(ParentChunk).delete()
    s.query(Document).delete()
    s.commit()
    s.close()
    vectorstore.reset_collections()


if __name__ == "__main__":
    models = sys.argv[1].split(",") if len(sys.argv) > 1 else ["bge"]
    reset()
    man = pd.read_csv(config.DOCS_DIR / "manifest.csv", keep_default_na=False)
    man = man.sort_values(["policy_name", "version"])      # older versions first
    total_p = total_c = 0
    for _, r in man.iterrows():
        meta = dict(doc_type=r["doc_type"], policy_name=r["policy_name"], version=str(r["version"]),
                    effective_date=str(r["effective_date"]), is_active=str(r["is_active"]).lower() == "true",
                    product_category=r["product_category"], region=r["region"],
                    customer_type=r["customer_type"], seller=r["seller"], warehouse=r["warehouse"],
                    order_status=r["order_status"])
        out = ingest_file(config.DOCS_DIR / r["file"], meta, models=models)
        total_p += out["parents"]
        total_c += out["children"]
        print(f"{r['file']:45s} parents={out['parents']:3d} children={out['children']:3d}")
    print(f"\nDONE: {len(man)} documents, {total_p} parent chunks, {total_c} child chunks, models={models}")