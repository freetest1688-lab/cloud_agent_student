# Cloud Platform Billing Rules and Refund Policy

## 1. Overview
The cloud platform offers flexible billing modes to meet the cost control requirements of different business scenarios. This document describes the main billing modes, bandwidth billing rules, and the conditions for resource release and refunds.

## 2. Core Billing Modes

### 2.1 Subscription
*   **Use case**: Suitable for stable workloads running 24 hours a day (e.g., core databases on RDS, enterprise web servers on ecs.g8a.xlarge).
*   **Billing rules**: Prepaid model. The longer the purchase term, the larger the discount (e.g., 15% off for one year, 50% off for three years).
*   **Conversion rules**: You can convert a pay-as-you-go instance to subscription; however, converting a subscription instance to pay-as-you-go or spot is **not supported**.

### 2.2 Pay-As-You-Go
*   **Use case**: Suitable for short-term workloads with distinct peak and off-peak periods, development and testing environments, or temporary capacity scaling during e-commerce promotions.
*   **Billing rules**: Postpaid model. Billed per second; invoices are generated at the top of each hour. Instance prices are generally higher than subscription.
*   **No-charge-when-stopped**:
    *   When an instance transitions to the `Stopped` state with no-charge-when-stopped enabled, compute resources (vCPU and memory) stop accruing charges.
    *   **Restrictions**: Instances with **local disks (NVMe SSD)** attached (e.g., the i4 series) or **GPU instances (gn7i)** with local disks **do not support** no-charge-when-stopped — compute resources continue to be billed even when the instance is stopped. Cloud disks (ESSD) and retained Elastic IPs are always billed regardless of instance state.

### 2.3 Spot Instances
*   **Use case**: Suitable for stateless web services, offline data analysis, batch computing, and other workloads that can tolerate interruptions.
*   **Billing rules**: Prices fluctuate with supply and demand; savings of up to 90% compared to pay-as-you-go are possible.
*   **Release risk**:
    *   **Protection period**: A 1-hour inventory and price protection period is provided after creation.
    *   **Automatic release mechanism**: After the protection period ends, if the market price exceeds your bid or the resource pool inventory is insufficient, the system will **send a system event notification 5 minutes in advance** and then automatically reclaim (release) the instance. Data cannot be recovered after release.
    *   **Conversion restriction**: Spot instances **absolutely do not support** conversion to subscription billing.

## 3. Network Bandwidth Billing Rules

Public network bandwidth is typically provided through an attached **Elastic IP (EIP)** and can be billed in two ways:

### 3.1 Billed by Fixed Bandwidth (PayByBandwidth)
*   **Rules**: A fixed fee is charged based on the provisioned bandwidth peak (e.g., 5 Mbps), regardless of actual traffic consumed.
*   **Use case**: Workloads with stable, high-utilization public traffic.
*   **Tiered pricing**: The per-Mbps price is typically lower for 1–5 Mbps; the unit price rises sharply for bandwidth above 5 Mbps.

### 3.2 Billed by Traffic (PayByTraffic)
*   **Rules**: Charges are based on actual **outbound traffic** in GB (e.g., ¥0.8/GB). **Inbound traffic is free.**
*   **Use case**: Workloads with highly variable public traffic, or workloads with overall low traffic volumes. You can set a high bandwidth peak (e.g., 100 Mbps) to handle burst requests without paying a fixed fee for high-bandwidth provisioning.

## 4. Resource Release and Refund Details

### 4.1 5-Day No-Questions-Asked Refund
*   **Conditions**: A newly purchased subscription instance is eligible for a full refund within **5 days** of purchase, provided the instance has not undergone a downgrade, renewal, or similar operation.
*   **Quota limit**: Each verified account is entitled to **1 use** of the 5-day no-questions-asked refund per calendar year (up to 10 instances per use).

### 4.2 Partial Refund (Pro-Rated Unsubscribe)
*   **Conditions**: Unsubscribing from a subscription instance after 5 days, or when the conditions for a no-questions-asked refund are not met.
*   **Refund formula**: Refund amount = Amount paid for the order − (Days used × Pay-as-you-go unit price) − (Amount paid for the order × 15% cancellation fee).
*   **Note**: If the calculated refund amount is less than or equal to zero, no refund is issued.

### 4.3 Overdue Payment and Automatic Release
*   **Pay-as-you-go instances**: If the account balance is insufficient and becomes overdue, the instance enters an "overdue suspension" state (data is retained for 15 days). If the account is not topped up within 15 days, the instance and its attached cloud disks are **permanently released (destroyed)**.
