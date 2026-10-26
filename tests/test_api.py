from collections.abc import Callable

import httpx
import pytest
from fastapi.testclient import TestClient

from app.client import PortalClient
from app.main import create_app


def make_app(
    handler: Callable[[httpx.Request], httpx.Response],
) -> TestClient:
    portal_client = PortalClient(
        "https://portal.example.invalid",
        transport=httpx.MockTransport(handler),
    )
    return TestClient(create_app(portal_client=portal_client))


def json_response(payload: object, status_code: int = 200) -> httpx.Response:
    return httpx.Response(
        status_code,
        json=payload,
        headers={"content-type": "application/json"},
    )


def test_search_meters_forwards_verified_query_and_page():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/portal/meters/search"
        assert request.url.params["q"] == "J100003"
        assert request.url.params["page"] == "2"
        return json_response(
            {
                "data": [
                    {
                        "meterId": "J100003",
                        "serialNo": "L&84997",
                        "make": "Genus",
                        "phaseType": "single",
                        "installStatus": "Installed",
                        "dtCode": "DT-004",
                    }
                ],
                "total": 1,
                "page": 2,
                "pageSize": 20,
            }
        )

    with make_app(handler) as client:
        response = client.get("/meters", params={"q": "J100003", "page": 2})

    assert response.status_code == 200
    assert response.json()["data"][0]["meterId"] == "J100003"
    assert response.json()["pageSize"] == 20


def test_search_meters_returns_empty_results():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/portal/meters/search"
        assert request.url.params["q"] == "no-match"
        return json_response(
            {"data": [], "total": 0, "page": 1, "pageSize": 20}
        )

    with make_app(handler) as client:
        response = client.get("/meters", params={"q": "no-match"})

    assert response.status_code == 200
    assert response.json() == {
        "data": [],
        "total": 0,
        "page": 1,
        "pageSize": 20,
    }


def test_meter_geo_forwards_identifier_and_response():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/portal/meters/J100003/geo"
        return json_response(
            {"data": {"latitude": "26.85", "longitude": "75.81"}}
        )

    with make_app(handler) as client:
        response = client.get("/meters/J100003/geo")

    assert response.status_code == 200
    assert response.json() == {
        "data": {"latitude": "26.85", "longitude": "75.81"}
    }


def test_meter_energy_returns_readings_and_empty_results():
    payloads = iter(
        [
            {
                "data": [
                    {
                        "timestamp": "2026-06-30 00:00",
                        "kwh": "28274.69",
                        "kvah": "30536.67",
                        "voltR": "224",
                    }
                ]
            },
            {"data": []},
        ]
    )

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/portal/meters/J100003/energy"
        return json_response(next(payloads))

    with make_app(handler) as client:
        response = client.get("/meters/J100003/energy")
        empty_response = client.get("/meters/J100003/energy")

    assert response.status_code == 200
    assert response.json()["data"][0]["voltR"] == "224"
    assert empty_response.status_code == 200
    assert empty_response.json() == {"data": []}


def test_transformers_forwards_page_and_response():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/portal/dts"
        assert request.url.params["page"] == "2"
        return json_response(
            {
                "data": [
                    {
                        "code": "DT-example",
                        "name": "Example DT",
                        "feederCode": "F-example",
                        "capacityKva": 100,
                    }
                ],
                "total": 40,
                "page": 2,
                "pageSize": 20,
            }
        )

    with make_app(handler) as client:
        response = client.get("/transformers", params={"page": 2})

    assert response.status_code == 200
    assert response.json()["data"][0]["capacityKva"] == 100


def test_transformers_returns_empty_results():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/portal/dts"
        return json_response(
            {"data": [], "total": 0, "page": 1, "pageSize": 20}
        )

    with make_app(handler) as client:
        response = client.get("/transformers")

    assert response.status_code == 200
    assert response.json()["data"] == []


def test_non_positive_page_is_rejected_before_upstream_request():
    called = False

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal called
        assert request.url.path == "/portal/meters/search"
        called = True
        return json_response({})

    with make_app(handler) as client:
        response = client.get("/meters", params={"page": 0})

    assert response.status_code == 422
    assert not called


@pytest.mark.parametrize("status_code", [401, 403, 500])
def test_upstream_http_failures_return_generic_bad_gateway(status_code):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/portal/meters/search"
        return httpx.Response(status_code, text="unexposed upstream body")

    with make_app(handler) as client:
        response = client.get("/meters")

    assert response.status_code == 502
    assert response.json() == {"detail": "Portal request failed"}
    assert "unexposed upstream body" not in response.text


def test_invalid_upstream_schema_returns_bad_gateway_without_body():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/portal/meters/search"
        return json_response({"data": [], "total": "not-a-number"})

    with make_app(handler) as client:
        response = client.get("/meters")

    assert response.status_code == 502
    assert response.json() == {"detail": "Portal request failed"}


def test_malformed_upstream_json_returns_bad_gateway():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/portal/meters/search"
        return httpx.Response(
            200,
            content=b"{invalid json",
            headers={"content-type": "application/json"},
        )

    with make_app(handler) as client:
        response = client.get("/meters")

    assert response.status_code == 502
    assert response.json() == {"detail": "Portal request failed"}


def test_upstream_timeout_returns_gateway_timeout():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("private timeout detail", request=request)

    with make_app(handler) as client:
        response = client.get("/meters")

    assert response.status_code == 504
    assert response.json() == {"detail": "Portal request timed out"}


def test_client_does_not_send_unverified_authentication_headers():
    def handler(request: httpx.Request) -> httpx.Response:
        assert "cookie" not in request.headers
        assert "authorization" not in request.headers
        return json_response(
            {"data": [], "total": 0, "page": 1, "pageSize": 20}
        )

    with make_app(handler) as client:
        response = client.get("/meters")

    assert response.status_code == 200


def test_upstream_connection_error_returns_generic_bad_gateway():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("private connection detail", request=request)

    with make_app(handler) as client:
        response = client.get("/meters")

    assert response.status_code == 502
    assert response.json() == {"detail": "Portal request failed"}
    assert "private connection detail" not in response.text


def test_hierarchy_route_is_not_claimed_without_portal_contract():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/portal/meters/search"
        raise AssertionError("No upstream request should be made")

    with make_app(handler) as client:
        response = client.get("/hierarchy")

    assert response.status_code == 404
