import json
import asyncio
import os
from db import init_pool, pool  
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

async def load():
    await init_pool()  

    with open("data/videos.json", "r", encoding="utf-8") as f:
        videos = json.load(f)

    async with pool.acquire() as conn:
        async with conn.transaction():
            for video in videos:
                await conn.execute("""
                    INSERT INTO videos 
                    (id, creator_id, video_created_at, views_count, likes_count, comments_count, reports_count)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (id) DO UPDATE SET
                        views_count = EXCLUDED.views_count,
                        likes_count = EXCLUDED.likes_count,
                        comments_count = EXCLUDED.comments_count,
                        reports_count = EXCLUDED.reports_count;
                """, video['id'], video['creator_id'], video['video_created_at'],
                   video['views_count'], video['likes_count'],
                   video['comments_count'], video['reports_count'])

                for snap in video.get('snapshots', []):
                    await conn.execute("""
                        INSERT INTO video_snapshots 
                        (id, video_id, views_count, likes_count, comments_count, reports_count,
                         delta_views_count, delta_likes_count, delta_comments_count, delta_reports_count,
                         created_at)
                        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
                        ON CONFLICT (id) DO NOTHING;
                    """, snap['id'], video['id'],
                       snap['views_count'], snap['likes_count'], snap['comments_count'], snap['reports_count'],
                       snap.get('delta_views_count', 0), snap.get('delta_likes_count', 0),
                       snap.get('delta_comments_count', 0), snap.get('delta_reports_count', 0),
                       snap['created_at'])

    print("Данные успешно загружены")

if __name__ == "__main__":
    asyncio.run(load())