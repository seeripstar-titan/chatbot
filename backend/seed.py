"""
Database seeder – populates the database with sample data for development/demo.
Run with: python -m backend.seed
"""

import asyncio
import uuid
from datetime import datetime, timedelta, timezone

from backend.auth.api_keys import generate_api_key
from backend.config import get_settings
from backend.db.models import (
    FAQ,
    APIKey,
    EndUser,
    Order,
    OrderStatus,
    Product,
    Tenant,
    TenantStatus,
)
from backend.db.session import async_session_factory, init_db
from backend.auth.passwords import hash_password
from backend.logging_config import setup_logging, get_logger

settings = get_settings()
logger = get_logger(__name__)


async def seed_database():
    """Seed the database with sample data."""
    setup_logging(log_level="INFO", log_format="console")

    # Initialize tables
    await init_db()
    logger.info("database_initialized")

    async with async_session_factory() as session:
        # ── Create Demo Tenant ───────────────────────────────────────────
        tenant = Tenant(
            name="GemAssist",
            domain="demo.techstore.com",
            status=TenantStatus.ACTIVE,
            welcome_message=(
                "👋 Welcome to Gemistry: The Science of Sparkle! \nI'm your AI assistant. "
                "I can help you with:\n\n"
                "🔍 **Product search** — Find the perfect product\n"
                "📦 **Order tracking** — Check your order status\n"
                "❓ **Support** — Answer your questions\n\n"
                "How can I help you today?"
            ),
            system_prompt=(
                """You are a friendly and knowledgeable Jewellery Store Assistant. Help customers search, compare, and purchase jewellery such as rings, necklaces, earrings, bracelets, and custom pieces.
                Provide clear product details (materials, pricing, craftsmanship, care, sizing) and offer styling or gift recommendations when relevant.
                Support customers with product search, order tracking, and general support including returns, resizing, repairs, and warranties.
                Maintain a warm, professional tone, ask clarifying questions about preferences (budget, occasion, metal, gemstone), and ensure a smooth, confident shopping experience."""
        ))
        session.add(tenant)
        await session.flush()

        logger.info("tenant_created", tenant_name=tenant.name, tenant_id=str(tenant.id))

        # ── Generate API Key ─────────────────────────────────────────────
        raw_key, key_hash, key_prefix = generate_api_key()
        api_key = APIKey(
            tenant_id=tenant.id,
            key_hash=key_hash,
            key_prefix=key_prefix,
            name="Demo API Key",
            is_active=True,
            allowed_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:8000"],
        )
        session.add(api_key)

        # ── Create Demo End User ─────────────────────────────────────────
        demo_user = EndUser(
            tenant_id=tenant.id,
            email="john@example.com",
            name="John Doe",
            is_verified=True,
            password_hash=hash_password("password123"),
        )
        session.add(demo_user)

        # ── Seed Products ────────────────────────────────────────────────
        products = [
            Product(
                tenant_id=tenant.id,
                sku="WH-1000XM5",
                name="Sony WH-1000XM5 Wireless Noise Cancelling Headphones",
                description=(
                    "Industry-leading noise cancellation with Auto NC Optimizer. "
                    "Crystal clear hands-free calling with 4 beamforming microphones. "
                    "Up to 30 hours battery life with quick charging. "
                    "Lightweight design at just 250g for all-day comfort."
                ),
                category="Audio",
                price=349.99,
                currency="USD",
                in_stock=True,
                stock_quantity=150,
                specifications={
                    "driver_size": "30mm",
                    "frequency_response": "4Hz-40kHz",
                    "battery_life": "30 hours",
                    "weight": "250g",
                    "bluetooth": "5.2",
                    "noise_cancelling": "Yes, Adaptive",
                    "color_options": ["Black", "Silver", "Midnight Blue"],
                },
                image_url="https://example.com/images/wh1000xm5.jpg",
            ),
            Product(
                tenant_id=tenant.id,
                sku="MBA-M3-15",
                name='MacBook Air 15" M3',
                description=(
                    "Supercharged by the M3 chip. The remarkably thin 15-inch MacBook Air "
                    "features up to 18 hours of battery life, a stunning Liquid Retina display, "
                    "8-core CPU, 10-core GPU, and supports up to 24GB of unified memory."
                ),
                category="Laptops",
                price=1299.00,
                currency="USD",
                in_stock=True,
                stock_quantity=45,
                specifications={
                    "processor": "Apple M3",
                    "ram": "8GB unified memory",
                    "storage": "256GB SSD",
                    "display": "15.3-inch Liquid Retina",
                    "battery": "Up to 18 hours",
                    "weight": "1.51kg",
                    "ports": ["2x Thunderbolt/USB-4", "MagSafe 3", "3.5mm headphone jack"],
                },
                image_url="https://example.com/images/macbook-air-15.jpg",
            ),
            Product(
                tenant_id=tenant.id,
                sku="IPHONE-16-PRO",
                name="iPhone 16 Pro",
                description=(
                    "The ultimate iPhone experience. Featuring the A18 Pro chip, "
                    "48MP camera system with 5x optical zoom, titanium design, "
                    "and all-day battery life. Available in 4 stunning finishes."
                ),
                category="Smartphones",
                price=999.00,
                currency="USD",
                in_stock=True,
                stock_quantity=200,
                specifications={
                    "processor": "A18 Pro",
                    "storage_options": ["128GB", "256GB", "512GB", "1TB"],
                    "display": "6.3-inch Super Retina XDR, ProMotion 120Hz",
                    "camera": "48MP main + 48MP ultrawide + 12MP telephoto (5x zoom)",
                    "battery": "All-day battery life",
                    "material": "Grade 5 Titanium",
                    "colors": ["Desert Titanium", "Natural Titanium", "White Titanium", "Black Titanium"],
                },
                image_url="https://example.com/images/iphone-16-pro.jpg",
            ),
            Product(
                tenant_id=tenant.id,
                sku="SAMSUNG-S24-ULTRA",
                name="Samsung Galaxy S24 Ultra",
                description=(
                    "The most powerful Galaxy smartphone. Features a 6.8-inch QHD+ display, "
                    "200MP camera, Snapdragon 8 Gen 3 processor, built-in S Pen, "
                    "and Galaxy AI features for incredible productivity."
                ),
                category="Smartphones",
                price=1199.99,
                currency="USD",
                in_stock=True,
                stock_quantity=80,
                specifications={
                    "processor": "Snapdragon 8 Gen 3",
                    "ram": "12GB",
                    "storage_options": ["256GB", "512GB", "1TB"],
                    "display": "6.8-inch QHD+ Dynamic AMOLED 2X, 120Hz",
                    "camera": "200MP main + 50MP telephoto (5x) + 10MP telephoto (3x) + 12MP ultrawide",
                    "battery": "5000mAh",
                    "s_pen": "Built-in",
                },
                image_url="https://example.com/images/galaxy-s24-ultra.jpg",
            ),
            Product(
                tenant_id=tenant.id,
                sku="AIRPODS-PRO-2",
                name="Apple AirPods Pro 2 (USB-C)",
                description=(
                    "Reimagined Pro-level active noise cancellation. Adaptive Audio seamlessly "
                    "blends transparency and noise cancellation. Personalized Spatial Audio. "
                    "Up to 6 hours of listening time with ANC enabled."
                ),
                category="Audio",
                price=249.00,
                currency="USD",
                in_stock=True,
                stock_quantity=300,
                specifications={
                    "chip": "H2",
                    "anc": "Active Noise Cancellation with Adaptive Transparency",
                    "battery_buds": "6 hours (ANC on)",
                    "battery_case": "30 hours total",
                    "connector": "USB-C",
                    "water_resistance": "IPX4",
                    "spatial_audio": "Yes, Personalized",
                },
                image_url="https://example.com/images/airpods-pro-2.jpg",
            ),
            Product(
                tenant_id=tenant.id,
                sku="DELL-U2723QE",
                name='Dell UltraSharp U2723QE 27" 4K USB-C Hub Monitor',
                description=(
                    "Stunning 4K resolution with IPS Black technology for deeper blacks. "
                    "USB-C hub with 90W power delivery. Factory calibrated for color accuracy. "
                    "Perfect for creative professionals and productivity."
                ),
                category="Monitors",
                price=619.99,
                currency="USD",
                in_stock=False,
                stock_quantity=0,
                specifications={
                    "resolution": "3840 x 2160 (4K UHD)",
                    "panel": "IPS Black",
                    "size": "27 inches",
                    "ports": ["USB-C (90W PD)", "HDMI", "DisplayPort", "USB-A Hub", "RJ45"],
                    "refresh_rate": "60Hz",
                    "color_accuracy": "98% DCI-P3",
                    "vesa_mount": "100x100mm",
                },
                image_url="https://example.com/images/dell-u2723qe.jpg",
            ),
            Product(
                tenant_id=tenant.id,
                sku="LOGITECH-MX-MASTER",
                name="Logitech MX Master 3S Wireless Mouse",
                description=(
                    "The most advanced master series mouse. Features MagSpeed scroll wheel, "
                    "8K DPI sensor, quiet clicks, and multi-device connectivity. "
                    "Works on virtually any surface including glass."
                ),
                category="Accessories",
                price=99.99,
                currency="USD",
                in_stock=True,
                stock_quantity=500,
                specifications={
                    "sensor": "8000 DPI Darkfield",
                    "buttons": "7 buttons",
                    "battery": "Up to 70 days on full charge",
                    "connectivity": ["Bluetooth", "USB-C Dongle (Logi Bolt)"],
                    "multi_device": "Up to 3 devices",
                    "weight": "141g",
                },
                image_url="https://example.com/images/mx-master-3s.jpg",
            ),
            Product(
                tenant_id=tenant.id,
                sku="IPAD-AIR-M2",
                name="iPad Air M2 11-inch",
                description=(
                    "Supercharged by the M2 chip. Features a beautiful 11-inch Liquid Retina display, "
                    "12MP camera, Wi-Fi 6E, and all-day battery life. "
                    "Works with Apple Pencil Pro and Magic Keyboard."
                ),
                category="Tablets",
                price=599.00,
                currency="USD",
                in_stock=True,
                stock_quantity=120,
                specifications={
                    "processor": "Apple M2",
                    "display": "11-inch Liquid Retina",
                    "storage_options": ["128GB", "256GB", "512GB", "1TB"],
                    "camera": "12MP Wide",
                    "battery": "Up to 10 hours",
                    "connectivity": "Wi-Fi 6E",
                    "compatible_accessories": ["Apple Pencil Pro", "Magic Keyboard"],
                },
                image_url="https://example.com/images/ipad-air-m2.jpg",
            ),
        ]

        for product in products:
            session.add(product)

        # ── Seed Orders ──────────────────────────────────────────────────
        now = datetime.now(timezone.utc)
        orders = [
            Order(
                tenant_id=tenant.id,
                order_number="ORD-001",
                customer_email="john@example.com",
                customer_name="John Doe",
                status=OrderStatus.DELIVERED,
                items=[
                    {"sku": "WH-1000XM5", "name": "Sony WH-1000XM5", "quantity": 1, "price": 349.99},
                ],
                total_amount=349.99,
                currency="USD",
                shipping_address={
                    "street": "123 Main St",
                    "city": "San Francisco",
                    "state": "CA",
                    "zip": "94102",
                    "country": "US",
                },
                tracking_number="TRK-9876543210",
                carrier="FedEx",
                estimated_delivery=now - timedelta(days=2),
                shipped_at=now - timedelta(days=7),
                delivered_at=now - timedelta(days=2),
            ),
            Order(
                tenant_id=tenant.id,
                order_number="ORD-002",
                customer_email="john@example.com",
                customer_name="John Doe",
                status=OrderStatus.IN_TRANSIT,
                items=[
                    {"sku": "MBA-M3-15", "name": 'MacBook Air 15" M3', "quantity": 1, "price": 1299.00},
                    {"sku": "LOGITECH-MX-MASTER", "name": "Logitech MX Master 3S", "quantity": 1, "price": 99.99},
                ],
                total_amount=1398.99,
                currency="USD",
                shipping_address={
                    "street": "123 Main St",
                    "city": "San Francisco",
                    "state": "CA",
                    "zip": "94102",
                    "country": "US",
                },
                tracking_number="TRK-1234567890",
                carrier="UPS",
                estimated_delivery=now + timedelta(days=3),
                shipped_at=now - timedelta(days=2),
            ),
            Order(
                tenant_id=tenant.id,
                order_number="ORD-003",
                customer_email="jane@example.com",
                customer_name="Jane Smith",
                status=OrderStatus.PROCESSING,
                items=[
                    {"sku": "IPHONE-16-PRO", "name": "iPhone 16 Pro", "quantity": 1, "price": 999.00},
                    {"sku": "AIRPODS-PRO-2", "name": "AirPods Pro 2", "quantity": 1, "price": 249.00},
                ],
                total_amount=1248.00,
                currency="USD",
                shipping_address={
                    "street": "456 Oak Ave",
                    "city": "New York",
                    "state": "NY",
                    "zip": "10001",
                    "country": "US",
                },
            ),
            Order(
                tenant_id=tenant.id,
                order_number="ORD-004",
                customer_email="john@example.com",
                customer_name="John Doe",
                status=OrderStatus.PENDING,
                items=[
                    {"sku": "IPAD-AIR-M2", "name": "iPad Air M2", "quantity": 1, "price": 599.00},
                ],
                total_amount=599.00,
                currency="USD",
                shipping_address={
                    "street": "123 Main St",
                    "city": "San Francisco",
                    "state": "CA",
                    "zip": "94102",
                    "country": "US",
                },
            ),
        ]

        for order in orders:
            session.add(order)

        # ── Seed FAQs ────────────────────────────────────────────────────
        faqs = [
            FAQ(
                tenant_id=tenant.id,
                question="What is your return policy?",
                answer=(
                    "We offer a **30-day return policy** for all products. Items must be in "
                    "their original packaging and in unused condition. To initiate a return, "
                    "please contact our support team with your order number. Refunds are "
                    "processed within 5-7 business days after we receive the returned item."
                ),
                category="returns",
                keywords=["return", "refund", "send back", "exchange", "money back"],
            ),
            FAQ(
                tenant_id=tenant.id,
                question="How long does shipping take?",
                answer=(
                    "**Standard shipping**: 5-7 business days\n"
                    "**Express shipping**: 2-3 business days\n"
                    "**Overnight shipping**: Next business day\n\n"
                    "Free standard shipping is available on orders over $50. "
                    "Express and overnight shipping costs are calculated at checkout based on weight and destination."
                ),
                category="shipping",
                keywords=["shipping", "delivery", "how long", "transit", "free shipping"],
            ),
            FAQ(
                tenant_id=tenant.id,
                question="What payment methods do you accept?",
                answer=(
                    "We accept the following payment methods:\n\n"
                    "- **Credit/Debit Cards**: Visa, Mastercard, American Express, Discover\n"
                    "- **Digital Wallets**: Apple Pay, Google Pay, PayPal\n"
                    "- **Buy Now, Pay Later**: Affirm, Klarna (available on orders over $100)\n"
                    "- **Gift Cards**: TechStore gift cards\n\n"
                    "All transactions are secured with 256-bit SSL encryption."
                ),
                category="payment",
                keywords=["payment", "pay", "credit card", "paypal", "apple pay", "financing"],
            ),
            FAQ(
                tenant_id=tenant.id,
                question="Do you offer a warranty?",
                answer=(
                    "Yes! All products come with the **manufacturer's warranty** (typically 1-2 years). "
                    "Additionally, we offer **TechStore Extended Protection**:\n\n"
                    "- **1-year extension**: $29.99 for items under $500, $49.99 for items over $500\n"
                    "- **2-year extension**: $49.99 for items under $500, $79.99 for items over $500\n\n"
                    "Extended protection covers accidental damage, defects, and battery degradation."
                ),
                category="warranty",
                keywords=["warranty", "guarantee", "protection", "coverage", "defect", "broken"],
            ),
            FAQ(
                tenant_id=tenant.id,
                question="How can I track my order?",
                answer=(
                    "You can track your order in several ways:\n\n"
                    "1. **Chat with me**: Just provide your order number and email, and I'll look it up!\n"
                    "2. **Email**: Check the shipping confirmation email for a tracking link\n"
                    "3. **Account**: Log into your account to see all order statuses\n\n"
                    "You'll receive email updates when your order is confirmed, shipped, and delivered."
                ),
                category="shipping",
                keywords=["track", "tracking", "where is my order", "order status", "shipment"],
            ),
            FAQ(
                tenant_id=tenant.id,
                question="Do you offer price matching?",
                answer=(
                    "Yes! We offer **price matching** within 14 days of purchase. If you find "
                    "the same product at a lower price from an authorized retailer, we'll match it. "
                    "Contact our support team with the competitor's listing and we'll issue a price adjustment.\n\n"
                    "**Note**: Price matching does not apply to marketplace sellers, flash sales, "
                    "or clearance items."
                ),
                category="pricing",
                keywords=["price match", "cheaper", "lower price", "best price", "competitor"],
            ),
            FAQ(
                tenant_id=tenant.id,
                question="How do I cancel an order?",
                answer=(
                    "To cancel an order:\n\n"
                    "1. If the order hasn't shipped yet, contact us immediately and we can cancel it\n"
                    "2. If the order has already shipped, you'll need to wait for delivery and then initiate a return\n\n"
                    "Please note that orders in **Processing** status can usually be cancelled. "
                    "Once an order moves to **Shipped**, cancellation is no longer possible."
                ),
                category="orders",
                keywords=["cancel", "cancellation", "stop order", "don't want"],
            ),
            FAQ(
                tenant_id=tenant.id,
                question="Do you ship internationally?",
                answer=(
                    "Currently, we ship to the following countries:\n\n"
                    "- **North America**: USA, Canada, Mexico\n"
                    "- **Europe**: UK, Germany, France, Italy, Spain, Netherlands\n"
                    "- **Asia-Pacific**: Japan, Australia, Singapore\n\n"
                    "International shipping takes 7-14 business days. Import duties and taxes "
                    "may apply and are the responsibility of the customer."
                ),
                category="shipping",
                keywords=["international", "overseas", "global", "outside US", "abroad"],
            ),
        ]

        for faq in faqs:
            session.add(faq)

        await session.commit()

        # Print the API key
        print("\n" + "=" * 60)
        print("🚀 DATABASE SEEDED SUCCESSFULLY!")
        print("=" * 60)
        print(f"\n📋 Tenant: {tenant.name}")
        print(f"🆔 Tenant ID: {tenant.id}")
        print(f"\n🔑 API Key (save this — shown only once):")
        print(f"   {raw_key}")
        print(f"\n👤 Demo User: john@example.com / password123")
        print(f"\n📦 Sample Orders: ORD-001, ORD-002, ORD-003, ORD-004")
        print(f"🛍️  Sample Products: {len(products)} products")
        print(f"❓ Sample FAQs: {len(faqs)} FAQs")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(seed_database())
