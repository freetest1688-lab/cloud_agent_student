# Enterprise ECS Cloud Server Product and Service White Paper

## 1. Product Overview
ECS (Elastic Compute Service) is an enterprise-grade elastic compute service built on a proprietary virtualization architecture (e.g., the Shenlong architecture) and co-designed hardware-software stack. ECS delivers up to 99.995% single-instance availability and 99.9999999% data durability, supporting demanding workloads ranging from microservices architectures to large-scale mission-critical databases.

## 2. Regions and Availability Zone Distribution
To enable geo-redundancy and multi-active architectures, ECS is deployed across multiple data centers worldwide. Power and networking are independent between availability zones (AZs), and AZs within the same region are interconnected via a low-latency internal network.

*   **China North 2 (Beijing)**:
    *   **Zone G (cn-beijing-g)**: Supports general-purpose g8a and compute-optimized c8a instance families. GPU instances are not supported. Only ESSD AutoPL and ESSD PL1 cloud disks are supported.
    *   **Zone K (cn-beijing-k)**: Core zone. Supports all 8th-generation instance types and GPU compute-optimized gn7i. Supports the full ESSD series (PL0/PL1/PL2/PL3).
    *   **Zone L (cn-beijing-l)**: Prioritizes spot instance scheduling. Supports memory-optimized r7 instances.
*   **China East 1 (Hangzhou)**:
    *   **Zone H (cn-hangzhou-h)**: Supports bare-metal instances (ebm), general-purpose g7, and compute-optimized c7.
    *   **Zone I (cn-hangzhou-i)**: Supports high-clock-speed compute-optimized hfc7 instances.
*   **Asia Pacific Southeast 1 (Singapore)**:
    *   **Zone A (ap-southeast-1a)**: Preferred zone for international deployments. Supports g7 and c7. Outbound public network bandwidth is strictly capped (maximum 10 Gbps per instance).

## 3. Enterprise Instance Families and Network Performance Constraints
ECS instances are organized into instance families based on underlying hardware architecture and target workload. Each family is subject to strict limits on network throughput (Gbps), packet-per-second rates (PPS), and the number of elastic network interfaces (ENIs) that can be attached.

### 3.1 8th-Generation Enterprise General-Purpose Instances (g8a)
Based on AMD EPYC™ 9004 (Genoa) processors and powered by a proprietary DPU, delivering over 40% compute performance improvement compared to the previous generation.
*   **ecs.g8a.xlarge**: 4 vCPU, 16 GiB memory. Maximum network bandwidth 10 Gbps, maximum packet throughput 2 million PPS, supports up to 3 ENIs.
*   **ecs.g8a.4xlarge**: 16 vCPU, 64 GiB memory. Maximum network bandwidth 25 Gbps, maximum packet throughput 6 million PPS, supports up to 8 ENIs.

### 3.2 7th-Generation Enterprise Compute-Optimized Instances (c7)
Based on 3rd-generation Intel® Xeon® Scalable processors with a 1:2 vCPU-to-memory ratio, ideal for high-concurrency web applications.
*   **ecs.c7.large**: 2 vCPU, 4 GiB memory. Maximum network bandwidth 5 Gbps, maximum packet throughput 500,000 PPS, supports up to 2 ENIs.
*   **ecs.c7.8xlarge**: 32 vCPU, 64 GiB memory. Maximum network bandwidth 40 Gbps, maximum packet throughput 12 million PPS, supports up to 15 ENIs.

### 3.3 GPU Compute-Optimized Instances (gn7i)
Designed for deep learning inference, AIGC generation, and cloud gaming, equipped with NVIDIA A10/A100 Tensor Core GPUs.
*   **ecs.gn7i-c8g1.2xlarge**: 8 vCPU, 30 GiB memory, with 1 NVIDIA A10 GPU (24 GB VRAM). Network bandwidth 16 Gbps. **Constraint**: Must be launched with an ESSD PL2 or higher system disk.

