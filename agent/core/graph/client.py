"""Neo4j client for database operations."""

import logging
from typing import Any

from neo4j import AsyncGraphDatabase, AsyncDriver

from config import get_settings

logger = logging.getLogger(__name__)


class Neo4jClient:
    """Async Neo4j client for knowledge graph operations.
    
    Example:
        client = Neo4jClient()
        await client.connect()
        
        # Execute a query
        result = await client.execute_query(
            "MATCH (n:Product) RETURN n.id, n.name"
        )
        
        await client.close()
    """
    
    def __init__(
        self,
        uri: str | None = None,
        user: str | None = None,
        password: str | None = None,
        database: str | None = None,
    ) -> None:
        """Initialize the Neo4j client.
        
        Args:
            uri: Neo4j Bolt URI. Falls back to settings.neo4j_uri if None.
            user: Neo4j username. Falls back to settings.neo4j_user if None.
            password: Neo4j password. Falls back to settings.neo4j_password if None.
            database: Database name. Falls back to settings.neo4j_database if None.
        """
        settings = get_settings()
        self.uri = uri or settings.neo4j_uri
        self.user = user or settings.neo4j_user
        self.password = password or settings.neo4j_password
        self.database = database or settings.neo4j_database
        
        self._driver: AsyncDriver | None = None
    
    async def connect(self) -> None:
        """Establish a connection to Neo4j."""
        self._driver = AsyncGraphDatabase.driver(
            self.uri,
            auth=(self.user, self.password)
        )
        await self._driver.verify_connectivity()
        logger.info("Connected to Neo4j at %s", self.uri)
    
    async def close(self) -> None:
        """Close the Neo4j connection."""
        if self._driver:
            await self._driver.close()
            self._driver = None
            logger.info("Neo4j connection closed")
    
    async def execute_query(
        self,
        query: str,
        parameters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Execute a Cypher query.
        
        Args:
            query: Cypher query string.
            parameters: Query parameters.
            
        Returns:
            Result records as a list of dictionaries.
            
        Raises:
            RuntimeError: If not connected to Neo4j.
        """
        if not self._driver:
            raise RuntimeError("Not connected to Neo4j. Call connect() first.")
        
        async with self._driver.session(database=self.database) as session:
            result = await session.run(query, parameters or {})
            records = await result.data()
            return records
    
    async def create_constraints(self) -> None:
        """Create uniqueness constraints for entity IDs."""
        constraints = [
            ("Product", "id"),
            ("InstanceType", "id"),
            ("Region", "id"),
            ("Image", "id"),
            ("BillingMode", "id"),
            ("DatabaseEngine", "id"),
            ("StorageType", "id"),
        ]
        
        for label, property_name in constraints:
            query = (
                f"CREATE CONSTRAINT {label.lower()}_{property_name} "
                f"IF NOT EXISTS FOR (n:{label}) "
                f"REQUIRE n.{property_name} IS UNIQUE"
            )
            try:
                await self.execute_query(query)
                logger.debug("Created constraint for %s.%s", label, property_name)
            except Exception as e:
                logger.warning("Constraint creation skipped for %s: %s", label, e)
        
        logger.info("Neo4j constraints created/verified")
    
    async def clear_database(self) -> None:
        """Delete all nodes and relationships. Use with caution!"""
        query = "MATCH (n) DETACH DELETE n"
        await self.execute_query(query)
        logger.warning("All nodes and relationships deleted from Neo4j")
    
    async def get_stats(self) -> dict[str, int]:
        """Get database statistics.
        
        Returns:
            Dictionary containing node and relationship counts.
        """
        stats = {}
        
        # Count nodes by label
        node_query = """
        MATCH (n)
        RETURN labels(n)[0] as label, count(n) as count
        """
        node_results = await self.execute_query(node_query)
        for record in node_results:
            stats[f"nodes_{record['label']}"] = record["count"]
        
        # Count relationships by type
        rel_query = """
        MATCH ()-[r]->()
        RETURN type(r) as type, count(r) as count
        """
        rel_results = await self.execute_query(rel_query)
        for record in rel_results:
            stats[f"rels_{record['type']}"] = record["count"]
        
        return stats
