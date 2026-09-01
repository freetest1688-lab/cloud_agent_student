import os
import pymysql
import json
import asyncio
import time
import requests
import sys
from decimal import Decimal
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# ==============================================================================
# Initialize environment configuration
# ==============================================================================
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path)

# ==============================================================================
# Initialize FastMCP server
# This server can run standalone, supporting SSE or stdio protocols
# ==============================================================================
mcp = FastMCP("CloudPlatformMCPServer")

# ==============================================================================
# Database connection helper
# ==============================================================================
def get_db_connection():
    """Get a remote MySQL connection. Use a connection pool in production."""
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST", "YOUR_MYSQL_HOST"),
        port=int(os.getenv("MYSQL_PORT", 3306)),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", "YOUR_MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE", "cloud_platform"),
        cursorclass=pymysql.cursors.DictCursor # Return results as dicts for easy JSON serialization
    )

# ==============================================================================
# MCP core tool definitions (Tools)
# ==============================================================================

# Simulated cloud product catalog database (based on real mock_data docs)
PRODUCT_CATALOG = {
    "P_ECS_G8A_XLARGE": {
        "name": "8th-Gen Enterprise General-Purpose Instance ecs.g8a.xlarge",
        "keywords": ["ecs", "cloud server", "general purpose", "g8a", "4c16g", "amd", "genoa"],
        "price": 299.0,
    },
    "P_ECS_C7_8XLARGE": {
        "name": "7th-Gen Enterprise Compute-Optimized Instance ecs.c7.8xlarge",
        "keywords": ["ecs", "cloud server", "compute optimized", "c7", "32c64g", "high concurrency", "intel"],
        "price": 1299.0,
    },
    "P_GPU_GN7I": {
        "name": "GPU Compute Instance ecs.gn7i-c8g1.2xlarge",
        "keywords": ["gpu", "compute", "llm", "a10", "deep learning", "inference", "gn7i"],
        "price": 3500.0,
    },
    "P_RDS_MYSQL_HA": {
        "name": "Cloud Database RDS MySQL High-Availability Edition",
        "keywords": ["rds", "mysql", "database", "relational", "high availability", "primary-standby", "geo-redundant"],
        "price": 599.0,
    },
    "P_ESSD_PL1": {
        "name": "ESSD PL1 Performance Cloud Disk",
        "keywords": ["cloud disk", "block storage", "essd", "pl1", "storage"],
        "price": 50.0,
    }
}

@mcp.tool()
def get_promotable_products() -> str:
    """
    Call when the user says "I want to promote products", "I want to earn money",
    or "what products can I promote".
    Returns the list of all products currently available for promotion and commission.
    """
    promotable_list = []
    for pid, pinfo in PRODUCT_CATALOG.items():
        # P_ESSD_PL1 does not support standalone promotion; filter it out as a demo
        if pid != "P_ESSD_PL1":
            promotable_list.append({
                "product_id": pid,
                "product_name": pinfo["name"],
                "price": pinfo["price"]
            })
            
    return json.dumps({
        "status": "success",
        "message": "Here are all promotable products:",
        "data": promotable_list
    }, ensure_ascii=False)

@mcp.tool()
def search_product_catalog(keyword: str) -> str:
    """
    Fuzzy-search the product catalog based on natural-language descriptions such as
    "cloud server", "2c4g", or "GPU", and return matching products with their product IDs.

    Args:
        keyword: Product keyword(s) described by the user.
    """
    results = []
    kw_lower = keyword.lower()
    
    for pid, pinfo in PRODUCT_CATALOG.items():
        # Simple keyword matching simulation
        if kw_lower in pinfo["name"].lower() or any(kw_lower in k for k in pinfo["keywords"]):
            results.append({
                "product_id": pid,
                "product_name": pinfo["name"],
                "price": pinfo["price"]
            })
            
    if not results:
        # No exact match; return not_found with a generic recommendation
        return json.dumps({
            "status": "not_found", 
            "message": f"No product exactly matching '{keyword}' was found.", 
            "recommendation": {"product_id": "P_ALL_000", "product_name": "All-Category Cloud Product Campaign"}
        }, ensure_ascii=False)
        
    return json.dumps({"status": "success", "data": results}, ensure_ascii=False)

