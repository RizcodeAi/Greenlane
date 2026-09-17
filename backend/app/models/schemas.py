from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from typing import Optional
from datetime import datetime


class OrgBase(BaseModel):
    name: str
    industry: str


class OrgCreate(OrgBase):
    pass


class Org(OrgBase):
    id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class UserBase(BaseModel):
    email: str
    full_name: str
    role: str
    org_id: Optional[str] = None


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: str
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AssetBase(BaseModel):
    name: str
    asset_type: str
    org_id: str


class AssetCreate(AssetBase):
    pass


class Asset(AssetBase):
    id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# --- Voyage Schemas ---

class VoyageBase(BaseModel):
    asset_id: str
    departure_port: str
    arrival_port: str
    departure_date: datetime
    arrival_date: Optional[datetime] = None
    fuel_type: str
    fuel_consumed_mt: float
    distance_nm: float
    cargo_mt: Optional[float] = 0.0

    @field_validator("fuel_consumed_mt")
    @classmethod
    def fuel_must_be_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError("fuel_consumed_mt must be greater than 0")
        return v

    @field_validator("distance_nm")
    @classmethod
    def distance_must_be_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError("distance_nm must be greater than 0")
        return v

    @field_validator("cargo_mt")
    @classmethod
    def cargo_must_be_non_negative(cls, v):
        if v is not None and v < 0:
            raise ValueError("cargo_mt cannot be negative")
        return v

    @model_validator(mode="after")
    def arrival_after_departure(self):
        if self.arrival_date and self.departure_date and self.arrival_date <= self.departure_date:
            raise ValueError("arrival_date must be after departure_date")
        return self


class VoyageCreate(VoyageBase):
    pass


class VoyageUpdate(BaseModel):
    departure_port: Optional[str] = None
    arrival_port: Optional[str] = None
    departure_date: Optional[datetime] = None
    arrival_date: Optional[datetime] = None
    fuel_type: Optional[str] = None
    fuel_consumed_mt: Optional[float] = None
    distance_nm: Optional[float] = None
    cargo_mt: Optional[float] = None

    @field_validator("fuel_consumed_mt")
    @classmethod
    def fuel_must_be_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError("fuel_consumed_mt must be greater than 0")
        return v

    @field_validator("distance_nm")
    @classmethod
    def distance_must_be_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError("distance_nm must be greater than 0")
        return v

    @field_validator("cargo_mt")
    @classmethod
    def cargo_must_be_non_negative(cls, v):
        if v is not None and v < 0:
            raise ValueError("cargo_mt cannot be negative")
        return v

    @model_validator(mode="after")
    def arrival_after_departure(self):
        if self.arrival_date and self.departure_date and self.arrival_date <= self.departure_date:
            raise ValueError("arrival_date must be after departure_date")
        return self


class Voyage(VoyageBase):
    id: str
    org_id: str
    departed_at: Optional[datetime] = None
    arrived_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# --- Emissions Computed Schema ---

class EmissionBreakdown(BaseModel):
    co2: float
    ch4: float
    n2o: float
    sox: float
    nox: float


class EmissionsComputed(BaseModel):
    asset_id: str
    voyage_id: str
    calculation_version: int
    methodology: str
    period: dict  # {"year": int, "month": int}
    fuel_type: str
    fuel_consumed_mt: float
    emissions: EmissionBreakdown
    co2_equivalent: float
    calculated_at: datetime
    is_current: bool
    model_config = ConfigDict(from_attributes=True)


class ReportBase(BaseModel):
    title: str
    org_id: str
    report_type: str


class ReportCreate(ReportBase):
    year: int


class ReportStatusUpdate(BaseModel):
    status: str


class FleetSummarySchema(BaseModel):
    total_ships: int
    total_fuel_consumed_mt: float
    total_co2_emissions_tonnes: float
    total_transport_work_tonne_miles: float
    fleet_average_eefi: Optional[float] = None
    fuel_breakdown: dict = {}


class Report(ReportBase):
    id: str
    year: int
    status: str
    generated_at: datetime
    pdf_url: Optional[str] = None
    fleet_summary: Optional[dict] = {}
    model_config = ConfigDict(from_attributes=True)


class AuditLogBase(BaseModel):
    org_id: str
    actor_id: str
    action: str
    resource_type: str
    resource_id: str


class AuditLog(AuditLogBase):
    id: str
    timestamp: datetime
    details: Optional[dict] = None
    model_config = ConfigDict(from_attributes=True)


# --- Fleet Ship Schemas ---

class ShipBase(BaseModel):
    imo_number: str
    name: str
    flag_state: str
    vessel_type: str
    gross_tonnage: float
    dwt: float
    fuel_type: str
    status: str


class ShipCreate(ShipBase):
    pass


class ShipUpdate(BaseModel):
    name: Optional[str] = None
    flag_state: Optional[str] = None
    vessel_type: Optional[str] = None
    gross_tonnage: Optional[float] = None
    dwt: Optional[float] = None
    fuel_type: Optional[str] = None
    status: Optional[str] = None


class Ship(ShipBase):
    id: str
    org_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class ShipListResponse(BaseModel):
    ships: list[Ship]
    total: int
    page: int
    page_size: int
