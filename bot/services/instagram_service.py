import asyncio
import tempfile
from pathlib import Path

import yt_dlp


_PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


class InstagramDownloadError(Exception):
    pass


def _download(url: str, tmp_dir: str) -> tuple[Path, str]:
    opts = {
        "outtmpl": f"{tmp_dir}/%(id)s.%(ext)s",
        "quiet": True,
        "no_warnings": True,
        "max_filesize": 50 * 1024 * 1024,  # Telegram limit
    }

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
    except Exception as exc:
        raise InstagramDownloadError(str(exc)) from exc

    path = Path(filename)
    if not path.exists():
        raise InstagramDownloadError("downloaded file not found")

    media_type = "photo" if path.suffix.lower() in _PHOTO_EXTENSIONS else "video"
    return path, media_type


async def download_instagram(url: str) -> tuple[Path, str, str]:
    """Download media from an Instagram URL.

    Returns (file_path, media_type, tmp_dir) so caller can clean up tmp_dir.
    """
    tmp_dir = tempfile.mkdtemp(prefix="ig_")
    path, media_type = await asyncio.to_thread(_download, url, tmp_dir)
    return path, media_type, tmp_dir
