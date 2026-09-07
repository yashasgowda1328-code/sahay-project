import os
import re
from typing import List, Dict, Optional

PROTOCOLS_DIR = os.path.join(os.path.dirname(__file__), "..", "protocols")

CATEGORY_KEYWORDS = {
    "counselling": ["counselling", "counseling", "therapy", "emotional support", "listening"],
    "medical_support": ["medical", "health", "vital signs", "doctor", "hospital", "clinic"],
    "protection": ["protection", "safety", "risk", "harm", "danger", "secure"],
    "relocation": ["relocation", "move", "shelter", "housing", "safe house"],
    "legal_aid": ["legal", "law", "court", "custody", "rights", "attorney"],
    "financial_support": ["financial", "money", "fund", "aid", "emergency funds", "support"],
    "rehabilitation": ["rehabilitation", "recovery", "reintegration", "therapy", "long-term"],
    "other": ["other", "miscellaneous", "general"],
}


def _load_protocol(category: str) -> Optional[str]:
    path = os.path.join(PROTOCOLS_DIR, f"{category}.md")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def search_protocols(query: str, max_results: int = 3) -> List[Dict[str, str]]:
    query_lower = query.lower()
    results = []
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in query_lower)
        if score > 0:
            content = _load_protocol(category)
            if content:
                results.append({
                    "category": category,
                    "score": score,
                    "content": content,
                    "source": f"protocols/{category}.md",
                })
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:max_results]


def get_protocol(category: str) -> Optional[Dict[str, str]]:
    content = _load_protocol(category)
    if not content:
        return None
    return {
        "category": category,
        "content": content,
        "source": f"protocols/{category}.md",
    }
