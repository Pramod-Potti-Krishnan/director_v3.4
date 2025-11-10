"""
Director Agent for managing presentation creation workflow.
v3.3: Secure authentication using Application Default Credentials (ADC)
"""
import os
import json
from typing import Union, Dict, Any
from pydantic_ai import Agent
from pydantic_ai.settings import ModelSettings
from pydantic_ai.exceptions import ModelHTTPError
# v3.3: Removed GoogleModel and GoogleProvider - now using Vertex AI with ADC
from src.models.agents import (
    StateContext, ClarifyingQuestions, ConfirmationPlan,
    PresentationStrawman, Slide, ContentGuidance
)
from src.models.layout_selection import LayoutSelection  # v3.2: AI layout selection
from src.utils.logger import setup_logger
from src.utils.slide_type_classifier import SlideTypeClassifier  # v3.4: Slide classification
from src.utils.diversity_tracker import DiversityTracker  # v3.4-diversity: Variant diversity enforcement
from src.utils.logfire_config import instrument_agents
from src.utils.context_builder import ContextBuilder
from src.utils.token_tracker import TokenTracker
from src.utils.asset_formatter import AssetFormatter
# v3.4-v1.2: Text Service v1.2 integration
from src.utils.variant_catalog import VariantCatalog
from src.utils.variant_selector import VariantSelector
# v2.0: Deck-builder integration
# v3.2: LayoutMapper removed - replaced by LayoutSchemaManager
from src.utils.layout_schema_manager import LayoutSchemaManager  # v3.2: Schema-driven architecture
from src.utils.content_transformer import ContentTransformer
from src.utils.deck_builder_client import DeckBuilderClient
# v3.3: GCP Authentication utility for ADC
from src.utils.gcp_auth import initialize_vertex_ai, get_project_info
# v3.4: Vertex AI retry logic for 429 errors
from src.utils.vertex_retry import call_with_retry

logger = setup_logger(__name__)


