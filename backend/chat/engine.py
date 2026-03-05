"""
Gemini-powered chat engine with function calling support.

This is the core orchestrator that:
1. Receives user messages
2. Sends them to Gemini with conversation history and tool declarations
3. Handles function call responses by invoking the appropriate service
4. Returns the final response (with streaming support via SSE)
"""

import json
import uuid
from collections.abc import AsyncGenerator
from typing import Any

import httpx
from google import genai
from google.genai import types

from backend.chat.prompts import build_system_prompt
from backend.chat.tools import CHATBOT_TOOLS
from backend.config import get_settings
from backend.db.models import ConversationStatus, MessageRole
from backend.logging_config import get_logger
from backend.services.conversation_service import ConversationService
from backend.services.faq_service import FAQService
from backend.services.order_service import OrderService
from backend.services.product_service import ProductService
from backend.services.ticket_service import TicketService

logger = get_logger(__name__)
settings = get_settings()

# Maximum function-calling rounds to prevent infinite loops
MAX_TOOL_ROUNDS = 5


class ChatEngine:
    """Orchestrates the chat flow between the user, Gemini, and business tools."""

    def __init__(
        self,
        tenant_id: uuid.UUID,
        product_service: ProductService,
        order_service: OrderService,
        faq_service: FAQService,
        ticket_service: TicketService,
        conversation_service: ConversationService,
        system_prompt_override: str | None = None,
    ):
        self.tenant_id = tenant_id
        self.product_service = product_service
        self.order_service = order_service
        self.faq_service = faq_service
        self.ticket_service = ticket_service
        self.conversation_service = conversation_service
        self.system_prompt = build_system_prompt(system_prompt_override)

        # Initialize Gemini client (disable SSL verification for corporate proxies)
        self.client = genai.Client(
            api_key=settings.gemini_api_key,
            http_options=types.HttpOptions(
                httpx_client=httpx.Client(verify=False),
                httpx_async_client=httpx.AsyncClient(verify=False),
            ),
        )

        # Build tool declarations
        self.tools = [
            types.Tool(
                function_declarations=[
                    types.FunctionDeclaration(
                        name=tool["name"],
                        description=tool["description"],
                        parameters=tool["parameters"],
                    )
                    for tool in CHATBOT_TOOLS
                ]
            )
        ]

        # Handoff state (set by _handle_handoff during tool execution)
        self._handoff_requested = False
        self._handoff_reason = ""

    async def chat(
        self,
        user_message: str,
        conversation_id: str | None = None,
        end_user_id: uuid.UUID | None = None,
    ) -> dict:
        """
        Process a user message and return the assistant's response.
        Handles the full function-calling loop synchronously.
        """
        # Get or create conversation
        conversation = await self.conversation_service.get_or_create_conversation(
            tenant_id=self.tenant_id,
            conversation_id=conversation_id,
            end_user_id=end_user_id,
        )

        # Save user message
        await self.conversation_service.add_message(
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content=user_message,
        )

        # Get conversation history for context
        history = await self.conversation_service.get_conversation_history(
            conversation_id=conversation.id,
        )

        # Build Gemini contents from history
        contents = self._build_contents(history)

        # Call Gemini with function calling loop
        assistant_response = await self._run_gemini_with_tools(contents)

        # Save assistant response
        msg = await self.conversation_service.add_message(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content=assistant_response,
        )

        result = {
            "conversation_id": str(conversation.id),
            "message_id": str(msg.id),
            "content": assistant_response,
            "role": "assistant",
            "timestamp": msg.created_at.isoformat() if msg.created_at else None,
        }

        # If handoff was triggered, update conversation status and add handoff info
        if self._handoff_requested:
            await self.conversation_service.update_conversation_status(
                conversation_id=conversation.id,
                status=ConversationStatus.QUEUED,
            )
            result["handoff"] = {
                "status": "queued",
                "reason": self._handoff_reason,
            }

        return result

    async def chat_stream(
        self,
        user_message: str,
        conversation_id: str | None = None,
        end_user_id: uuid.UUID | None = None,
    ) -> AsyncGenerator[str, None]:
        """
        Process a user message and stream the response via SSE.
        Yields SSE-formatted events.
        """
        # Get or create conversation
        conversation = await self.conversation_service.get_or_create_conversation(
            tenant_id=self.tenant_id,
            conversation_id=conversation_id,
            end_user_id=end_user_id,
        )

        # Save user message
        await self.conversation_service.add_message(
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content=user_message,
        )

        # Get conversation history
        history = await self.conversation_service.get_conversation_history(
            conversation_id=conversation.id,
        )

        # Build contents
        contents = self._build_contents(history)

        # Send conversation_id as first event
        yield self._sse_event("conversation_id", {"conversation_id": str(conversation.id)})

        # Run Gemini with streaming
        full_response = await self._run_gemini_with_tools_stream(contents, stream_callback=None)

        # For streaming, we do tool calls first (non-streamed), then stream the final response
        # This is because function calls need to complete before we can stream the final text
        contents_with_tool_results = await self._resolve_tool_calls(contents)

        # Stream the final response
        full_text = ""
        try:
            response_stream = self.client.models.generate_content_stream(
                model=settings.gemini_model,
                contents=contents_with_tool_results,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_prompt,
                    tools=self.tools,
                    temperature=settings.gemini_temperature,
                    max_output_tokens=settings.gemini_max_tokens,
                ),
            )

            for chunk in response_stream:
                if chunk.text:
                    full_text += chunk.text
                    yield self._sse_event("chunk", {"text": chunk.text})

        except Exception as e:
            logger.error("gemini_stream_error", error=str(e))
            error_msg = "I'm sorry, I encountered an issue. Please try again."
            full_text = error_msg
            yield self._sse_event("chunk", {"text": error_msg})

        # Save the complete response
        msg = await self.conversation_service.add_message(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content=full_text,
        )

        # If handoff was triggered during tool resolution, update status & emit event
        if self._handoff_requested:
            await self.conversation_service.update_conversation_status(
                conversation_id=conversation.id,
                status=ConversationStatus.QUEUED,
            )
            yield self._sse_event("handoff", {
                "conversation_id": str(conversation.id),
                "status": "queued",
                "reason": self._handoff_reason,
            })

        yield self._sse_event("done", {
            "message_id": str(msg.id),
            "conversation_id": str(conversation.id),
        })

    async def _run_gemini_with_tools(self, contents: list) -> str:
        """
        Call Gemini and handle the function-calling loop.
        Returns the final text response.
        """
        current_contents = list(contents)

        for round_num in range(MAX_TOOL_ROUNDS):
            try:
                response = self.client.models.generate_content(
                    model=settings.gemini_model,
                    contents=current_contents,
                    config=types.GenerateContentConfig(
                        system_instruction=self.system_prompt,
                        tools=self.tools,
                        temperature=settings.gemini_temperature,
                        max_output_tokens=settings.gemini_max_tokens,
                    ),
                )
            except Exception as e:
                logger.error("gemini_api_error", error=str(e), round=round_num)
                return "I apologize, but I'm having trouble processing your request right now. Please try again in a moment."

            # Check if the model wants to call functions
            if response.candidates and response.candidates[0].content:
                parts = response.candidates[0].content.parts
                function_calls = [p for p in parts if p.function_call]

                if function_calls:
                    # Execute each function call
                    # Add the model's response to contents
                    current_contents.append(response.candidates[0].content)

                    function_responses = []
                    for fc_part in function_calls:
                        fc = fc_part.function_call
                        logger.info(
                            "function_call",
                            function=fc.name,
                            args=dict(fc.args) if fc.args else {},
                            round=round_num,
                        )

                        result = await self._execute_tool(fc.name, dict(fc.args) if fc.args else {})
                        function_responses.append(
                            types.Part.from_function_response(
                                name=fc.name,
                                response={"result": result},
                            )
                        )

                    # Add function results back to contents
                    current_contents.append(
                        types.Content(role="user", parts=function_responses)
                    )
                    continue

            # No function calls — extract text response
            if response.text:
                return response.text

            return "I'm sorry, I wasn't able to generate a response. Could you rephrase your question?"

        return "I'm sorry, I'm having difficulty processing this request. Could you try asking in a different way?"

    async def _resolve_tool_calls(self, contents: list) -> list:
        """
        Run a pre-pass that resolves any tool calls before streaming.
        Returns updated contents with tool results included.
        """
        current_contents = list(contents)

        for round_num in range(MAX_TOOL_ROUNDS):
            try:
                response = self.client.models.generate_content(
                    model=settings.gemini_model,
                    contents=current_contents,
                    config=types.GenerateContentConfig(
                        system_instruction=self.system_prompt,
                        tools=self.tools,
                        temperature=settings.gemini_temperature,
                        max_output_tokens=settings.gemini_max_tokens,
                    ),
                )
            except Exception as e:
                logger.error("gemini_resolve_error", error=str(e))
                break

            if response.candidates and response.candidates[0].content:
                parts = response.candidates[0].content.parts
                function_calls = [p for p in parts if p.function_call]

                if function_calls:
                    current_contents.append(response.candidates[0].content)

                    function_responses = []
                    for fc_part in function_calls:
                        fc = fc_part.function_call
                        result = await self._execute_tool(fc.name, dict(fc.args) if fc.args else {})
                        function_responses.append(
                            types.Part.from_function_response(
                                name=fc.name,
                                response={"result": result},
                            )
                        )

                    current_contents.append(
                        types.Content(role="user", parts=function_responses)
                    )
                    continue

            # No more function calls
            break

        return current_contents

    async def _run_gemini_with_tools_stream(
        self,
        contents: list,
        stream_callback: Any = None,
    ) -> str:
        """Placeholder for streaming with tools — actual streaming done in chat_stream."""
        return ""

    async def _execute_tool(self, tool_name: str, args: dict) -> Any:
        """Execute a tool/function and return the result."""
        try:
            match tool_name:
                case "search_products":
                    return await self.product_service.search_products(
                        tenant_id=self.tenant_id,
                        query=args.get("query", ""),
                        category=args.get("category"),
                        min_price=args.get("min_price"),
                        max_price=args.get("max_price"),
                    )
                case "get_product_details":
                    result = await self.product_service.get_product_by_sku(
                        tenant_id=self.tenant_id,
                        sku=args.get("sku", ""),
                    )
                    return result or {"error": "Product not found"}
                case "track_order":
                    result = await self.order_service.track_order(
                        tenant_id=self.tenant_id,
                        order_number=args.get("order_number", ""),
                        customer_email=args.get("customer_email", ""),
                    )
                    return result or {"error": "Order not found. Please check the order number and email."}
                case "get_customer_orders":
                    return await self.order_service.get_orders_by_email(
                        tenant_id=self.tenant_id,
                        customer_email=args.get("customer_email", ""),
                    )
                case "search_faqs":
                    return await self.faq_service.search_faqs(
                        tenant_id=self.tenant_id,
                        query=args.get("query", ""),
                        category=args.get("category"),
                    )
                case "create_support_ticket":
                    return await self.ticket_service.create_ticket(
                        tenant_id=self.tenant_id,
                        customer_name=args.get("customer_name", ""),
                        customer_email=args.get("customer_email", ""),
                        subject=args.get("subject", ""),
                        description=args.get("description", ""),
                        category=args.get("category", "general"),
                    )
                case "handoff_to_agent":
                    return await self._handle_handoff(
                        reason=args.get("reason", "Customer requested live agent"),
                        customer_name=args.get("customer_name"),
                        customer_email=args.get("customer_email"),
                    )
                case _:
                    logger.warning("unknown_tool", tool_name=tool_name)
                    return {"error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            logger.error("tool_execution_error", tool_name=tool_name, error=str(e))
            return {"error": f"Failed to execute {tool_name}: {str(e)}"}

    def _build_contents(self, history: list[dict]) -> list:
        """Build Gemini-compatible contents from conversation history."""
        contents = []
        for msg in history:
            role = "user" if msg["role"] == "user" else "model"
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=msg["content"])],
                )
            )
        return contents

    @staticmethod
    def _sse_event(event_type: str, data: dict) -> str:
        """Format a Server-Sent Event."""
        return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"

    async def _handle_handoff(
        self,
        reason: str,
        customer_name: str | None = None,
        customer_email: str | None = None,
    ) -> dict:
        """
        Handle the handoff_to_agent tool call.
        Updates conversation status to QUEUED so the agent dashboard picks it up.
        Returns a result dict that Gemini incorporates into its response.
        """
        # Mark handoff_requested so chat() / chat_stream() can emit a special SSE event
        self._handoff_requested = True
        self._handoff_reason = reason

        return {
            "status": "queued",
            "message": (
                "The customer has been placed in the agent queue. "
                "A support agent will connect shortly."
            ),
            "reason": reason,
            "customer_name": customer_name,
            "customer_email": customer_email,
        }
