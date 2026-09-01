"""Knowledge graph ingestor for loading data into Neo4j."""

import logging
from typing import Any

from .client import Neo4jClient
from .models import (
    Product,
    InstanceType,
    Region,
    Image,
    BillingMode,
    DatabaseEngine,
    StorageType,
    Relation,
)

logger = logging.getLogger(__name__)


class KnowledgeGraphIngestor:
    """Ingestor for loading cloud product knowledge into Neo4j.
    
    Example:
        client = Neo4jClient()
        await client.connect()
        
        ingestor = KnowledgeGraphIngestor(client)
        
        # Ingest products
        products = [Product(id="ecs", name="ECS", ...)]
        await ingestor.ingest_products(products)
        
        # Ingest relations
        relations = [Relation(source_id="ecs", target_id="cn-beijing", ...)]
        await ingestor.ingest_relations(relations)
        
        await client.close()
    """
    
    def __init__(self, client: Neo4jClient) -> None:
        """Initialize the ingestor with a Neo4j client.
        
        Args:
            client: A connected Neo4jClient instance.
        """
        self.client = client
    
    async def ingest_products(self, products: list[Product]) -> int:
        """Ingest product entities.
        
        Args:
            products: List of product entities.
            
        Returns:
            Number of products ingested.
        """
        if not products:
            return 0
        
        query = """
        UNWIND $products AS product
        MERGE (p:Product {id: product.id})
        SET p.name = product.name,
            p.category = product.category,
            p.description = product.description,
            p.features = product.features,
            p.use_cases = product.use_cases,
            p.updated_at = datetime()
        RETURN count(p) AS count
        """
        
        params = {
            "products": [
                {
                    "id": p.id,
                    "name": p.name,
                    "category": p.category,
                    "description": p.description,
                    "features": p.features,
                    "use_cases": p.use_cases,
                }
                for p in products
            ]
        }
        
        result = await self.client.execute_query(query, params)
        count = result[0]["count"] if result else 0
        logger.info("Ingested %d products", count)
        return count
    
    async def ingest_instance_types(self, instances: list[InstanceType]) -> int:
        """Ingest instance type entities.
        
        Args:
            instances: List of instance type entities.
            
        Returns:
            Number of instance types ingested.
        """
        if not instances:
            return 0
        
        query = """
        UNWIND $instances AS inst
        MERGE (i:InstanceType {id: inst.id})
        SET i.name = inst.name,
            i.vcpu = inst.vcpu,
            i.memory_gb = inst.memory_gb,
            i.bandwidth_gbps = inst.bandwidth_gbps,
            i.storage_type = inst.storage_type,
            i.price_per_hour = inst.price_per_hour,
            i.updated_at = datetime()
        WITH i, inst
        MATCH (p:Product {id: inst.product_id})
        MERGE (i)-[:BELONGS_TO]->(p)
        RETURN count(i) AS count
        """
        
        params = {
            "instances": [
                {
                    "id": i.id,
                    "name": i.name,
                    "product_id": i.product_id,
                    "vcpu": i.vcpu,
                    "memory_gb": i.memory_gb,
                    "bandwidth_gbps": i.bandwidth_gbps,
                    "storage_type": i.storage_type,
                    "price_per_hour": i.price_per_hour,
                }
                for i in instances
            ]
        }
        
        result = await self.client.execute_query(query, params)
        count = result[0]["count"] if result else 0
        logger.info("Ingested %d instance types", count)
        return count
    
    async def ingest_regions(self, regions: list[Region]) -> int:
        """Ingest region entities.
        
        Args:
            regions: List of region entities.
            
        Returns:
            Number of regions ingested.
        """
        if not regions:
            return 0
        
        query = """
        UNWIND $regions AS region
        MERGE (r:Region {id: region.id})
        SET r.name = region.name,
            r.region_type = region.region_type,
            r.availability_zones = region.availability_zones,
            r.updated_at = datetime()
        RETURN count(r) AS count
        """
        
        params = {
            "regions": [
                {
                    "id": r.id,
                    "name": r.name,
                    "region_type": r.region_type,
                    "availability_zones": r.availability_zones,
                }
                for r in regions
            ]
        }
        
        result = await self.client.execute_query(query, params)
        count = result[0]["count"] if result else 0
        logger.info("Ingested %d regions", count)
        return count
    
    async def ingest_images(self, images: list[Image]) -> int:
        """Ingest image entities.
        
        Args:
            images: List of image entities.
            
        Returns:
            Number of images ingested.
        """
        if not images:
            return 0
        
        query = """
        UNWIND $images AS image
        MERGE (i:Image {id: image.id})
        SET i.name = image.name,
            i.os_type = image.os_type,
            i.version = image.version,
            i.architecture = image.architecture,
            i.updated_at = datetime()
        RETURN count(i) AS count
        """
        
        params = {
            "images": [
                {
                    "id": img.id,
                    "name": img.name,
                    "os_type": img.os_type,
                    "version": img.version,
                    "architecture": img.architecture,
                }
                for img in images
            ]
        }
        
        result = await self.client.execute_query(query, params)
        count = result[0]["count"] if result else 0
        logger.info("Ingested %d images", count)
        return count
    
    async def ingest_billing_modes(self, modes: list[BillingMode]) -> int:
        """Ingest billing mode entities.
        
        Args:
            modes: List of billing mode entities.
            
        Returns:
            Number of billing modes ingested.
        """
        if not modes:
            return 0
        
        query = """
        UNWIND $modes AS mode
        MERGE (b:BillingMode {id: mode.id})
        SET b.name = mode.name,
            b.description = mode.description,
            b.billing_cycle = mode.billing_cycle,
            b.updated_at = datetime()
        RETURN count(b) AS count
        """
        
        params = {
            "modes": [
                {
                    "id": m.id,
                    "name": m.name,
                    "description": m.description,
                    "billing_cycle": m.billing_cycle,
                }
                for m in modes
            ]
        }
        
        result = await self.client.execute_query(query, params)
        count = result[0]["count"] if result else 0
        logger.info("Ingested %d billing modes", count)
        return count
    
    async def ingest_database_engines(self, engines: list[DatabaseEngine]) -> int:
        """Ingest database engine entities.
        
        Args:
            engines: List of database engine entities.
            
        Returns:
            Number of database engines ingested.
        """
        if not engines:
            return 0
        
        query = """
        UNWIND $engines AS engine
        MERGE (e:DatabaseEngine {id: engine.id})
        SET e.name = engine.name,
            e.engine_type = engine.engine_type,
            e.version = engine.version,
            e.updated_at = datetime()
        WITH e, engine
        MATCH (p:Product {id: engine.product_id})
        MERGE (e)-[:BELONGS_TO]->(p)
        RETURN count(e) AS count
        """
        
        params = {
            "engines": [
                {
                    "id": e.id,
                    "name": e.name,
                    "engine_type": e.engine_type,
                    "version": e.version,
                    "product_id": e.product_id,
                }
                for e in engines
            ]
        }
        
        result = await self.client.execute_query(query, params)
        count = result[0]["count"] if result else 0
        logger.info("Ingested %d database engines", count)
        return count
    
    async def ingest_storage_types(self, storage_types: list[StorageType]) -> int:
        """Ingest storage type entities.
        
        Args:
            storage_types: List of storage type entities.
            
        Returns:
            Number of storage types ingested.
        """
        if not storage_types:
            return 0
        
        query = """
        UNWIND $storage_types AS st
        MERGE (s:StorageType {id: st.id})
        SET s.name = st.name,
            s.performance_level = st.performance_level,
            s.use_case = st.use_case,
            s.updated_at = datetime()
        RETURN count(s) AS count
        """
        
        params = {
            "storage_types": [
                {
                    "id": st.id,
                    "name": st.name,
                    "performance_level": st.performance_level,
                    "use_case": st.use_case,
                }
                for st in storage_types
            ]
        }
        
        result = await self.client.execute_query(query, params)
        count = result[0]["count"] if result else 0
        logger.info("Ingested %d storage types", count)
        return count
    
    async def ingest_relations(self, relations: list[Relation]) -> int:
        """Ingest relationships between entities.
        
        Args:
            relations: List of relation entities.
            
        Returns:
            Number of relations ingested.
        """
        if not relations:
            return 0
        
        # Group relations by type for batch processing
        relations_by_type: dict[str, list[Relation]] = {}
        for rel in relations:
            if rel.relation_type not in relations_by_type:
                relations_by_type[rel.relation_type] = []
            relations_by_type[rel.relation_type].append(rel)
        
        total_count = 0
        
        for rel_type, rels in relations_by_type.items():
            query = f"""
            UNWIND $relations AS rel
            MATCH (a {{id: rel.source_id}})
            MATCH (b {{id: rel.target_id}})
            MERGE (a)-[r:{rel_type}]->(b)
            SET r += rel.properties,
                r.updated_at = datetime()
            RETURN count(r) AS count
            """
            
            params = {
                "relations": [
                    {
                        "source_id": r.source_id,
                        "target_id": r.target_id,
                        "properties": r.properties,
                    }
                    for r in rels
                ]
            }
            
            result = await self.client.execute_query(query, params)
            count = result[0]["count"] if result else 0
            total_count += count
            logger.debug("Ingested %d %s relations", count, rel_type)
        
        logger.info("Ingested %d total relations", total_count)
        return total_count
    
    async def ingest_all(
        self,
        products: list[Product] | None = None,
        instance_types: list[InstanceType] | None = None,
        regions: list[Region] | None = None,
        images: list[Image] | None = None,
        billing_modes: list[BillingMode] | None = None,
        database_engines: list[DatabaseEngine] | None = None,
        storage_types: list[StorageType] | None = None,
        relations: list[Relation] | None = None,
    ) -> dict[str, int]:
        """Ingest all entity types and relationships.
        
        Args:
            products: List of product entities.
            instance_types: List of instance type entities.
            regions: List of region entities.
            images: List of image entities.
            billing_modes: List of billing mode entities.
            database_engines: List of database engine entities.
            storage_types: List of storage type entities.
            relations: List of relation entities.
            
        Returns:
            Dictionary containing the count of ingested entities per type.
        """
        stats = {}
        
        # Create constraints first
        await self.client.create_constraints()
        
        # Ingest entities in order (nodes before relationships)
        stats["products"] = await self.ingest_products(products or [])
        stats["instance_types"] = await self.ingest_instance_types(instance_types or [])
        stats["regions"] = await self.ingest_regions(regions or [])
        stats["images"] = await self.ingest_images(images or [])
        stats["billing_modes"] = await self.ingest_billing_modes(billing_modes or [])
        stats["database_engines"] = await self.ingest_database_engines(database_engines or [])
        stats["storage_types"] = await self.ingest_storage_types(storage_types or [])
        
        # Ingest relations last
        stats["relations"] = await self.ingest_relations(relations or [])
        
        logger.info("Knowledge graph ingestion complete: %s", stats)
        return stats