class DirectorAgent:
    """Main agent for handling presentation creation states."""

    def __init__(self):
        """Initialize state-specific agents with embedded modular prompts."""
        # Instrument agents for token tracking
        instrument_agents()

        # Get settings to check which AI service is available
        from config.settings import get_settings
        settings = get_settings()

        # v3.3: GCP/Vertex AI only - no fallback providers
        if not settings.GCP_ENABLED:
            raise ValueError(
                "GCP/Vertex AI must be enabled. Please either:\n"
                "  1. Set GCP_ENABLED=true in .env, AND\n"
                "  2. For local: Run 'gcloud auth application-default login'\n"
                "  3. For Railway: Set GCP_SERVICE_ACCOUNT_JSON environment variable"
            )

        # v3.3: Initialize Vertex AI with Application Default Credentials
        try:
            initialize_vertex_ai()
            gcp_info = get_project_info()
            logger.info(f"✓ Using Google Gemini via Vertex AI (Project: {gcp_info['project_id']})")
            logger.info(f"  Authentication: {'Service Account' if gcp_info['has_service_account'] else 'ADC (local)'}")

            # v3.3: Use individual model for each stage from settings with Vertex AI prefix
            model_greeting = f'google-vertex:{settings.GCP_MODEL_GREETING}'
            model_questions = f'google-vertex:{settings.GCP_MODEL_QUESTIONS}'
            model_plan = f'google-vertex:{settings.GCP_MODEL_PLAN}'
            model_strawman = f'google-vertex:{settings.GCP_MODEL_STRAWMAN}'
            model_refine = f'google-vertex:{settings.GCP_MODEL_REFINE}'

            logger.info(f"  Greeting model: {settings.GCP_MODEL_GREETING}")
            logger.info(f"  Questions model: {settings.GCP_MODEL_QUESTIONS}")
            logger.info(f"  Plan model: {settings.GCP_MODEL_PLAN}")
            logger.info(f"  Strawman model: {settings.GCP_MODEL_STRAWMAN}")
            logger.info(f"  Refine model: {settings.GCP_MODEL_REFINE}")

        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI: {e}")
            raise ValueError(f"Vertex AI initialization failed: {e}")

        # Initialize agents with embedded modular prompts
        logger.info("DirectorAgent initializing with embedded modular prompts (5 individual models)")
        self._init_agents_with_embedded_prompts(
            model_greeting,
            model_questions,
            model_plan,
            model_strawman,
            model_refine
        )

        # Initialize context builder and token tracker
        self.context_builder = ContextBuilder()
        self.token_tracker = TokenTracker()

        # v2.0: Initialize deck-builder components
        self.deck_builder_enabled = getattr(settings, 'DECK_BUILDER_ENABLED', True)
        if self.deck_builder_enabled:
            try:
                # v3.2: Initialize schema-driven architecture
                self.layout_schema_manager = LayoutSchemaManager()
                # v3.2: ContentTransformer no longer requires LayoutMapper
                self.content_transformer = ContentTransformer()
                deck_builder_url = getattr(settings, 'DECK_BUILDER_API_URL', 'http://localhost:8000')
                self.deck_builder_client = DeckBuilderClient(deck_builder_url)
                logger.info(f"Deck-builder integration enabled: {deck_builder_url}")
                logger.info(f"Schema-driven architecture: {len(self.layout_schema_manager.schemas)} layouts available")
            except Exception as e:
                logger.warning(f"Failed to initialize deck-builder components: {e}")
                logger.warning("Deck-builder integration disabled, will return JSON only")
                self.deck_builder_enabled = False
        else:
            logger.info("Deck-builder integration disabled in settings")

        # v3.1: Initialize Text Service client for Stage 6
        self.text_service_enabled = getattr(settings, 'TEXT_SERVICE_ENABLED', True)
        if self.text_service_enabled:
            try:
                from src.utils.text_service_client import TextServiceClient
                text_service_url = getattr(settings, 'TEXT_SERVICE_URL',
                    'https://web-production-5daf.up.railway.app')  # v1.2 URL
                self.text_client = TextServiceClient(text_service_url)
                logger.info(f"Text Service integration enabled: {text_service_url}")
            except Exception as e:
                logger.warning(f"Failed to initialize Text Service client: {e}")
                logger.warning("Text Service integration disabled, Stage 6 will use placeholders")
                self.text_service_enabled = False
        else:
            logger.info("Text Service integration disabled in settings")

        # v3.4-v1.2: Initialize variant catalog and selector for Text Service v1.2
        self.variant_catalog = None
        self.variant_selector = None
        # Store text service URL for variant catalog loading
        self.text_service_url = getattr(settings, 'TEXT_SERVICE_URL',
            'https://web-production-5daf.up.railway.app')
        logger.info(f"Text Service v1.2 URL configured: {self.text_service_url}")

        # v3.4-v1.2: Store title generation model
        self.title_generation_model = f'google-vertex:{settings.GCP_MODEL_STRAWMAN}'  # Use strawman model

        logger.info("DirectorAgent initialized with 6 individual Gemini models (granular per-stage configuration)")

    def _load_modular_prompt(self, state: str) -> str:
        """Load and combine base prompt with state-specific prompt."""
        # Get the base path - this now points to the agent's config directory
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        prompt_dir = os.path.join(base_dir, 'config', 'prompts', 'modular')

        # Load base prompt
        base_path = os.path.join(prompt_dir, 'base_prompt.md')
        with open(base_path, 'r') as f:
            base_prompt = f.read()

        # Load state-specific prompt
        state_prompt_map = {
            'PROVIDE_GREETING': 'provide_greeting.md',
            'ASK_CLARIFYING_QUESTIONS': 'ask_clarifying_questions.md',
            'CREATE_CONFIRMATION_PLAN': 'create_confirmation_plan.md',
            'GENERATE_STRAWMAN': 'generate_strawman.md',
            'REFINE_STRAWMAN': 'refine_strawman.md',
            'CONTENT_GENERATION': 'content_generation.md'  # v3.1: Stage 6
        }

        state_file = state_prompt_map.get(state)
        if not state_file:
            raise ValueError(f"Unknown state for prompt loading: {state}")

        state_path = os.path.join(prompt_dir, state_file)
        with open(state_path, 'r') as f:
            state_prompt = f.read()

        # Combine prompts
        return f"{base_prompt}\n\n{state_prompt}"

    def _init_agents_with_embedded_prompts(
        self,
        model_greeting,
        model_questions,
        model_plan,
        model_strawman,
        model_refine
    ):
        """Initialize agents with embedded modular prompts and individual models per stage."""
        # Load state-specific combined prompts (base + state instructions)
        greeting_prompt = self._load_modular_prompt("PROVIDE_GREETING")
        questions_prompt = self._load_modular_prompt("ASK_CLARIFYING_QUESTIONS")
        plan_prompt = self._load_modular_prompt("CREATE_CONFIRMATION_PLAN")
        strawman_prompt = self._load_modular_prompt("GENERATE_STRAWMAN")
        refine_prompt = self._load_modular_prompt("REFINE_STRAWMAN")

        # Store system prompt tokens for each state (for tracking)
        self.state_prompt_tokens = {
            "PROVIDE_GREETING": len(greeting_prompt) // 4,
            "ASK_CLARIFYING_QUESTIONS": len(questions_prompt) // 4,
            "CREATE_CONFIRMATION_PLAN": len(plan_prompt) // 4,
            "GENERATE_STRAWMAN": len(strawman_prompt) // 4,
            "REFINE_STRAWMAN": len(refine_prompt) // 4,
            "CONTENT_GENERATION": 0  # v3.1: Stage 6 doesn't use LLM prompts (calls Text Service directly)
        }

        # Initialize greeting agent (Stage 1)
        self.greeting_agent = Agent(
            model=model_greeting,
            output_type=str,
            system_prompt=greeting_prompt,
            retries=2,
            name="director_greeting"
        )

        # Initialize questions agent (Stage 2)
        self.questions_agent = Agent(
            model=model_questions,
            output_type=ClarifyingQuestions,
            system_prompt=questions_prompt,
            retries=2,
            name="director_questions"
        )

        # Initialize plan agent (Stage 3)
        self.plan_agent = Agent(
            model=model_plan,
            output_type=ConfirmationPlan,
            system_prompt=plan_prompt,
            retries=2,
            name="director_plan"
        )

        # Initialize strawman agent (Stage 4)
        self.strawman_agent = Agent(
            model=model_strawman,
            output_type=PresentationStrawman,
            system_prompt=strawman_prompt,
            retries=2,
            name="director_strawman"
        )

        # Initialize refine strawman agent (Stage 5)
        self.refine_strawman_agent = Agent(
            model=model_refine,
            output_type=PresentationStrawman,
            system_prompt=refine_prompt,
            retries=2,
            name="director_refine_strawman"
        )

    async def process(self, state_context: StateContext) -> Union[str, ClarifyingQuestions,
                                                                   ConfirmationPlan, PresentationStrawman]:
        """
        Process based on current state following PydanticAI best practices.

        Args:
            state_context: The current state context

        Returns:
            Response appropriate for the current state
        """
        try:
            session_id = state_context.session_data.get("id", "unknown")

            # Build context for the user prompt (system prompts are already embedded in agents)
            context, user_prompt = self.context_builder.build_context(
                state=state_context.current_state,
                session_data={
                    "id": session_id,
                    "user_initial_request": state_context.session_data.get("user_initial_request"),
                    "clarifying_answers": state_context.session_data.get("clarifying_answers"),
                    "conversation_history": state_context.conversation_history,
                    "presentation_strawman": state_context.session_data.get("presentation_strawman")  # v3.2: Pass strawman for context
                },
                user_intent=state_context.user_intent.dict() if hasattr(state_context, 'user_intent') and state_context.user_intent else None
            )

            # Track token usage
            user_tokens = len(user_prompt) // 4
            system_tokens = self.state_prompt_tokens.get(state_context.current_state, 0)

            await self.token_tracker.track_modular(
                session_id,
                state_context.current_state,
                user_tokens,
                system_tokens
            )

            logger.info(
                f"Processing - State: {state_context.current_state}, "
                f"User Tokens: {user_tokens}, System Tokens: {system_tokens}, "
                f"Total: {user_tokens + system_tokens}"
            )

            # Get settings for retry configuration
            from config.settings import get_settings
            settings = get_settings()

            # Route to appropriate agent based on state
            if state_context.current_state == "PROVIDE_GREETING":
                result = await call_with_retry(
                    lambda: self.greeting_agent.run(
                        user_prompt,
                        model_settings=ModelSettings(temperature=0.7, max_tokens=500)
                    ),
                    max_retries=settings.MAX_VERTEX_RETRIES,
                    base_delay=settings.VERTEX_RETRY_BASE_DELAY,
                    operation_name="Stage 1: Greeting Generation"
                )
                response = result.output  # Simple string
                logger.info("Generated greeting")

            elif state_context.current_state == "ASK_CLARIFYING_QUESTIONS":
                result = await call_with_retry(
                    lambda: self.questions_agent.run(
                        user_prompt,
                        model_settings=ModelSettings(temperature=0.5, max_tokens=1000)
                    ),
                    max_retries=settings.MAX_VERTEX_RETRIES,
                    base_delay=settings.VERTEX_RETRY_BASE_DELAY,
                    operation_name="Stage 2: Clarifying Questions Generation"
                )
                response = result.output  # ClarifyingQuestions object
                logger.info(f"Generated {len(response.questions)} clarifying questions")

            elif state_context.current_state == "CREATE_CONFIRMATION_PLAN":
                result = await call_with_retry(
                    lambda: self.plan_agent.run(
                        user_prompt,
                        model_settings=ModelSettings(temperature=0.3, max_tokens=2000)
                    ),
                    max_retries=settings.MAX_VERTEX_RETRIES,
                    base_delay=settings.VERTEX_RETRY_BASE_DELAY,
                    operation_name="Stage 3: Confirmation Plan Generation"
                )
                response = result.output  # ConfirmationPlan object
                logger.info(f"Generated confirmation plan with {response.proposed_slide_count} slides")

            elif state_context.current_state == "GENERATE_STRAWMAN":
                logger.info("Generating strawman presentation")
                result = await call_with_retry(
                    lambda: self.strawman_agent.run(
                        user_prompt,
                        model_settings=ModelSettings(temperature=0.4, max_tokens=8000)
                    ),
                    max_retries=settings.MAX_VERTEX_RETRIES,
                    base_delay=settings.VERTEX_RETRY_BASE_DELAY,
                    operation_name="Stage 4: Strawman Generation"
                )
                strawman = result.output  # PresentationStrawman object
                logger.info(f"Generated strawman with {len(strawman.slides)} slides")
                logger.debug(f"First slide: {strawman.slides[0].slide_id if strawman.slides else 'No slides'}")

                # Post-process to ensure asset fields are in correct format
                strawman = AssetFormatter.format_strawman(strawman)
                logger.info("Applied asset field formatting to strawman")

                # v3.2: AI-powered semantic layout selection
                # v3.4: Added slide classification and content guidance generation
                total_slides = len(strawman.slides)
                logger.info(f"Starting AI-powered layout selection and classification for {total_slides} slides")

                # v3.4-v1.2: Load variant catalog and initialize selector
                logger.info("Loading v1.2 variant catalog for random variant selection")
                try:
                    if not self.variant_catalog:
                        self.variant_catalog = VariantCatalog(self.text_service_url)
                        await self.variant_catalog.load_catalog()
                        logger.info(f"✅ Loaded variant catalog with {self.variant_catalog.get_total_variants()} variants")

                    if not self.variant_selector:
                        self.variant_selector = VariantSelector(self.variant_catalog)
                        logger.info("✅ Initialized variant selector for random selection")
                except Exception as e:
                    logger.error(f"❌ Variant catalog loading failed: {str(e)}", exc_info=True)
                    logger.error(f"   Attempted URL: {self.text_service_url}/v1.2/variants")
                    logger.warning("⚠️  Will use fallback default variants instead")
                    # Don't initialize variant_selector - this triggers fallback logic in slide processing

                # v3.4-diversity: Initialize diversity tracker for variant selection
                diversity_tracker = DiversityTracker(max_consecutive_variant=2, max_consecutive_type=3)
                logger.info("✅ Initialized diversity tracker (max_consecutive: variant=2, type=3)")

                previous_slide_type = None
                for idx, slide in enumerate(strawman.slides):
                    # Determine slide position
                    if idx == 0:
                        position = "first"
                    elif idx == total_slides - 1:
                        position = "last"
                    else:
                        position = "middle"

                    # AI-powered semantic layout selection with retry logic
                    from config.settings import get_settings
                    settings = get_settings()

                    layout_selection = await call_with_retry(
                        lambda: self._select_layout_by_use_case(
                            slide=slide,
                            position=position,
                            total_slides=total_slides
                        ),
                        max_retries=settings.MAX_VERTEX_RETRIES,
                        base_delay=settings.VERTEX_RETRY_BASE_DELAY,
                        operation_name=f"Layout selection for slide {slide.slide_number}"
                    )

                    # Assign selected layout and reasoning to slide
                    slide.layout_id = layout_selection.layout_id
                    slide.layout_selection_reasoning = layout_selection.reasoning

                    # v3.4: Classify slide into 13-type taxonomy
                    slide_type_classification = SlideTypeClassifier.classify(
                        slide=slide,
                        position=idx + 1,  # 1-indexed position
                        total_slides=total_slides
                    )
                    slide.slide_type_classification = slide_type_classification

                    # v3.4-diversity: Detect semantic group (if any)
                    semantic_group = SlideTypeClassifier.detect_semantic_group(slide)

                    # v3.4-diversity: Check diversity rules and potentially override classification
                    should_override, suggested_classification = diversity_tracker.should_override_for_diversity(
                        classification=slide_type_classification,
                        variant_id=None,  # Don't know variant yet
                        semantic_group=semantic_group
                    )

                    if should_override and suggested_classification:
                        original_classification = slide_type_classification
                        slide_type_classification = suggested_classification
                        slide.slide_type_classification = suggested_classification
                        logger.info(
                            f"📊 Diversity override: '{original_classification}' → '{suggested_classification}' "
                            f"for slide {slide.slide_number} (reason: consecutive limit)"
                        )

                    # v3.4: Generate content guidance for specialized text generators
                    content_guidance = self._generate_content_guidance(
                        slide=slide,
                        slide_type_classification=slide_type_classification,
                        position=idx + 1,
                        total_slides=total_slides,
                        previous_slide_type=previous_slide_type
                    )
                    slide.content_guidance = content_guidance

                    # v3.4-v1.2: Select random variant from available options
                    if self.variant_selector and slide_type_classification:
                        try:
                            variant_id = self.variant_selector.select_variant(slide_type_classification)
                            slide.variant_id = variant_id
                            logger.debug(f"Selected variant '{variant_id}' for slide {slide.slide_number}")
                        except Exception as e:
                            logger.error(f"Variant selection failed for slide {slide.slide_number}: {e}")
                            # Fallback to default variant
                            from src.utils.slide_type_mapper import SlideTypeMapper
                            fallback = SlideTypeMapper.get_default_variant(slide_type_classification)
                            slide.variant_id = fallback
                            logger.warning(f"Using fallback variant '{fallback}' for slide {slide.slide_number}")
                    elif slide_type_classification:
                        # No variant selector available - use fallback defaults
                        from src.utils.slide_type_mapper import SlideTypeMapper
                        fallback = SlideTypeMapper.get_default_variant(slide_type_classification)
                        slide.variant_id = fallback
                        logger.info(f"Variant catalog unavailable, using default variant '{fallback}' for slide {slide.slide_number}")

                    # v3.4-diversity: Track slide for diversity metrics
                    diversity_tracker.add_slide(
                        classification=slide_type_classification,
                        variant_id=slide.variant_id,
                        semantic_group=semantic_group,
                        slide_number=slide.slide_number
                    )

                    # v3.4-v1.2: Generate slide title with LLM (50 char limit) + retry logic
                    try:
                        generated_title = await call_with_retry(
                            lambda: self._generate_slide_title(
                                original_title=slide.title,
                                narrative=slide.narrative or "",
                                max_chars=50
                            ),
                            max_retries=settings.MAX_VERTEX_RETRIES,
                            base_delay=settings.VERTEX_RETRY_BASE_DELAY,
                            operation_name=f"Title generation for slide {slide.slide_number}"
                        )
                        slide.generated_title = generated_title
                        logger.debug(f"Generated title for slide {slide.slide_number}: '{generated_title}'")
                    except Exception as e:
                        logger.error(f"Title generation failed for slide {slide.slide_number}: {e}")
                        slide.generated_title = slide.title[:50]  # Fallback to truncated original

                    # v3.4-v1.2: Generate slide subtitle with LLM (90 char limit) + retry logic
                    try:
                        key_message = slide.key_points[0] if slide.key_points else None
                        generated_subtitle = await call_with_retry(
                            lambda: self._generate_slide_subtitle(
                                narrative=slide.narrative or "",
                                key_message=key_message,
                                max_chars=90
                            ),
                            max_retries=settings.MAX_VERTEX_RETRIES,
                            base_delay=settings.VERTEX_RETRY_BASE_DELAY,
                            operation_name=f"Subtitle generation for slide {slide.slide_number}"
                        )
                        slide.generated_subtitle = generated_subtitle
                        logger.debug(f"Generated subtitle for slide {slide.slide_number}: '{generated_subtitle}'")
                    except Exception as e:
                        logger.error(f"Subtitle generation failed for slide {slide.slide_number}: {e}")
                        slide.generated_subtitle = ""  # Fallback to empty

                    logger.info(
                        f"Slide {slide.slide_number} '{slide.title}': "
                        f"Layout={layout_selection.layout_id}, "
                        f"Type={slide_type_classification}, "
                        f"Variant={slide.variant_id}, "
                        f"Complexity={content_guidance.visual_complexity}"
                    )

                    # Track previous slide type for relationship analysis
                    previous_slide_type = slide_type_classification

                    # v3.4: Rate limiting - delay between slides to prevent 429 errors
                    # Skip delay for the last slide
                    if idx < total_slides - 1:
                        import asyncio
                        delay = settings.RATE_LIMIT_DELAY_SECONDS
                        logger.debug(f"Rate limiting: waiting {delay}s before processing next slide")
                        await asyncio.sleep(delay)

                logger.info(f"✅ Assigned layouts, classifications, and content guidance to all {total_slides} slides")

                # v3.4-diversity: Log diversity metrics
                diversity_metrics = diversity_tracker.get_diversity_metrics()
                logger.info("="*70)
                logger.info("📊 VARIANT DIVERSITY METRICS:")
                logger.info(f"   Total Slides: {diversity_metrics['total_slides']}")
                logger.info(f"   Unique Classifications: {diversity_metrics['unique_classifications']}")
                logger.info(f"   Unique Variants: {diversity_metrics['unique_variants']}")
                logger.info(f"   Diversity Score: {diversity_metrics['diversity_score']}/100")
                logger.info(f"   Classification Distribution: {diversity_metrics['classification_distribution']}")
                logger.info(f"   Variant Distribution: {diversity_metrics['variant_distribution']}")
                if diversity_metrics['semantic_groups']:
                    logger.info(f"   Semantic Groups Detected: {diversity_metrics['semantic_groups']}")
                logger.info("="*70)

                # v3.4-v1.2: Generate presentation footer text (20 char limit)
                try:
                    logger.info("Generating presentation footer text")
                    generated_footer = await self._generate_footer_text(
                        presentation_title=strawman.main_title,
                        max_chars=20
                    )
                    strawman.footer_text = generated_footer
                    logger.info(f"Generated footer: '{generated_footer}' ({len(generated_footer)} chars)")
                except Exception as e:
                    logger.error(f"Footer generation failed: {e}")
                    strawman.footer_text = strawman.main_title[:20]  # Fallback to truncated title

                # v2.0: Transform and send to deck-builder API
                if self.deck_builder_enabled:
                    try:
                        # v3.4 FIX: Add diagnostic logging for deck-builder call
                        import sys
                        from datetime import datetime
                        from config.settings import get_settings
                        settings = get_settings()

                        print("="*80, flush=True)
                        print("🏗️  STAGE 4: CALLING DECK-BUILDER FOR PREVIEW", flush=True)
                        print(f"   URL: {settings.DECK_BUILDER_API_URL}", flush=True)
                        print(f"   Slide count: {len(strawman.slides)}", flush=True)
                        print(f"   Timestamp: {datetime.utcnow().isoformat()}", flush=True)
                        print("="*80, flush=True)
                        sys.stdout.flush()

                        logger.info("Transforming presentation for deck-builder")
                        api_payload = self.content_transformer.transform_presentation(strawman)
                        logger.debug(f"Transformed to {len(api_payload['slides'])} deck-builder slides")

                        print(f"✅ Transformation complete: {len(api_payload['slides'])} slides", flush=True)
                        sys.stdout.flush()

                        logger.info("Calling deck-builder API")
                        api_response = await self.deck_builder_client.create_presentation(api_payload)
                        presentation_url = self.deck_builder_client.get_full_url(api_response['url'])

                        print(f"✅ Deck-builder API call successful", flush=True)
                        print(f"   Presentation ID: {api_response.get('id', 'N/A')}", flush=True)
                        print(f"   URL: {presentation_url}", flush=True)
                        sys.stdout.flush()

                        logger.info(f"✅ Preview created: {presentation_url}")

                        # v3.4 FIX: Store preview URL in strawman, but return strawman object
                        # This allows packager to send BOTH preview link AND action buttons
                        # The preview URL is stored for reference but doesn't change message type
                        strawman.preview_url = presentation_url
                        strawman.preview_presentation_id = api_response['id']

                        # v3.4 DIAGNOSTIC: Verify preview URL assignment (using print for Railway visibility)
                        import sys
                        print("="*80, flush=True)
                        print("📸 STAGE 4 - PREVIEW URL ASSIGNMENT", flush=True)
                        print(f"   strawman.preview_url = {presentation_url}", flush=True)
                        print(f"   strawman.preview_presentation_id = {api_response['id']}", flush=True)
                        print(f"   strawman type: {type(strawman)}", flush=True)
                        print(f"   hasattr(strawman, 'preview_url'): {hasattr(strawman, 'preview_url')}", flush=True)
                        print(f"   Actual value: {getattr(strawman, 'preview_url', 'ATTRIBUTE_NOT_FOUND')}", flush=True)
                        print("="*80, flush=True)
                        sys.stdout.flush()

                        response = strawman  # Return PresentationStrawman object, not dict

                    except Exception as e:
                        # v3.4 FIX: Comprehensive error diagnostics for deck-builder failure
                        error_type = type(e).__name__
                        error_message = str(e)

                        print("="*80, flush=True)
                        print("❌ DECK-BUILDER API CALL FAILED (STAGE 4)", flush=True)
                        print(f"   Error Type: {error_type}", flush=True)
                        print(f"   Error Message: {error_message}", flush=True)
                        print(f"   URL: {settings.DECK_BUILDER_API_URL if 'settings' in locals() else 'unknown'}", flush=True)

                        # Check for specific error types
                        if "timeout" in error_message.lower() or "asyncio" in error_message.lower():
                            print(f"   ⚠️  TIMEOUT ERROR - Deck-builder not responding", flush=True)
                        elif "connection" in error_message.lower():
                            print(f"   ⚠️  CONNECTION ERROR - Cannot reach deck-builder", flush=True)
                        elif "404" in error_message or "not found" in error_message.lower():
                            print(f"   ⚠️  NOT FOUND - Deck-builder endpoint missing", flush=True)
                        else:
                            print(f"   ⚠️  UNKNOWN ERROR TYPE", flush=True)

                        print(f"   preview_url will be None (no preview available)", flush=True)
                        print("="*80, flush=True)
                        sys.stdout.flush()

                        logger.error(f"Deck-builder API failed: {e}", exc_info=True)
                        logger.warning("Falling back to JSON response without preview_url")

                        # Store error info in strawman for debugging
                        strawman._preview_url_error = f"{error_type}: {error_message}"
                        response = strawman
                else:
                    response = strawman

            elif state_context.current_state == "REFINE_STRAWMAN":
                logger.info("Refining strawman presentation")

                # v3.4-v1.2: Get original strawman to preserve v1.2 fields
                original_strawman_data = state_context.session_data.get("presentation_strawman")
                if not original_strawman_data:
                    logger.error("No original strawman found in session_data")
                    raise ValueError("Cannot refine: No original strawman found in session")

                # Reconstruct original strawman
                original_strawman = PresentationStrawman(**original_strawman_data)
                logger.info(f"Retrieved original strawman with {len(original_strawman.slides)} slides")

                # Generate refinements using LLM
                result = await call_with_retry(
                    lambda: self.refine_strawman_agent.run(
                        user_prompt,
                        model_settings=ModelSettings(temperature=0.4, max_tokens=8000)
                    ),
                    max_retries=settings.MAX_VERTEX_RETRIES,
                    base_delay=settings.VERTEX_RETRY_BASE_DELAY,
                    operation_name="Stage 5: Strawman Refinement"
                )
                refined_strawman = result.output  # PresentationStrawman object
                logger.info(f"Generated refined strawman with {len(refined_strawman.slides)} slides")

                # v3.4-diversity: Detect and log variant override requests
                variant_override_detected = self._detect_variant_override(user_prompt)
                if variant_override_detected:
                    logger.info(f"🎨 Variant override detected in user request: '{user_prompt[:100]}...'")
                    # Validate that structure_preference was updated with classification keywords
                    overridden_slides = self._identify_overridden_slides(
                        original=original_strawman,
                        refined=refined_strawman
                    )
                    if overridden_slides:
                        logger.info(
                            f"✅ Variant overrides applied to {len(overridden_slides)} slide(s): "
                            f"{[s.slide_number for s in overridden_slides]}"
                        )
                        for slide in overridden_slides:
                            logger.debug(
                                f"   Slide {slide.slide_number}: '{slide.structure_preference}'"
                            )
                    else:
                        logger.warning(
                            "⚠️ Variant override requested but no structure_preference changes detected. "
                            "LLM may need more explicit keywords in refinement."
                        )

                # v3.4-v1.2: Merge refined with original, preserving v1.2 fields
                strawman = self._merge_refined_strawman(
                    original=original_strawman,
                    refined=refined_strawman,
                    user_refinement_request=user_prompt
                )
                logger.info("Merged refined strawman with original (v1.2 fields preserved)")

                # v3.4-v1.2: Regenerate v1.2 fields for modified slides only
                await self._regenerate_v1_2_fields_for_modified_slides(strawman, original_strawman)
                logger.info(f"Regenerated v1.2 fields for modified slides")

                # Post-process to ensure asset fields are in correct format
                strawman = AssetFormatter.format_strawman(strawman)
                logger.info("Applied asset field formatting to refined strawman")

                # v2.0: Transform and send to deck-builder API
                if self.deck_builder_enabled:
                    try:
                        logger.info("Transforming refined presentation for deck-builder")
                        api_payload = self.content_transformer.transform_presentation(strawman)
                        logger.debug(f"Transformed to {len(api_payload['slides'])} deck-builder slides")

                        logger.info("Calling deck-builder API")
                        api_response = await self.deck_builder_client.create_presentation(api_payload)
                        presentation_url = self.deck_builder_client.get_full_url(api_response['url'])

                        logger.info(f"✅ Refined presentation created: {presentation_url}")

                        # v3.1: Return hybrid response with both URL and refined strawman
                        # URL for frontend display, refined strawman for CONTENT_GENERATION
                        response = {
                            "type": "presentation_url",
                            "url": presentation_url,
                            "presentation_id": api_response['id'],
                            "slide_count": len(strawman.slides),
                            "message": f"Your refined presentation is ready! View it at: {presentation_url}",
                            "strawman": strawman  # Include refined strawman for session storage
                        }
                    except Exception as e:
                        logger.error(f"Deck-builder API failed: {e}", exc_info=True)
                        logger.warning("Falling back to JSON response")
                        response = strawman
                else:
                    response = strawman

            elif state_context.current_state == "CONTENT_GENERATION":
                # v3.4-v1.2: Stage 6 - Text Service v1.2 with unified endpoint

                # v3.4 FIX: Use print() for Railway visibility (logger may be suppressed)
                import sys
                from datetime import datetime
                print("="*80, flush=True)
                print("🚀 ENTERING STAGE 6: CONTENT_GENERATION", flush=True)
                print(f"   Session ID: {session_id if 'session_id' in locals() else 'N/A'}", flush=True)
                print(f"   Timestamp: {datetime.utcnow().isoformat()}", flush=True)
                print("="*80, flush=True)
                sys.stdout.flush()

                logger.info("="*80)
                logger.info("🚀 Starting Stage 6: Content Generation (Text Service v1.2)")
                logger.info("="*80)

                # Get strawman from session
                logger.info(f"📥 Retrieving strawman from session_data...")
                logger.debug(f"   Available session_data keys: {list(state_context.session_data.keys())}")

                # v3.4 FIX: Add diagnostic logging for session data retrieval
                print(f"💾 SESSION DATA RETRIEVAL", flush=True)
                print(f"   Available keys: {list(state_context.session_data.keys())}", flush=True)
                print(f"   Has presentation_strawman: {'presentation_strawman' in state_context.session_data}", flush=True)
                sys.stdout.flush()

                strawman_data = state_context.session_data.get("presentation_strawman")
                if not strawman_data:
                    print(f"❌ ERROR: No strawman found in session_data!", flush=True)
                    print(f"   Session data keys: {list(state_context.session_data.keys())}", flush=True)
                    sys.stdout.flush()
                    logger.error("❌ No strawman found in session_data!")
                    logger.error(f"   Session data: {state_context.session_data}")
                    raise ValueError("No strawman found in session for content generation")

                logger.info(f"✅ Strawman retrieved successfully")
                print(f"✅ Strawman data retrieved from session", flush=True)
                sys.stdout.flush()

                strawman = PresentationStrawman(**strawman_data)
                logger.info(f"📊 Processing {len(strawman.slides)} slides with v1.2 routing")

                print(f"📊 Strawman deserialized: {len(strawman.slides)} slides", flush=True)
                sys.stdout.flush()

                # Validate slides have classifications
                unclassified = [s for s in strawman.slides if not s.slide_type_classification]
                if unclassified:
                    logger.error(f"{len(unclassified)} slides missing classification")
                    raise ValueError(
                        f"{len(unclassified)} slides are missing slide_type_classification. "
                        "Ensure GENERATE_STRAWMAN stage completed successfully."
                    )

                # Import content models and v1.2 routing components
                from src.models.content import EnrichedSlide, EnrichedPresentationStrawman
                from src.utils.service_router_v1_2 import ServiceRouterV1_2
                from src.utils.text_service_client_v1_2 import TextServiceClientV1_2
                from datetime import datetime

                # v3.4-v1.2: Initialize Text Service v1.2 client and router
                logger.info("⚙️  Initializing Text Service v1.2 client and router")

                try:
                    from config.settings import get_settings
                    settings = get_settings()

                    logger.info(f"🔗 Text Service URL: {settings.TEXT_SERVICE_URL}")
                    logger.info(f"⏱️  Text Service Timeout: {settings.TEXT_SERVICE_TIMEOUT}s")

                    # Initialize Text Service v1.2 client
                    v1_2_client = TextServiceClientV1_2(
                        base_url=settings.TEXT_SERVICE_URL,
                        timeout=settings.TEXT_SERVICE_TIMEOUT
                    )
                    logger.info(f"✅ v1.2 Client initialized successfully")

                    # Create v1.2 router
                    router = ServiceRouterV1_2(v1_2_client)
                    logger.info("✅ v1.2 Router initialized successfully")

                    # v3.4 FIX: Add diagnostic logging before Text Service call
                    print("="*80, flush=True)
                    print("🌐 CALLING TEXT SERVICE v1.2", flush=True)
                    print(f"   URL: {settings.TEXT_SERVICE_URL}", flush=True)
                    print(f"   Timeout: {settings.TEXT_SERVICE_TIMEOUT}s", flush=True)
                    print(f"   Total slides to process: {len(strawman.slides)}", flush=True)
                    print(f"   Starting at: {datetime.utcnow().isoformat()}", flush=True)
                    print("="*80, flush=True)
                    sys.stdout.flush()

                    # Route entire presentation through v1.2 unified endpoint
                    start_time = datetime.utcnow()
                    routing_result = await router.route_presentation(
                        strawman=strawman,
                        session_id=session_id
                    )

                    # v3.4 FIX: Log routing completion
                    print(f"✅ TEXT SERVICE ROUTING COMPLETE", flush=True)
                    print(f"   Duration: {(datetime.utcnow() - start_time).total_seconds():.2f}s", flush=True)
                    sys.stdout.flush()

                    # Parse routing results
                    generated_content = routing_result.get("generated_slides", [])
                    failed_generations = routing_result.get("failed_slides", [])
                    skipped_slides_list = routing_result.get("skipped_slides", [])
                    routing_metadata = routing_result.get("metadata", {})

                    logger.info(
                        f"Routing complete: {routing_metadata.get('successful_count', 0)} successful, "
                        f"{routing_metadata.get('failed_count', 0)} failed, "
                        f"{routing_metadata.get('skipped_count', 0)} skipped"
                    )

                    # Build enriched slides from routing results
                    enriched_slides = []
                    successful_slides = 0
                    failed_slides = 0
                    skipped_slides = 0

                    # Create lookup dicts for generated and skipped content
                    generated_lookup = {
                        gen.get("slide_id", gen.get("metadata", {}).get("slide_id")): gen
                        for gen in generated_content
                    }

                    skipped_lookup = {
                        skip.get("slide_id"): skip
                        for skip in skipped_slides_list
                    }

                    # Match generated content to slides
                    for slide in strawman.slides:
                        if slide.slide_id in generated_lookup:
                            # Successful generation
                            generated = generated_lookup[slide.slide_id]
                            enriched_slides.append(EnrichedSlide(
                                original_slide=slide,
                                slide_id=slide.slide_id,
                                generated_text=generated,
                                has_text_failure=False
                            ))
                            successful_slides += 1
                        elif slide.slide_id in skipped_lookup:
                            # Hero slide - skipped (uses title/subtitle only, NOT a failure)
                            enriched_slides.append(EnrichedSlide(
                                original_slide=slide,
                                slide_id=slide.slide_id,
                                generated_text=None,
                                has_text_failure=False  # NOT a failure!
                            ))
                            skipped_slides += 1
                            logger.info(
                                f"Hero slide {slide.slide_id} skipped "
                                f"(using generated_title/subtitle only)"
                            )
                        else:
                            # Actual failed generation
                            enriched_slides.append(EnrichedSlide(
                                original_slide=slide,
                                slide_id=slide.slide_id,
                                generated_text=None,
                                has_text_failure=True
                            ))
                            failed_slides += 1
                            logger.warning(f"No generated content for slide {slide.slide_id}")

                    generation_time = (datetime.utcnow() - start_time).total_seconds()

                    # Create enriched presentation with v3.4-v1.2 metadata
                    enriched_presentation = EnrichedPresentationStrawman(
                        original_strawman=strawman,
                        enriched_slides=enriched_slides,
                        generation_metadata={
                            "total_slides": len(strawman.slides),
                            "successful_slides": successful_slides,
                            "failed_slides": failed_slides,
                            "skipped_slides": skipped_slides,
                            "generation_time_seconds": generation_time,
                            "timestamp": datetime.utcnow().isoformat(),
                            "service_used": "text_service_v1.2",
                            "processing_mode": "sequential",
                            "routing_metadata": routing_metadata
                        }
                    )

                    logger.info(
                        f"✅ Content generation complete: {successful_slides}/{len(strawman.slides)} successful, "
                        f"{skipped_slides} skipped (hero slides) using Text Service v1.2"
                    )

                except Exception as e:
                    # v3.4 FIX: Comprehensive error diagnostics for Text Service failure
                    error_type = type(e).__name__
                    error_message = str(e)

                    print("="*80, flush=True)
                    print("❌ TEXT SERVICE ROUTING FAILED (STAGE 6)", flush=True)
                    print(f"   Error Type: {error_type}", flush=True)
                    print(f"   Error Message: {error_message}", flush=True)
                    print(f"   Text Service URL: {settings.TEXT_SERVICE_URL if 'settings' in locals() else 'unknown'}", flush=True)

                    # Check for specific error types
                    if "timeout" in error_message.lower() or "asyncio" in error_message.lower():
                        print(f"   ⚠️  TIMEOUT ERROR - Text Service not responding", flush=True)
                    elif "connection" in error_message.lower() or "refused" in error_message.lower():
                        print(f"   ⚠️  CONNECTION ERROR - Cannot reach Text Service", flush=True)
                    elif "404" in error_message or "not found" in error_message.lower():
                        print(f"   ⚠️  NOT FOUND - Text Service endpoint missing", flush=True)
                    elif "401" in error_message or "403" in error_message or "unauthorized" in error_message.lower():
                        print(f"   ⚠️  AUTH ERROR - Text Service authentication failed", flush=True)
                    else:
                        print(f"   ⚠️  UNKNOWN ERROR TYPE", flush=True)

                    print(f"   Falling back to strawman-only presentation (no enriched content)", flush=True)
                    print(f"   Affected slides: {len(strawman.slides)}", flush=True)
                    print("="*80, flush=True)
                    sys.stdout.flush()

                    logger.error("="*80)
                    logger.error(f"❌ STAGE 6 ERROR: Text Service routing failed")
                    logger.error(f"   Error type: {type(e).__name__}")
                    logger.error(f"   Error message: {str(e)}")
                    logger.error("="*80, exc_info=True)
                    logger.warning("⚠️  Text Service v1.2 routing unavailable, falling back to strawman")

                    # Fallback: Create minimal enriched presentation or return None
                    enriched_presentation = None
                    successful_slides = 0
                    failed_slides = len(strawman.slides)
                    logger.warning(f"📋 Fallback mode: {failed_slides} slides will use placeholder content")

                # Send enriched presentation to Layout Architect
                if self.deck_builder_enabled and enriched_presentation:
                    try:
                        deck_url = await self._send_enriched_to_layout_architect(enriched_presentation)
                        response = {
                            "type": "presentation_url",
                            "url": deck_url,
                            "slide_count": len(strawman.slides),
                            "content_generated": True,
                            "successful_slides": successful_slides,
                            "failed_slides": failed_slides,
                            "skipped_slides": skipped_slides,
                            "message": f"Your presentation with generated content is ready! View it at: {deck_url}"
                        }

                        # v3.4 DIAGNOSTIC: Log Stage 6 completion details (using print for Railway visibility)
                        import sys
                        print("="*80, flush=True)
                        print("✅ STAGE 6 COMPLETE - RETURNING URL (Content Generated)", flush=True)
                        print(f"   Response type: {response.get('type')}", flush=True)
                        print(f"   URL returned: {response.get('url')}", flush=True)
                        print(f"   Presentation ID: {response.get('presentation_id', 'N/A')}", flush=True)
                        print(f"   Content generated: {response.get('content_generated')}", flush=True)
                        print(f"   Successful slides: {response.get('successful_slides')}", flush=True)
                        print(f"   Failed slides: {response.get('failed_slides')}", flush=True)
                        print(f"   Skipped slides: {response.get('skipped_slides')}", flush=True)
                        print(f"   Message: {response.get('message')}", flush=True)
                        print("="*80, flush=True)
                        sys.stdout.flush()
                    except Exception as e:
                        logger.error(f"Layout Architect integration failed: {e}", exc_info=True)
                        logger.warning("Falling back to v2.0-style deck with placeholders")
                        # Fallback: use v2.0 approach (strawman with placeholders)
                        api_payload = self.content_transformer.transform_presentation(strawman)
                        api_response = await self.deck_builder_client.create_presentation(api_payload)
                        fallback_url = self.deck_builder_client.get_full_url(api_response['url'])
                        response = {
                            "type": "presentation_url",
                            "url": fallback_url,
                            "slide_count": len(strawman.slides),
                            "content_generated": False,
                            "message": f"Presentation created (fallback mode): {fallback_url}"
                        }
                elif self.deck_builder_enabled and not enriched_presentation:
                    # Text Service routing failed, use v2.0 approach
                    logger.warning("="*80)
                    logger.warning("⚠️  FALLBACK: No enriched content available, using v2.0 approach")
                    logger.warning("   This will create a deck with placeholder content (strawman)")
                    logger.warning("="*80)

                    api_payload = self.content_transformer.transform_presentation(strawman)
                    logger.info(f"📦 Sending {len(api_payload['slides'])} slides to deck-builder")

                    api_response = await self.deck_builder_client.create_presentation(api_payload)
                    fallback_url = self.deck_builder_client.get_full_url(api_response['url'])

                    logger.info(f"📋 Fallback deck created: {fallback_url}")

                    response = {
                        "type": "presentation_url",
                        "url": fallback_url,
                        "slide_count": len(strawman.slides),
                        "content_generated": False,
                        "message": f"Presentation created (no text generation): {fallback_url}"
                    }

                    # v3.4 DIAGNOSTIC: Log Stage 6 fallback completion (using print for Railway visibility)
                    import sys
                    print("="*80, flush=True)
                    print("✅ STAGE 6 COMPLETE - RETURNING URL (Fallback - No Content Generation)", flush=True)
                    print(f"   Response type: {response.get('type')}", flush=True)
                    print(f"   URL returned: {response.get('url')}", flush=True)
                    print(f"   Presentation ID: {api_response.get('id', 'N/A')}", flush=True)
                    print(f"   Content generated: {response.get('content_generated')}", flush=True)
                    print(f"   Slide count: {response.get('slide_count')}", flush=True)
                    print(f"   Message: {response.get('message')}", flush=True)
                    print("="*80, flush=True)
                    sys.stdout.flush()
                else:
                    # Return enriched presentation object if deck-builder disabled
                    response = enriched_presentation if enriched_presentation else strawman

            else:
                raise ValueError(f"Unknown state: {state_context.current_state}")

            return response

        except ModelHTTPError as e:
            logger.error(f"API error in state {state_context.current_state}: {e}")
            raise
        except Exception as e:
            error_msg = str(e)
            # Handle Gemini-specific errors
            if "MALFORMED_FUNCTION_CALL" in error_msg:
                logger.error(f"Gemini function call error in state {state_context.current_state}. This may be due to complex output structure.")
                logger.error(f"Full error: {error_msg}")
            elif "MAX_TOKENS" in error_msg:
                logger.error(f"Token limit exceeded in state {state_context.current_state}. Consider increasing max_tokens.")
            elif "Connection error" in error_msg:
                logger.error(f"Connection error in state {state_context.current_state} - Please check your API key is set in .env file")
            else:
                logger.error(f"Error processing state {state_context.current_state}: {error_msg}")
            raise

    def _generate_content_guidance(
        self,
        slide: Slide,
        slide_type_classification: str,
        position: int,
        total_slides: int,
        previous_slide_type: str = None
    ) -> ContentGuidance:
        """
        Generate ContentGuidance for a slide based on its classification and properties.

        v3.4: Rule-based content guidance generation for specialized text generators.

        Args:
            slide: Slide object with narrative, key_points, etc.
            slide_type_classification: Classified slide type from taxonomy
            position: Slide position (1-indexed)
            total_slides: Total slides in presentation
            previous_slide_type: Type of previous slide for relationship analysis

        Returns:
            ContentGuidance object with generation metadata
        """
        # Determine content_type based on slide classification
        content_type_map = {
            # Hero types (L29)
            "title_slide": "opening",
            "section_divider": "transition",
            "closing_slide": "conclusion",
            # Content types (L25)
            "bilateral_comparison": "comparison",
            "sequential_3col": "process",
            "impact_quote": "quote",
            "metrics_grid": "data",
            "matrix_2x2": "framework",
            "grid_3x3": "framework",
            "asymmetric_8_4": "narrative",
            "hybrid_1_2x2": "mixed",
            "single_column": "narrative",
            "styled_table": "data"
        }
        content_type = content_type_map.get(slide_type_classification, "narrative")

        # Determine visual_complexity based on slide type
        complex_types = ["matrix_2x2", "grid_3x3", "hybrid_1_2x2", "styled_table"]
        moderate_types = ["metrics_grid", "bilateral_comparison", "sequential_3col", "asymmetric_8_4"]
        visual_complexity = (
            "complex" if slide_type_classification in complex_types else
            "moderate" if slide_type_classification in moderate_types else
            "simple"
        )

        # Determine content_density based on key_points count
        key_points_count = len(slide.key_points) if slide.key_points else 0
        content_density = (
            "dense" if key_points_count > 5 else
            "balanced" if key_points_count > 2 else
            "minimal"
        )

        # Determine tone_indicator from slide content
        narrative_lower = slide.narrative.lower() if slide.narrative else ""
        if any(word in narrative_lower for word in ["inspire", "motivate", "imagine", "transform"]):
            tone = "inspirational"
        elif any(word in narrative_lower for word in ["data", "metric", "analysis", "statistic"]):
            tone = "analytical"
        elif any(word in narrative_lower for word in ["quote", "said", "believe"]):
            tone = "testimonial"
        else:
            tone = "professional"

        # Determine data_type if applicable
        data_type = None
        if slide_type_classification in ["metrics_grid", "styled_table"]:
            data_type = "metrics" if "metric" in slide_type_classification else "tabular"
        elif slide_type_classification == "matrix_2x2":
            data_type = "framework"
        elif slide_type_classification == "sequential_3col":
            data_type = "timeline"

        # Build emphasis_hierarchy based on slide structure
        emphasis_hierarchy = []
        if slide.title:
            emphasis_hierarchy.append("main_message")
        if slide.key_points and len(slide.key_points) > 0:
            emphasis_hierarchy.append("supporting_points")
        if slide.analytics_needed or slide.diagrams_needed:
            emphasis_hierarchy.append("visual_elements")
        if slide.narrative:
            emphasis_hierarchy.append("narrative_context")
        if not emphasis_hierarchy:
            emphasis_hierarchy = ["main_message"]

        # Determine relationship_to_previous
        relationship = None
        if position == 1:
            relationship = "opening"
        elif previous_slide_type:
            if previous_slide_type == slide_type_classification:
                relationship = "continuation"
            elif previous_slide_type == "section_divider":
                relationship = "new_section"
            elif slide_type_classification in ["bilateral_comparison", "matrix_2x2"]:
                relationship = "contrast"
            elif slide_type_classification in ["styled_table", "metrics_grid"]:
                relationship = "deep_dive"
            else:
                relationship = "progression"

        # Build generation_instructions based on slide type
        instruction_map = {
            "title_slide": "Create impactful opening with clear value proposition. Keep concise and memorable.",
            "section_divider": "Signal clear transition. Prepare audience for new topic. Brief and directive.",
            "closing_slide": "Strong call-to-action with memorable takeaway. Include next steps.",
            "bilateral_comparison": "Balance both columns equally. Highlight key differences. Clear labels.",
            "sequential_3col": "Show clear progression across steps. Connect each phase logically.",
            "impact_quote": "Center the quote as hero element. Attribute properly. Context if needed.",
            "metrics_grid": "Emphasize quantitative impact. Use consistent formatting for numbers.",
            "matrix_2x2": "Ensure 4 quadrants are balanced. Clear axis labels. Distinct positioning.",
            "grid_3x3": "Distribute content evenly across 9 cells. Maintain visual balance.",
            "asymmetric_8_4": "Main content should dominate. Sidebar supports but doesn't compete.",
            "hybrid_1_2x2": "Overview at top sets context. 2x2 below provides details.",
            "single_column": "Rich, detailed content. Use hierarchy and whitespace effectively.",
            "styled_table": "Structure data clearly. Headers must be descriptive. Highlight key values."
        }
        generation_instructions = instruction_map.get(
            slide_type_classification,
            "Generate clear, professional content aligned with slide purpose."
        )

        # Build pattern_rationale
        pattern_rationale = (
            f"Classified as '{slide_type_classification}' based on position={position}/{total_slides}, "
            f"content structure (key_points={key_points_count}), and semantic analysis. "
            f"This slide type best supports the {content_type} presentation goal."
        )

        return ContentGuidance(
            content_type=content_type,
            visual_complexity=visual_complexity,
            content_density=content_density,
            tone_indicator=tone,
            data_type=data_type,
            emphasis_hierarchy=emphasis_hierarchy,
            relationship_to_previous=relationship,
            generation_instructions=generation_instructions,
            pattern_rationale=pattern_rationale
        )

    async def _generate_slide_title(
        self,
        original_title: str,
        narrative: str,
        max_chars: int = 50
    ) -> str:
        """
        Generate concise slide title using LLM.

        v3.4-v1.2: Director generates titles with strict character limits.

        Args:
            original_title: Original title from strawman
            narrative: Slide narrative for context
            max_chars: Maximum character limit (default 50)

        Returns:
            Generated title (enforced to max_chars)
        """
        try:
            # Use Gemini to generate concise title
            prompt = f"""Create a concise, impactful slide title (max {max_chars} characters).

Original title: {original_title}
Context: {narrative[:200]}

Requirements:
- Maximum {max_chars} characters (STRICT)
- Professional and clear
- No special characters or emojis
- Captures key message
- Title case formatting

Return ONLY the title text, nothing else."""

            # Use the strawman model for title generation
            from pydantic_ai import Agent
            from pydantic import BaseModel

            class TitleResponse(BaseModel):
                title: str

            title_agent = Agent(
                model=self.title_generation_model,
                result_type=TitleResponse,
                system_prompt="You are a concise title generator for professional presentations."
            )

            result = await title_agent.run(prompt)
            generated_title = result.output.title

            # Enforce character limit with truncation fallback
            if len(generated_title) > max_chars:
                logger.warning(f"Generated title exceeds {max_chars} chars, truncating")
                generated_title = generated_title[:max_chars-3] + "..."

            logger.debug(f"Generated title ({len(generated_title)} chars): {generated_title}")
            return generated_title

        except Exception as e:
            logger.error(f"Title generation failed: {e}, using original title")
            # Fallback: truncate original title
            if len(original_title) > max_chars:
                return original_title[:max_chars-3] + "..."
            return original_title

    async def _generate_slide_subtitle(
        self,
        narrative: str,
        key_message: str = None,
        max_chars: int = 90
    ) -> str:
        """
        Generate concise slide subtitle using LLM.

        v3.4-v1.2: Director generates subtitles with strict character limits.

        Args:
            narrative: Slide narrative
            key_message: Optional key message for context
            max_chars: Maximum character limit (default 90)

        Returns:
            Generated subtitle (enforced to max_chars)
        """
        try:
            # Use Gemini to generate concise subtitle
            key_context = f"\nKey message: {key_message}" if key_message else ""
            prompt = f"""Create a concise subtitle that supports the slide (max {max_chars} characters).

Narrative: {narrative[:300]}{key_context}

Requirements:
- Maximum {max_chars} characters (STRICT)
- Complements the main title
- Professional and clear
- No special characters or emojis
- Adds context or value proposition

Return ONLY the subtitle text, nothing else."""

            # Use the strawman model for subtitle generation
            from pydantic_ai import Agent
            from pydantic import BaseModel

            class SubtitleResponse(BaseModel):
                subtitle: str

            subtitle_agent = Agent(
                model=self.title_generation_model,
                result_type=SubtitleResponse,
                system_prompt="You are a concise subtitle generator for professional presentations."
            )

            result = await subtitle_agent.run(prompt)
            generated_subtitle = result.output.subtitle

            # Enforce character limit with truncation fallback
            if len(generated_subtitle) > max_chars:
                logger.warning(f"Generated subtitle exceeds {max_chars} chars, truncating")
                generated_subtitle = generated_subtitle[:max_chars-3] + "..."

            logger.debug(f"Generated subtitle ({len(generated_subtitle)} chars): {generated_subtitle}")
            return generated_subtitle

        except Exception as e:
            logger.error(f"Subtitle generation failed: {e}, using narrative excerpt")
            # Fallback: use first sentence of narrative
            fallback = narrative.split('.')[0] if narrative else ""
            if len(fallback) > max_chars:
                return fallback[:max_chars-3] + "..."
            return fallback

    async def _generate_footer_text(
        self,
        presentation_title: str,
        max_chars: int = 20
    ) -> str:
        """
        Generate concise footer text using LLM.

        v3.4-v1.2: Director generates footer with strict character limits.

        Args:
            presentation_title: Presentation title for context
            max_chars: Maximum character limit (default 20)

        Returns:
            Generated footer text (enforced to max_chars)
        """
        try:
            # Use Gemini to generate concise footer
            prompt = f"""Create a very concise footer text for presentation (max {max_chars} characters).

Presentation: {presentation_title}

Requirements:
- Maximum {max_chars} characters (STRICT)
- Short company name, project name, or theme
- Professional
- No special characters
- Often just 2-4 words

Examples: "Q4 Strategy", "Sales Deck", "Product Launch"

Return ONLY the footer text, nothing else."""

            # Use the strawman model for footer generation
            from pydantic_ai import Agent
            from pydantic import BaseModel

            class FooterResponse(BaseModel):
                footer: str

            footer_agent = Agent(
                model=self.title_generation_model,
                result_type=FooterResponse,
                system_prompt="You are a concise footer text generator for professional presentations."
            )

            result = await footer_agent.run(prompt)
            generated_footer = result.output.footer

            # Enforce character limit with truncation fallback
            if len(generated_footer) > max_chars:
                logger.warning(f"Generated footer exceeds {max_chars} chars, truncating")
                generated_footer = generated_footer[:max_chars-3] + "..."

            logger.debug(f"Generated footer ({len(generated_footer)} chars): {generated_footer}")
            return generated_footer

        except Exception as e:
            logger.error(f"Footer generation failed: {e}, using abbreviated title")
            # Fallback: use abbreviated presentation title
            words = presentation_title.split()
            if len(words) > 2:
                fallback = f"{words[0]} {words[1]}"
            else:
                fallback = presentation_title

            if len(fallback) > max_chars:
                return fallback[:max_chars-3] + "..."
            return fallback

    def _detect_variant_override(self, user_prompt: str) -> bool:
        """
        Detect if user request contains variant override intent.

        v3.4-diversity: Recognizes patterns like:
        - "make slide X a matrix"
        - "change slide Y to grid format"
        - "use comparison for slide Z"

        Args:
            user_prompt: User's refinement request

        Returns:
            True if variant override detected
        """
        import re

        # Variant override patterns from refine_strawman.md
        patterns = [
            r'make slide \d+ (?:a |an )?(?:matrix|grid|comparison|sequential|metrics|quote|table|hybrid|asymmetric|single)',
            r'change slide \d+ to (?:matrix|grid|comparison|sequential|metrics|quote|table|hybrid|asymmetric|single)',
            r'use (?:matrix|grid|comparison|sequential|metrics|quote|table|hybrid|asymmetric|single) (?:for|format|layout) (?:for )?slide \d+',
            r'format slide \d+ as (?:a |an )?(?:matrix|grid|comparison|sequential|metrics|quote|table|hybrid|asymmetric|single)',
            r'slide \d+ should be (?:a |an )?(?:matrix|grid|comparison|sequential|metrics|quote|table|hybrid|asymmetric|single)',
        ]

        prompt_lower = user_prompt.lower()
        for pattern in patterns:
            if re.search(pattern, prompt_lower):
                return True

        return False

    def _identify_overridden_slides(
        self,
        original: PresentationStrawman,
        refined: PresentationStrawman
    ) -> List[Any]:
        """
        Identify slides where structure_preference was changed.

        v3.4-diversity: Used to validate that variant overrides were applied.

        Args:
            original: Original strawman before refinement
            refined: Refined strawman after LLM update

        Returns:
            List of refined slides with changed structure_preference
        """
        from src.models.agents import Slide

        overridden_slides: List[Slide] = []

        # Create lookup of original slides by slide_number
        original_slides_map = {
            slide.slide_number: slide
            for slide in original.slides
        }

        # Compare structure_preference for each refined slide
        for refined_slide in refined.slides:
            original_slide = original_slides_map.get(refined_slide.slide_number)

            if original_slide:
                # Check if structure_preference changed
                original_pref = (original_slide.structure_preference or "").strip()
                refined_pref = (refined_slide.structure_preference or "").strip()

                if original_pref != refined_pref:
                    overridden_slides.append(refined_slide)

        return overridden_slides

    def _merge_refined_strawman(
        self,
        original: PresentationStrawman,
        refined: PresentationStrawman,
        user_refinement_request: str
    ) -> PresentationStrawman:
        """
        Merge refined strawman with original, preserving v1.2 fields.

        v3.4-v1.2: Critical fix for REFINE_STRAWMAN stage to preserve:
        - variant_id (random selection from catalog)
        - slide_type_classification (13-type taxonomy)
        - generated_title (LLM-generated, 50 char limit)
        - generated_subtitle (LLM-generated, 90 char limit)
        - footer_text (LLM-generated, 20 char limit)
        - layout_id (L25 or L29)
        - content_guidance (generation metadata)

        Strategy:
        1. Keep all v1.2 fields from original slides
        2. Update content fields (narrative, key_points) from refined
        3. Preserve presentation-level footer_text

        Args:
            original: Original strawman with v1.2 fields
            refined: Refined strawman from LLM
            user_refinement_request: User's refinement request (unused but available)

        Returns:
            Merged strawman with v1.2 fields preserved
        """
        logger.info("Merging refined strawman with original (preserving v1.2 fields)")

        # Start with original strawman (deep copy)
        merged = original.model_copy(deep=True)

        # Update presentation-level fields from refined
        merged.main_title = refined.main_title
        merged.target_audience = refined.target_audience
        merged.overall_theme = refined.overall_theme
        merged.presentation_duration = refined.presentation_duration
        # PRESERVE footer_text from original (v1.2 field)

        # Slide count must match
        if len(original.slides) != len(refined.slides):
            logger.warning(
                f"Slide count mismatch: original={len(original.slides)}, "
                f"refined={len(refined.slides)}. Keeping original slide count."
            )
            # Return original if slide counts don't match
            return merged

        # Merge each slide
        for i, (orig_slide, ref_slide) in enumerate(zip(original.slides, refined.slides)):
            # PRESERVE v1.2 fields from original
            merged.slides[i].variant_id = orig_slide.variant_id
            merged.slides[i].slide_type_classification = orig_slide.slide_type_classification
            merged.slides[i].generated_title = orig_slide.generated_title
            merged.slides[i].generated_subtitle = orig_slide.generated_subtitle
            merged.slides[i].layout_id = orig_slide.layout_id
            merged.slides[i].layout_selection_reasoning = orig_slide.layout_selection_reasoning
            merged.slides[i].content_guidance = orig_slide.content_guidance

            # UPDATE content fields from refined
            merged.slides[i].title = ref_slide.title
            merged.slides[i].narrative = ref_slide.narrative
            merged.slides[i].key_points = ref_slide.key_points
            merged.slides[i].analytics_needed = ref_slide.analytics_needed
            merged.slides[i].visuals_needed = ref_slide.visuals_needed
            merged.slides[i].diagrams_needed = ref_slide.diagrams_needed
            merged.slides[i].structure_preference = ref_slide.structure_preference

            logger.debug(f"Merged slide {i+1}: preserved v1.2 fields, updated content")

        logger.info(f"✅ Merged {len(merged.slides)} slides successfully")
        return merged

    async def _regenerate_v1_2_fields_for_modified_slides(
        self,
        merged_strawman: PresentationStrawman,
        original_strawman: PresentationStrawman
    ) -> None:
        """
        Re-generate v1.2 fields (titles, subtitle) for slides with modified content.

        v3.4-v1.2: Only regenerates titles/subtitles if slide content changed significantly.
        Keeps variant_id and classification unchanged.

        Args:
            merged_strawman: Merged strawman (modified in place)
            original_strawman: Original strawman for comparison
        """
        logger.info("Checking for modified slides to regenerate v1.2 titles/subtitles")

        for i, (merged_slide, orig_slide) in enumerate(zip(merged_strawman.slides, original_strawman.slides)):
            # Check if content changed
            content_changed = (
                merged_slide.narrative != orig_slide.narrative or
                merged_slide.key_points != orig_slide.key_points
            )

            if content_changed:
                logger.info(f"Slide {i+1} content changed, regenerating title/subtitle")

                # Regenerate title
                try:
                    new_title = await self._generate_slide_title(
                        original_title=merged_slide.title,
                        narrative=merged_slide.narrative or "",
                        max_chars=50
                    )
                    merged_slide.generated_title = new_title
                    logger.debug(f"Regenerated title for slide {i+1}: '{new_title}'")
                except Exception as e:
                    logger.error(f"Title regeneration failed for slide {i+1}: {e}")
                    # Keep original title if regeneration fails

                # Regenerate subtitle
                try:
                    key_message = merged_slide.key_points[0] if merged_slide.key_points else None
                    new_subtitle = await self._generate_slide_subtitle(
                        narrative=merged_slide.narrative or "",
                        key_message=key_message,
                        max_chars=90
                    )
                    merged_slide.generated_subtitle = new_subtitle
                    logger.debug(f"Regenerated subtitle for slide {i+1}: '{new_subtitle}'")
                except Exception as e:
                    logger.error(f"Subtitle regeneration failed for slide {i+1}: {e}")
                    # Keep original subtitle if regeneration fails
            else:
                logger.debug(f"Slide {i+1} unchanged, keeping original v1.2 fields")

    async def _select_layout_by_use_case(
        self,
        slide: Slide,
        position: str,
        total_slides: int
    ) -> LayoutSelection:
        """
        Simplified layout selection for v7.5-main (2 layouts only).

        v3.4: Simplified from 24 layouts to 2 layouts (L25 and L29).
        No AI semantic matching needed - simple decision tree.

        Layouts:
        - L29 (Full-Bleed Hero): Opening, closing, section dividers
        - L25 (Main Content Shell): All content slides

        Args:
            slide: Slide object with narrative, key_points, etc.
            position: Slide position ("first", "last", "middle")
            total_slides: Total number of slides in presentation

        Returns:
            LayoutSelection with layout_id and reasoning
        """
        # Hero slides (L29) - maximum visual impact
        if position == "first":
            return LayoutSelection(
                layout_id="L29",
                reasoning="Opening hero slide - full-bleed impact",
                confidence=1.0
            )

        if position == "last":
            return LayoutSelection(
                layout_id="L29",
                reasoning="Closing hero slide - memorable finish",
                confidence=1.0
            )

        if slide.slide_type == "section_divider":
            # Smart detection: Check if this is actually an agenda/outline slide
            # Agenda slides typically appear early (position 2) and have specific keywords
            agenda_keywords = ["agenda", "outline", "overview", "roadmap", "contents", "table of contents"]
            is_likely_agenda = (
                position == "middle" and
                slide.slide_number == 2 and
                any(keyword in slide.title.lower() for keyword in agenda_keywords)
            )

            if is_likely_agenda:
                return LayoutSelection(
                    layout_id="L25",
                    reasoning="Agenda/outline slide - needs content layout for structured list",
                    confidence=0.9
                )
            else:
                return LayoutSelection(
                    layout_id="L29",
                    reasoning="Section divider - dramatic transition",
                    confidence=1.0
                )

        # All content slides use L25
        # L25 handles all content types: text, bullets, analytics, tables, diagrams
        return LayoutSelection(
            layout_id="L25",
            reasoning="Standard content slide - flexible rich content area",
            confidence=1.0
        )

    def _classify_l29_slide_purpose(
        self,
        slide: Slide,
        position: str,
        slide_number: int
    ) -> str:
        """
        Classify the purpose of an L29 hero slide for content generation guidance.

        Categories (with different word limits):
        - title_slide: Opening slide with presentation title (~75 words)
        - section_divider: Transition between major sections (~75 words)
        - closing_slide: Final CTA or thank you slide (~100 words)
        - regular_hero: Content-rich hero slide (~150 words)

        Args:
            slide: Slide object
            position: Slide position ("first", "last", "middle")
            slide_number: 1-indexed slide number

        Returns:
            Purpose classification string
        """
        # Opening slide = title_slide
        if position == "first" and slide_number == 1:
            return "title_slide"

        # Closing slide = closing_slide
        if position == "last":
            return "closing_slide"

        # Section dividers
        if slide.slide_type == "section_divider":
            return "section_divider"

        # Everything else is a regular hero with full creative freedom
        return "regular_hero"

    def _suggest_visual_pattern(
        self,
        slide: Slide,
        layout_id: str
    ) -> str:
        """
        Suggest visual design pattern based on slide content type.

        For L25 slides, analyzes key_points to suggest appropriate pattern:
        - 3-card-metrics-grid: When key_points contain numbers/metrics
        - styled-table: When key_points suggest comparison/data
        - 2-column-split-lists: When key_points suggest two categories
        - standard-content: Default rich content

        For L29 slides, suggests hero pattern based on purpose.

        Args:
            slide: Slide object with key_points
            layout_id: Layout being used (L25 or L29)

        Returns:
            Suggested pattern name
        """
        if layout_id == "L29":
            # L29 patterns handled by slide_purpose classification
            return "hero-gradient"

        # L25 pattern detection
        key_points = slide.key_points or []
        key_points_text = " ".join(key_points).lower()

        # Check for metrics (numbers, percentages, dollar amounts)
        has_metrics = any(char.isdigit() or char == '%' or char == '$' for char in key_points_text)

        # Check for comparison keywords
        comparison_keywords = ["vs", "versus", "compared", "before", "after", "current", "with", "without"]
        has_comparison = any(keyword in key_points_text for keyword in comparison_keywords)

        # Check for timeline/phases
        timeline_keywords = ["phase", "step", "stage", "quarter", "q1", "q2", "q3", "q4", "month", "week"]
        has_timeline = any(keyword in key_points_text for keyword in timeline_keywords)

        # Pattern selection logic
        if len(key_points) >= 3 and has_metrics:
            return "3-card-metrics-grid"
        elif has_comparison:
            return "styled-table"
        elif has_timeline or len(key_points) >= 4:
            return "2-column-split-lists"
        else:
            return "standard-content"

    # DEPRECATED v3.1 method - removed in v3.2
    # Replaced by _build_constraints_from_schema() which uses LayoutSchemaManager

    async def _generate_slide_text(
        self,
        slide: Slide,
        presentation: PresentationStrawman,
        session_id: str,
        slide_number: int
    ):
        """
        Generate text content for a single slide using Text Service.

        v3.2: Uses schema-driven architecture with layout_schema_manager.
        Sends complete layout schema to Text Service for structured generation.
        v3.3: Adds slide_purpose classification and visual pattern guidance.

        Args:
            slide: The slide to generate text for (with layout_id assigned)
            presentation: The full presentation context
            session_id: Session identifier for context tracking
            slide_number: Position of slide in presentation (1-indexed)

        Returns:
            GeneratedText object with structured content

        Raises:
            Exception: If Text Service is disabled or call fails
        """
        if not self.text_service_enabled:
            raise Exception("Text Service is not enabled")

        # v3.2: Get layout_id (should be assigned during GENERATE_STRAWMAN)
        layout_id = slide.layout_id
        if not layout_id:
            logger.warning(f"Slide {slide_number} has no layout_id, falling back to L05")
            layout_id = "L05"

        # v3.3: Determine slide position for purpose classification
        total_slides = len(presentation.slides)
        if slide_number == 1:
            position = "first"
        elif slide_number == total_slides:
            position = "last"
        else:
            position = "middle"

        # v3.3: Classify L29 slide purpose for targeted content generation
        slide_purpose = None
        if layout_id == "L29":
            slide_purpose = self._classify_l29_slide_purpose(slide, position, slide_number)
            logger.debug(f"Slide {slide_number} L29 purpose: {slide_purpose}")

        # v3.3: Suggest visual pattern based on content
        suggested_pattern = self._suggest_visual_pattern(slide, layout_id)
        logger.debug(f"Slide {slide_number} suggested pattern: {suggested_pattern}")

        # v3.2: Build schema-driven request using LayoutSchemaManager
        presentation_context = {
            "main_title": presentation.main_title,
            "overall_theme": presentation.overall_theme,
            "target_audience": presentation.target_audience,
            "presentation_duration": presentation.presentation_duration
        }

        schema_request = self.layout_schema_manager.build_content_request(
            layout_id=layout_id,
            slide=slide,
            presentation_context=presentation_context
        )

        # Add session tracking and v3.3 enhancements
        schema_request["presentation_id"] = session_id
        schema_request["slide_number"] = slide_number
        schema_request["slide_purpose"] = slide_purpose  # v3.3: L29 purpose classification
        schema_request["suggested_pattern"] = suggested_pattern  # v3.3: Visual pattern guidance

        logger.info(
            f"Generating content for slide {slide_number} using layout {layout_id} ({schema_request['layout_name']})"
        )
        logger.debug(f"Schema fields: {list(schema_request['layout_schema'].keys())}")

        # TODO v3.2: When Text Service v1.1 is deployed, use structured endpoint
        # For now, convert schema request to v1.0 format (backward compatibility)
        v1_request = self._convert_schema_request_to_v1(schema_request)

        # Call Text Service (v1.0 endpoint for now)
        generated = await self.text_client.generate(v1_request)
        logger.debug(f"Generated {len(generated.content)} chars for slide {slide_number}")

        return generated

    def _convert_schema_request_to_v1(self, schema_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert v3.2 schema request to v1.0 Text Service format.

        Temporary compatibility layer until Text Service v1.1 is deployed.
        v3.3: Adds slide_purpose and suggested_pattern to constraints.

        Args:
            schema_request: Schema-driven request from LayoutSchemaManager

        Returns:
            v1.0 compatible request dictionary
        """
        guidance = schema_request['content_guidance']
        layout_schema = schema_request['layout_schema']

        # v3.3: Extract slide_purpose and suggested_pattern
        slide_purpose = schema_request.get("slide_purpose")
        suggested_pattern = schema_request.get("suggested_pattern")

        # Build v1.0 compatible constraints from schema (v3.3: includes slide_purpose)
        constraints = self._build_constraints_from_schema(
            layout_schema,
            slide_purpose=slide_purpose,
            suggested_pattern=suggested_pattern
        )

        return {
            "presentation_id": schema_request.get("presentation_id", "default"),
            "slide_id": schema_request["slide_id"],
            "slide_number": schema_request["slide_number"],
            "topics": guidance.get("key_points", []),
            "narrative": guidance.get("narrative", ""),
            "context": {
                "presentation_context": f"{guidance.get('presentation_context', {}).get('main_title', '')} - {guidance.get('presentation_context', {}).get('overall_theme', '')}",
                "slide_context": guidance.get("narrative", ""),
                "previous_slides": []
            },
            "constraints": constraints,
            # v3.3: Explicit layout metadata fields for prompt conditionals
            "layout_id": schema_request.get("layout_id"),  # L25 or L29
            "slide_purpose": slide_purpose,  # title_slide, section_divider, closing_slide, regular_hero (L29 only)
            "suggested_pattern": suggested_pattern  # 3-card-metrics-grid, styled-table, etc.
        }

    def _build_constraints_from_schema(
        self,
        layout_schema: Dict[str, Any],
        slide_purpose: str = None,
        suggested_pattern: str = None
    ) -> Dict[str, Any]:
        """
        Build v1.0 constraints from v3.2 layout schema with smart content area sizing.

        Uses layout-specific character limits based on content area dimensions:
        - L25 rich_content (1800×720px): 1250 chars (~250 words)
        - L29 hero_content (1920×1080px): Variable based on slide_purpose
          - title_slide: 375 chars (~75 words) - simple, elegant
          - section_divider: 375 chars (~75 words) - clean transitions
          - closing_slide: 500 chars (~100 words) - CTA with details
          - regular_hero: 750 chars (~150 words) - rich content

        Only counts text_service-owned fields, ignoring layout_builder-owned fields
        (slide_title, subtitle, footer) to prevent underestimating content needs.

        Args:
            layout_schema: Schema from layout_schemas.json
            slide_purpose: L29 slide purpose classification (v3.3)
            suggested_pattern: Suggested visual pattern (v3.3)

        Returns:
            v1.0 compatible constraints dictionary
        """
        # Calculate total max characters from text_service-owned fields only
        total_chars = 0
        has_bullets = False
        has_numbered = False

        for field_name, field_spec in layout_schema.items():
            # Only process text_service-owned fields
            # Skip layout_builder-owned fields (slide_title, subtitle, footer)
            if field_spec.get('format_owner') != 'text_service':
                continue

            if field_spec.get('type') == 'string':
                if 'max_chars' in field_spec:
                    # Use explicit max_chars if specified
                    total_chars += field_spec['max_chars']
                else:
                    # Smart defaults based on content area size
                    # These fields have no max_chars because text_service has creative freedom
                    if field_name == 'rich_content':
                        # L25 main content area: 1800×720px = large content area
                        total_chars += 1250  # ~250 words for rich, engaging content
                    elif field_name == 'hero_content':
                        # L29 full-bleed hero: 1920×1080px = full screen impact
                        # v3.3: Adjust based on slide_purpose
                        if slide_purpose == 'title_slide':
                            total_chars += 375  # ~75 words - simple, elegant title
                        elif slide_purpose == 'section_divider':
                            total_chars += 375  # ~75 words - clean section transition
                        elif slide_purpose == 'closing_slide':
                            total_chars += 500  # ~100 words - CTA with contact info
                        else:  # regular_hero or None
                            total_chars += 750  # ~150 words - full creative freedom

            elif field_spec.get('type') == 'array':
                has_bullets = True
                items = field_spec.get('max_items', 5)
                chars_per = field_spec.get('max_chars_per_item', 100)
                total_chars += items * chars_per

            elif field_spec.get('type') == 'array_of_objects':
                has_numbered = True

        # Determine format based on content structure
        if has_bullets:
            format_type = "bullet_points"
        elif has_numbered:
            format_type = "numbered_list"
        else:
            format_type = "paragraph"

        return {
            "max_characters": total_chars or 800,  # Fallback to 800 if no fields found
            "tone": "professional",
            "format": format_type
        }

    async def _send_enriched_to_layout_architect(self, enriched: 'EnrichedPresentationStrawman') -> str:
        """
        Send enriched presentation to Layout Architect and get deck URL.

        Args:
            enriched: EnrichedPresentationStrawman with generated text content

        Returns:
            Full deck URL from Layout Architect

        Raises:
            Exception: If deck-builder call fails
        """
        logger.info("Sending enriched presentation to Layout Architect")

        # Transform enriched presentation to deck-builder format
        # Pass enriched data to content_transformer so it can inject real text
        api_payload = self.content_transformer.transform_presentation(
            enriched.original_strawman,
            enriched_data=enriched
        )

        logger.info(f"Transformed {len(api_payload['slides'])} slides with generated content")

        # Call deck-builder API
        api_response = await self.deck_builder_client.create_presentation(api_payload)
        deck_url = self.deck_builder_client.get_full_url(api_response['url'])

        logger.info(f"Layout Architect created deck: {deck_url}")

        return deck_url

    def get_token_report(self, session_id: str) -> dict:
        """Get token usage report for a specific session."""
        return self.token_tracker.get_savings_report(session_id)

    def print_token_report(self, session_id: str) -> None:
        """Print formatted token usage report for a session."""
        self.token_tracker.print_session_report(session_id)

    def get_aggregate_token_report(self) -> dict:
        """Get aggregate token usage report across all sessions."""
        return self.token_tracker.get_aggregate_report()

    def print_aggregate_token_report(self) -> None:
        """Print formatted aggregate token usage report."""
        self.token_tracker.print_aggregate_report()