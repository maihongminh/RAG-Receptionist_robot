import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_ROOT = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_ROOT))

from check_tool_map import validate_tool_map
from check_rag_registry import validate_rag_registry
from build_qdrant_index import plan_incremental_sync
from rag_index_manifest import build_manifest_rows
from rag_documents import RAG_DOCUMENT_SOURCES, build_content_hash, normalize_rag_document


def test_app_contract_has_unique_views_and_columns():
    contract_path = PROJECT_ROOT / "db" / "app" / "contract.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))

    assert contract["schema"] == "robo_app"
    view_names = [view["name"] for view in contract["views"]]
    assert len(view_names) == len(set(view_names))

    for view in contract["views"]:
        assert view["access_level"] in {"public", "operational", "private"}
        assert view["source_tables"]
        assert view["columns"]
        column_names = [column["name"] for column in view["columns"]]
        assert len(column_names) == len(set(column_names))
        assert "id" in column_names


def test_clinic_domain_tools_do_not_query_raw_schema_directly():
    clinic_domain_dir = PROJECT_ROOT / "backend" / "app" / "domains" / "clinic"
    checked_files = [
        path
        for path in clinic_domain_dir.rglob("*.py")
        if path.name != "__init__.py"
    ]
    assert checked_files

    for path in checked_files:
        assert "robo_raw." not in path.read_text(encoding="utf-8"), path


def test_tool_map_matches_app_contract_and_policy_guard():
    contract = json.loads((PROJECT_ROOT / "db" / "app" / "contract.json").read_text(encoding="utf-8"))
    tool_map = json.loads((PROJECT_ROOT / "db" / "app" / "tool_map.json").read_text(encoding="utf-8"))

    assert validate_tool_map(contract, tool_map) == []


def test_rag_registry_is_valid():
    assert validate_rag_registry() == []


def test_rag_document_normalization_adds_production_metadata():
    source = RAG_DOCUMENT_SOURCES[0]
    document = normalize_rag_document(
        {
            "source_id": "article-1",
            "topic": "checkin",
            "title": "Check-in",
            "title_vi": "Quy trinh check-in",
            "content": "Patient check-in",
            "content_vi": "Benh nhan lam thu tuc check-in",
        },
        source,
    )

    assert document["source"] == source.source_name
    assert document["source_table"] == source.source_view
    assert document["source_view"] == source.source_view
    assert document["source_tables"] == list(source.source_tables)
    assert document["domain"] == "clinic"
    assert document["access_level"] == "public"
    assert document["visibility"] == "public"
    assert document["language"] == "vi"
    assert document["clinic_id"] is None
    assert document["document_type"] == "knowledge_article"
    assert document["content_hash"] == build_content_hash(document)
    assert len(document["content_hash"]) == 64


def test_rag_index_manifest_schema_exists():
    schema_path = PROJECT_ROOT / "db" / "rag" / "schema.sql"

    assert schema_path.exists()
    schema_sql = schema_path.read_text(encoding="utf-8")
    assert "CREATE SCHEMA IF NOT EXISTS robo_rag" in schema_sql
    assert "CREATE TABLE IF NOT EXISTS robo_rag.index_manifest" in schema_sql


def test_rag_index_manifest_rows_are_derived_from_qdrant_payload():
    rows = build_manifest_rows(
        [
            {
                "point_id": "point-1",
                "payload": {
                    "qdrant_collection": "clinic_knowledge",
                    "source": "knowledge_articles",
                    "source_table": "robo_app.knowledge_articles",
                    "source_view": "robo_app.knowledge_articles",
                    "source_id": "article-1",
                    "chunk_index": 2,
                    "content_hash": "abc123",
                    "domain": "clinic",
                    "access_level": "public",
                    "visibility": "public",
                    "language": "vi",
                    "document_type": "knowledge_article",
                    "updated_at": "2026-06-16T00:00:00Z",
                },
            }
        ]
    )

    assert rows == [
        {
            "id": "clinic_knowledge:knowledge_articles:article-1:2",
            "qdrant_collection": "clinic_knowledge",
            "source": "knowledge_articles",
            "source_table": "robo_app.knowledge_articles",
            "source_view": "robo_app.knowledge_articles",
            "source_id": "article-1",
            "chunk_index": 2,
            "point_id": "point-1",
            "content_hash": "abc123",
            "domain": "clinic",
            "clinic_id": None,
            "access_level": "public",
            "visibility": "public",
            "language": "vi",
            "document_type": "knowledge_article",
            "source_updated_at": "2026-06-16T00:00:00Z",
        }
    ]


def test_rag_incremental_plan_detects_changed_new_and_stale_documents():
    rows = [
        {
            "source": "knowledge_articles",
            "source_id": "same",
            "content_hash": "hash-same",
        },
        {
            "source": "knowledge_articles",
            "source_id": "changed",
            "content_hash": "hash-new",
        },
        {
            "source": "knowledge_articles",
            "source_id": "new",
            "content_hash": "hash-new-doc",
        },
    ]
    manifest = {
        ("knowledge_articles", "same"): {
            "content_hashes": ["hash-same"],
            "point_ids": ["point-same"],
        },
        ("knowledge_articles", "changed"): {
            "content_hashes": ["hash-old"],
            "point_ids": ["point-changed-old"],
        },
        ("knowledge_articles", "stale"): {
            "content_hashes": ["hash-stale"],
            "point_ids": ["point-stale-1", "point-stale-2"],
        },
    }

    plan = plan_incremental_sync(rows, manifest)

    assert [row["source_id"] for row in plan.unchanged] == ["same"]
    assert [row["source_id"] for row in plan.changed_or_new] == ["changed", "new"]
    assert plan.stale_keys == {("knowledge_articles", "stale")}
    assert plan.stale_point_ids == ["point-stale-1", "point-stale-2"]