@mcp.tool()
def get_promotion_materials(product_id: str, user_id: str = "") -> str:
    """
    Retrieve the exclusive promotion link and commission campaign details for a given product ID.
    Must call search_product_catalog first to obtain the exact product_id before calling this tool.

    Args:
        product_id: A canonical product ID such as "P_ECS_G8A_XLARGE" or "P_GPU_GN7I".
        user_id: [System-injected] The current user's ID, used to generate a personalized referral link.
    """
    # Simulated marketing material from the backend system (keyed by product_id)
    promotions = {
        "P_ECS_G8A_XLARGE": {
            "title": "ECS 8th-Gen General-Purpose (g8a.xlarge) Developer Discount",
            "desc": "Powered by AMD EPYC 9004, 4c16G. Up to 10 Gbps network bandwidth. 15% off in the first year — a top pick for enterprise cloud migration!",
            "base_link": "https://promotion.cloud.com/ecs-g8a-special",
            "commission_rate": "15%"
        },
        "P_ECS_C7_8XLARGE": {
            "title": "ECS 7th-Gen Compute-Optimized (c7.8xlarge) Big Sale",
            "desc": "32c64G, up to 40 Gbps and 12M PPS! Built for high-concurrency web workloads. Buy an annual plan and receive a free 100G ESSD PL1 disk!",
            "base_link": "https://promotion.cloud.com/ecs-c7-high-concurrency",
            "commission_rate": "18%"
        },
        "P_GPU_GN7I": {
            "title": "GPU Compute Discount (gn7i-c8g1.2xlarge)",
            "desc": "Equipped with 1x NVIDIA A10 GPU (24 GB VRAM). Designed for deep-learning inference and AIGC generation. Order now for 50% off the first month, pairs seamlessly with ESSD PL2!",
            "base_link": "https://promotion.cloud.com/gpu-a10-aigc",
            "commission_rate": "25%"
        },
        "P_RDS_MYSQL_HA": {
            "title": "RDS MySQL High-Availability Edition — Best for Active-Active Geo-Redundancy",
            "desc": "Primary/standby dual-node architecture with automatic failover within 30 seconds. Guarantees 99.99% availability. Activate now and get a free read/write split proxy!",
            "base_link": "https://promotion.cloud.com/rds-mysql-ha",
            "commission_rate": "12%"
        },
        "P_ALL_000": {
            "title": "Cloud All-in-One Bundle Discount",
            "desc": "All cloud products (ECS, RDS, cloud disks) — spend 1000, save 100. The more you buy, the more you save.",
            "base_link": "https://promotion.cloud.com/all-in-one",
            "commission_rate": "10%"
        }
    }
    
    promo = promotions.get(product_id, promotions["P_ALL_000"])
    
    # Core logic: use the injected user_id to build a personalized referral link
    exclusive_link = f"{promo['base_link']}?inviter={user_id}&pid={product_id}" if user_id else promo['base_link']
    
    result = {
        "status": "success",
        "data": {
            "product_id": product_id,
            "activity_title": promo["title"],
            "selling_points": promo["desc"],
            "exclusive_link": exclusive_link,
            "commission_rate": promo["commission_rate"]
        }
    }
    return json.dumps(result, ensure_ascii=False)

@mcp.tool()
def generate_ai_poster(prompt: str) -> str:
    """
    Call the Qwen text-to-image model qwen-image-2.0 to generate a vertical promotional poster based on a prompt.

    Args:
        prompt: Detailed image generation prompt (e.g. "cyberpunk-style server room, cool blue neon lights, tech aesthetic, vertical poster style").
    """
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        return json.dumps({"status": "error", "message": "DASHSCOPE_API_KEY is not configured"}, ensure_ascii=False)

    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "model": "qwen-image-2.0",
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": prompt}]
                }
            ]
        },
        "parameters": {
            "negative_prompt": "low resolution, low quality, distorted limbs, distorted fingers, oversaturated colors, wax figure look, no facial details, overly smooth, blurry text, chaotic composition",
            "prompt_extend": True,
            "watermark": False,
            "size": "1536*2688"
        }
    }

    last_error = "Generation failed"
    for attempt in range(1, 3):
        try:
            sys.stderr.write(f"[AI-POSTER][QWEN] attempt={attempt} submit start\n")
            res = requests.post(url, json=payload, headers=headers, timeout=120)
            data = res.json()
            request_id = data.get("request_id", "")
            sys.stderr.write(f"[AI-POSTER][QWEN] attempt={attempt} status={res.status_code} request_id={request_id}\n")

            image_url = (
                data.get("output", {})
                .get("choices", [{}])[0]
                .get("message", {})
                .get("content", [{}])[0]
                .get("image")
            )
            if res.status_code == 200 and image_url:
                sys.stderr.write(f"[AI-POSTER][QWEN] attempt={attempt} success\n")
                return json.dumps({
                    "status": "success",
                    "data": {
                        "poster_url": image_url,
                        "message": "Poster generated successfully (Qwen-Image)",
                        "request_id": request_id
                    }
                }, ensure_ascii=False)

            last_error = data.get("message") or data.get("code") or f"HTTP {res.status_code}"
            sys.stderr.write(f"[AI-POSTER][QWEN] attempt={attempt} failed: {last_error}\n")
        except Exception as e:
            last_error = str(e)
            sys.stderr.write(f"[AI-POSTER][QWEN] attempt={attempt} exception: {last_error}\n")

    return json.dumps({"status": "error", "message": f"Qwen-Image generation failed: {last_error}"}, ensure_ascii=False)

