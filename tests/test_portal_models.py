import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.models import (
    DistributionTransformer,
    EnergyReading,
    MeterLocation,
    MeterSummary,
    PortalPage,
)


EXPORT_PATH = Path(__file__).parent / "fixtures" / "meter-export.json"


def test_meter_summary_accepts_fields_from_real_export():
    with EXPORT_PATH.open(encoding="utf-8") as fixture_file:
        raw_meter = json.load(fixture_file)[0]

    summary = MeterSummary.model_validate(
        {
            key: raw_meter[key]
            for key in (
                "meterId",
                "serialNo",
                "make",
                "phaseType",
                "installStatus",
                "dtCode",
            )
        }
    )

    assert summary.meter_id == raw_meter["meterId"]
    assert summary.model_dump(by_alias=True) == {
        key: raw_meter[key]
        for key in (
            "meterId",
            "serialNo",
            "make",
            "phaseType",
            "installStatus",
            "dtCode",
        )
    }


def test_meter_location_preserves_observed_string_fields():
    location = MeterLocation.model_validate(
        {"latitude": "26.85", "longitude": "75.81"}
    )

    assert location.latitude == "26.85"
    assert location.longitude == "75.81"


def test_energy_reading_maps_portal_voltr_field():
    reading = EnergyReading.model_validate(
        {
            "timestamp": "2026-06-30 00:00",
            "kwh": "28274.69",
            "kvah": "30536.67",
            "voltR": "224",
        }
    )

    assert reading.volt_r == "224"
    assert reading.model_dump(by_alias=True)["voltR"] == "224"


def test_distribution_transformer_maps_observed_fields():
    transformer = DistributionTransformer.model_validate(
        {
            "code": "DT-001",
            "name": "Example DT",
            "feederCode": "F-001",
            "capacityKva": 100,
        }
    )

    assert transformer.feeder_code == "F-001"
    assert transformer.capacity_kva == 100


def test_portal_page_uses_portal_pagination_alias():
    page = PortalPage[MeterSummary].model_validate(
        {
            "data": [
                {
                    "meterId": "example-meter",
                    "serialNo": "example-serial",
                    "make": "example-make",
                    "phaseType": "single",
                    "installStatus": "Installed",
                    "dtCode": "DT-example",
                }
            ],
            "total": 1,
            "page": 1,
            "pageSize": 20,
        }
    )

    assert len(page.data) == 1
    assert page.page_size == 20


def test_portal_response_models_reject_unobserved_extra_fields():
    with pytest.raises(ValidationError):
        MeterLocation.model_validate(
            {
                "latitude": "26.85",
                "longitude": "75.81",
                "hierarchy": {},
            }
        )
