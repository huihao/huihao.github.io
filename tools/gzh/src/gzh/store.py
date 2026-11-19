"""SQLite 持久化层。

保存四类数据：

* ``articles``  —— 内容池与发布状态（幂等去重的依据是 content_hash 唯一索引）。
* ``runs``      —— 每次调度触发的执行记录，用于复盘与配额统计。
* ``events``    —— 结构化事件流水。
* ``blobs``     —— 素材（封面/正文图片）缓存，避免重复上传。
* ``kv``        —— 键值状态（access_token 缓存、上次触发时间等）。
"""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from .models import (
    STATUS_APPROVED,
    STATUS_BLOCKED,
    STATUS_FAILED,
    STATUS_PENDING,
    STATUS_RENDERED,
    Article,
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS articles (
    id                TEXT PRIMARY KEY,
    content_hash      TEXT UNIQUE,
    plan_id           TEXT NOT NULL DEFAULT '',
    account_id        TEXT NOT NULL DEFAULT '',
    title             TEXT NOT NULL DEFAULT '',
    digest            TEXT NOT NULL DEFAULT '',
    author            TEXT NOT NULL DEFAULT '',
    source_type       TEXT NOT NULL DEFAULT '',
    source_key        TEXT NOT NULL DEFAULT '',
    source_url        TEXT NOT NULL DEFAULT '',
    tags              TEXT NOT NULL DEFAULT '[]',
    markdown          TEXT NOT NULL DEFAULT '',
    source_html       TEXT NOT NULL DEFAULT '',
    content_html      TEXT NOT NULL DEFAULT '',
    cover             TEXT NOT NULL DEFAULT '',
    thumb_media_id    TEXT NOT NULL DEFAULT '',
    media_id          TEXT NOT NULL DEFAULT '',
    publish_id        TEXT NOT NULL DEFAULT '',
    wechat_article_id TEXT NOT NULL DEFAULT '',
    status            TEXT NOT NULL DEFAULT 'pending',
    error             TEXT NOT NULL DEFAULT '',
    attempts          INTEGER NOT NULL DEFAULT 0,
    extra             TEXT NOT NULL DEFAULT '{}',
    created_at        TEXT NOT NULL DEFAULT '',
    updated_at        TEXT NOT NULL DEFAULT '',
    published_at      TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_articles_status ON articles(status);
CREATE INDEX IF NOT EXISTS idx_articles_plan   ON articles(plan_id, status);
CREATE INDEX IF NOT EXISTS idx_articles_acct   ON articles(account_id, status);

CREATE TABLE IF NOT EXISTS runs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id     TEXT NOT NULL DEFAULT '',
    account_id  TEXT NOT NULL DEFAULT '',
    mode        TEXT NOT NULL DEFAULT '',
    trigger     TEXT NOT NULL DEFAULT '',
    started_at  TEXT NOT NULL DEFAULT '',
    finished_at TEXT NOT NULL DEFAULT '',
    status      TEXT NOT NULL DEFAULT '',
    published   INTEGER NOT NULL DEFAULT 0,
    skipped     INTEGER NOT NULL DEFAULT 0,
    failed      INTEGER NOT NULL DEFAULT 0,
    error       TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS events (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    ts         TEXT NOT NULL,
    level      TEXT NOT NULL DEFAULT 'INFO',
    component  TEXT NOT NULL DEFAULT '',
    account_id TEXT NOT NULL DEFAULT '',
    plan_id    TEXT NOT NULL DEFAULT '',
    article_id TEXT NOT NULL DEFAULT '',
    message    TEXT NOT NULL DEFAULT '',
    data       TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts);

CREATE TABLE IF NOT EXISTS blobs (
    kind       TEXT NOT NULL,
    sha256     TEXT NOT NULL,
    remote_id  TEXT NOT NULL DEFAULT '',
    url        TEXT NOT NULL DEFAULT '',
    meta       TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (kind, sha256)
);

CREATE TABLE IF NOT EXISTS kv (
    key        TEXT PRIMARY KEY,
    value      TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL DEFAULT ''
);
"""

#: 计入「已发布」配额的终态。
PUBLISHED_STATUSES = ("published", "mass_sent")


def now_iso() -> str:
    """本地时区的 ISO 时间戳。"""
    return datetime.now().astimezone().isoformat(timespec="seconds")


class Store:
    """线程安全的 SQLite 封装（单进程多线程场景下加锁）。"""

    def __init__(self, db_path: Path | str) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False, timeout=30)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    # ------------------------------------------------------------------ 基础
    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def __enter__(self) -> "Store":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def _execute(self, sql: str, params: Iterable[Any] = ()) -> sqlite3.Cursor:
        with self._lock:
            return self._conn.execute(sql, tuple(params))

    def _commit(self) -> None:
        with self._lock:
            self._conn.commit()

    # -------------------------------------------------------------- 文章池
    def upsert_article(self, article: Article) -> bool:
        """写入文章；content_hash 已存在时返回 False（实现幂等去重）。"""
        now = now_iso()
        with self._lock:
            existing = self._conn.execute(
                "SELECT id FROM articles WHERE content_hash = ?", (article.content_hash,)
            ).fetchone()
            if existing:
                return False
            self._conn.execute(
                """
                INSERT INTO articles (
                    id, content_hash, plan_id, account_id, title, digest, author,
                    source_type, source_key, source_url, tags, markdown, source_html,
                    content_html, cover, thumb_media_id, media_id, publish_id,
                    wechat_article_id, status, error, attempts, extra,
                    created_at, updated_at, published_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    article.id,
                    article.content_hash,
                    article.plan_id,
                    article.account_id,
                    article.title,
                    article.digest,
                    article.author,
                    article.source_type,
                    article.source_key,
                    article.source_url,
                    json.dumps(article.tags, ensure_ascii=False),
                    article.markdown,
                    article.source_html,
                    article.content_html,
                    article.cover,
                    article.thumb_media_id,
                    article.media_id,
                    article.publish_id,
                    article.article_id,
                    article.status,
                    article.error,
                    article.attempts,
                    json.dumps(article_extra(article), ensure_ascii=False, default=str),
                    article.created_at or now,
                    now,
                    "",
                ),
            )
            self._conn.commit()
        return True

    def update_article(self, article_id: str, **fields: Any) -> None:
        """按字段更新文章。字段名与列名一致，tags/extra 自动序列化。"""
        if not fields:
            return
        assignments: list[str] = []
        values: list[Any] = []
        for key, value in fields.items():
            if key in ("tags", "extra"):
                value = json.dumps(value, ensure_ascii=False, default=str)
            assignments.append(f"{key} = ?")
            values.append(value)
        assignments.append("updated_at = ?")
        values.append(now_iso())
        values.append(article_id)
        with self._lock:
            self._conn.execute(
                f"UPDATE articles SET {', '.join(assignments)} WHERE id = ?", values
            )
            self._conn.commit()

    def get_article(self, article_id: str) -> Article | None:
        row = self._execute("SELECT * FROM articles WHERE id = ?", (article_id,)).fetchone()
        return _row_to_article(row) if row else None

    def find_by_hash(self, content_hash: str) -> Article | None:
        row = self._execute(
            "SELECT * FROM articles WHERE content_hash = ?", (content_hash,)
        ).fetchone()
        return _row_to_article(row) if row else None

    def list_articles(
        self,
        *,
        status: str | None = None,
        plan_id: str | None = None,
        account_id: str | None = None,
        limit: int | None = None,
    ) -> list[Article]:
        clauses: list[str] = []
        params: list[Any] = []
        if status:
            if status == "queue":
                clauses.append("status IN (?, ?, ?)")
                params.extend([STATUS_PENDING, STATUS_APPROVED, STATUS_RENDERED])
            else:
                clauses.append("status = ?")
                params.append(status)
        if plan_id:
            clauses.append("plan_id = ?")
            params.append(plan_id)
        if account_id:
            clauses.append("account_id = ?")
            params.append(account_id)
        sql = "SELECT * FROM articles"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY created_at ASC, id ASC"
        if limit:
            sql += f" LIMIT {int(limit)}"
        rows = self._execute(sql, params).fetchall()
        return [_row_to_article(row) for row in rows]

    def pick_candidates(
        self,
        plan_id: str,
        *,
        limit: int,
        strategy: str = "oldest",
        require_tags: Iterable[str] = (),
        exclude_tags: Iterable[str] = (),
        require_approval: bool = False,
    ) -> list[Article]:
        """按策略挑出待发布文章。

        顺序：oldest（先进先出）/ newest（后进先出）/ random（随机打散）。
        """
        statuses = [STATUS_PENDING, STATUS_RENDERED, STATUS_APPROVED]
        placeholders = ", ".join("?" for _ in statuses)
        sql = f"SELECT * FROM articles WHERE plan_id = ? AND status IN ({placeholders})"
        params: list[Any] = [plan_id, *statuses]
        order = {
            "oldest": "created_at ASC, id ASC",
            "newest": "created_at DESC, id DESC",
            "random": "RANDOM()",
        }.get(strategy, "created_at ASC, id ASC")
        sql += f" ORDER BY {order}"
        rows = self._execute(sql, params).fetchall()
        articles = [_row_to_article(row) for row in rows]

        require = {t.strip() for t in require_tags if t and t.strip()}
        exclude = {t.strip() for t in exclude_tags if t and t.strip()}
        if require or exclude:
            filtered = []
            for article in articles:
                tags = {t.strip() for t in article.tags}
                if require and not (tags & require):
                    continue
                if exclude and (tags & exclude):
                    continue
                filtered.append(article)
            articles = filtered
        return articles[:limit]

    def count_published_today(self, account_id: str, day: str | None = None) -> int:
        """统计某账号当日已发布（published / mass_sent）篇数。"""
        day = day or datetime.now().astimezone().strftime("%Y-%m-%d")
        row = self._execute(
            """
            SELECT COUNT(*) AS n FROM articles
            WHERE account_id = ? AND status IN (?, ?) AND substr(published_at, 1, 10) = ?
            """,
            (account_id, *PUBLISHED_STATUSES, day),
        ).fetchone()
        return int(row["n"]) if row else 0

    def count_status_today(
        self, account_id: str, status: str, day: str | None = None
    ) -> int:
        """统计某账号当日处于指定状态的篇数（用于分模式配额）。"""
        day = day or datetime.now().astimezone().strftime("%Y-%m-%d")
        row = self._execute(
            """
            SELECT COUNT(*) AS n FROM articles
            WHERE account_id = ? AND status = ? AND substr(published_at, 1, 10) = ?
            """,
            (account_id, status, day),
        ).fetchone()
        return int(row["n"]) if row else 0

    # -------------------------------------------------------------- 执行记录
    def start_run(self, plan_id: str, account_id: str, mode: str, trigger: str) -> int:
        cursor = self._execute(
            """
            INSERT INTO runs (plan_id, account_id, mode, trigger, started_at, status)
            VALUES (?,?,?,?,?,?)
            """,
            (plan_id, account_id, mode, trigger, now_iso(), "running"),
        )
        self._commit()
        return int(cursor.lastrowid or 0)

    def finish_run(
        self,
        run_id: int,
        *,
        status: str,
        published: int = 0,
        skipped: int = 0,
        failed: int = 0,
        error: str = "",
    ) -> None:
        self._execute(
            """
            UPDATE runs SET finished_at = ?, status = ?, published = ?, skipped = ?,
                            failed = ?, error = ?
            WHERE id = ?
            """,
            (now_iso(), status, published, skipped, failed, error, run_id),
        )
        self._commit()

    def recent_runs(self, limit: int = 20) -> list[dict[str, Any]]:
        rows = self._execute(
            "SELECT * FROM runs ORDER BY id DESC LIMIT ?", (int(limit),)
        ).fetchall()
        return [dict(row) for row in rows]

    # ---------------------------------------------------------------- 事件
    def add_event(
        self,
        level: str,
        message: str,
        *,
        component: str = "",
        account_id: str = "",
        plan_id: str = "",
        article_id: str = "",
        data: dict[str, Any] | None = None,
    ) -> None:
        self._execute(
            """
            INSERT INTO events (ts, level, component, account_id, plan_id, article_id, message, data)
            VALUES (?,?,?,?,?,?,?,?)
            """,
            (
                now_iso(),
                level,
                component,
                account_id,
                plan_id,
                article_id,
                message,
                json.dumps(data or {}, ensure_ascii=False, default=str),
            ),
        )
        self._commit()

    def recent_events(self, limit: int = 50, level: str | None = None) -> list[dict[str, Any]]:
        sql = "SELECT * FROM events"
        params: list[Any] = []
        if level:
            sql += " WHERE level = ?"
            params.append(level)
        sql += " ORDER BY id DESC LIMIT ?"
        params.append(int(limit))
        rows = self._execute(sql, params).fetchall()
        return [dict(row) for row in rows]

    # ---------------------------------------------------------------- 素材
    def get_blob(self, kind: str, sha256: str) -> dict[str, Any] | None:
        row = self._execute(
            "SELECT * FROM blobs WHERE kind = ? AND sha256 = ?", (kind, sha256)
        ).fetchone()
        return dict(row) if row else None

    def put_blob(
        self, kind: str, sha256: str, *, remote_id: str = "", url: str = "", meta: dict[str, Any] | None = None
    ) -> None:
        self._execute(
            """
            INSERT INTO blobs (kind, sha256, remote_id, url, meta, created_at)
            VALUES (?,?,?,?,?,?)
            ON CONFLICT(kind, sha256) DO UPDATE SET remote_id = excluded.remote_id, url = excluded.url
            """,
            (kind, sha256, remote_id, url, json.dumps(meta or {}, ensure_ascii=False), now_iso()),
        )
        self._commit()

    # ------------------------------------------------------------------ kv
    def kv_get(self, key: str, default: Any = None) -> Any:
        row = self._execute("SELECT value FROM kv WHERE key = ?", (key,)).fetchone()
        if not row:
            return default
        try:
            return json.loads(row["value"])
        except json.JSONDecodeError:
            return row["value"]

    def kv_set(self, key: str, value: Any) -> None:
        self._execute(
            """
            INSERT INTO kv (key, value, updated_at) VALUES (?,?,?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
            """,
            (key, json.dumps(value, ensure_ascii=False, default=str), now_iso()),
        )
        self._commit()

    def stats(self) -> dict[str, int]:
        rows = self._execute(
            "SELECT status, COUNT(*) AS n FROM articles GROUP BY status"
        ).fetchall()
        return {row["status"]: int(row["n"]) for row in rows}


def article_extra(article: Article) -> dict[str, Any]:
    """文章里没有独立列的字段 → extra 字典（落库用）。

    articles 表没有 content_source_url / need_open_comment /
    only_fans_can_comment / publish_at 这几列，写库时必须塞进 extra，
    否则重新读出来就丢了（阅读原文链接、留言开关都会失效）。
    """
    extra = dict(article.extra or {})
    if article.content_source_url:
        extra.setdefault("content_source_url", article.content_source_url)
    if article.need_open_comment:
        extra.setdefault("need_open_comment", int(article.need_open_comment))
    if article.only_fans_can_comment:
        extra.setdefault("only_fans_can_comment", int(article.only_fans_can_comment))
    if article.publish_at:
        extra.setdefault("publish_at", article.publish_at)
    return extra


def _row_to_article(row: sqlite3.Row) -> Article:
    """数据库行 → Article 对象。"""
    article = Article(
        id=row["id"],
        title=row["title"],
        source_type=row["source_type"],
        source_key=row["source_key"],
        plan_id=row["plan_id"],
        account_id=row["account_id"],
        author=row["author"],
        digest=row["digest"],
        markdown=row["markdown"],
        source_html=row["source_html"],
        cover=row["cover"],
        source_url=row["source_url"],
        status=row["status"],
        content_hash=row["content_hash"],
        content_html=row["content_html"],
        thumb_media_id=row["thumb_media_id"],
        media_id=row["media_id"],
        publish_id=row["publish_id"],
        article_id=row["wechat_article_id"],
        error=row["error"],
        attempts=int(row["attempts"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
    try:
        article.tags = json.loads(row["tags"]) or []
    except json.JSONDecodeError:
        article.tags = []
    try:
        article.extra = json.loads(row["extra"]) or {}
    except json.JSONDecodeError:
        article.extra = {}
    # extra 里带回读原文/留言开关等没有独立列的字段
    article.content_source_url = str(article.extra.get("content_source_url", "") or "")
    article.need_open_comment = int(article.extra.get("need_open_comment", 0) or 0)
    article.only_fans_can_comment = int(article.extra.get("only_fans_can_comment", 0) or 0)
    article.publish_at = str(article.extra.get("publish_at", "") or "")
    if not article.content_hash:
        article.content_hash = row["content_hash"]
    return article
