import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_ROOT = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_ROOT))

from check_tool_map import validate_tool_map
from check_rag_registry import validate_rag_registry
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
