import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


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