@mcp.tool()
def query_user_orders(user_id: str, limit: int = 5) -> str:
    """
    Query the user's cloud server orders and billing records.

    Args:
        user_id: [System-injected] The user's unique identifier; must not be fabricated by the model.
        limit: [Model-generated] Maximum number of records to return; default is 5.
    """
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = """
                SELECT order_id, product_name, billing_mode, amount, status, DATE_FORMAT(created_at, '%%Y-%%m-%%d %%H:%%i:%%s') as created_at
                FROM cloud_orders 
                WHERE user_id = %s 
                ORDER BY created_at DESC 
                LIMIT %s
            """
            cursor.execute(sql, (user_id, limit))
            results = cursor.fetchall()
            
            if not results:
                return json.dumps({"status": "success", "message": "This user has no order records."}, ensure_ascii=False)
                
            for row in results:
                if 'amount' in row and row['amount'] is not None:
                    row['amount'] = float(row['amount'])
                    
            return json.dumps({"status": "success", "data": results}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Database query failed: {str(e)}"}, ensure_ascii=False)
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()

@mcp.tool()
def query_user_instances(user_id: str, limit: int = 5) -> str:
    """
    Query the server instance status for a given user, returning instance ID, spec, public IP, and running state.
    The system-injected user_id must be provided.
    """
    sql = """
        SELECT instance_id, instance_type, region_id, zone_id, public_ip, status
        FROM cloud_instances
        WHERE user_id = %s
        ORDER BY instance_id DESC
        LIMIT %s
    """
    
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(sql, (user_id, limit))
            result = cursor.fetchall()
            
            if not result:
                return json.dumps({"status": "success", "message": f"No server instances found for your account."}, ensure_ascii=False)
            
            return json.dumps({"status": "success", "data": result}, ensure_ascii=False)
            
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Database query failed: {str(e)}"}, ensure_ascii=False)
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()

@mcp.tool()
def analyze_instance_usage(instance_id: str, user_id: str = "") -> str:
    """
    Retrieve the 7-day average CPU utilization, memory utilization, and peak bandwidth for a given instance.
    Commonly used in architecture diagnostics or FinOps cost-optimization scenarios to determine whether resources are idle.

    Args:
        instance_id: The unique ID of the server instance, e.g. "i-bp1abcdefg". Must be obtained via query_user_instances first.
        user_id: [System-injected] The current user's ID, used for authorization to prevent unauthorized access to other users' monitoring data.
    """
    if not instance_id:
        return json.dumps({"status": "error", "message": "instance_id is required"}, ensure_ascii=False)
    
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            auth_sql = """
                SELECT instance_id
                FROM cloud_instances
                WHERE instance_id = %s AND user_id = %s
                LIMIT 1
            """
            cursor.execute(auth_sql, (instance_id, user_id))
            owned_instance = cursor.fetchone()
            if not owned_instance:
                return json.dumps({"status": "error", "message": "Instance not found or you do not have permission to view its monitoring data."}, ensure_ascii=False)

            metrics_sql = """
                SELECT
                    ROUND(AVG(avg_cpu_usage_percent), 2) AS cpu_usage_percent,
                    ROUND(AVG(avg_memory_usage_percent), 2) AS memory_usage_percent,
                    ROUND(MAX(max_network_out_mbps), 2) AS network_out_bandwidth_mbps,
                    COUNT(*) AS days_count
                FROM instance_metrics_daily
                WHERE instance_id = %s
                  AND user_id = %s
                  AND metric_date >= DATE_SUB(CURDATE(), INTERVAL 6 DAY)
            """
            cursor.execute(metrics_sql, (instance_id, user_id))
            agg = cursor.fetchone()

            if not agg or not agg.get("days_count"):
                return json.dumps({"status": "error", "message": "No monitoring data found for this instance in the past 7 days. Please try again later."}, ensure_ascii=False)

            cpu = float(agg["cpu_usage_percent"] or 0)
            memory = float(agg["memory_usage_percent"] or 0)
            bandwidth = float(agg["network_out_bandwidth_mbps"] or 0)

            if cpu < 10 and memory < 30:
                diagnosis = "RESOURCES_IDLE"
            elif cpu > 70 or memory > 80:
                diagnosis = "RESOURCES_TIGHT"
            else:
                diagnosis = "RESOURCES_NORMAL"

            result = {
                "instance_id": instance_id,
                "owner_id": user_id,
                "metrics_7d_avg": {
                    "cpu_usage_percent": cpu,
                    "memory_usage_percent": memory,
                    "network_out_bandwidth_mbps": bandwidth
                },
                "diagnosis": diagnosis
            }
            return json.dumps({"status": "success", "data": result}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Failed to query monitoring data: {str(e)}"}, ensure_ascii=False)
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()

@mcp.tool()
def get_promotion_materials(product_name: str, user_id: str = "") -> str:
    """
    Retrieve the promotional poster, exclusive link, and commission campaign details for a given product name.
    Call when the user says "I want to share this product" or "are there any GPU-related campaigns".

    Args:
        product_name: The name of the product to promote or query, e.g. "ECS", "GPU", "RDS".
        user_id: [System-injected] The current user's ID, used to generate a personalized referral link.
    """
    # Simulated marketing material from the backend system
    promotions = {
        "ecs": {
            "title": "Cloud Server ECS New-User Discount",
            "desc": "Standard 2c4G instance, only ¥99 for the first year! Top choice for enterprise cloud migration, unbeatable value.",
            "base_link": "https://promotion.cloud.com/ecs-new-user",
            "poster": "https://img.cloud.com/posters/ecs_2c4g_99.png",
            "commission_rate": "15%"
        },
        "gpu": {
            "title": "GPU Compute Dark Horse Discount Season",
            "desc": "A10/V100/A800 GPU instances available on-demand — the perfect partner for LLM training and inference. ¥500 off your first order!",
            "base_link": "https://promotion.cloud.com/gpu-ai-special",
            "poster": "https://img.cloud.com/posters/gpu_ai_500.png",
            "commission_rate": "20%"
        },
        "default": {
            "title": "Cloud All-in-One Bundle Discount",
            "desc": "All cloud products — spend 1000, save 100. The more you buy, the more you save.",
            "base_link": "https://promotion.cloud.com/all-in-one",
            "poster": "https://img.cloud.com/posters/all_in_one.png",
            "commission_rate": "10%"
        }
    }
    
    product_lower = product_name.lower()
    key = "default"
    if "ecs" in product_lower or "server" in product_lower:
        key = "ecs"
    elif "gpu" in product_lower or "compute" in product_lower or "llm" in product_lower:
        key = "gpu"
        
    promo = promotions[key]
    
    # Core logic: use the injected user_id to build a personalized referral link
    exclusive_link = f"{promo['base_link']}?inviter={user_id}" if user_id else promo['base_link']
    
    result = {
        "status": "success",
        "data": {
            "activity_title": promo["title"],
            "selling_points": promo["desc"],
            "exclusive_link": exclusive_link,
            "poster_url": promo["poster"],
            "commission_rate": promo["commission_rate"]
        }
    }
    return json.dumps(result, ensure_ascii=False)

# ==============================================================================
# Service startup entry point
# ==============================================================================
if __name__ == "__main__":
    import sys
    sys.stderr.write("🚀 Starting Cloud Platform MCP Server (stdio mode)...\n")
    # FastMCP communicates with the LLM agent via standard input/output (stdio) by default
    mcp.run()
