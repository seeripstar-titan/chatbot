"""
Tool definitions for Gemini function calling.

Each tool maps to a business service function that the LLM can invoke
to answer user queries about products, orders, FAQs, and support.
"""

# Tool declarations in OpenAPI-compatible schema format for Gemini
CHATBOT_TOOLS = [
    {
        "name": "search_products",
        "description": (
            "Search the product catalog by keyword, category, or price range. "
            "Use this when the user asks about products, items, what's available, "
            "pricing, product features, or product comparisons."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search keywords for product name, description, or features",
                },
                "category": {
                    "type": "string",
                    "description": "Product category to filter by (e.g., 'electronics', 'clothing')",
                },
                "min_price": {
                    "type": "number",
                    "description": "Minimum price filter",
                },
                "max_price": {
                    "type": "number",
                    "description": "Maximum price filter",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_product_details",
        "description": (
            "Get detailed information about a specific product by its SKU code. "
            "Use this when the user asks about a specific product, wants full details, "
            "specifications, or availability of a particular item."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "sku": {
                    "type": "string",
                    "description": "The product SKU (stock keeping unit) identifier",
                },
            },
            "required": ["sku"],
        },
    },
    {
        "name": "track_order",
        "description": (
            "Track the status of a customer's order using their order number and email. "
            "Use this when the user wants to check order status, delivery updates, "
            "shipping information, or tracking details. Always ask for both order number "
            "AND email address before calling this function."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "order_number": {
                    "type": "string",
                    "description": "The order number (e.g., 'ORD-001')",
                },
                "customer_email": {
                    "type": "string",
                    "description": "The customer's email address used for the order",
                },
            },
            "required": ["order_number", "customer_email"],
        },
    },
    {
        "name": "get_customer_orders",
        "description": (
            "Retrieve all orders for a customer by their email address. "
            "Use this when a customer wants to see their order history or has "
            "multiple orders and wants an overview."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "customer_email": {
                    "type": "string",
                    "description": "The customer's email address",
                },
            },
            "required": ["customer_email"],
        },
    },
    {
        "name": "search_faqs",
        "description": (
            "Search the FAQ knowledge base for answers to common questions. "
            "Use this for questions about policies, shipping, returns, warranties, "
            "payment methods, account management, or general inquiries."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The question or keywords to search for in FAQs",
                },
                "category": {
                    "type": "string",
                    "description": "FAQ category filter (e.g., 'shipping', 'returns', 'payment')",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "create_support_ticket",
        "description": (
            "Create a customer support ticket for issues that need human attention. "
            "Use this when the chatbot cannot resolve the issue, the customer explicitly "
            "wants to talk to a human, or the issue requires escalation. Always collect "
            "the customer's name, email, and a description of the issue first."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "customer_name": {
                    "type": "string",
                    "description": "The customer's full name",
                },
                "customer_email": {
                    "type": "string",
                    "description": "The customer's email address",
                },
                "subject": {
                    "type": "string",
                    "description": "Brief summary of the issue",
                },
                "description": {
                    "type": "string",
                    "description": "Detailed description of the customer's issue",
                },
                "category": {
                    "type": "string",
                    "description": "Issue category (e.g., 'order_issue', 'product_defect', 'refund', 'general')",
                },
            },
            "required": ["customer_name", "customer_email", "subject", "description"],
        },
    },
    {
        "name": "handoff_to_agent",
        "description": (
            "Transfer the conversation to a live human support agent. "
            "Use this when: 1) the customer explicitly asks to speak with a human/agent/representative, "
            "2) the issue is too complex for AI to resolve (e.g. billing disputes, account security), "
            "3) the customer is clearly frustrated after multiple attempts, or "
            "4) you cannot find the information needed to help them. "
            "Before calling this, briefly explain to the customer that you are connecting them with an agent."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "Brief summary of why the conversation is being handed off (for the agent's context)",
                },
                "customer_name": {
                    "type": "string",
                    "description": "The customer's name if provided during the conversation",
                },
                "customer_email": {
                    "type": "string",
                    "description": "The customer's email if provided during the conversation",
                },
            },
            "required": ["reason"],
        },
    },
]
