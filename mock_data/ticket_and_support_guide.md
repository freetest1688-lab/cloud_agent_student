# Cloud Platform Smart Customer Service and Support Ticket Operations Guide

## 1. Overview
To ensure business continuity for cloud platform users, the platform provides a multi-tier customer service and technical operations support system. When users encounter resource usage issues, billing questions, or underlying system failures, they can submit a support ticket or contact the smart customer service agent for assistance.

## 2. Customer Service Tiers and Response SLAs

### 2.1 Smart Customer Service (L1/L2)
*   **Response time**: Real-time response, 24/7.
*   **Use cases**:
    *   **L1 (Semantic cache direct response)**: Handles high-frequency, standardized questions. Examples: "How do I query instance details?", "What is the subscription cancellation fee?", "What is the maximum bandwidth for ecs.g8a.xlarge?"
    *   **L2 (LLM retrieval-augmented generation)**: Handles complex multi-condition queries. Examples: "Which spot instances with GPU support Windows in Beijing Zone K?", "My ECS cannot connect to RDS — what network and security group settings should I check?"
*   **Escalation mechanism**: If the smart customer service determines that its confidence in an answer is very low (below 0.4), or if the user provides "unresolved" feedback twice consecutively, the case is automatically escalated to a human agent.

### 2.2 Human Support Ticket (Ticket Support)
*   **Support tiers**:
    *   **Basic Service**: Available on business days from 09:00–18:00, with a first response typically within 4–8 hours. Suitable for general inquiries.
    *   **Enterprise Support**: 24/7 response; P1-level incidents (e.g., core database outage) receive a response within 15 minutes.
*   **Ticket submission recommendations**: When submitting a support ticket, it is strongly recommended to include the complete **instance ID (e.g., i-bp1xxx)**, **region**, **screenshot of the error message**, or the **specific error code (e.g., InvalidInstanceType.NotFound)** to help engineers quickly identify the issue.

## 3. Common Support Ticket Categories and Troubleshooting

### 3.1 Instance Resize and Scaling Failures
*   **Ticket type**: Compute & Network > Instance Type Resize.
*   **Common issues**:
    *   A user attempts to upgrade from `ecs.c7.large` to `ecs.g8a.xlarge`, but the console displays "Insufficient inventory" or "Unsupported resize path."
    *   A user attempts to attach a third cloud disk to an instance, but the system returns `OperationDenied.StorageNotSupported`.
*   **Operations recommendation**: Users are advised to first query the resize compatibility matrix through the smart customer service, or verify whether the target availability zone has sufficient underlying physical host resources.

### 3.2 Network Connectivity Issues and High Latency
*   **Ticket type**: Network & Security > VPC / Elastic IP (EIP).
*   **Common issues**:
    *   An instance cannot access the public internet, or external clients cannot connect via SSH.
    *   Two VPCs in different regions cannot communicate over the internal network.
*   **Operations recommendation**: 90% of such issues are caused by **misconfigured security group rules** or **no EIP attached**. Engineers typically start by requesting a screenshot of the security group inbound rules and confirming whether a route entry for the target subnet exists in the VPC routing table.

### 3.3 Billing and Charge Disputes
*   **Ticket type**: Finance & Billing > Unsubscribe & Refund.
*   **Common issues**:
    *   A user's "5-day no-questions-asked refund" request is rejected.
    *   A pay-as-you-go instance has been stopped, but the account continues to be charged.
*   **Operations recommendation**: Customer service will verify whether the user's refund quota has been exhausted (limited to 1 use per account per year) and will explain the restrictions of the "no-charge-when-stopped" feature (e.g., not supported for local-disk instances).

## 4. Underlying System Maintenance and Automated Drills
*   **System events**: The cloud platform periodically performs upgrades, patch fixes, or hardware replacements on the underlying physical hosts.
*   **User notification**: If a user's instance (e.g., an RDS primary node) is on a physical host scheduled for maintenance, a notification of "instance will restart or migrate" is sent 3–7 days in advance.
*   **Operations recommendation**: Enterprise users are strongly advised to use the **High Availability Edition RDS (dual-node master-standby)** and deploy ECS clusters across multiple availability zones, so that underlying maintenance operations are transparent and imperceptible to the business layer.
