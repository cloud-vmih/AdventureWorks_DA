import os
import json
import requests
from src.common.database import get_dwh_engine

# Determine if we are in Docker or on Host
IN_DOCKER = os.environ.get('DWH_DB_HOST') == 'postgres_dwh'
SUPERSET_HOST = 'superset' if IN_DOCKER else 'localhost'
SUPERSET_PORT = os.environ.get('SUPERSET_PORT', '8088')
BASE_URL = f"http://{SUPERSET_HOST}:{SUPERSET_PORT}"

class SupersetClient:
    def __init__(self, username="admin", password="admin"):
        self.base_url = BASE_URL
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.token = None

    def login(self):
        url = f"{self.base_url}/api/v1/security/login"
        payload = {
            "username": self.username,
            "password": self.password,
            "provider": "db",
            "refresh": True
        }
        res = self.session.post(url, json=payload)
        res.raise_for_status()
        self.token = res.json()["access_token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
        # Get CSRF token
        csrf_url = f"{self.base_url}/api/v1/security/csrf_token/"
        csrf_res = self.session.get(csrf_url)
        csrf_res.raise_for_status()
        csrf_token = csrf_res.json()["result"]
        self.session.headers.update({"X-CSRFToken": csrf_token})

    def request(self, method, endpoint, json=None, params=None):
        url = f"{self.base_url}{endpoint}"
        res = self.session.request(method, url, json=json, params=params)
        if res.status_code >= 400:
            print(f"Error {res.status_code} on {method} {endpoint}: {res.text}")
        res.raise_for_status()
        return res.json()

    def list_all(self, resource_type: str) -> list[dict]:
        results = []
        page = 0
        page_size = 100
        while True:
            endpoint = f"/api/v1/{resource_type}/"
            params = {
                "q": json.dumps({
                    "page": page,
                    "page_size": page_size
                })
            }
            res = self.request("GET", endpoint, params=params)
            count = res.get("count", 0)
            result = res.get("result", [])
            results.extend(result)
            if len(results) >= count or not result:
                break
            page += 1
        return results

def get_database_id(client: SupersetClient) -> int:
    databases = client.list_all("database")
    for db in databases:
        if db.get("database_name") == "AdventureWorks DWH":
            return int(db["id"])
    raise RuntimeError("AdventureWorks DWH database connection not found in Superset.")

def get_or_create_dataset(
    client: SupersetClient,
    database_id: int,
    schema: str,
    table_name: str,
) -> int:
    datasets = client.list_all("dataset")
    for ds in datasets:
        if ds.get("table_name") == table_name and ds.get("schema") == schema:
            return int(ds["id"])
    
    payload = {
        "database": database_id,
        "schema": schema,
        "table_name": table_name
    }
    res = client.request("POST", "/api/v1/dataset/", json=payload)
    return int(res["id"])

def get_or_create_dashboard(client: SupersetClient, title: str, slug: str, legacy_titles: set[str] = None) -> int:
    if legacy_titles is None:
        legacy_titles = set()
    accepted = {title, *legacy_titles}
    for dashboard in client.list_all("dashboard"):
        if dashboard.get("dashboard_title") in accepted:
            return int(dashboard["id"])
    response = client.request(
        "POST",
        "/api/v1/dashboard/",
        json={
            "dashboard_title": title,
            "slug": slug,
            "published": True,
            "json_metadata": json.dumps({}),
            "position_json": json.dumps({}),
        },
    )
    return int(response["id"])

def get_or_create_chart(
    client: SupersetClient,
    dashboard_id: int,
    dataset_id: int,
    slice_name: str,
    legacy_slice_names: tuple[str, ...],
    viz_type: str,
    params: dict[str, object],
) -> int:
    payload = {
        "slice_name": slice_name,
        "viz_type": viz_type,
        "datasource_id": dataset_id,
        "datasource_type": "table",
        "params": json.dumps(params),
        "dashboards": [dashboard_id],
    }
    accepted_names = {slice_name, *legacy_slice_names}
    stable_prefixes = {
        f"{name.split('|', 1)[0].strip()} |"
        for name in (slice_name, *legacy_slice_names)
        if "|" in name
    }
    for chart in client.list_all("chart"):
        owner_ids = {
            int(dashboard["id"])
            for dashboard in chart.get("dashboards") or []
            if dashboard.get("id") is not None
        }
        if dashboard_id not in owner_ids:
            continue
        chart_name = str(chart.get("slice_name") or "")
        if chart_name in accepted_names or any(
            chart_name.startswith(prefix) for prefix in stable_prefixes
        ):
            chart_id = int(chart["id"])
            client.request("PUT", f"/api/v1/chart/{chart_id}", json=payload)
            return chart_id
    response = client.request("POST", "/api/v1/chart/", json=payload)
    return int(response["id"])

def remove_stale_dashboard_charts(
    client: SupersetClient,
    dashboard_id: int,
    keep_ids: set[int],
) -> None:
    for chart in client.list_all("chart"):
        owner_ids = {
            int(dashboard["id"])
            for dashboard in chart.get("dashboards") or []
            if dashboard.get("id") is not None
        }
        chart_id = int(chart["id"])
        if dashboard_id in owner_ids and chart_id not in keep_ids:
            client.request("DELETE", f"/api/v1/chart/{chart_id}")

def simple_metric(column: str, label: str, aggregate: str = "SUM") -> dict[str, object]:
    return {
        "expressionType": "SIMPLE",
        "column": {
            "column_name": column,
        },
        "aggregate": aggregate,
        "label": label,
        "optionName": f"metric_{column}_{aggregate.lower()}"
    }

def sql_metric(expression: str, label: str, option_name: str) -> dict[str, object]:
    return {
        "expressionType": "SQL",
        "sqlExpression": expression,
        "label": label,
        "optionName": option_name,
    }

def numeric_filter(
    subject: str,
    operator: str,
    comparator: object,
    name: str,
) -> dict[str, object]:
    return {
        "clause": "WHERE",
        "comparator": comparator,
        "expressionType": "SIMPLE",
        "filterOptionName": name,
        "operator": operator,
        "sqlExpression": None,
        "subject": subject,
    }

def categorical_filter(
    subject: str,
    operator: str,
    comparator: list[object],
    name: str,
) -> dict[str, object]:
    return {
        "clause": "WHERE",
        "comparator": comparator,
        "expressionType": "SIMPLE",
        "filterOptionName": name,
        "operator": operator,
        "sqlExpression": None,
        "subject": subject,
    }

def dashboard_layout(charts: list[tuple[int, str]], sections: list[list[tuple[str, int, int]]]) -> str:
    chart_lookup = {slice_name: chart_id for chart_id, slice_name in charts}
    root_id = "ROOT_ID"
    grid_id = "GRID_ID"
    layout: dict[str, object] = {
        "DASHBOARD_VERSION_KEY": "v2",
        root_id: {"id": root_id, "type": "ROOT", "children": [grid_id]},
        grid_id: {
            "id": grid_id,
            "type": "GRID",
            "children": [],
            "parents": [root_id],
        },
    }

    row_index = 1
    for section in sections:
        row_id = f"ROW-{row_index}"
        row_index += 1
        layout[grid_id]["children"].append(row_id)
        
        chart_nodes = []
        for slice_name, width, height in section:
            if slice_name in chart_lookup:
                chart_nodes.append(f"CHART-{chart_lookup[slice_name]}")
            else:
                print(f"Warning: slice_name '{slice_name}' not found in charts lookup.")
                
        layout[row_id] = {
            "id": row_id,
            "type": "ROW",
            "children": chart_nodes,
            "meta": {"background": "BACKGROUND_TRANSPARENT"},
            "parents": [root_id, grid_id],
        }
        for slice_name, width, height in section:
            if slice_name not in chart_lookup:
                continue
            chart_id = chart_lookup[slice_name]
            node_id = f"CHART-{chart_id}"
            layout[node_id] = {
                "id": node_id,
                "type": "CHART",
                "children": [],
                "meta": {
                    "chartId": chart_id,
                    "height": height,
                    "width": width,
                    "sliceName": slice_name,
                },
                "parents": [root_id, grid_id, row_id],
            }

    return json.dumps(layout)

def build_native_filter(
    filter_id: str,
    name: str,
    column: str,
    dataset_id: int,
    excluded_chart_ids: list[int] = None,
) -> dict[str, object]:
    if excluded_chart_ids is None:
        excluded_chart_ids = []
    return {
        "id": filter_id,
        "name": name,
        "type": "filter_select",
        "controlValues": {
            "enableEmptyFilter": True,
            "defaultToFirstItem": False,
            "multiSelect": True,
            "searchAllOptions": True
        },
        "targets": [
            {
                "datasetId": dataset_id,
                "column": {
                    "name": column
                }
            }
        ],
        "defaultDataMask": {
            "extraFormData": {},
            "filterState": {},
            "ownState": {}
        },
        "cascadeParentIds": [],
        "scope": {
            "excluded": excluded_chart_ids,
            "rootPath": ["ROOT"]
        }
    }
