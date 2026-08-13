from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any

import numpy as np
import requests
import streamlit as st
from bs4 import BeautifulSoup

from openai_client import get_client, get_model

USER_AGENT = "DadMumBot/1.0 (educational prototype; Singapore-source retrieval)"
FETCH_TIMEOUT = 12
MAX_PAGE_CHARS = 35000
CHUNK_CHARS = 1200
CHUNK_OVERLAP = 150
TOP_K = 5


def _load_sources() -> list[dict[str, Any]]:
    import json
    from pathlib import Path
    path = Path(__file__).parent / "data" / "approved_sources.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg", "nav", "footer", "header", "form"]):
        tag.decompose()
    text = soup.get_text(" ")
    return " ".join(text.split())[:MAX_PAGE_CHARS]


def _fetch_url(url: str) -> str:
    response = requests.get(
        url,
        timeout=FETCH_TIMEOUT,
        headers={"User-Agent": USER_AGENT, "Accept-Language": "en-SG,en;q=0.8"},
    )
    response.raise_for_status()
    return _clean_html(response.text)


def _chunk_text(text: str) -> list[str]:
    words = text.split()
    if not words:
        return []
    approx_words = max(120, CHUNK_CHARS // 6)
    overlap_words = max(10, CHUNK_OVERLAP // 6)
    chunks = []
    start = 0
    while start < len(words):
        end = min(len(words), start + approx_words)
        chunks.append(" ".join(words[start:end]))
        if end >= len(words):
            break
        start = max(start + 1, end - overlap_words)
    return chunks


def _fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@st.cache_data(ttl=86400, show_spinner=False)
def load_source_chunks() -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    for source in _load_sources():
        try:
            text = _fetch_url(source["url"])
            if not text:
                continue
            for idx, chunk in enumerate(_chunk_text(text)):
                chunks.append({
                    "id": f"{source['name']}::{idx}",
                    "text": chunk,
                    "source_name": source["name"],
                    "institution": source["institution"],
                    "source_type": source["type"],
                    "url": source["url"],
                    "topics": source.get("topics", []),
                    "fingerprint": _fingerprint(chunk),
                })
        except requests.RequestException as exc:
            st.session_state.setdefault("retrieval_warnings", []).append(
                f"Could not fetch {source['name']}: {type(exc).__name__}"
            )
    return chunks


@st.cache_data(ttl=86400, show_spinner=False)
def _embed_texts(texts: tuple[str, ...]) -> list[list[float]]:
    client = get_client()
    response = client.embeddings.create(model="text-embedding-3-small", input=list(texts))
    return [item.embedding for item in response.data]


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    return float(np.dot(a, b) / denom) if denom else 0.0


def _lexical_score(query: str, doc: str) -> float:
    q = set(re.findall(r"[a-z0-9]+", query.lower()))
    d = set(re.findall(r"[a-z0-9]+", doc.lower()))
    if not q or not d:
        return 0.0
    return len(q & d) / len(q)


def retrieve(query: str, mother_age: int | None = None, conception_method: str | None = None, current_week: int | None = None, top_k: int = TOP_K) -> tuple[str, list[dict[str, Any]]]:
    chunks = load_source_chunks()
    if not chunks:
        return "", []

    profile_terms = " ".join(
        str(x) for x in [
            conception_method or "",
            f"week {current_week}" if current_week else "",
            "pregnancy",
            f"age {mother_age}" if mother_age else "",
        ] if x
    )
    retrieval_query = f"{query} {profile_terms}".strip()

    texts = tuple(item["text"] for item in chunks)
    try:
        query_embedding = np.asarray(_embed_texts((retrieval_query,))[0], dtype=np.float32)
        doc_embeddings = np.asarray(_embed_texts(texts), dtype=np.float32)
        semantic_scores = np.array([_cosine(query_embedding, row) for row in doc_embeddings])
    except Exception:
        semantic_scores = np.zeros(len(chunks), dtype=np.float32)

    scored = []
    for idx, item in enumerate(chunks):
        meta_text = " ".join(item.get("topics", [])) + " " + item["source_name"] + " " + item["institution"]
        lexical = _lexical_score(retrieval_query, item["text"] + " " + meta_text)
        score = 0.82 * float(semantic_scores[idx]) + 0.18 * lexical
        scored.append((score, item))
    scored.sort(key=lambda x: x[0], reverse=True)

    selected = []
    seen_sources = set()
    for score, item in scored:
        if item["source_name"] in seen_sources and len(selected) < 3:
            continue
        item = dict(item)
        item["score"] = round(score, 4)
        selected.append(item)
        seen_sources.add(item["source_name"])
        if len(selected) >= top_k:
            break

    context_parts = []
    for item in selected:
        context_parts.append(
            f"SOURCE: {item['source_name']} | {item['institution']} | {item['url']}\n"
            f"EXCERPT: {item['text']}"
        )
    return "\n\n".join(context_parts), selected
