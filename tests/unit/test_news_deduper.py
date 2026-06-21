"""NewsDeduper 单元测试（Spec v3 §6.1.2 — M2-b）。

三层去重：
1. L1 — URL 完全一致
2. L2 — 标题 normalize 后一致
3. L3 — SimHash 距离 < 阈值（默认 3）

同事件多源汇总到 `news_events`，回填 `news_items.event_id`。
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlmodel import Session, select

from amarket.domain.models import NewsEvent, NewsItem
from amarket.domain.schemas import RawNewsItem
from amarket.repositories.news_repo import NewsRepo
from amarket.repositories.news_source_repo import NewsSourceRepo
from amarket.services.news.deduper import (
    NewsDeduper,
    compute_simhash,
    hamming_distance,
    normalize_title,
)

# --------------------------------------------------------------------------- #
# 纯函数测试（无 DB 依赖）
# --------------------------------------------------------------------------- #


def test_normalize_title_lowercases_and_strips_whitespace() -> None:
    assert normalize_title("  Hello World  ") == "helloworld"


def test_normalize_title_removes_ascii_punctuation() -> None:
    assert normalize_title("A.B,C!D?E") == "abcde"


def test_normalize_title_removes_chinese_punctuation() -> None:
    # 中文逗号、句号、引号、括号、破折号等
    raw = "央行：12月15日起，下调存款准备金率0.5%（释放约1万亿）"
    norm = normalize_title(raw)
    # 中文字符保留，标点全去
    assert "央行" in norm
    assert "12月15日起" in norm
    assert "，" not in norm
    assert "：" not in norm
    assert "（" not in norm
    assert "）" not in norm


def test_normalize_title_empty_returns_empty() -> None:
    assert normalize_title("") == ""
    assert normalize_title("   ") == ""
    assert normalize_title("！！！") == ""


def test_compute_simhash_returns_16_hex_chars() -> None:
    h = compute_simhash("hello world")
    assert isinstance(h, str)
    assert len(h) == 16
    int(h, 16)  # 验证是合法 hex


def test_compute_simhash_stable_for_same_input() -> None:
    assert compute_simhash("abc def 123") == compute_simhash("abc def 123")


def test_hamming_distance_zero_for_identical() -> None:
    h = compute_simhash("一些中文文本和数字 12345")
    assert hamming_distance(h, h) == 0


def test_hamming_distance_small_for_minor_change() -> None:
    h1 = compute_simhash("央行宣布降低存款准备金率0.5个百分点")
    h2 = compute_simhash("央行宣布降低存款准备金率0.5个百分点 ")  # 末尾空格
    assert hamming_distance(h1, h2) <= 3


def test_hamming_distance_large_for_unrelated() -> None:
    h1 = compute_simhash("央行降准0.5个百分点释放万亿资金")
    h2 = compute_simhash("特斯拉发布全新自动驾驶FSD V13")
    assert hamming_distance(h1, h2) > 10


# --------------------------------------------------------------------------- #
# DB 集成测试
# --------------------------------------------------------------------------- #


def _make_source(session: Session, code: str = "src1") -> int:
    src_repo = NewsSourceRepo(session)
    src = src_repo.upsert(code=code, name=code.upper())
    assert src.id is not None
    return src.id


def _insert_news(
    session: Session,
    source_id: int,
    *,
    msg_id: str,
    title: str,
    url: str | None = None,
    published_at: datetime | None = None,
) -> NewsItem:
    repo = NewsRepo(session)
    raw = RawNewsItem(
        source_code="src1",
        source_msg_id=msg_id,
        title=title,
        url=url,
        published_at=published_at or datetime.now(UTC),
    )
    item, _ = repo.upsert_from_raw(raw, source_id=source_id)
    return item


def test_dedupe_single_item_creates_new_event(session: Session) -> None:
    src_id = _make_source(session)
    item = _insert_news(session, src_id, msg_id="1", title="央行降准 0.5 个百分点")
    deduper = NewsDeduper(session)

    result = deduper.dedupe_batch([item])

    assert result.total == 1
    assert result.new_events == 1
    assert result.merged_into_existing == 0
    assert item.event_id is not None
    # event 已经存进 DB
    events = list(session.exec(select(NewsEvent)))
    assert len(events) == 1
    assert events[0].news_count == 1
    assert events[0].canonical_title == normalize_title("央行降准 0.5 个百分点")


def test_dedupe_same_url_joins_same_event(session: Session) -> None:
    src_id = _make_source(session)
    a = _insert_news(
        session,
        src_id,
        msg_id="1",
        title="央行降准 0.5 个百分点",
        url="https://example.com/news/a",
    )
    b = _insert_news(
        session,
        src_id,
        msg_id="2",
        title="完全不一样的标题以避免 L2 L3 干扰",
        url="https://example.com/news/a",  # 同 URL
    )
    deduper = NewsDeduper(session)

    result = deduper.dedupe_batch([a, b])

    assert result.total == 2
    assert result.new_events == 1
    assert result.merged_into_existing == 1
    assert a.event_id is not None
    assert b.event_id == a.event_id


def test_dedupe_normalized_title_match_joins_same_event(session: Session) -> None:
    src_id = _make_source(session)
    a = _insert_news(session, src_id, msg_id="1", title="央行降准0.5%", url="https://example.com/a")
    b = _insert_news(
        session,
        src_id,
        msg_id="2",
        title="  央行降准 0.5% !!!  ",  # 加空格 + 标点
        url="https://example.com/b",  # 不同 URL
    )
    deduper = NewsDeduper(session)

    result = deduper.dedupe_batch([a, b])

    assert result.new_events == 1
    assert result.merged_into_existing == 1
    assert a.event_id == b.event_id


def test_dedupe_simhash_similar_titles_join_same_event(session: Session) -> None:
    """L3 SimHash 阈值内合并。

    实测中文标题增删 1 个字 → SimHash distance ≈ 7-15。默认阈值 3 只能抓字面
    近乎相同的（normalize 后仍有 minor 差异），相似措辞需更高阈值（M2-d 评分
    会用，M2-e AI 会补语义判断）。这里显式开 15 验证 L3 机制本身有效。
    """
    src_id = _make_source(session)
    a = _insert_news(
        session,
        src_id,
        msg_id="1",
        title="美联储宣布降息25个基点",
        url="https://a.example.com/news/1",
    )
    b = _insert_news(
        session,
        src_id,
        msg_id="2",
        title="美联储宣布降息0.25%",  # 不同表述同事件
        url="https://b.example.com/news/2",  # 不同 URL（避开 L1）
    )
    deduper = NewsDeduper(session, simhash_threshold=15)

    result = deduper.dedupe_batch([a, b])

    assert result.new_events == 1
    assert result.merged_into_existing == 1
    assert a.event_id == b.event_id


def test_dedupe_unrelated_titles_create_separate_events(session: Session) -> None:
    src_id = _make_source(session)
    a = _insert_news(session, src_id, msg_id="1", title="央行降准 0.5 个百分点")
    b = _insert_news(session, src_id, msg_id="2", title="特斯拉发布 FSD V13 自动驾驶")
    c = _insert_news(session, src_id, msg_id="3", title="iPhone 18 全系采用钛合金中框")
    deduper = NewsDeduper(session)

    result = deduper.dedupe_batch([a, b, c])

    assert result.new_events == 3
    assert result.merged_into_existing == 0
    assert len({a.event_id, b.event_id, c.event_id}) == 3


def test_dedupe_outside_lookback_creates_new_event(session: Session) -> None:
    src_id = _make_source(session)
    old_time = datetime.now(UTC) - timedelta(hours=48)
    a = _insert_news(
        session, src_id, msg_id="1", title="央行降准 0.5 个百分点", published_at=old_time
    )
    deduper = NewsDeduper(session, lookback_hours=24)
    result_a = deduper.dedupe_batch([a])
    assert result_a.new_events == 1
    # 手工把 event 的 last_seen_at 拉回 48h 前（模拟历史事件）
    ev = session.exec(select(NewsEvent)).first()
    assert ev is not None
    ev.last_seen_at = old_time
    session.add(ev)
    session.commit()

    # 新 item，标题相同，但 lookback 窗口外 — 应建新 event
    b = _insert_news(session, src_id, msg_id="2", title="央行降准 0.5 个百分点")
    result_b = deduper.dedupe_batch([b])
    assert result_b.new_events == 1
    assert result_b.merged_into_existing == 0
    assert b.event_id != a.event_id


def test_dedupe_is_idempotent(session: Session) -> None:
    src_id = _make_source(session)
    a = _insert_news(session, src_id, msg_id="1", title="央行降准 0.5 个百分点")
    deduper = NewsDeduper(session)

    result_1 = deduper.dedupe_batch([a])
    first_event_id = a.event_id

    # 重跑同一 item — 不该再创建 event，也不该当成 merge
    result_2 = deduper.dedupe_batch([a])
    assert a.event_id == first_event_id
    assert result_2.new_events == 0
    assert result_2.merged_into_existing == 0
    assert result_1.new_events == 1

    # DB 里 event 仍只有 1 个
    assert len(list(session.exec(select(NewsEvent)))) == 1


def test_dedupe_handles_missing_url(session: Session) -> None:
    src_id = _make_source(session)
    a = _insert_news(session, src_id, msg_id="1", title="无 URL 的新闻一", url=None)
    b = _insert_news(session, src_id, msg_id="2", title="无 URL 的新闻二", url=None)
    deduper = NewsDeduper(session)

    result = deduper.dedupe_batch([a, b])
    # 标题完全不同 → 应分两个 event
    assert result.new_events == 2
    assert a.event_id != b.event_id


def test_dedupe_writes_content_hash_back(session: Session) -> None:
    """去重后应回填 news_items.content_hash（=SimHash hex），供后续查询。"""
    src_id = _make_source(session)
    a = _insert_news(session, src_id, msg_id="1", title="某条新闻")
    deduper = NewsDeduper(session)
    deduper.dedupe_batch([a])

    session.refresh(a)
    assert a.content_hash is not None
    assert len(a.content_hash) == 16


def test_dedupe_event_updates_news_count_and_top_source(session: Session) -> None:
    src_a_id = _make_source(session, code="srcA")
    src_b_id = _make_source(session, code="srcB")
    item_a = _insert_news(session, src_a_id, msg_id="1", title="同事件不同源 标题一致")
    item_b = _insert_news(session, src_b_id, msg_id="2", title="同事件不同源 标题一致")

    deduper = NewsDeduper(session)
    deduper.dedupe_batch([item_a, item_b])

    assert item_a.event_id == item_b.event_id
    ev = session.get(NewsEvent, item_a.event_id)
    assert ev is not None
    assert ev.news_count == 2
    # top_source 是出现频次最多的，两个各 1 → 任意一个都可接受
    assert ev.top_source in {"srcA", "srcB"}
