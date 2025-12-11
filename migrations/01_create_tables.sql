CREATE TABLE IF NOT EXISTS videos (
    id              BIGINT PRIMARY KEY,
    creator_id      BIGINT NOT NULL,
    video_created_at TIMESTAMPTZ NOT NULL,
    views_count     BIGINT NOT NULL DEFAULT 0,
    likes_count     BIGINT NOT NULL DEFAULT 0,
    comments_count  BIGINT NOT NULL DEFAULT 0,
    reports_count   BIGINT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS video_snapshots (
    id                    BIGINT PRIMARY KEY,
    video_id              BIGINT NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    views_count           BIGINT NOT NULL DEFAULT 0,
    likes_count           BIGINT NOT NULL DEFAULT 0,
    comments_count        BIGINT NOT NULL DEFAULT 0,
    reports_count         BIGINT NOT NULL DEFAULT 0,
    delta_views_count     BIGINT NOT NULL DEFAULT 0,
    delta_likes_count     BIGINT NOT NULL DEFAULT 0,
    delta_comments_count  BIGINT NOT NULL DEFAULT 0,
    delta_reports_count   BIGINT NOT NULL DEFAULT 0,
    created_at            TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_videos_creator_date ON videos(creator_id, video_created_at);
CREATE INDEX IF NOT EXISTS idx_snapshots_date ON video_snapshots(created_at);
CREATE INDEX IF NOT EXISTS idx_snapshots_video_date ON video_snapshots(video_id, created_at);