"""LLM-based document parser for extracting entities and relationships."""

import json
import logging
from pathlib import Path
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_community.chat_models import ChatTongyi

from config import get_settings
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


def get_extraction_prompt(document_content: str) -> str:
    """Build the extraction prompt with the provided document content."""
    return f"""You are a professional cloud-product knowledge extraction assistant.
Extract entities and relationships from the product documentation below and output them as JSON.

## Entity Types

1. **Product**
   - id: product ID (lowercase English, e.g. ecs, rds)
   - name: product name
   - category: category (compute/database/storage/network)
   - description: product description
   - features: list of feature highlights
   - use_cases: list of applicable use cases

2. **InstanceType**
   - id: SKU ID (e.g. ecs.g7.large)
   - name: SKU name
   - product_id: parent product ID
   - vcpu: number of vCPUs
   - memory_gb: memory in GB
   - bandwidth_gbps: network bandwidth in Gbps
   - storage_type: storage type (ESSD/SSD/efficient-cloud-disk)
   - price_per_hour: pay-as-you-go price per hour (USD)

3. **Region**
   - id: region ID (e.g. cn-beijing)
   - name: region name
   - region_type: domestic or international
   - availability_zones: list of availability zones

4. **Image**
   - id: image ID (e.g. centos-7-9)
   - name: image name
   - os_type: Linux or Windows
   - version: version number
   - architecture: architecture (x86_64/arm64)

5. **BillingMode**
   - id: billing mode ID (pay-as-you-go/subscription)
   - name: billing mode name
   - description: description
   - billing_cycle: billing cycle (hourly/monthly/yearly)

6. **DatabaseEngine**
   - id: engine ID (e.g. mysql-8-0)
   - name: engine name
   - engine_type: engine type (MySQL/PostgreSQL/SQLServer)
   - version: version number
   - product_id: parent product ID

7. **StorageType**
   - id: storage type ID (cloud-ssd/cloud-essd/local-ssd)
   - name: storage type name
   - performance_level: performance tier (low/medium/high/ultra)
   - use_case: applicable use case

## Relationship Types

- **BELONGS_TO**: instance belongs to a product; engine belongs to a product
- **AVAILABLE_IN**: product is available in a region
- **SUPPORTS_BILLING**: instance supports a billing mode (with price property)
- **COMPATIBLE_WITH**: image is compatible with a product; SKU is compatible with an engine
- **SUPPORTS_STORAGE**: SKU supports a storage type

## Output Format

```json
{{
  "entities": {{
    "products": [...],
    "instance_types": [...],
    "regions": [...],
    "images": [...],
    "billing_modes": [...],
    "database_engines": [...],
    "storage_types": [...]
  }},
  "relations": [
    {{"source_id": "...", "target_id": "...", "type": "BELONGS_TO", "properties": {{...}}}}
  ]
}}
```

## Document to Parse

{document_content}

Output only the JSON — no additional text or explanation."""


class KnowledgeGraphParser:
    """Parser that extracts knowledge graph entities from documents.
    
    Example:
        parser = KnowledgeGraphParser()
        
        # Parse from a file
        result = await parser.parse_file("data/raw_documents/ecs_product_manual.txt")
        
        # Parse from text
        with open("document.txt") as f:
            result = await parser.parse_text(f.read())
        
        # Access extracted entities
        products = result["products"]
        instance_types = result["instance_types"]
        relations = result["relations"]
    """
    
    def __init__(self, llm: BaseChatModel | None = None) -> None:
        """Initialize the parser with an LLM.
        
        Args:
            llm: LangChain chat model. Uses ChatTongyi if None.
        """
        settings = get_settings()
        self.llm = llm or ChatTongyi(**settings.get_model_config())
    
    async def parse_text(self, text: str) -> dict[str, list[Any]]:
        """Parse document text and extract entities.
        
        Args:
            text: Document content.
            
        Returns:
            Dictionary containing extracted entities and relationships.
        """
        prompt = get_extraction_prompt(text)
        
        logger.info("Sending document to LLM for extraction...")
        response = await self.llm.ainvoke(prompt)
        content = response.content
        
        # Extract JSON from the response
        try:
            # Try to find a JSON code block
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            else:
                json_str = content.strip()
            
            data = json.loads(json_str)
            
            # Convert to model instances
            result = self._convert_to_models(data)
            
            logger.info(
                "Extraction complete: %d products, %d instances, %d regions, %d relations",
                len(result.get("products", [])),
                len(result.get("instance_types", [])),
                len(result.get("regions", [])),
                len(result.get("relations", [])),
            )
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error("Failed to parse LLM response as JSON: %s", e)
            logger.error("Response content: %s", content[:500])
            raise
    
    async def parse_file(self, file_path: str | Path) -> dict[str, list[Any]]:
        """Parse a document file and extract entities.
        
        Args:
            file_path: Path to the document file.
            
        Returns:
            Dictionary containing extracted entities and relationships.
        """
        file_path = Path(file_path)
        logger.info("Parsing file: %s", file_path)
        
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        return await self.parse_text(content)
    
    def _convert_to_models(self, data: dict) -> dict[str, list[Any]]:
        """Convert raw JSON data to model instances.
        
        Args:
            data: Parsed JSON data.
            
        Returns:
            Dictionary containing model instances.
        """
        entities = data.get("entities", {})
        relations_data = data.get("relations", [])
        
        result = {}
        
        result["products"] = [
            Product(**p) for p in entities.get("products", [])
        ]
        
        result["instance_types"] = [
            InstanceType(**i) for i in entities.get("instance_types", [])
        ]
        
        result["regions"] = [
            Region(**r) for r in entities.get("regions", [])
        ]
        
        result["images"] = [
            Image(**i) for i in entities.get("images", [])
        ]
        
        result["billing_modes"] = [
            BillingMode(**b) for b in entities.get("billing_modes", [])
        ]
        
        result["database_engines"] = [
            DatabaseEngine(**d) for d in entities.get("database_engines", [])
        ]
        
        result["storage_types"] = [
            StorageType(**s) for s in entities.get("storage_types", [])
        ]
        
        result["relations"] = [
            Relation(
                source_id=r["source_id"],
                target_id=r["target_id"],
                relation_type=r["type"],
                properties=r.get("properties", {}),
            )
            for r in relations_data
        ]
        
        return result


async def main():
    """Example usage of KnowledgeGraphParser."""
    import asyncio
    
    # Sample document
    sample_doc = """
# Elastic Compute Service (ECS)

ECS is a scalable cloud compute service.

## Instance Types

- ecs.g7.large: 2 vCPU / 8 GB, 1 Gbps bandwidth, $0.12/hr
- ecs.g7.xlarge: 4 vCPU / 16 GB, 1.5 Gbps bandwidth, $0.24/hr

## Regions

- North China 2 (Beijing): cn-beijing
- East China 2 (Shanghai): cn-shanghai

## Billing Modes

- Pay-as-you-go: billed by the hour
- Subscription: billed monthly
"""
    
    parser = KnowledgeGraphParser()
    result = await parser.parse_text(sample_doc)
    
    print("Extraction results:")
    print(f"  Products: {len(result['products'])}")
    print(f"  Instance types: {len(result['instance_types'])}")
    print(f"  Regions: {len(result['regions'])}")
    print(f"  Billing modes: {len(result['billing_modes'])}")
    print(f"  Relations: {len(result['relations'])}")
    
    # Print first product
    if result['products']:
        print("\nFirst product:")
        p = result['products'][0]
        print(f"  ID: {p.id}")
        print(f"  Name: {p.name}")
        print(f"  Category: {p.category}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
