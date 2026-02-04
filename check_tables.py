#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Supabase 테이블 존재 확인 스크립트

participants, announcements 테이블 생성 확인용
"""

import sys
import requests
from pathlib import Path
import toml

# UTF-8 출력 설정 (Windows 콘솔 호환)
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

SUPABASE_URL = "https://gticuuzplbemivfturuz.supabase.co"


def load_service_role_key():
    """service_role key 로드"""
    secrets_path = Path(".secrets/supabase_secrets.toml")
    if not secrets_path.exists():
        print(f"[X] secrets 파일 없음: {secrets_path}")
        return None

    secrets = toml.load(secrets_path)
    # SERVICE_ROLE_KEY (대문자) 우선, 소문자도 시도
    key = secrets.get("SERVICE_ROLE_KEY") or secrets.get("supabase", {}).get(
        "service_role_key"
    )
    if not key:
        print("[X] SERVICE_ROLE_KEY를 찾을 수 없습니다.")
    return key


def check_table_exists(table_name, headers):
    """테이블 존재 확인"""
    print(f"\n🔍 {table_name} 테이블 확인 중...")

    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/{table_name}?select=id&limit=1",
            headers=headers,
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()
            count = len(data) if isinstance(data, list) else 0
            print(f"   ✅ {table_name} 테이블 존재 (현재 데이터: {count}개)")
            return True
        elif response.status_code == 404:
            print(f"   ❌ {table_name} 테이블 없음 (404 Not Found)")
            return False
        else:
            print(f"   ⚠️  상태 코드: {response.status_code}")
            print(f"   응답: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"   ❌ 오류: {e}")
        return False


def main():
    print("=" * 60)
    print("Supabase 테이블 생성 확인")
    print("=" * 60)

    # service_role key 로드
    service_role_key = load_service_role_key()
    if not service_role_key:
        print("\n❌ service_role key를 찾을 수 없습니다.")
        return 1

    headers = {
        "apikey": service_role_key,
        "Authorization": f"Bearer {service_role_key}",
        "Content-Type": "application/json",
    }

    # 테이블 확인
    tables = ["participants", "announcements"]
    results = {}

    for table in tables:
        results[table] = check_table_exists(table, headers)

    # 요약
    print("\n" + "=" * 60)
    print("테이블 확인 요약")
    print("=" * 60)

    all_exist = all(results.values())

    for table, exists in results.items():
        status = "✅ 존재" if exists else "❌ 없음"
        print(f"{table}: {status}")

    print("\n" + "=" * 60)

    if all_exist:
        print("🎉 모든 테이블이 생성되었습니다!")
        return 0
    else:
        print("⚠️  일부 테이블이 생성되지 않았습니다.")
        print("\n해결 방법:")
        print("1. Supabase Dashboard 접속")
        print("2. SQL Editor → New Query")
        print("3. .sisyphus/create_missing_tables.sql 내용 붙여넣기")
        print("4. Run 클릭")
        return 1


if __name__ == "__main__":
    sys.exit(main())
