# Cloud Database RDS Core Architecture and Multi-Active Deployment Guide

## 1. Product Overview and Underlying Dependencies
RDS (Relational Database Service) is a database service deeply optimized on top of a proprietary cloud infrastructure. Its underlying compute nodes rely on ECS instances (e.g., ecs.c7.large), and its storage nodes rely on ESSD cloud disks.

## 2. Supported Engines and Use Cases
*   **RDS MySQL**: The world's most popular open-source database.
    *   **Supported versions**: 5.7, 8.0.
    *   **Use cases**: High-concurrency transaction systems (paired with ecs.g8a.4xlarge for increased throughput), internet social platforms, and gaming data storage.
*   **RDS PostgreSQL**: Advanced open-source relational database.
    *   **Supported versions**: 13, 14, 15.
    *   **Use cases**: GIS (geographic information systems), complex financial data processing, and recommendation systems.

## 3. Deployment Architecture and Disaster Recovery (Intra-City Multi-Active)
To ensure availability of up to 99.99%, RDS instances are strongly recommended to use an enterprise-grade high-availability architecture.

### 3.1 Basic Edition
*   **Architecture**: Single-node deployment with no standby node; the underlying storage may use ESSD PL1.
*   **Limitation**: If the underlying ECS host encounters a hardware failure, the instance will be unavailable for several minutes until it recovers on another physical host, causing a business interruption. This edition is intended for personal blogs and development/testing environments and does not carry a high-availability SLA.

### 3.2 High Availability Edition
*   **Architecture**: Dual-node master-standby (Master-Standby) architecture. The primary node handles read and write requests; the standby node synchronizes data in real time over the internal network.
*   **Intra-city disaster recovery deployment**: It is strongly recommended to deploy the primary and standby nodes in different availability zones.
    *   **Primary node**: Deployed in **China North 2 (Beijing) Zone K (cn-beijing-k)**.
    *   **Standby node**: Deployed in **China North 2 (Beijing) Zone L (cn-beijing-l)**.
*   **Failover**: If a power failure in Zone K causes the primary node to go down, the RDS system automatically migrates the VIP (virtual IP) to the standby node in Zone L within 30 seconds. No changes to the application's connection string are required.

## 4. Read/Write Splitting Architecture
For high-concurrency web servers such as `ecs.c7.8xlarge`, a single RDS primary node may become a performance bottleneck.
*   **Read-only instances**: The High Availability Edition supports attaching up to 10 read-only instances.
*   **Read/write splitting endpoint**: After enabling read/write splitting, the system provides a unified endpoint (e.g., `rm-bp1xxx.mysql.rds.aliyuncs.com`). Write requests are automatically routed to the primary node, while read requests are automatically distributed across the read-only instances according to configured weights.

## 5. Three Prerequisites for ECS-to-RDS Internal Network Connectivity
These are the most critical configuration requirements for cloud deployments. If any one of them is not met, ECS will be unable to connect to RDS and will receive a Connection Refused error.

1.  **Same region and same network**: The ECS instance (e.g., ecs.g8a.xlarge) and the RDS instance must be in the **same region (e.g., China North 2, Beijing)** and the **same VPC (e.g., vpc-prod-beijing)**. Cross-VPC connectivity is not available by default and requires Cloud Enterprise Network (CEN).
2.  **RDS whitelist authorization**: RDS blocks all requests by default (the whitelist is empty). You **must** add the private IP address of the accessing ECS instance (e.g., `10.0.0.15`) or the VPC CIDR block (e.g., `10.0.0.0/16`) to the RDS access whitelist.
3.  **ECS outbound security group rule**: Although ECS outbound traffic is allowed by default, if your organization has configured strict outbound restrictions, you must ensure that traffic to the RDS internal IP on destination port **TCP 3306 (MySQL)** or **TCP 5432 (PostgreSQL)** is explicitly permitted.
