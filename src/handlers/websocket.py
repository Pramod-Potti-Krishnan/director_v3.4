"""
WebSocket handler for Director Agent.
"""
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, List
from fastapi import WebSocket
from starlette.websockets import WebSocketState

from src.utils.logger import setup_logger
from src.agents.intent_router import IntentRouter
from src.agents.director import DirectorAgent
from src.utils.session_manager import SessionManager
from src.utils.message_packager import MessagePackager
from src.utils.streamlined_packager import StreamlinedMessagePackager
from src.storage.supabase import get_supabase_client
from src.models.agents import UserIntent, StateContext
from src.models.websocket_messages import StreamlinedMessage, create_chat_message
from src.workflows.state_machine import WorkflowOrchestrator
from config.settings import get_settings

logger = setup_logger(__name__)


class WebSocketHandler:
    """Handles WebSocket connections and message routing."""

    def __init__(self):
        """Initialize handler components."""
        logger.info("Initializing WebSocketHandler...")

        # Get settings
        self.settings = get_settings()
        logger.info(f"Settings loaded: streamlined={self.settings.USE_STREAMLINED_PROTOCOL}, percentage={self.settings.STREAMLINED_PROTOCOL_PERCENTAGE}")

        # Defer Supabase and SessionManager initialization (lazy init pattern)
        # These will be initialized on first async call via _ensure_initialized()
        self.supabase = None
        self.sessions = None

        # Initialize components that don't require async operations
        logger.info("Initializing handler components...")
        self.intent_router = IntentRouter()
        self.director = DirectorAgent()
        self.packager = MessagePackager()
        self.streamlined_packager = StreamlinedMessagePackager()
        self.workflow = WorkflowOrchestrator()

        # Connection tracking to prevent multiple connections per session
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_lock = asyncio.Lock()

        logger.info("WebSocketHandler initialized successfully (Supabase will be initialized on first connection)")

    async def _ensure_initialized(self):
        """
        Ensure Supabase client and SessionManager are initialized (lazy initialization).

        This method is called at the start of async operations to initialize
        components that require async operations.
        """
        if self.supabase is None:
            try:
                self.supabase = await get_supabase_client()
                self.sessions = SessionManager(self.supabase)
                logger.info("✓ Supabase client and SessionManager initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {str(e)}", exc_info=True)
                raise

    def _should_use_streamlined(self, session_id: str) -> bool:
        """
        Determine if this session should use streamlined protocol.

        Args:
            session_id: Session identifier

        Returns:
            True if streamlined protocol should be used
        """
        # If feature is disabled globally, always use old protocol
        if not self.settings.USE_STREAMLINED_PROTOCOL:
            return False

        # If percentage is 100, always use streamlined
        if self.settings.STREAMLINED_PROTOCOL_PERCENTAGE >= 100:
            return True

        # If percentage is 0, never use streamlined
        if self.settings.STREAMLINED_PROTOCOL_PERCENTAGE <= 0:
            return False

        # Use session ID for consistent A/B testing
        # Hash the session ID to get a number between 0-99
        hash_value = hash(session_id) % 100
        return hash_value < self.settings.STREAMLINED_PROTOCOL_PERCENTAGE

    async def _send_messages(self, websocket: WebSocket, messages: List[StreamlinedMessage]):
        """
        Send multiple streamlined messages with small delays.

        Args:
            websocket: WebSocket connection
            messages: List of streamlined messages to send
        """
        for i, message in enumerate(messages):
            # Use model_dump with mode='json' for proper serialization
            message_data = message.model_dump(mode='json')

            # v3.4 DIAGNOSTIC: Detailed message transmission logging (using print for Railway visibility)
            import sys
            print("="*80, flush=True)
            print(f"📤 SENDING MESSAGE {i+1}/{len(messages)}", flush=True)
            print(f"   Type: {message_data.get('type')}", flush=True)
            print(f"   Session: {message_data.get('payload', {}).get('session_id', 'N/A')}", flush=True)

            # Special logging for slide_update messages
            if message_data.get('type') == 'slide_update':
                metadata = message_data.get('payload', {}).get('metadata', {})
                print(f"   📋 Slide Update Metadata:", flush=True)
                print(f"      - preview_url: {metadata.get('preview_url')}", flush=True)
                print(f"      - preview_presentation_id: {metadata.get('preview_presentation_id')}", flush=True)
                print(f"      - main_title: {metadata.get('main_title')}", flush=True)
                print(f"      - slide_count: {len(message_data.get('payload', {}).get('slides', []))}", flush=True)

            # Special logging for presentation_url messages
            if message_data.get('type') == 'presentation_url':
                print(f"   🔗 Presentation URL Message:", flush=True)
                print(f"      - url: {message_data.get('payload', {}).get('url')}", flush=True)
                print(f"      - presentation_id: {message_data.get('payload', {}).get('presentation_id')}", flush=True)
                print(f"      - message: {message_data.get('payload', {}).get('message')}", flush=True)

            # v3.4 CRITICAL DIAGNOSTIC: Print complete JSON for slide_update messages
            if message_data.get('type') == 'slide_update':
                import json
                print("="*80, flush=True)
                print("🔍 COMPLETE WEBSOCKET JSON BEING SENT:", flush=True)
                print(json.dumps(message_data, indent=2, default=str)[:2000])  # First 2000 chars
                print("="*80, flush=True)

            print("="*80, flush=True)
            sys.stdout.flush()

            await websocket.send_json(message_data)

            # Add small delay between messages for better UX
            if i < len(messages) - 1:
                await asyncio.sleep(0.1)

    async def handle_connection(self, websocket: WebSocket, session_id: str, user_id: str):
        """
        Handle a WebSocket connection for a session.

        Args:
            websocket: The WebSocket connection
            session_id: The session ID from query parameter
            user_id: The user ID from query parameter
        """
        # Initialize Supabase client and SessionManager if not already done
        await self._ensure_initialized()

        # CRITICAL FIX: Check for existing connection to prevent multiple connections per session
        # This prevents race conditions, duplicate message processing, and strawman regeneration loops
        async with self.connection_lock:
            if session_id in self.active_connections:
                existing_ws = self.active_connections[session_id]

                # Check if existing connection is still alive
                if existing_ws.client_state == WebSocketState.CONNECTED:
                    logger.warning(
                        f"🚫 Rejected duplicate connection for session {session_id} (user: {user_id}). "
                        f"A connection already exists for this session."
                    )
                    await websocket.close(code=1008, reason="Session already connected from another tab or window")
                    return
                else:
                    # Stale connection exists, remove it
                    logger.info(f"🔄 Removing stale connection for session {session_id}")
                    del self.active_connections[session_id]

            # Register new connection
            self.active_connections[session_id] = websocket
            logger.info(f"✅ Registered new connection for session {session_id} (user: {user_id})")

        try:
            # Store user_id and websocket for use in other methods
            self.current_user_id = user_id
            self.current_websocket = websocket
            logger.info(f"Starting handle_connection for user: {user_id}, session: {session_id}")

            # Get or create session with user_id
            try:
                session = await self.sessions.get_or_create(session_id, user_id)
                logger.info(f"Session {session_id} initialized for user {user_id} with state: {session.current_state}")
                logger.info(f"🔌 Reconnection: session_id={session_id}, user_id={user_id}, loaded_state={session.current_state}")
            except Exception as session_error:
                logger.error(f"Failed to create/get session {session_id} for user {user_id}: {str(session_error)}", exc_info=True)
                raise

            # Send initial greeting if new session, otherwise restore conversation history
            if session.current_state == "PROVIDE_GREETING":
                logger.info(f"New session - sending greeting (state: {session.current_state})")
                try:
                    await self._send_greeting(websocket, session)
                    logger.info(f"Greeting sent successfully for session {session_id}")
                except Exception as greeting_error:
                    logger.error(f"Failed to send greeting for session {session_id}: {str(greeting_error)}", exc_info=True)
                    raise
            else:
                logger.info(f"Existing session - restoring history (state: {session.current_state})")
                logger.info(f"✅ Restoring conversation history for session {session_id} (state: {session.current_state})")
                try:
                    await self._restore_conversation_history(websocket, session)
                    logger.info(f"Conversation history restored successfully for session {session_id}")
                except Exception as restore_error:
                    logger.error(f"Failed to restore conversation history for session {session_id}: {str(restore_error)}", exc_info=True)
                    # Don't raise - allow user to continue even if restoration fails

            # Main message loop
            logger.info(f"Entering message loop for session {session_id}")
            while True:
                # Receive message
                logger.debug(f"Waiting for message from session {session_id}")
                data = await websocket.receive_text()

                # TRANSITION FIX: Handle both raw "ping" and JSON {"type":"ping"} formats
                # Frontend changed to raw "ping" on 2025-11-21, but we need backward compatibility
                if data.strip() == "ping":
                    logger.info(f"💓 Heartbeat ping (raw text) received for session {session_id}, ignoring")
                    try:
                        await websocket.send_text("pong")  # Respond to raw ping
                    except Exception as pong_error:
                        logger.debug(f"Failed to send pong: {pong_error}")
                    continue  # Skip processing

                message = json.loads(data)

                message_type = message.get('type', '')

                # CRITICAL FIX: Filter ping messages (heartbeat keep-alive)
                # Frontend sends {"type": "ping"} every 15 seconds to keep connection alive
                # These should NOT be processed as user messages
                if message_type == 'ping':
                    logger.info(f"💓 Heartbeat ping received for session {session_id}, ignoring")
                    continue  # Skip processing, wait for next message

                logger.info(f"Received message for session {session_id}: type={message_type}, data keys={list(message.get('data', {}).keys())}")

                # Process message
                await self._handle_message(websocket, session, message)

        except Exception as e:
            logger.error(f"Error in WebSocket handler for session {session_id}: {str(e)}", exc_info=True)
            # Don't try to close if already disconnected
            if websocket.client_state.value <= 2:  # CONNECTING=0, CONNECTED=1, DISCONNECTED=2
                try:
                    await websocket.close()
                except Exception:
                    pass  # Ignore errors when closing
        finally:
            # CRITICAL FIX: Cleanup connection tracking on disconnect
            # This ensures the session can reconnect after disconnect
            async with self.connection_lock:
                if session_id in self.active_connections:
                    del self.active_connections[session_id]
                    logger.info(f"🧹 Removed connection tracking for session {session_id} on disconnect")

    async def _send_greeting(self, websocket: WebSocket, session: Any):
        """Send initial greeting message."""
        logger.info(f"Starting _send_greeting for session {session.id}")
        try:
            use_streamlined = self._should_use_streamlined(session.id)
            logger.info(f"Session {session.id} using streamlined protocol: {use_streamlined}")

            if use_streamlined:
                # Use streamlined protocol
                messages = self.streamlined_packager.package_messages(
                    session_id=session.id,
                    state="PROVIDE_GREETING",
                    agent_output=None,  # Greeting doesn't need agent output
                    context=None
                )
                logger.info(f"Packaged {len(messages)} messages for greeting")
                await self._send_messages(websocket, messages)
            else:
                # Use legacy protocol
                state_context = StateContext(
                    current_state="PROVIDE_GREETING",
                    user_intent=None,  # No intent for greeting
                    conversation_history=[],
                    session_data={}
                )

                # Get greeting from director
                greeting = await self.director.process(state_context)

                # Package and send
                message = self.packager.package(
                    response=greeting,
                    session_id=session.id,
                    current_state="PROVIDE_GREETING"
                )

                await websocket.send_json(message)

            logger.info(f"Sent greeting for session {session.id}")

        except Exception as e:
            logger.error(f"Error sending greeting: {str(e)}", exc_info=True)
            raise

    async def _restore_conversation_history(self, websocket: WebSocket, session: Any):
        """
        Restore conversation history for existing sessions on reconnection.

        When users reconnect to an existing session (browser refresh, loading from history),
        this method reconstructs and sends all past messages to the frontend so they see
        the full conversation context.

        Args:
            websocket: WebSocket connection
            session: Session object with conversation_history and current state
        """
        logger.info(f"📊 Restoring {len(session.conversation_history)} history items for session {session.id}")

        use_streamlined = self._should_use_streamlined(session.id)

        if not use_streamlined:
            logger.warning("Legacy protocol not supported for history restoration")
            return

        all_messages = []

        # Iterate through conversation history to reconstruct messages
        for idx, history_item in enumerate(session.conversation_history):
            role = history_item.get('role')
            content = history_item.get('content')
            state = history_item.get('state')  # Only for assistant messages

            if role == 'user':
                # Reconstruct user message as simple chat_message
                all_messages.append(
                    create_chat_message(
                        session_id=session.id,
                        text=content,  # Raw user text
                        format="plain"
                    )
                )

            elif role == 'assistant':
                # Reconstruct assistant messages based on state
                reconstructed = await self._reconstruct_assistant_message(
                    session=session,
                    state=state,
                    content=content,
                    history_idx=idx
                )
                if reconstructed:
                    all_messages.extend(reconstructed)

        # Send all reconstructed messages
        if all_messages:
            logger.info(f"✅ Sending {len(all_messages)} reconstructed messages to frontend")
            logger.info(f"📊 Restoration stats - Current state: {session.current_state}, Has strawman: {bool(session.presentation_strawman)}, Has final URL: {bool(session.presentation_url)}")
            await self._send_messages(websocket, all_messages)
        else:
            logger.warning(f"⚠️ No messages reconstructed for session {session.id}")

    async def _reconstruct_assistant_message(
        self,
        session: Any,
        state: str,
        content: Any,
        history_idx: int
    ) -> List[StreamlinedMessage]:
        """
        Reconstruct assistant message from history item.

        Uses existing streamlined_packager methods to convert stored history
        into proper StreamlinedMessages for frontend display.

        Args:
            session: Session object (for accessing current strawman/URL)
            state: State when message was created
            content: Message content (varies by state - dict or Pydantic object)
            history_idx: Index in conversation history (for debugging/logging)

        Returns:
            List of StreamlinedMessages to send (empty list if reconstruction fails)
        """
        try:
            # Import models at runtime to avoid circular imports
            from src.models.agents import (
                ClarifyingQuestions,
                ConfirmationPlan,
                PresentationStrawman
            )

            if state == "PROVIDE_GREETING":
                # Static greeting - no agent_output needed
                return self.streamlined_packager.package_messages(
                    session_id=session.id,
                    state="PROVIDE_GREETING",
                    agent_output=None,
                    context=None
                )

            elif state == "ASK_CLARIFYING_QUESTIONS":
                # Reconstruct from ClarifyingQuestions object in history
                if isinstance(content, dict) and 'questions' in content:
                    questions = ClarifyingQuestions(**content)
                    return self.streamlined_packager.package_messages(
                        session_id=session.id,
                        state="ASK_CLARIFYING_QUESTIONS",
                        agent_output=questions,
                        context=None
                    )
                else:
                    logger.warning(f"Invalid questions format in history[{history_idx}]")
                    return []

            elif state == "CREATE_CONFIRMATION_PLAN":
                # Reconstruct from ConfirmationPlan object in history
                if isinstance(content, dict):
                    plan = ConfirmationPlan(**content)
                    return self.streamlined_packager.package_messages(
                        session_id=session.id,
                        state="CREATE_CONFIRMATION_PLAN",
                        agent_output=plan,
                        context=None
                    )
                else:
                    logger.warning(f"Invalid plan format in history[{history_idx}]")
                    return []

            elif state in ["GENERATE_STRAWMAN", "REFINE_STRAWMAN"]:
                # ⚠️ CRITICAL: Always use session.presentation_strawman (current version)
                # NOT history content! This ensures we get the latest preview_url
                if session.presentation_strawman:
                    strawman = PresentationStrawman(**session.presentation_strawman)
                    return self.streamlined_packager.package_messages(
                        session_id=session.id,
                        state=state,
                        agent_output=strawman,
                        context=None
                    )
                else:
                    logger.warning(f"No strawman in session for history[{history_idx}]")
                    return []

            elif state == "CONTENT_GENERATION":
                # Reconstruct presentation URL message
                if isinstance(content, dict) and content.get("type") == "presentation_url":
                    return self.streamlined_packager.package_messages(
                        session_id=session.id,
                        state="CONTENT_GENERATION",
                        agent_output=content,
                        context=None
                    )
                # Alternative: use session.presentation_url if content format different
                elif session.presentation_url:
                    return self.streamlined_packager.package_messages(
                        session_id=session.id,
                        state="CONTENT_GENERATION",
                        agent_output={
                            "type": "presentation_url",
                            "url": session.presentation_url,
                            "presentation_id": session.presentation_strawman.get("preview_presentation_id", "") if session.presentation_strawman else "",
                            "slide_count": len(session.presentation_strawman.get("slides", [])) if session.presentation_strawman else 0
                        },
                        context=None
                    )
                else:
                    logger.warning(f"No presentation URL for history[{history_idx}]")
                    return []

            else:
                logger.warning(f"Unknown state '{state}' in history[{history_idx}]")
                return []

        except Exception as e:
            logger.error(f"Error reconstructing message at history[{history_idx}]: {e}", exc_info=True)
            return []

    async def _handle_message(self, websocket: WebSocket, session: Any, message: Dict[str, Any]):
        """
        Handle an incoming message.

        Args:
            websocket: The WebSocket connection
            session: The session object
            message: The incoming message
        """
        try:
            # CRITICAL FIX: Refresh session from database/cache to get latest state
            # This prevents stale session bug where presentation_strawman is None
            # even though it was saved to the database, causing infinite regeneration loops
            session = await self.sessions.get_or_create(session.id, self.current_user_id)

            # Validate we have user_id
            if not hasattr(self, 'current_user_id') or not self.current_user_id:
                raise RuntimeError("User ID not set in handler - connection not properly initialized")

            # Extract user input
            user_input = message.get('data', {}).get('text', '')

            # CRITICAL FIX: Validate user input is not empty
            # Empty input should NOT trigger state transitions or intent classification
            if not user_input or not user_input.strip():
                logger.warning(f"Received empty/whitespace user input for session {session_id}, ignoring message")
                return  # Skip processing empty input

            logger.info(f"Processing user input in state {session.current_state}")

            # STEP 1: Classify user intent
            # v3.4 FIX: Direct button action mapping to avoid LLM classification failures
            intent = None
            if user_input == "accept_strawman" and session.current_state == "GENERATE_STRAWMAN":
                intent = UserIntent(
                    intent_type="Accept_Strawman",
                    confidence=1.0,
                    extracted_info=None
                )
                logger.info("🔘 Directly mapped button action 'accept_strawman' → Accept_Strawman intent")
            elif user_input == "accept_plan" and session.current_state == "CREATE_CONFIRMATION_PLAN":
                intent = UserIntent(
                    intent_type="Accept_Plan",
                    confidence=1.0,
                    extracted_info=None
                )
                logger.info("🔘 Directly mapped button action 'accept_plan' → Accept_Plan intent")
            elif user_input == "request_refinement" and session.current_state in ["GENERATE_STRAWMAN", "REFINE_STRAWMAN"]:
                # For refinement requests, we still need LLM to extract the refinement details
                # So don't map directly, let LLM classify
                logger.info("📝 User requested refinement - using LLM classification to extract details")
                intent = await self.intent_router.classify(
                    user_message=user_input,
                    context={
                        'current_state': session.current_state,
                        'recent_history': session.conversation_history[-3:] if session.conversation_history else []
                    }
                )

            # If not a known button action, use LLM classification
            if intent is None:
                intent = await self.intent_router.classify(
                    user_message=user_input,
                    context={
                        'current_state': session.current_state,
                        'recent_history': session.conversation_history[-3:] if session.conversation_history else []
                    }
                )
                logger.info(f"🤖 LLM classified intent: {intent.intent_type} with confidence {intent.confidence}")

            logger.info(f"Final intent: {intent.intent_type} (confidence: {intent.confidence})")

            # STEP 2: Handle intent-based actions
            if intent.intent_type == "Change_Topic":
                # Clear context and reset to questions
                await self.sessions.clear_context(session.id, self.current_user_id)
                # FIX: Persist state to Supabase before continuing
                await self.sessions.update_state(
                    session.id,
                    self.current_user_id,
                    "ASK_CLARIFYING_QUESTIONS"
                )
                session = await self.sessions.get_or_create(session.id, self.current_user_id)
                session.current_state = "ASK_CLARIFYING_QUESTIONS"
                session.user_initial_request = intent.extracted_info or user_input

            elif intent.intent_type == "Submit_Initial_Topic":
                # Save the initial topic
                await self.sessions.save_session_data(
                    session.id,
                    self.current_user_id,
                    'user_initial_request',
                    user_input
                )
                session = await self.sessions.get_or_create(session.id, self.current_user_id)

            elif intent.intent_type == "Submit_Clarification_Answers":
                # Save clarifying answers
                await self.sessions.save_session_data(
                    session.id,
                    self.current_user_id,
                    'clarifying_answers',
                    {
                        "raw_answers": user_input,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                session = await self.sessions.get_or_create(session.id, self.current_user_id)

            # STEP 3: Determine next state
            next_state = self._determine_next_state(
                session.current_state,
                intent,
                None,
                session
            )

            # Update state if it changed
            if next_state != session.current_state:
                # v3.4 DIAGNOSTIC: Detailed state transition logging (using print for Railway visibility)
                import sys
                print("="*80, flush=True)
                print("🔄 STATE TRANSITION", flush=True)
                print(f"   FROM: {session.current_state}", flush=True)
                print(f"   TO: {next_state}", flush=True)
                print(f"   Intent: {intent.intent_type} (confidence: {intent.confidence})", flush=True)
                print(f"   User input: {user_input[:100] if len(user_input) <= 100 else user_input[:100] + '...'}", flush=True)
                print("="*80, flush=True)
                print(f"🔵 DEBUG: About to call update_state({session.id}, {self.current_user_id}, {next_state})", flush=True)
                sys.stdout.flush()
                await self.sessions.update_state(session.id, self.current_user_id, next_state)
                print(f"✅ DEBUG: update_state completed, updating in-memory state", flush=True)
                session.current_state = next_state
                print(f"✅ DEBUG: In-memory state updated to {session.current_state}", flush=True)

            # STEP 4: Build state context
            state_context = StateContext(
                current_state=session.current_state,
                user_intent=intent,
                conversation_history=session.conversation_history or [],
                session_data={
                    'user_initial_request': session.user_initial_request,
                    'clarifying_answers': session.clarifying_answers,
                    'confirmation_plan': session.confirmation_plan,
                    'presentation_strawman': session.presentation_strawman
                }
            )

            # STEP 4.5: Send pre-generation status for long-running states
            use_streamlined = self._should_use_streamlined(session.id)
            # v3.1: Added CONTENT_GENERATION as a long-running state (text generation takes 5-15s per slide)
            if use_streamlined and session.current_state in ["GENERATE_STRAWMAN", "REFINE_STRAWMAN", "CONTENT_GENERATION"]:
                # CRITICAL FIX: Check if strawman already exists before sending pre-generation status
                # This prevents unnecessary regeneration and provides cached response immediately
                if session.current_state == "GENERATE_STRAWMAN" and session.presentation_strawman:
                    logger.info(f"✅ Strawman already exists for session {session.id}, returning cached version (idempotency check)")

                    # Build response from cached strawman
                    response = self._build_cached_strawman_response(session)

                    # Package and send cached response
                    messages = self.streamlined_packager.package_messages(
                        session_id=session.id,
                        state=session.current_state,
                        agent_output=response,
                        context=state_context
                    )
                    await self._send_messages(websocket, messages)
                    logger.info(f"Sent cached strawman response for session {session.id}")
                    return  # Early return - skip Director processing

                # Only send pre-generation status if actually generating (not cached)
                pre_status = self.streamlined_packager.create_pre_generation_status(
                    session_id=session.id,
                    state=session.current_state
                )
                await websocket.send_json(pre_status.model_dump(mode='json'))
                await asyncio.sleep(0.1)

            # STEP 5: Process with Director (only if not already cached)
            response = await self.director.process(state_context)

            # Store in history
            await self.sessions.add_to_history(session.id, self.current_user_id, {
                'role': 'user',
                'content': user_input,
                'intent': intent.dict()
            })
            await self.sessions.add_to_history(session.id, self.current_user_id, {
                'role': 'assistant',
                'state': session.current_state,
                'content': response
            })

            # v3.1: Save strawman to session for REFINE_STRAWMAN and CONTENT_GENERATION
            if session.current_state in ["GENERATE_STRAWMAN", "REFINE_STRAWMAN"]:
                strawman_data = None
                presentation_url = None

                # Extract strawman from response (handles both v1.0 and v2.0/v3.1 formats)
                if response.__class__.__name__ == 'PresentationStrawman':
                    # v1.0: Direct strawman object (no deck-builder)
                    strawman_data = response.model_dump()
                    logger.debug("Extracted strawman from PresentationStrawman object")
                elif isinstance(response, dict):
                    if response.get("type") == "presentation_url" and "strawman" in response:
                        # v2.0/v3.1: Hybrid response with embedded strawman
                        strawman_obj = response["strawman"]
                        if hasattr(strawman_obj, 'model_dump'):
                            strawman_data = strawman_obj.model_dump()
                        elif isinstance(strawman_obj, dict):
                            strawman_data = strawman_obj
                        presentation_url = response.get("url")
                        logger.debug(f"Extracted strawman from hybrid response with URL: {presentation_url}")

                # Save strawman data to session
                if strawman_data:
                    await self.sessions.save_session_data(
                        session.id,
                        self.current_user_id,
                        'presentation_strawman',
                        strawman_data
                    )
                    logger.info(f"Saved strawman to session {session.id} ({len(strawman_data.get('slides', []))} slides)")

                    # v3.4 DIAGNOSTIC: Verify session data storage (using print for Railway visibility)
                    session = await self.sessions.get_or_create(session.id, self.current_user_id)
                    saved_data = session.presentation_strawman
                    import sys
                    print("="*80, flush=True)
                    print("💾 SESSION DATA VERIFICATION (Strawman)", flush=True)
                    print(f"   Data saved: {strawman_data is not None}", flush=True)
                    print(f"   Data retrieved from session: {saved_data is not None}", flush=True)
                    if saved_data:
                        print(f"   Has preview_url in saved data: {'preview_url' in saved_data}", flush=True)
                        print(f"   Preview URL value in session: {saved_data.get('preview_url')}", flush=True)
                        print(f"   Slide count in session: {len(saved_data.get('slides', []))}", flush=True)
                    print("="*80, flush=True)
                    sys.stdout.flush()

                    # Also save URL if available
                    if presentation_url:
                        await self.sessions.save_session_data(
                            session.id,
                            self.current_user_id,
                            'presentation_url',
                            presentation_url
                        )
                        logger.info(f"Saved presentation URL to session: {presentation_url}")

                    # Refresh session from DB to ensure cache consistency
                    session = await self.sessions.get_or_create(session.id, self.current_user_id)

            # Package and send response based on protocol
            if use_streamlined:
                # Use streamlined protocol
                messages = self.streamlined_packager.package_messages(
                    session_id=session.id,
                    state=session.current_state,
                    agent_output=response,
                    context=state_context
                )
                await self._send_messages(websocket, messages)
            else:
                # Use legacy protocol
                ws_message = self.packager.package(
                    response=response,
                    session_id=session.id,
                    current_state=session.current_state
                )
                await websocket.send_json(ws_message)

            logger.info(f"Sent response for session {session.id} in state {session.current_state}")

        except Exception as e:
            logger.error(f"Error handling message: {str(e)}", exc_info=True)
            # Send error message based on protocol
            use_streamlined = self._should_use_streamlined(session.id)

            if use_streamlined:
                error_messages = self.streamlined_packager.create_error_message(
                    session_id=session.id,
                    error_text=str(e)
                )
                await self._send_messages(websocket, error_messages)
            else:
                error_message = self.packager.package_error(
                    error=str(e),
                    session_id=session.id
                )
                await websocket.send_json(error_message)

    def _determine_next_state(self, current_state: str, intent: UserIntent,
                             response: Any, session: Any = None) -> str:
        """
        Determine next state based on directional intent.

        v3.1: Updated to support CONTENT_GENERATION state (Stage 6).

        Args:
            current_state: Current workflow state
            intent: Classified user intent
            response: Response from director (can be None for pre-processing)
            session: Session object to check state details

        Returns:
            Next state name
        """
        # Map directional intents to next states
        intent_to_next_state = {
            "Submit_Initial_Topic": "ASK_CLARIFYING_QUESTIONS",
            "Submit_Clarification_Answers": "CREATE_CONFIRMATION_PLAN",
            "Accept_Plan": "GENERATE_STRAWMAN",
            "Reject_Plan": "CREATE_CONFIRMATION_PLAN",  # Loop back
            "Accept_Strawman": "CONTENT_GENERATION",  # v3.1: Go to Stage 6 instead of END
            "Submit_Refinement_Request": "REFINE_STRAWMAN",
            "Change_Topic": "ASK_CLARIFYING_QUESTIONS",  # Reset
            "Change_Parameter": "CREATE_CONFIRMATION_PLAN",  # Regenerate
            "Ask_Help_Or_Question": current_state  # No state change
        }

        # Get next state from mapping
        next_state = intent_to_next_state.get(intent.intent_type, current_state)

        # v3.1: CONTENT_GENERATION is terminal - automatically transitions to END when complete
        # Director returns deck URL with generated content, no user input needed
        if current_state == "CONTENT_GENERATION":
            next_state = "END"

        # Log the transition
        if next_state != current_state:
            logger.info(f"State transition: {current_state} -> {next_state} (intent: {intent.intent_type})")
        else:
            logger.info(f"State remains: {current_state} (intent: {intent.intent_type})")

        return next_state

    def _build_cached_strawman_response(self, session: Any) -> Any:
        """
        Build response from cached strawman data (idempotency helper).

        This method is used when a strawman already exists in the session,
        preventing unnecessary regeneration and API calls.

        Args:
            session: Session object with existing strawman in presentation_strawman field

        Returns:
            Response object matching Director output format (either PresentationStrawman
            or hybrid dict with type="presentation_url")
        """
        from src.models.agents import PresentationStrawman

        strawman_data = session.presentation_strawman

        if not strawman_data:
            logger.warning(f"_build_cached_strawman_response called but no strawman data in session {session.id}")
            return None

        # Check if strawman includes preview_url (v2.0+ format with deck-builder integration)
        if isinstance(strawman_data, dict) and 'preview_url' in strawman_data:
            # Return hybrid response format (matches v2.0/v3.1 Director output)
            logger.debug(f"Building cached hybrid response with preview_url for session {session.id}")
            return {
                "type": "presentation_url",
                "url": strawman_data['preview_url'],
                "strawman": PresentationStrawman(**strawman_data) if not isinstance(strawman_data.get('slides'), type(None)) else strawman_data
            }
        else:
            # Return plain strawman object (v1.0 format)
            logger.debug(f"Building cached PresentationStrawman response for session {session.id}")
            return PresentationStrawman(**strawman_data) if isinstance(strawman_data, dict) else strawman_data