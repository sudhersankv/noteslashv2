"""Verify local setup: env vars, Supabase, OpenAI. Run from backend/: python scripts/verify_setup.py"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow imports from backend root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings


def check_env() -> list[str]:
    errors: list[str] = []
    required = {
        "SUPABASE_URL": settings.supabase_url,
        "SUPABASE_SERVICE_ROLE_KEY": settings.supabase_service_role_key,
        "OPENAI_API_KEY": settings.openai_api_key,
    }
    for name, value in required.items():
        if not value or value.startswith("YOUR_") or value.startswith("sk-..."):
            errors.append(f"Missing or placeholder: {name}")
    if not settings.cors_origin_list:
        errors.append("CORS_ORIGINS is empty")
    return errors


def check_supabase() -> tuple[bool, str]:
    try:
        from supabase import create_client

        client = create_client(settings.supabase_url, settings.supabase_service_role_key)
        client.table("projects").select("id").limit(1).execute()
        return True, "Supabase OK — projects table reachable"
    except Exception as e:
        msg = str(e)
        if "projects" in msg.lower() or "schema" in msg.lower() or "relation" in msg.lower():
            return False, f"Supabase connected but schema missing? Run migrations. ({msg[:120]})"
        return False, f"Supabase failed: {msg[:200]}"


def check_openai() -> tuple[bool, str]:
    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)
        client.embeddings.create(
            model=settings.openai_embedding_model,
            input="setup check",
        )
        return True, f"OpenAI OK — embedding model {settings.openai_embedding_model}"
    except Exception as e:
        return False, f"OpenAI failed: {str(e)[:200]}"


def main() -> int:
    print("=== Noteslash — setup verify ===\n")

    env_errors = check_env()
    if env_errors:
        print("ENV:")
        for err in env_errors:
            print(f"  FAIL  {err}")
        print("\nFix backend/.env and re-run.")
        return 1
    print("ENV:  OK  (required variables present)\n")

    ok, msg = check_supabase()
    print(f"{'SUPABASE' if ok else 'SUPABASE'}:  {'OK' if ok else 'FAIL'}  {msg}\n")

    ok_oai, msg_oai = check_openai()
    print(f"{'OPENAI' if ok_oai else 'OPENAI'}:  {'OK' if ok_oai else 'FAIL'}  {msg_oai}\n")

    if not ok or not ok_oai:
        return 1

    print("All checks passed. Ready to build.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
