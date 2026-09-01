-- ==========================================================
-- Cloud platform user order and billing mock data initialization script
-- ==========================================================

-- 1. Create orders table (if not exists)
CREATE TABLE IF NOT EXISTS cloud_orders (
    order_id VARCHAR(50) PRIMARY KEY COMMENT 'Unique order ID',
    user_id VARCHAR(50) NOT NULL COMMENT 'User ID',
    product_name VARCHAR(100) NOT NULL COMMENT 'Product name (e.g. ecs.g8a.xlarge)',
    billing_mode VARCHAR(20) NOT NULL COMMENT 'Billing mode (subscription, pay-as-you-go)',
    amount DECIMAL(10, 2) NOT NULL COMMENT 'Order amount',
    status VARCHAR(20) NOT NULL COMMENT 'Order status (paid, unpaid, refunded)',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'Creation timestamp',
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Cloud product orders table';

-- 2. Truncate old data (for repeated test runs)
TRUNCATE TABLE cloud_orders;

-- 3. Insert test data (generate data for two different users to validate permission isolation)

-- Data for user_1001 (high-value customer, purchased enterprise-grade instances)
INSERT INTO cloud_orders (order_id, user_id, product_name, billing_mode, amount, status, created_at) VALUES
('ORD-1001-001', 'user_1001', 'ecs.g8a.4xlarge', 'subscription', 12500.00, 'paid', '2023-10-01 10:00:00'),
('ORD-1001-002', 'user_1001', 'rds.mysql.c1.large', 'subscription', 3600.00, 'paid', '2023-10-05 14:30:00'),
('ORD-1001-003', 'user_1001', 'Shared Bandwidth 100Mbps', 'pay-as-you-go', 150.50, 'paid', '2023-11-01 08:15:00');

-- Data for user_1002 (individual developer, purchased budget instances)
INSERT INTO cloud_orders (order_id, user_id, product_name, billing_mode, amount, status, created_at) VALUES
('ORD-1002-001', 'user_1002', 'ecs.c7.large', 'pay-as-you-go', 45.20, 'paid', '2023-11-15 09:00:00'),
('ORD-1002-002', 'user_1002', 'Cloud Disk ESSD PL0 40G', 'subscription', 120.00, 'paid', '2023-11-15 09:05:00'),
('ORD-1002-003', 'user_1002', 'ecs.c7.large', 'pay-as-you-go', 12.80, 'unpaid', '2023-11-16 10:00:00'); -- Simulate an unpaid bill

-- 4. Create resource instances table (simulates real instances visible in the cloud platform console)
CREATE TABLE IF NOT EXISTS cloud_instances (
    instance_id VARCHAR(50) PRIMARY KEY COMMENT 'Unique instance ID',
    user_id VARCHAR(50) NOT NULL COMMENT 'Owning user',
    order_id VARCHAR(50) NOT NULL COMMENT 'Associated purchase order',
    instance_type VARCHAR(100) NOT NULL COMMENT 'Instance type',
    region_id VARCHAR(50) NOT NULL COMMENT 'Region',
    zone_id VARCHAR(50) NOT NULL COMMENT 'Availability zone',
    status VARCHAR(20) NOT NULL COMMENT 'Instance status (running, stopped)',
    public_ip VARCHAR(20) COMMENT 'Public IP',
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Cloud resource instances table';

TRUNCATE TABLE cloud_instances;

INSERT INTO cloud_instances (instance_id, user_id, order_id, instance_type, region_id, zone_id, status, public_ip) VALUES
('i-bp1_user1001_ecs', 'user_1001', 'ORD-1001-001', 'ecs.g8a.4xlarge', 'cn-beijing', 'cn-beijing-k', 'running', '47.100.1.1'),
('rm-bp1_user1001_rds', 'user_1001', 'ORD-1001-002', 'rds.mysql.c1.large', 'cn-beijing', 'cn-beijing-l', 'running', NULL),
('i-bp1_user1002_ecs', 'user_1002', 'ORD-1002-001', 'ecs.c7.large', 'cn-hangzhou', 'cn-hangzhou-h', 'stopped', '114.55.2.2');

CREATE TABLE IF NOT EXISTS instance_metrics_daily (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT 'Auto-increment primary key',
    instance_id VARCHAR(50) NOT NULL COMMENT 'Instance ID',
    user_id VARCHAR(50) NOT NULL COMMENT 'Owning user ID',
    metric_date DATE NOT NULL COMMENT 'Metrics date',
    avg_cpu_usage_percent DECIMAL(5,2) NOT NULL COMMENT 'Average daily CPU utilization (%)',
    avg_memory_usage_percent DECIMAL(5,2) NOT NULL COMMENT 'Average daily memory utilization (%)',
    max_network_out_mbps DECIMAL(8,2) NOT NULL COMMENT 'Peak daily outbound bandwidth (Mbps)',
    INDEX idx_instance_date (instance_id, metric_date),
    INDEX idx_user_instance (user_id, instance_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Instance daily metrics table';

TRUNCATE TABLE instance_metrics_daily;

INSERT INTO instance_metrics_daily (instance_id, user_id, metric_date, avg_cpu_usage_percent, avg_memory_usage_percent, max_network_out_mbps) VALUES
('i-bp1_user1001_ecs', 'user_1001', DATE_SUB(CURDATE(), INTERVAL 6 DAY), 2.10, 18.50, 1.20),
('i-bp1_user1001_ecs', 'user_1001', DATE_SUB(CURDATE(), INTERVAL 5 DAY), 2.50, 19.10, 1.60),
('i-bp1_user1001_ecs', 'user_1001', DATE_SUB(CURDATE(), INTERVAL 4 DAY), 3.20, 20.40, 2.00),
('i-bp1_user1001_ecs', 'user_1001', DATE_SUB(CURDATE(), INTERVAL 3 DAY), 1.90, 17.90, 1.00),
('i-bp1_user1001_ecs', 'user_1001', DATE_SUB(CURDATE(), INTERVAL 2 DAY), 2.80, 18.20, 1.40),
('i-bp1_user1001_ecs', 'user_1001', DATE_SUB(CURDATE(), INTERVAL 1 DAY), 2.40, 19.00, 1.30),
('i-bp1_user1001_ecs', 'user_1001', CURDATE(), 2.00, 18.70, 1.10),
('i-bp1_user1002_ecs', 'user_1002', DATE_SUB(CURDATE(), INTERVAL 6 DAY), 36.50, 62.10, 42.00),
('i-bp1_user1002_ecs', 'user_1002', DATE_SUB(CURDATE(), INTERVAL 5 DAY), 41.20, 65.00, 51.00),
('i-bp1_user1002_ecs', 'user_1002', DATE_SUB(CURDATE(), INTERVAL 4 DAY), 38.40, 63.50, 48.00),
('i-bp1_user1002_ecs', 'user_1002', DATE_SUB(CURDATE(), INTERVAL 3 DAY), 44.00, 67.30, 55.00),
('i-bp1_user1002_ecs', 'user_1002', DATE_SUB(CURDATE(), INTERVAL 2 DAY), 39.10, 60.80, 47.00),
('i-bp1_user1002_ecs', 'user_1002', DATE_SUB(CURDATE(), INTERVAL 1 DAY), 42.80, 64.20, 53.00),
('i-bp1_user1002_ecs', 'user_1002', CURDATE(), 40.30, 61.90, 49.00);
