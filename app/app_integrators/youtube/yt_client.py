import logging
import os
import time
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger("app.yt_client")


class YouTubeClient:
    """
    Integrates with YouTube Data API v3.
    Used to validate API keys and fetch video data.
    """

    BASE_URL = "https://www.googleapis.com/youtube/v3"

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.environ.get("YOUTUBE_API_KEY", "")

    def validate_api_key(self, api_key: Optional[str] = None) -> Dict[str, Any]:
        key = api_key or self.api_key
        if not key:
            return {"valid": False, "error": "No API key provided."}

        try:
            resp = requests.get(
                f"{self.BASE_URL}/search",
                params={
                    "part": "snippet",
                    "q": "test",
                    "maxResults": 1,
                    "key": key,
                },
                timeout=10,
            )
            if resp.status_code == 200:
                return {"valid": True, "message": "API key is valid."}
            else:
                body = resp.json()
                error_msg = body.get("error", {}).get("message", resp.text)
                return {"valid": False, "error": error_msg}
        except requests.RequestException as e:
            return {"valid": False, "error": str(e)}

    def get_videos(
        self,
        query: str,
        max_results: int = 10,
        api_key: Optional[str] = None,
        published_after: Optional[str] = None,
        published_before: Optional[str] = None,
        channel_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        key = api_key or self.api_key
        params: Dict[str, Any] = {
            "part": "snippet",
            "q": query,
            "maxResults": max_results,
            "type": "video",
            "key": key,
        }
        if published_after:
            params["publishedAfter"] = self._to_rfc3339(published_after)
        if published_before:
            params["publishedBefore"] = self._to_rfc3339(published_before)
        if channel_id:
            params["channelId"] = channel_id

        # Log params (mask API key)
        log_params = {k: v for k, v in params.items() if k != "key"}
        logger.info(f"YouTube API request: {log_params}")

        t0 = time.time()
        resp = requests.get(
            f"{self.BASE_URL}/search",
            params=params,
            timeout=15,
        )
        t1 = time.time()
        logger.info(f"YouTube API response: status={resp.status_code} time={t1-t0:.3f}s")

        resp.raise_for_status()
        data = resp.json()

        t2 = time.time()
        results = []
        for item in data.get("items", []):
            snippet = item.get("snippet", {})
            results.append({
                "video_id": item.get("id", {}).get("videoId", ""),
                "title": snippet.get("title", ""),
                "description": snippet.get("description", ""),
                "channel": snippet.get("channelTitle", ""),
                "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
                "published_at": snippet.get("publishedAt", ""),
            })
        logger.info(f"YouTube API parsed {len(results)} results in {time.time()-t2:.3f}s (total {time.time()-t0:.3f}s)")
        return results

    @staticmethod
    def _to_rfc3339(date_str: str) -> str:
        """Convert a date string (YYYY-MM-DD) to RFC 3339 format for YouTube API."""
        if "T" in date_str:
            return date_str  # already RFC 3339
        return f"{date_str}T00:00:00Z"

