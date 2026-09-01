import asyncio
import sys
import os

# Make this directory importable so `from infra.cache ...` works when running directly.
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
if PROJECT_DIR not in sys.path:
    sys.path.append(PROJECT_DIR)

from infra.cache import semantic_cache

# Preset QA pairs (high-frequency standard questions: refund rules, course validity, etc.).
PRESET_QA = [
    {
        "query": "What are the refund rules for ECS cloud servers?",
        "response": "### ☁️ ECS Refund Rules\n\n- **Subscription (pay-as-you-go-yearly/monthly) instances**: Five-day no-questions-asked refund. After five days, the remaining balance is refunded after deducting the prorated cost of days used.\n- **Pay-by-traffic (on-demand) instances**: Not refundable; can be released at any time and billing stops on release.\n- **Refund path**: Console -> Billing Center -> Unsubscribe Management -> Initiate Unsubscribe.\n\n> ⚠️ Note: Promotional/discounted instances may not qualify for the 5-day no-questions-asked refund. Refer to the specific campaign rules."
    },
    {
        "query": "How long does a refund take to arrive?",
        "response": "Once an unsubscribe is initiated and approved, the refund will normally be returned to your original payment account (Alipay, WeChat Pay, or bank card) within **1–3 business days**."
    },
    {
        "query": "How long is your Cloud Architect course valid?",
        "response": "Hi! Our **Cloud Architect Certification Course** is valid for **365 days (one year)** from the date of activation.\n\nDuring the validity period you get unlimited video replay, access to online labs, and one free certification exam attempt. Renewals can be requested by contacting support within 30 days before expiry."
    },
    {
        "query": "How is VPC billed?",
        "response": "VPC itself is **free**.\n\nLogical components inside a VPC (VSwitches, route tables, etc.) are also free of charge. However, the following VPC-related resources do incur charges:\n1. **Elastic IP (EIP)**\n2. **NAT Gateway**\n3. **Cross-region bandwidth via Cloud Enterprise Network (CEN)**\n4. **VPN Gateway**\n\nPlan based on your actual workload requirements."
    }
]

async def preload_cache():
    print("🔄 Warming up the L1 semantic cache...")
    await semantic_cache.initialize()

    for item in PRESET_QA:
        query = item["query"]
        response = item["response"]
        print(f"Injecting -> Query: '{query}'")

        # Embed the question and write it into the Milvus semantic cache collection.
        await semantic_cache.set_cache(query, response)

    print("✅ Cache warmup complete.")

if __name__ == "__main__":
    asyncio.run(preload_cache())
