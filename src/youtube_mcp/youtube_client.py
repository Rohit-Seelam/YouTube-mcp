"""YouTube API client for extracting video information."""

import glob
import os
import re
import tempfile
from typing import Any

import yt_dlp
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .utils import clean_caption_text, extract_playlist_id, extract_video_id


class YouTubeClient:
    """Client for interacting with YouTube API and yt-dlp."""

    def __init__(self, api_key: str | None = None):
        """Initialize YouTube client with API key."""
        self.api_key = api_key or os.getenv("YOUTUBE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "YouTube API key is required. Set YOUTUBE_API_KEY environment variable.",
            )

        self.youtube = build("youtube", "v3", developerKey=self.api_key, cache_discovery=False)

    def get_video_captions(
        self,
        video_url: str,
        language_preference: str | None = None,
    ) -> dict[str, Any]:
        """Extract captions from YouTube video using yt-dlp."""
        video_id = extract_video_id(video_url)
        if not video_id:
            raise ValueError(f"Invalid YouTube URL: {video_url}")

        # Use temporary directory for subtitle files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Configure yt-dlp to write subtitle files
            ydl_opts = {
                "writesubtitles": True,
                "writeautomaticsub": True,
                "subtitlesformat": "srt",
                "skip_download": True,
                "quiet": True,
                "no_warnings": True,
                "noprogress": True,
                "no_color": True,
                "extract_flat": False,
                "outtmpl": os.path.join(temp_dir, "%(title)s.%(ext)s"),
                "subtitleslangs": [language_preference or "en"] if language_preference else ["en"],
            }

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    # Extract info to get available languages
                    info = ydl.extract_info(
                        f"https://www.youtube.com/watch?v={video_id}",
                        download=False,
                    )

                    subtitles = info.get("subtitles", {})
                    automatic_captions = info.get("automatic_captions", {})
                    all_captions = {**subtitles, **automatic_captions}

                    if not all_captions:
                        return {
                            "video_id": video_id,
                            "video_title": info.get("title", "Unknown"),
                            "captions": None,
                            "available_languages": [],
                            "message": "No captions available for this video",
                        }

                    # Determine best language
                    target_lang = language_preference or "en"
                    if target_lang in all_captions:
                        chosen_lang = target_lang
                    elif any(lang.startswith(target_lang) for lang in all_captions):
                        chosen_lang = next(
                            lang for lang in all_captions if lang.startswith(target_lang)
                        )
                    else:
                        chosen_lang = list(all_captions.keys())[0]

                    # Configure for specific language and download subtitles
                    ydl_opts_download = {
                        **ydl_opts,
                        "subtitleslangs": [chosen_lang],
                    }

                    with yt_dlp.YoutubeDL(ydl_opts_download) as ydl_download:
                        ydl_download.download([f"https://www.youtube.com/watch?v={video_id}"])

                    # Find and read the subtitle file
                    subtitle_files = glob.glob(os.path.join(temp_dir, f"*.{chosen_lang}.srt"))
                    if not subtitle_files:
                        # Try without country code
                        lang_base = chosen_lang.split("-")[0]
                        subtitle_files = glob.glob(os.path.join(temp_dir, f"*.{lang_base}.srt"))

                    if subtitle_files:
                        with open(subtitle_files[0], encoding="utf-8") as f:
                            caption_text = f.read()
                            cleaned_text = clean_caption_text(caption_text)

                        return {
                            "video_id": video_id,
                            "video_title": info.get("title", "Unknown"),
                            "captions": cleaned_text,
                            "language_used": chosen_lang,
                            "available_languages": list(all_captions.keys()),
                            "caption_type": (
                                "automatic" if chosen_lang in automatic_captions else "manual"
                            ),
                        }
                    return {
                        "video_id": video_id,
                        "video_title": info.get("title", "Unknown"),
                        "captions": None,
                        "available_languages": list(all_captions.keys()),
                        "message": f"Failed to download captions for language {chosen_lang}",
                    }

            except Exception as e:
                return {
                    "video_id": video_id,
                    "error": str(e),
                    "message": "Failed to extract captions",
                }

    def get_video_topics(self, video_url: str) -> dict[str, Any]:
        """Extract topics and sections from video description."""
        video_id = extract_video_id(video_url)
        if not video_id:
            raise ValueError(f"Invalid YouTube URL: {video_url}")

        try:
            # Get video details from YouTube API
            request = self.youtube.videos().list(part="snippet,contentDetails", id=video_id)

            response = request.execute()

            if not response["items"]:
                return {
                    "video_id": video_id,
                    "error": "Video not found or is private",
                    "topics": [],
                }

            video_info = response["items"][0]
            snippet = video_info["snippet"]
            description = snippet.get("description", "")

            # Extract topics from description
            topics = self._extract_topics_from_description(description)

            return {
                "video_id": video_id,
                "video_title": snippet.get("title", "Unknown"),
                "channel_title": snippet.get("channelTitle", "Unknown"),
                "description": description,
                "topics": topics,
                "tags": snippet.get("tags", []),
                "category_id": snippet.get("categoryId"),
                "published_at": snippet.get("publishedAt"),
            }

        except HttpError as e:
            return {"video_id": video_id, "error": f"YouTube API error: {e!s}", "topics": []}
        except Exception as e:
            return {"video_id": video_id, "error": str(e), "topics": []}

    def get_playlist_titles(self, playlist_url: str) -> dict[str, Any]:
        """Extract video titles from YouTube playlist."""
        playlist_id = extract_playlist_id(playlist_url)
        if not playlist_id:
            raise ValueError(f"Invalid YouTube playlist URL: {playlist_url}")

        try:
            videos = []
            next_page_token = None

            while True:
                request = self.youtube.playlistItems().list(
                    part="snippet",
                    playlistId=playlist_id,
                    maxResults=50,
                    pageToken=next_page_token,
                )

                response = request.execute()

                for item in response["items"]:
                    snippet = item["snippet"]
                    video_info = {
                        "video_id": snippet["resourceId"]["videoId"],
                        "title": snippet["title"],
                        "channel_title": snippet["channelTitle"],
                        "published_at": snippet["publishedAt"],
                        "position": snippet["position"],
                    }
                    videos.append(video_info)

                next_page_token = response.get("nextPageToken")
                if not next_page_token:
                    break

            # Get playlist metadata
            playlist_request = self.youtube.playlists().list(part="snippet", id=playlist_id)

            playlist_response = playlist_request.execute()
            playlist_info = {}

            if playlist_response["items"]:
                playlist_snippet = playlist_response["items"][0]["snippet"]
                playlist_info = {
                    "title": playlist_snippet.get("title", "Unknown"),
                    "description": playlist_snippet.get("description", ""),
                    "channel_title": playlist_snippet.get("channelTitle", "Unknown"),
                    "published_at": playlist_snippet.get("publishedAt"),
                }

            return {
                "playlist_id": playlist_id,
                "playlist_info": playlist_info,
                "videos": videos,
                "total_videos": len(videos),
            }

        except HttpError as e:
            return {
                "playlist_id": playlist_id,
                "error": f"YouTube API error: {e!s}",
                "videos": [],
            }
        except Exception as e:
            return {"playlist_id": playlist_id, "error": str(e), "videos": []}

    def _extract_topics_from_description(self, description: str) -> list[dict[str, str]]:
        """Extract topics/sections from video description."""
        topics = []

        # Common patterns for timestamps and topics
        timestamp_patterns = [
            r"(\d{1,2}:\d{2}(?::\d{2})?)\s*[-–—]\s*(.+?)(?=\n|\d{1,2}:\d{2}|$)",
            r"(\d{1,2}:\d{2}(?::\d{2})?)\s+(.+?)(?=\n|\d{1,2}:\d{2}|$)",
            r"(?:^|\n)(\d{1,2}:\d{2}(?::\d{2})?)\s*[:\-–—]?\s*(.+?)(?=\n|$)",
        ]

        for pattern in timestamp_patterns:
            matches = re.findall(pattern, description, re.MULTILINE | re.IGNORECASE)
            if matches:
                for timestamp, topic in matches:
                    topic = topic.strip()
                    if topic and len(topic) > 3:  # Filter out very short topics
                        topics.append({"timestamp": timestamp, "topic": topic})
                break  # Use first pattern that finds matches

        # If no timestamp patterns found, look for numbered lists or bullet points
        if not topics:
            bullet_patterns = [
                r"(?:^|\n)(?:\d+\.?\s*|[-•*]\s*)(.+?)(?=\n|$)",
                r"(?:^|\n)(?:Chapter \d+|Section \d+)[:\-–—]?\s*(.+?)(?=\n|$)",
            ]

            for pattern in bullet_patterns:
                matches = re.findall(pattern, description, re.MULTILINE | re.IGNORECASE)
                if matches:
                    for i, topic in enumerate(matches):
                        topic = topic.strip()
                        if topic and len(topic) > 3:
                            topics.append({"timestamp": f"Section {i+1}", "topic": topic})
                    break

        return topics
