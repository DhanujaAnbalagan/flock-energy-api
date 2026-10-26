import json
from pathlib import Path

import pytest

from app.models import parse_export


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "meter-export.json"


@pytest.fixture(scope="module")
def raw_export() -> list[dict]:
    with FIXTURE_PATH.open(encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


@pytest.fixture(scope="module")
def meters(raw_export):
    return parse_export(raw_export)


def test_parses_all_403_fixture_records(raw_export, meters):
    assert len(raw_export) == 403
    assert len(meters) == len(raw_export)


def test_meter_ids_are_unique(meters):
    meter_ids = [meter.meter_id for meter in meters]
    assert len(meter_ids) == len(set(meter_ids))


def test_missing_feeder_code_is_flagged(meters):
    meter = next(meter for meter in meters if meter.meter_id == "J100044")

    assert meter.hierarchy.feeder.code is None
    assert "hierarchy.feeder.code_missing" in meter.data_quality_flags


def test_empty_hierarchy_codes_become_none(raw_export, meters):
    for raw_record, meter in zip(raw_export, meters):
        for node_name in (
            "zone",
            "circle",
            "division",
            "subdivision",
            "substation",
            "feeder",
            "dt",
        ):
            if raw_record["hierarchy"][node_name]["code"] == "":
                assert getattr(meter.hierarchy, node_name).code is None


def test_j100003_serial_number(meters):
    meter = next(meter for meter in meters if meter.meter_id == "J100003")

    assert meter.serial_no == "L&84997"


def test_missing_hierarchy_names_are_flagged(meters):
    meter = next(meter for meter in meters if meter.meter_id == "J100162")

    assert meter.hierarchy.feeder.name is None
    assert "hierarchy.feeder.name_missing" in meter.data_quality_flags


def test_invalid_record_is_reported_not_dropped(raw_export):
    invalid_record = raw_export[0].copy()
    del invalid_record["meterId"]

    with pytest.raises(ValueError, match=r"Invalid meter export record at index 0"):
        parse_export([invalid_record])
