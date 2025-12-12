import json
import asyncio
import os
from datetime import datetime
from db import get_pool

if not os.path.exists("data/videos.json"):
    print("ОШИБКА: положи data/videos.json в корень проекта!")
    exit(1)

def parse_datetime(s: str):
    """Парсим ISO-формат с таймзоной и без"""
    if not s:
        return None
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s.replace("Z", "+00:00"))

async def load():
    pool = await get_pool()

    with open("data/videos.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    videos = data["videos"] if isinstance(data, dict) and "videos" in data else data

    print(f"Загружаем {len(videos)} видео...")

    async with pool.acquire() as conn:
        async with conn.transaction():
            for i, video in enumerate(videos, 1):
                video_created_at = parse_datetime(video['video_created_at'])

                await conn.execute("""
                    INSERT INTO videos (id, creator_id, video_created_at, views_count, likes_count, comments_count, reports_count)
                    VALUES ($1,$2,$3,$4,$5,$6,$7)
                    ON CONFLICT (id) DO UPDATE SET
                        views_count = EXCLUDED.views_count,
                        likes_count = EXCLUDED.likes_count,
                        comments_count = EXCLUDED.comments_count,
                        reports_count = EXCLUDED.reports_count;
                """,
                video['id'], video['creator_id'], video_created_at,
                video['views_count'], video['likes_count'],
                video['comments_count'], video['reports_count'])

                for snap in video.get('snapshots', []):
                    snap_created_at = parse_datetime(snap['created_at'])

                    await conn.execute("""
                        INSERT INTO video_snapshots
                        (id, video_id, views_count, likes_count, comments_count, reports_count,
                         delta_views_count, delta_likes_count, delta_comments_count, delta_reports_count, created_at)
                        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
                        ON CONFLICT (id) DO NOTHING;
                    """,
                    
                    snap['id'], video['id'],
                    snap.get('views_count',0), snap.get('likes_count',0),
                    snap.get('comments_count',0), snap.get('reports_count',0),
                    snap.get('delta_views_count',0), snap.get('delta_likes_count',0),
                    snap.get('delta_comments_count',0), snap.get('delta_reports_count',0),
                    snap_created_at
                    )

                if i % 50 == 0:
                    print(f"Загружено {i} видео...")

if __name__ == "__main__":
    asyncio.run(load())