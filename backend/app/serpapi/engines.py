"""
SerpApi Engine Configurations & Result Normalizers.
Converts raw provider responses into standardized internal models.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
import urllib.parse
from app.models.schemas import NormalizedSearchResult, NormalizedSearchResponse

class SearchEngineType(str, Enum):
    GOOGLE = "google"
    GOOGLE_SHOPPING = "google_shopping"
    YOUTUBE = "youtube"

def build_engine_params(
    engine: str,
    query: str,
    location: Optional[str] = None,
    gl: str = "in",
    hl: str = "en",
    num: int = 10,
    **extra_params
) -> Dict[str, Any]:
    """
    Constructs search parameters compliant with SerpApi engine specifications.
    """
    params: Dict[str, Any] = {
        "engine": engine,
        "hl": hl,
        "gl": gl,
    }

    if engine == SearchEngineType.YOUTUBE.value:
        # YouTube engine in SerpApi accepts search_query
        params["search_query"] = query
        params["q"] = query
    else:
        params["q"] = query
        if location:
            params["location"] = location

    if engine in [SearchEngineType.GOOGLE.value, SearchEngineType.GOOGLE_SHOPPING.value]:
        params["num"] = num

    params.update(extra_params)
    return params

def _extract_domain(url: str) -> Optional[str]:
    try:
        parsed = urllib.parse.urlparse(url)
        netloc = parsed.netloc
        if netloc.startswith("www."):
            return netloc[4:]
        return netloc
    except Exception:
        return None

def normalize_organic_results(raw_data: Dict[str, Any]) -> List[NormalizedSearchResult]:
    results: List[NormalizedSearchResult] = []
    
    # 1. Parse knowledge graph if present
    kg = raw_data.get("knowledge_graph")
    if isinstance(kg, dict) and kg.get("title"):
        kg_link = kg.get("source", {}).get("link") or kg.get("website") or ""
        results.append(
            NormalizedSearchResult(
                id=kg.get("entity_id"),
                title=kg.get("title", ""),
                link=kg_link,
                source=kg.get("source", {}).get("name") or _extract_domain(kg_link) or "Google Knowledge Graph",
                snippet=kg.get("description") or kg.get("snippet"),
                result_type="knowledge_graph",
                raw_metadata={"type": kg.get("type"), "attributes": kg.get("attributes")}
            )
        )

    # 2. Parse organic results
    organic_list = raw_data.get("organic_results", [])
    if isinstance(organic_list, list):
        for item in organic_list:
            if not isinstance(item, dict):
                continue
            
            link = item.get("link", "")
            if not link:
                continue

            displayed_link = item.get("displayed_link", "")
            domain_source = _extract_domain(link) or displayed_link

            # Extract rating / reviews if available in rich snippets
            rating = None
            reviews_count = None
            rich_snippet = item.get("rich_snippet", {})
            if isinstance(rich_snippet, dict):
                top_dict = rich_snippet.get("top", {})
                if isinstance(top_dict, dict) and "detected_extensions" in top_dict:
                    ext = top_dict["detected_extensions"]
                    if isinstance(ext, dict):
                        rating = ext.get("rating")
                        reviews_count = ext.get("reviews")

            results.append(
                NormalizedSearchResult(
                    id=str(item.get("position")),
                    title=item.get("title", "Untitled"),
                    link=link,
                    source=domain_source,
                    snippet=item.get("snippet"),
                    rating=float(rating) if rating is not None else None,
                    reviews_count=int(reviews_count) if reviews_count is not None else None,
                    result_type="organic",
                    raw_metadata={
                        "position": item.get("position"),
                        "sitelinks": item.get("sitelinks"),
                        "cached_page_link": item.get("cached_page_link")
                    }
                )
            )

    return results

def normalize_shopping_results(raw_data: Dict[str, Any]) -> List[NormalizedSearchResult]:
    results: List[NormalizedSearchResult] = []
    
    # Check shopping_results or inline_shopping_results
    shopping_list = raw_data.get("shopping_results") or raw_data.get("inline_shopping_results") or []
    if isinstance(shopping_list, list):
        for idx, item in enumerate(shopping_list):
            if not isinstance(item, dict):
                continue
            
            title = item.get("title", "Untitled Shopping Result")
            link = item.get("link") or item.get("product_link") or ""
            source = item.get("source") or item.get("merchant") or _extract_domain(link)
            
            # Price details
            price_str = item.get("price")
            extracted_price = item.get("extracted_price")
            
            # Rating & reviews
            rating = item.get("rating")
            reviews = item.get("reviews")
            
            # Additional product info
            product_info = {}
            if item.get("extensions"):
                product_info["extensions"] = item.get("extensions")
            if item.get("product_id"):
                product_info["product_id"] = item.get("product_id")
            if item.get("tag"):
                product_info["tag"] = item.get("tag")
            if item.get("delivery"):
                product_info["delivery"] = item.get("delivery")

            results.append(
                NormalizedSearchResult(
                    id=str(item.get("position", idx + 1)),
                    title=title,
                    link=link,
                    source=source,
                    snippet=f"Merchant: {source}. {item.get('snippet', '')}".strip(),
                    price=price_str,
                    price_raw=float(extracted_price) if extracted_price is not None else None,
                    currency=item.get("currency"),
                    product_info=product_info if product_info else None,
                    rating=float(rating) if rating is not None else None,
                    reviews_count=int(reviews) if reviews is not None else None,
                    thumbnail=item.get("thumbnail"),
                    result_type="shopping",
                    raw_metadata={"position": item.get("position", idx + 1)}
                )
            )

    return results

def normalize_youtube_results(raw_data: Dict[str, Any]) -> List[NormalizedSearchResult]:
    results: List[NormalizedSearchResult] = []
    
    video_list = raw_data.get("video_results", [])
    if isinstance(video_list, list):
        for idx, item in enumerate(video_list):
            if not isinstance(item, dict):
                continue
            
            link = item.get("link") or ""
            if not link and item.get("video_id"):
                link = f"https://www.youtube.com/watch?v={item['video_id']}"
                
            channel = item.get("channel", {})
            channel_name = channel.get("name") if isinstance(channel, dict) else str(channel)

            thumbnail_url = None
            thumb = item.get("thumbnail")
            if isinstance(thumb, dict):
                thumbnail_url = thumb.get("static") or thumb.get("src")
            elif isinstance(thumb, str):
                thumbnail_url = thumb

            snippet_parts = []
            if item.get("description"):
                snippet_parts.append(item["description"])
            if item.get("views"):
                snippet_parts.append(f"Views: {item['views']}")
            if item.get("length"):
                snippet_parts.append(f"Duration: {item['length']}")
            if item.get("published_date"):
                snippet_parts.append(f"Published: {item['published_date']}")

            results.append(
                NormalizedSearchResult(
                    id=str(item.get("video_id") or idx + 1),
                    title=item.get("title", "Untitled Video"),
                    link=link,
                    source=f"YouTube ({channel_name})" if channel_name else "YouTube",
                    snippet=" | ".join(snippet_parts) if snippet_parts else None,
                    thumbnail=thumbnail_url,
                    result_type="youtube",
                    raw_metadata={
                        "views": item.get("views"),
                        "length": item.get("length"),
                        "channel": channel
                    }
                )
            )

    return results

def normalize_serpapi_response(engine: str, query: str, raw_data: Dict[str, Any]) -> NormalizedSearchResponse:
    """
    Normalizes any SerpApi engine response into standard NormalizedSearchResponse.
    """
    if engine == SearchEngineType.GOOGLE_SHOPPING.value:
        results = normalize_shopping_results(raw_data)
    elif engine == SearchEngineType.YOUTUBE.value:
        results = normalize_youtube_results(raw_data)
    else:
        results = normalize_organic_results(raw_data)

    search_metadata = raw_data.get("search_metadata", {})

    return NormalizedSearchResponse(
        query=query,
        engine=engine,
        total_results=len(results),
        results=results,
        search_metadata={
            "id": search_metadata.get("id"),
            "status": search_metadata.get("status"),
            "created_at": search_metadata.get("created_at"),
            "processed_at": search_metadata.get("processed_at"),
            "total_time_taken": search_metadata.get("total_time_taken"),
        } if isinstance(search_metadata, dict) else None
    )
