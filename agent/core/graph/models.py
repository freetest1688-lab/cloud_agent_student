"""Data models for knowledge graph entities."""

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class Product:
    """Cloud product entity."""
    id: str
    name: str
    category: str
    description: str
    features: list[str] = field(default_factory=list)
    use_cases: list[str] = field(default_factory=list)


@dataclass
class InstanceType:
    """Instance type (SKU) entity."""
    id: str
    name: str
    product_id: str
    vcpu: int
    memory_gb: int
    bandwidth_gbps: float
    storage_type: str
    price_per_hour: float


@dataclass
class Region:
    """Cloud region entity."""
    id: str
    name: str
    region_type: Literal["domestic", "international"]
    availability_zones: list[str] = field(default_factory=list)


@dataclass
class Image:
    """OS image entity."""
    id: str
    name: str
    os_type: Literal["Linux", "Windows"]
    version: str
    architecture: str = "x86_64"


@dataclass
class BillingMode:
    """Billing mode entity."""
    id: str
    name: str
    description: str
    billing_cycle: str


@dataclass
class DatabaseEngine:
    """RDS database engine entity."""
    id: str
    name: str
    engine_type: str
    version: str
    product_id: str


@dataclass
class StorageType:
    """Storage type entity."""
    id: str
    name: str
    performance_level: str
    use_case: str


@dataclass
class Relation:
    """Relationship between entities."""
    source_id: str
    target_id: str
    relation_type: Literal[
        "BELONGS_TO",
        "AVAILABLE_IN", 
        "SUPPORTS_BILLING",
        "COMPATIBLE_WITH",
        "SUPPORTS_STORAGE",
    ]
    properties: dict = field(default_factory=dict)
