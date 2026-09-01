# ECS Cloud Server Advanced Troubleshooting and Instance-Level Error Code Reference

## 1. Overview
This guide covers in-depth troubleshooting for enterprise-grade ECS instances (particularly the g8a, c7, and gn7i instance families) related to underlying hardware scheduling, ENI attachment, and OS boot failures.

## 2. Instance Lifecycle States and Underlying Scheduler Error Codes
When calling the `RunInstances` API or initiating start or resize operations from the console, the underlying Shenlong scheduler or storage controller may return the following specific status codes.

### 2.1 OperationDenied.StorageNotSupported
*   **Trigger scenario**: Attaching an incompatible block storage device (cloud disk) to an instance.
*   **Related instance constraints**:
    *   If you attempt to attach a **local NVMe SSD** to an **ecs.g8a.xlarge** or **ecs.c7.large** instance, this error is triggered. The g8a and c7 series are based on a cloud-disk architecture and **do not support** local disks.
    *   If you attempt to boot an **ecs.gn7i-c8g1.2xlarge (GPU instance)** with an **ESSD PL0 cloud disk**, this error is also triggered. The gn7i requires an **ESSD PL2 or higher** system disk, because deep learning inference demands extremely high system disk IOPS.
*   **Resolution**: Check the compatibility matrix between instance types and block storage, then change the system disk or data disk type to ESSD PL1 or PL2.

### 2.2 InvalidInstanceType.ZoneMismatch
*   **Trigger scenario**: The availability zone specified when creating an instance does not match the physical deployment zone for the selected instance type.
*   **Related zone constraints**:
    *   Requesting a **GPU compute-optimized gn7i** instance in **China North 2 (Beijing) Zone G (cn-beijing-g)**. This zone does not have GPU physical hardware deployed.
    *   Requesting a **spot instance** in **China North 2 (Beijing) Zone K (cn-beijing-k)** when the inventory for the selected instance type in Zone K is exhausted may also result in this error being surfaced.
*   **Resolution**: It is recommended to deploy GPU instances in **Zone K**. For spot instances, enable "random availability zone assignment" or select **Zone L** (which prioritizes spot instance scheduling).

### 2.3 InvalidNetworkInterface.ExceedQuota
*   **Trigger scenario**: Attempting to attach more ENIs to an ECS instance than the instance type supports.
*   **Related instance constraints**:
    *   **ecs.c7.large** (2 vCPU, 4 GiB) supports a maximum of **2 ENIs** (1 primary + 1 secondary). Attempting to attach a third will trigger this error.
    *   **ecs.g8a.xlarge** (4 vCPU, 16 GiB) supports a maximum of **3 ENIs**.
    *   **ecs.c7.8xlarge** (32 vCPU, 64 GiB) supports a maximum of **15 ENIs**.
*   **Resolution**: Call the `DescribeInstanceTypes` API and check the `EniQuantity` quota for the current instance type. If more ENIs are required, you must upgrade (resize) the instance to a larger instance type with a higher vCPU count.

## 3. OS Boot and Connectivity Deep-Dive Troubleshooting
Covers boot-level failures for enterprise images (Alibaba Cloud Linux 3 / Windows Server 2022).

### 3.1 Instance Stuck in Starting State
*   **Symptom**: The console shows the instance is stuck in the Starting state and never transitions to Running.
*   **Related system constraints**:
    *   **Windows license restriction**: If you selected **Windows Server 2022 Datacenter Edition** at creation time but chose **ecs.c7.large (2 vCPU)** as the instance type, the OS will fail to boot. Windows Server 2022 **requires 4 or more vCPUs** (e.g., ecs.g8a.xlarge).
    *   **Resolution**: Force-stop the instance and use the console "Replace OS" option to switch to Alibaba Cloud Linux 3, or upgrade the instance type to one with 4 or more vCPUs.

### 3.2 High-Concurrency Network Packet Loss and PPS Bottleneck Troubleshooting
*   **Symptom**: Under high-concurrency conditions, the web server experiences TCP connection rejections or significant packet loss, but CPU and memory utilization are not saturated.
*   **Troubleshooting steps and instance bottlenecks**:
    1.  **Check the PPS (Packets Per Second) bottleneck**: Each instance type has a strict physical PPS ceiling.
        *   **ecs.c7.large** has a maximum packet throughput of **500,000 PPS**.
        *   **ecs.g8a.xlarge** has a maximum packet throughput of **2 million PPS**.
    2.  **Check the bandwidth ceiling (Gbps)**:
        *   **ecs.c7.large** has a maximum aggregate network bandwidth of **5 Gbps**. If burst traffic exceeds 5 Gbps, the underlying virtual switch will actively drop packets.
*   **Resolution**: If cloud monitoring reveals that PPS or bandwidth has reached one of the thresholds above (e.g., hitting 500,000 PPS), you have reached the physical ceiling of the instance type. Adjusting security group rules or OS-level parameters will have no effect. **You must resize the instance** (e.g., upgrade to ecs.c7.8xlarge, which supports 12 million PPS and 40 Gbps bandwidth).
