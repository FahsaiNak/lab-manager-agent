"""Ingests every markdown doc in sandbox/corpus/ into wiki_index.json.

wiki_index.json is gitignored (generated state, like sandbox/cluster_fs/) — run
this before any Knowledge Curator demo/eval.
"""

import glob
import os

from app.knowledge_tools import WIKI_INDEX_PATH, ingest_doc

CORPUS_ROOT = os.path.join(os.path.dirname(__file__), "..", "sandbox", "corpus")


def main() -> None:
    if os.path.exists(WIKI_INDEX_PATH):
        os.remove(WIKI_INDEX_PATH)

    doc_paths = sorted(
        glob.glob(os.path.join(CORPUS_ROOT, "**", "*.md"), recursive=True)
    )
    for doc_path in doc_paths:
        result = ingest_doc(os.path.abspath(doc_path))
        print(f"Ingested {result['page_id']}: {result['title']}")

    print(f"Wiki index written to {WIKI_INDEX_PATH}")


if __name__ == "__main__":
    main()
