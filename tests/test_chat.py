"""
Tests for chat tools and prompt configuration.
"""

from backend.chat.tools import CHATBOT_TOOLS
from backend.chat.prompts import build_system_prompt, DEFAULT_SYSTEM_PROMPT


class TestTools:
    def test_all_tools_have_required_fields(self):
        for tool in CHATBOT_TOOLS:
            assert "name" in tool
            assert "description" in tool
            assert "parameters" in tool
            assert tool["parameters"]["type"] == "object"
            assert "properties" in tool["parameters"]
            assert "required" in tool["parameters"]

    def test_tool_names_unique(self):
        names = [t["name"] for t in CHATBOT_TOOLS]
        assert len(names) == len(set(names))

    def test_expected_tools_exist(self):
        names = {t["name"] for t in CHATBOT_TOOLS}
        expected = {
            "search_products",
            "get_product_details",
            "track_order",
            "get_customer_orders",
            "search_faqs",
            "create_support_ticket",
            "handoff_to_agent",
        }
        assert expected == names

    def test_track_order_requires_email_and_number(self):
        track_tool = next(t for t in CHATBOT_TOOLS if t["name"] == "track_order")
        assert "order_number" in track_tool["parameters"]["required"]
        assert "customer_email" in track_tool["parameters"]["required"]

    def test_handoff_tool_requires_reason(self):
        handoff_tool = next(t for t in CHATBOT_TOOLS if t["name"] == "handoff_to_agent")
        assert "reason" in handoff_tool["parameters"]["required"]
        assert "customer_name" in handoff_tool["parameters"]["properties"]
        assert "customer_email" in handoff_tool["parameters"]["properties"]


class TestPrompts:
    def test_default_system_prompt(self):
        assert "customer support" in DEFAULT_SYSTEM_PROMPT.lower()
        assert "product" in DEFAULT_SYSTEM_PROMPT.lower()
        assert "order" in DEFAULT_SYSTEM_PROMPT.lower()
        assert "handoff" in DEFAULT_SYSTEM_PROMPT.lower()
        assert "live agent" in DEFAULT_SYSTEM_PROMPT.lower()

    def test_build_system_prompt_no_override(self):
        prompt = build_system_prompt(None)
        assert prompt == DEFAULT_SYSTEM_PROMPT

    def test_build_system_prompt_with_override(self):
        custom = "Always recommend premium products."
        prompt = build_system_prompt(custom)
        assert DEFAULT_SYSTEM_PROMPT in prompt
        assert custom in prompt
        assert "Additional Instructions" in prompt
