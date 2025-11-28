#!/usr/bin/env python3
"""
Diagnostic script to check session state in Supabase.
Used to verify session persistence and debug restoration issues.
"""

import os
import sys
from datetime import datetime
from supabase import create_client, Client

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config.settings import get_settings


def check_session(session_id: str):
    """Check session state in Supabase."""

    # Initialize Supabase client
    settings = get_settings()

    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        print("❌ Supabase configuration missing!")
        print("Please set SUPABASE_URL and SUPABASE_ANON_KEY environment variables.")
        return

    try:
        supabase: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_ANON_KEY
        )
        print(f"✅ Connected to Supabase: {settings.SUPABASE_URL}")
        print()
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        return

    # Query session
    print(f"🔍 Querying session: {session_id}")
    print("=" * 80)

    try:
        result = supabase.table("sessions").select("*").eq("id", session_id).execute()

        if not result.data:
            print(f"❌ Session not found: {session_id}")
            print()
            print("Possible reasons:")
            print("1. Session was never created")
            print("2. Session_id is incorrect")
            print("3. Session was deleted")
            return

        session = result.data[0]

        # Display session information
        print(f"✅ Session found!")
        print()
        print("📊 SESSION DETAILS:")
        print("-" * 80)
        print(f"ID:                    {session.get('id')}")
        print(f"User ID:               {session.get('user_id')}")
        print(f"Current State:         {session.get('current_state')}")
        print(f"Created At:            {session.get('created_at')}")
        print(f"Updated At:            {session.get('updated_at')}")
        print()

        # Check conversation history
        history = session.get('conversation_history', [])
        print(f"💬 CONVERSATION HISTORY: {len(history)} messages")
        print("-" * 80)
        if history:
            for i, msg in enumerate(history, 1):
                role = msg.get('role', 'unknown')
                intent = msg.get('intent', {}).get('intent_type', 'N/A')
                state = msg.get('state', 'N/A')
                print(f"{i}. [{role}] Intent: {intent}, State: {state}")
        else:
            print("(No conversation history)")
        print()

        # Check workflow data
        print("📋 WORKFLOW DATA:")
        print("-" * 80)
        print(f"Initial Request:       {session.get('user_initial_request')}")
        print(f"Clarifying Answers:    {session.get('clarifying_answers')}")
        print(f"Confirmation Plan:     {'Yes' if session.get('confirmation_plan') else 'No'}")
        print(f"Presentation Strawman: {'Yes' if session.get('presentation_strawman') else 'No'}")
        print(f"Presentation URL:      {session.get('presentation_url')}")
        print(f"Refinement Feedback:   {session.get('refinement_feedback')}")
        print()

        # Analyze state for restoration
        print("🔍 RESTORATION ANALYSIS:")
        print("-" * 80)
        current_state = session.get('current_state')

        if current_state == "PROVIDE_GREETING":
            print("❌ State is PROVIDE_GREETING - Will send greeting on reconnection")
            print("   This means NO restoration will occur!")
        else:
            print(f"✅ State is {current_state} - Will restore history on reconnection")
            print(f"   Restoration should send {len(history)} messages to frontend")

        print()
        print("=" * 80)

    except Exception as e:
        print(f"❌ Error querying session: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python check_session_state.py <session_id>")
        print()
        print("Example:")
        print("  python check_session_state.py fce87bea-acf5-4003-9b38-e460d6eeb46f")
        sys.exit(1)

    session_id = sys.argv[1]
    check_session(session_id)


if __name__ == "__main__":
    main()
