import json
from mcp_server import query_user_orders, query_user_instances

def test_db_tools():
    print("="*50)
    print("🚀 Testing MCP database query tools...")
    print("="*50)
    
    print("\n[Test 1] Simulate system injection: query orders for user_1001 (high-value customer)")
    result1 = query_user_orders(user_id="user_1001", limit=10)
    parsed_res1 = json.loads(result1)
    if parsed_res1.get("status") == "success":
        print(f"✅ Successfully retrieved {len(parsed_res1['data'])} order(s) for user_1001")
        print(json.dumps(parsed_res1['data'][:1], ensure_ascii=False, indent=2))
    else:
        print(f"❌ Query failed: {parsed_res1.get('message')}")
        
    print("\n[Test 2] Simulate system injection: query all instance statuses for user_1002 (no instance ID required)")
    result2 = query_user_instances(user_id="user_1002")
    parsed_res2 = json.loads(result2)
    if parsed_res2.get("status") == "success":
        print(f"✅ Successfully retrieved {len(parsed_res2['data'])} instance status(es) for user_1002")
        print(json.dumps(parsed_res2['data'], ensure_ascii=False, indent=2))
    else:
        print(f"❌ Query failed: {parsed_res2.get('message')}")

    print("\n[Test 3] Privilege escalation guard test (query non-existent user user_9999)")
    result3 = query_user_instances(user_id="user_9999")
    parsed_res3 = json.loads(result3)
    print(f"✅ Guard result (should be empty): {parsed_res3.get('message')}")

if __name__ == "__main__":
    test_db_tools()