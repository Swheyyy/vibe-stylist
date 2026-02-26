from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import quote_plus


@dataclass(frozen=True)
class Retailer:
    name: str
    search_url_template: str


RETAILERS = [
    Retailer("Amazon", "https://www.amazon.in/s?k={query}"),
    Retailer("Myntra", "https://www.myntra.com/{segment}?q={query}"),
    Retailer("Zara", "https://www.zara.com/in/en/search?searchTerm={query}"),
]


def _gender_segment(gender: str) -> str:
    gender = (gender or "").strip().lower()
    if gender == "male":
        return "men"
    if gender == "female":
        return "women"
    return "men"


def _budget_phrase(budget: str) -> str:
    budget = (budget or "").strip().lower()
    if budget == "low":
        return "budget affordable"
    if budget == "high":
        return "premium"
    return "mid price"


def _campus_keywords(context: dict[str, Any]) -> list[str]:
    campus_style = (context.get("campus_style") or "").strip().lower()
    occasion = (context.get("occasion") or "").strip().lower()
    season = (context.get("season") or "").strip().lower()

    keywords = []
    if campus_style:
        keywords.append(campus_style.replace("-", " "))
    if occasion:
        keywords.append(occasion)
    if season:
        keywords.append(season)
    return keywords


def _category_queries(context: dict[str, Any]) -> dict[str, list[str]]:
    gender_segment = _gender_segment(context.get("gender", ""))
    budget_phrase = _budget_phrase(context.get("budget_tier", ""))
    campus_keywords = " ".join(_campus_keywords(context))

    base = f"{gender_segment} {budget_phrase} {campus_keywords}".strip()

    return {
        "tops": [
            f"{base} t-shirt",
            f"{base} shirt",
            f"{base} sweatshirt",
        ],
        "bottoms": [
            f"{base} jeans",
            f"{base} chinos",
            f"{base} trousers",
        ],
        "shoes": [
            f"{base} sneakers",
            f"{base} casual shoes",
            f"{base} loafers",
        ],
        "accessories": [
            f"{base} backpack",
            f"{base} watch",
            f"{base} minimal jewelry",
        ],
    }


def _build_links_for_query(query: str, context: dict[str, Any]) -> list[dict[str, str]]:
    links: list[dict[str, str]] = []
    gender_segment = _gender_segment(context.get("gender", ""))
    encoded_query = quote_plus(query.strip())

    for retailer in RETAILERS:
        if retailer.name == "Myntra":
            url = retailer.search_url_template.format(segment=gender_segment, query=encoded_query)
        else:
            url = retailer.search_url_template.format(query=encoded_query)
        links.append(
            {
                "retailer": retailer.name,
                "label": query,
                "url": url,
            }
        )
    return links


def generate_shopping_links(profile: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    # Profile is currently unused, but kept for future scoring/ranking.
    _ = profile

    category_queries = _category_queries(context)
    catalog: dict[str, list[dict[str, str]]] = {}

    for category, queries in category_queries.items():
        links: list[dict[str, str]] = []
        for query in queries[:2]:
            links.extend(_build_links_for_query(query, context))
        catalog[category] = links

    return {
        "categories": catalog,
        "note": "Links are curated search URLs based on profile and campus context.",
    }
