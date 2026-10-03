"""
Research Agent: Receives a ResearchPlan, executes targeted search queries via SerpApi
across Web, Shopping, and YouTube engines, normalizes results into ResearchResult models,
and deduplicates findings while preserving full source provenance.
"""

import uuid
import asyncio
import urllib.parse
from typing import List, Optional, Set
from app.models.schemas import ResearchPlan, ResearchResult, NormalizedSearchResponse
from app.services.query_builder import QueryBuilder, SearchQueryTarget
from app.serpapi.client import SerpApiClient, SerpApiError

class ResearchError(Exception):
    """Exception raised when entire research execution fails."""
    pass

def normalize_url(url: str) -> str:
    """
    Normalizes a URL string for reliable deduplication.
    Strips trailing slashes and common tracking query parameters.
    """
    if not url:
        return ""
    try:
        parsed = urllib.parse.urlparse(url.strip())
        # Clean query parameters
        query_pairs = urllib.parse.parse_qsl(parsed.query)
        clean_query = [(k, v) for k, v in query_pairs if not k.startswith("utm_") and k not in ["ref", "source"]]
        new_query = urllib.parse.urlencode(clean_query)
        
        path = parsed.path.rstrip("/")
        netloc = parsed.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
            
        return urllib.parse.urlunparse((parsed.scheme.lower(), netloc, path, parsed.params, new_query, ""))
    except Exception:
        return url.strip().lower().rstrip("/")

class InformationResearcher:
    def __init__(
        self,
        serpapi_client: Optional[SerpApiClient] = None,
        query_builder: Optional[QueryBuilder] = None
    ):
        self.serpapi_client = serpapi_client or SerpApiClient()
        self.query_builder = query_builder or QueryBuilder()

    async def execute_research(self, plan: ResearchPlan) -> List[ResearchResult]:
        """
        Executes research queries generated from the ResearchPlan concurrently.
        Collects, normalizes, and deduplicates research results.
        """
        if not plan:
            raise ValueError("ResearchPlan cannot be None.")

        # 1. Generate targeted search queries
        query_targets: List[SearchQueryTarget] = self.query_builder.build_queries(plan)

        all_results: List[ResearchResult] = []
        seen_urls: Set[str] = set()

        # 2. Execute query targets concurrently via asyncio.gather
        async def fetch_target(target: SearchQueryTarget) -> tuple[SearchQueryTarget, Optional[NormalizedSearchResponse]]:
            try:
                if target.search_type == "shopping":
                    res = await self.serpapi_client.search_shopping(query=target.query)
                elif target.search_type == "youtube":
                    res = await self.serpapi_client.search_youtube(query=target.query)
                else:
                    res = await self.serpapi_client.search_web(query=target.query)
                return target, res
            except SerpApiError:
                return target, None
            except Exception:
                return target, None

        fetched = await asyncio.gather(*[fetch_target(t) for t in query_targets])

        # 3. Convert SerpApi items to ResearchResult & Deduplicate
        for target, response in fetched:
            if not response or not response.results:
                continue

            for item in response.results:
                if not item.link:
                    continue

                norm_url = normalize_url(item.link)
                if norm_url in seen_urls:
                    continue
                seen_urls.add(norm_url)

                res_obj = ResearchResult(
                    result_id=f"res_{uuid.uuid4().hex[:10]}",
                    query=target.query,
                    source_type=target.search_type,
                    title=item.title,
                    url=item.link,  # Preserves exact source URL for provenance
                    snippet=item.snippet,
                    price=item.price,
                    price_raw=item.price_raw,
                    currency=item.currency,
                    rating=item.rating,
                    reviews_count=item.reviews_count,
                    thumbnail=item.thumbnail,
                    raw_metadata=item.raw_metadata
                )
                all_results.append(res_obj)

        return all_results