## 4. Block Storage Types and Performance Specifications
An instance must attach a block storage device (cloud disk) as its system disk and may attach additional data disks.
1.  **ESSD PL0 Cloud Disk**: Maximum single-disk capacity 32,768 GiB, maximum IOPS 10,000, maximum throughput 180 MB/s. Suitable for development and testing environments.
2.  **ESSD PL1 Cloud Disk**: Maximum single-disk capacity 32,768 GiB, maximum IOPS 50,000, maximum throughput 350 MB/s. Suitable for small-to-medium databases and production environments. Supported by all instance families.
3.  **ESSD PL2 Cloud Disk**: Maximum single-disk capacity 32,768 GiB, maximum IOPS 100,000, maximum throughput 750 MB/s. Can only be attached to g8a, gn7i, and c7 instances with 16 or more vCPUs.
4.  **Local NVMe SSD**: Does not provide data persistence guarantees — data is lost on instance restart — but offers extremely low latency. Only available with specific local-disk instance families (e.g., i4). **Not supported** on g8a or c7.

## 5. Networking and Security Group Rules
*   **VPC**: All enterprise-grade instances are required to run inside a VPC. Classic network mode is not supported.
*   **Public Network Bandwidth Billing**:
    *   **Billed by Fixed Bandwidth**: Tiered pricing from 1 Mbps to 5 Mbps (e.g., ¥23/Mbps/month); the per-Mbps price increases sharply above 5 Mbps (e.g., ¥80/Mbps/month). Maximum bandwidth varies by instance type (typically up to 200 Mbps).
    *   **Billed by Traffic**: Charges apply only to actual outbound traffic (e.g., ¥0.8/GB); inbound traffic is free. Peak bandwidth can be set up to 100 Mbps (Beijing region).
*   **Security Group**: Denies all inbound traffic by default; allows all outbound traffic by default. A single instance can belong to up to 5 security groups.

## 6. Billing Modes and Refund Policies
### 6.1 Subscription
*   **Use case**: Core business workloads, 24/7 continuously running services.
*   **Discounts**: 15% off for one-year purchases; 45% off for three-year purchases.
*   **Refund rules**:
    *   **5-Day No-Questions-Asked Refund**: Full refund available within 5 days of purchasing a new instance. Limited to 1 refund per account per calendar year (up to 10 instances per refund).
    *   **Partial Refund (Unsubscribe after 5 days)**: Refund amount is the order payment minus charges for days already used at the on-demand rate, minus a 15% cancellation fee. If the amount already used exceeds the amount paid, no refund is issued.

### 6.2 Pay-As-You-Go
*   **Billing cycle**: Billed per second; invoices are generated at the top of each hour.
*   **No-charge-when-stopped**: After an instance is stopped, compute resources (vCPU and memory) stop accruing charges. However, attached cloud disks and Elastic IPs (if not released) continue to be billed. **Note**: Local-disk instances (e.g., i4) and GPU instances with local disks do not support no-charge-when-stopped.

### 6.3 Spot Instances
*   **Pricing mechanism**: Prices fluctuate with supply and demand; discounts can reach up to 90% off the on-demand rate.
*   **Protection period**: A 1-hour price and inventory protection period is provided after creation. After that period, if the market price exceeds your bid or the resource pool is insufficient, the system will send a 5-minute advance notification and then **automatically release (terminate) the instance**.
*   **Constraints**: Spot instances **do not support** conversion to subscription billing and **do not support** instance type changes.

## 7. Operating System and Image Support
*   **Alibaba Cloud Linux 3 / TencentOS Server 3.1**: Officially optimized CentOS alternatives, with enterprise-grade support provided at no additional cost.
*   **Windows Server 2022 Datacenter Edition**: Requires instances with 4 or more vCPUs. Due to Microsoft licensing costs, the subscription price for the same instance type is approximately 15% higher than the Linux equivalent.
*   **Custom Image**: Supports cross-region replication of custom images, but the replication process consumes public network traffic and incurs corresponding charges.
