# Cloud Platform Network Planning and Security Control Policies (VPC / Security Groups / EIP)

## 1. VPC and Subnet Design
Before building an architecture in the cloud, you must plan your VPC. A VPC (Virtual Private Cloud) is a logically isolated network scoped to a single region.

### 1.1 Core Components and Topology
*   **VPC instance**: For example, `vpc-prod-beijing` (Beijing production environment). Address ranges are typically chosen from RFC 1918 private address space, such as `10.0.0.0/8`.
*   **VSwitch**: A VPC must be divided into VSwitches. **VSwitches are availability-zone-scoped resources.**
    *   **vsw-beijing-k**: Belongs to `vpc-prod-beijing`, deployed in Zone K (`cn-beijing-k`). Recommended for hosting core databases (e.g., RDS) and enterprise-grade instances (e.g., ecs.g8a.4xlarge).
    *   **vsw-beijing-g**: Belongs to `vpc-prod-beijing`, deployed in Zone G (`cn-beijing-g`). Note: GPU instances (gn7i) cannot be deployed under this VSwitch.

### 1.2 Internal Connectivity and Isolation
*   **Intra-VPC connectivity**: Instances deployed under `vsw-beijing-k` and `vsw-beijing-g` (even across different availability zones) are fully reachable over the internal network by default (unrestricted by subnet, but controlled by security groups).
*   **Cross-VPC isolation**: If a development environment uses `vpc-dev-beijing`, ECS instances in the production environment `vpc-prod-beijing` cannot access the development environment by default. You must configure **Cloud Enterprise Network (CEN)** to enable routing between the two VPCs.

## 2. Elastic IP (EIP) and Shared Bandwidth
When an ECS instance requires public network access, it is recommended to attach an Elastic IP (EIP).

### 2.1 Attachment and Detachment Constraints
*   **Attachment targets**: An EIP can only be attached to **VPC-type resources**. For example, it can be attached to the primary ENI or secondary ENI of an `ecs.c7.large` instance.
*   **Regional constraint**: EIPs are regional resources. A Beijing EIP can only be attached to ECS instances in the Beijing region. **Cross-region attachment is strictly prohibited.**

### 2.2 Shared Bandwidth
*   **Use case**: If multiple ECS instances (e.g., 10 `ecs.g8a.xlarge` web servers) each have an EIP attached, it is recommended to move those EIPs into a single Shared Bandwidth instance.
*   **Benefits**: Handles burst traffic peaks while reducing public bandwidth costs by 30%–40%. **Note**: ECS instances billed under the subscription model using "fixed bandwidth" billing cannot join Shared Bandwidth. They must first be switched to "pay-by-traffic" billing.

## 3. Security Groups and Elastic Network Interfaces (ENIs)
Security groups act as stateful virtual firewalls based on stateful packet inspection, controlling inbound and outbound traffic for instances.

### 3.1 ENI and Security Group Association
Security group rules are enforced at the **ENI** level, not directly at the ECS instance level.
*   **Multiple security groups**: A single ENI (e.g., the second ENI attached to an ecs.g8a.4xlarge) can belong to up to **5 security groups**. The system applies the union of all rules across those security groups.
*   **Multi-ENI isolation**: If `ecs.c7.8xlarge` has 2 ENIs attached, you can assign ENI A to `sg-web` (allowing ports 80/443) and ENI B to `sg-db` (internal traffic only, no public access), achieving physical separation of internal and external network traffic.

### 3.2 Typical Enterprise Security Group Configuration
*   **sg-web-prod** (Web cluster security group)
    *   **Inbound**: Allow `0.0.0.0/0` on TCP `80` and `443`. Allow a specific bastion host IP (e.g., `203.0.113.1/32`) on TCP `22` (SSH). Deny all other inbound traffic.
    *   **Outbound**: Allow all outbound traffic.
*   **sg-rds-internal** (Database security group)
    *   **Inbound**: **Deny all public network access.** Configure an authorization rule that allows only instances whose source security group is `sg-web-prod` to access TCP port `3306` over the internal network. This is a highly secure **security-group-ID-based authorization** configuration.
