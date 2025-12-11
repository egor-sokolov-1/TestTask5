import json
import psycopg
from datetime import datetime

with open("data/videos.json") as f:
    data = json.load(f)

with psycopg.connect(DATABASE_URL) as conn:
    with conn.cursor() as cur:
        for video in data:
            cur.execute("""
                INSERT INTO videos VALUES (%s,%s,%s,%s,%s,%s,%s,NOW(),NOW())
                ON CONFLICT (id) DO UPDATE SET
                    views_count = EXCLUDED.views_count,
                    likes_count = EXCLUDED.likes_count,
                    comments_count = EXCLUDED.comments_count,
                    reports_count = EXCLUDED.reports_count;
            """, (
                video['id'], video['creator_id'], video['video_created_at'],
                video['views_count'], video['likes_count'],
                video['comments_count'], video['reports_count']
            ))

            for snap in video.get('snapshots', []):
                cur.execute("""
                    INSERT INTO video_snapshots VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
                    ON CONFLICT (id) DO NOTHING;
                """, (
                    snap['id'], video['id'],
                    snap['views_count'], snap['likes_count'], snap['comments_count'], snap['reports_count'],
                    snap['delta_views_count'], snap['delta_likes_count'],
                    snap['delta_comments_count'], snap['delta_reports_count'],
                    snap['created_at']
                ))
    conn.commit()