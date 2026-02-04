#!/usr/bin/env python3
"""
Configuration Management Module
Supabase 및 데이터베이스 설정을 관리합니다.
"""

import streamlit as st
from pathlib import Path
from typing import Dict, Optional

# 전역 캐시
_config_cache: Optional[Dict] = None

# secrets 파일 경로 우선순위
SECRETS_PATHS = [
    Path(".secrets/supabase_secrets.toml"),  # 최우선 (gitignored)
    Path(".streamlit/secrets.toml"),  # Streamlit 기본
]


def _load_secrets() -> Dict:
    """여러 위치에서 secrets를 로드합니다."""
    for secrets_path in SECRETS_PATHS:
        if secrets_path.exists():
            try:
                import toml

                return toml.load(secrets_path)
            except Exception:
                continue
    return {}


def _get_secrets_value(key: str, default=None):
    """secrets 값을 가져옵니다."""
    secrets = _load_secrets()
    if key in secrets:
        return secrets[key]
    try:
        return st.secrets.get(key, default)
    except Exception:
        return default


def get_config() -> Dict:
    """
    전체 설정을 반환합니다 (캐시됨).
    """
    global _config_cache
    if _config_cache is None:
        _config_cache = {
            "db_type": _get_db_type(),
            "supabase": _get_supabase_config(),
            "auth": _get_auth_config(),
            "security": _get_security_config(),
            "session": _get_session_config(),
        }
    return _config_cache


def _get_db_type() -> str:
    """데이터베이스 타입 반환"""
    return _get_secrets_value("DB_TYPE", "supabase")


def _get_supabase_config() -> Dict:
    """Supabase 설정 반환"""
    return {
        "url": _get_secrets_value(
            "SUPABASE_URL", "https://gticuuzplbemivfturuz.supabase.co"
        ),
        "anon_key": _get_secrets_value("SUPABASE_KEY", ""),
        "service_role_key": _get_secrets_value("SERVICE_ROLE_KEY", ""),
        "use_auth": _get_secrets_value("USE_SUPABASE_AUTH", False),
    }


def _get_auth_config() -> Dict:
    """인증 설정 반환"""
    return {
        "master_username": _get_secrets_value("MASTER_USERNAME", ""),
        "master_password": _get_secrets_value("MASTER_PASSWORD", ""),
        "max_login_attempts": _get_secrets_value("MAX_LOGIN_ATTEMPTS", 5),
    }


def _get_security_config() -> Dict:
    """보안 설정 반환"""
    return {
        "password_hash_rounds": _get_secrets_value("PASSWORD_HASH_ROUNDS", 12),
    }


def _get_session_config() -> Dict:
    """세션 설정 반환"""
    return {
        "timeout_minutes": _get_secrets_value("SESSION_TIMEOUT_MINUTES", 60),
    }


def get_supabase_url(table: str) -> str:
    """Supabase REST API URL 반환"""
    config = get_config()
    return f"{config['supabase']['url']}/rest/v1/{table}"


def get_headers() -> Dict[str, str]:
    """Supabase API 헤더 반환 (service_role 우선)"""
    config = get_config()
    key = config["supabase"]["service_role_key"] or config["supabase"]["anon_key"]
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }


def reload_config() -> None:
    """설정 캐시를 재로드합니다."""
    global _config_cache
    _config_cache = None
