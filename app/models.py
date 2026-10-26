from enum import Enum
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator


class PhaseType(str, Enum):
    single = "single"
    three = "three"


class InstallStatus(str, Enum):
    Installed = "Installed"
    Faulty = "Faulty"
    Decommissioned = "Decommissioned"


class InstallType(str, Enum):
    WholeCurrent = "Whole Current"
    CTOperated = "CT Operated"


class Build(str, Enum):
    legacy = "legacy"
    v2 = "v2"


class HierarchyNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    code: str | None = None

    @field_validator("name", "code", mode="before")
    @classmethod
    def empty_strings_are_none(cls, value: Any) -> Any:
        return None if value == "" else value


class Hierarchy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    zone: HierarchyNode
    circle: HierarchyNode
    division: HierarchyNode
    subdivision: HierarchyNode
    substation: HierarchyNode
    feeder: HierarchyNode
    dt: HierarchyNode


class Geo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lat: float
    lng: float


class Meter(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    meter_id: str = Field(validation_alias="meterId")
    serial_no: str = Field(validation_alias="serialNo")
    make: str
    phase_type: PhaseType = Field(validation_alias="phaseType")
    install_status: InstallStatus = Field(validation_alias="installStatus")
    install_type: InstallType = Field(validation_alias="installType")
    build: Build
    dt_code: str = Field(validation_alias="dtCode")
    hierarchy: Hierarchy
    geo: Geo
    data_quality_flags: list[str] = Field(default_factory=list)


class MeterSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    meter_id: str = Field(alias="meterId")
    serial_no: str = Field(alias="serialNo")
    make: str
    phase_type: PhaseType = Field(alias="phaseType")
    install_status: InstallStatus = Field(alias="installStatus")
    dt_code: str = Field(alias="dtCode")


class MeterLocation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    latitude: str
    longitude: str


class MeterLocationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    data: MeterLocation


class EnergyReading(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    timestamp: str
    kwh: str
    kvah: str
    volt_r: str = Field(alias="voltR")


class EnergyResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    data: list[EnergyReading]


class DistributionTransformer(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    code: str
    name: str
    feeder_code: str = Field(alias="feederCode")
    capacity_kva: float = Field(alias="capacityKva")


PageItem = TypeVar("PageItem")


class PortalPage(BaseModel, Generic[PageItem]):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    data: list[PageItem]
    total: int
    page: int
    page_size: int = Field(alias="pageSize")


def parse_export(raw: list[dict]) -> list[Meter]:
    meters: list[Meter] = []

    for index, record in enumerate(raw):
        try:
            meter = Meter.model_validate(record)
        except ValidationError as exc:
            raise ValueError(
                f"Invalid meter export record at index {index}: {exc}"
            ) from exc

        for node_name in (
            "zone",
            "circle",
            "division",
            "subdivision",
            "substation",
            "feeder",
            "dt",
        ):
            node = getattr(meter.hierarchy, node_name)
            for field_name in ("name", "code"):
                if getattr(node, field_name) is None:
                    flag = f"hierarchy.{node_name}.{field_name}_missing"
                    if flag not in meter.data_quality_flags:
                        meter.data_quality_flags.append(flag)

        meters.append(meter)

    return meters