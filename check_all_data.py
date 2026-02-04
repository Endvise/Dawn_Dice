#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Supabase 데이터 확인 스크립트

테이블 및 마스터 계정 생성 확인
"""

import sys
import requests
from pathlib import Path
import toml

SUPABASE_URL = "https://gticuuzplbemivfturuz.supabase.co"

# UTF-8 출력 설정 (Windows 콘솔 호환)
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def load_service_role_key():
    """service_role key 로드"""
    secrets_path = Path(".secrets/supabase_secrets.toml")
    if not secrets_path.exists():
        print(f"[X] secrets 파일 없음: {secrets_path}")
        return None

    secrets = toml.load(secrets_path)
    key = secrets.get("SERVICE_ROLE_KEY") or secrets.get("supabase", {}).get(
        "service_role_key"
    )
    if not key:
        print("[X] SERVICE_ROLE_KEY를 찾을 수 없습니다.")
    return key


def check_table(table_name, headers):
    """테이블 데이터 수 확인"""
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
            return True, count
        else:
            print(f"   ❌ 상태 코드: {response.status_code}")
            print(f"   응답: {response.text[:200]}")
            return False, 0

    except Exception as e:
        print(f"   ❌ 오류: {e}")
        return False, 0


def check_master_account(headers):
    """마스터 계정 확인"""
    print(f"\n🔑 마스터 계정 확인 중...")

    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/admins?username=eq.DaWnntt0623&select=id,username,role",
            headers=headers,
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                print(f"   ✅ 마스터 계정 존재")
                print(f"   ID: {data[0].get('id')}")
                print(f"   Username: {data[0].get('username')}")
                print(f"   Role: {data[0].get('role')}")
                return True
            else:
                print(f"   ❌ 마스터 계정 없음")
                print(f"   💡 SQL Editor에서 INSERT 문 실행 필요")
                return False
        else:
            print(f"   ❌ 상태 코드: {response.status_code}")
            return False

    except Exception as e:
        print(f"   ❌ 오류: {e}")
        return False


def main():
    """메인 함수"""
    print("=" * 60)
    print("Supabase 데이터 확인")
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
    tables = [
        "admins",
        "users",
        "reservations",
        "blacklist",
        "participants",
        "announcements",
    ]
    table_results = {}

    for table in tables:
        exists, count = check_table(table, headers)
        table_results[table] = {"exists": exists, "count": count}

    # 마스터 계정 확인
    master_exists = check_master_account(headers)

    # 요약
    print("\n" + "=" * 60)
    print("확인 요약")
    print("=" * 60)

    for table, result in table_results.items():
        status = "✅ 존재" if result["exists"] else "❌ 없음"
        print(f"{table}: {status} ({result['count']}개)")

    print(f"\n마스터 계정: {'✅ 존재' if master_exists else '❌ 없음'}")

    print("\n" + "=" * 60)

    # 체크리스트 결과
    all_ok = all(r["exists"] for r in table_results.values())

    if all_ok and master_exists:
        print("🎉 모든 준비 완료!")
        print("\n📋 다음 단계:")
        print("1. Streamlit 앱 접속: http://localhost:8502")
        print("2. 마스터 계정으로 로그인")
        print("   - ID: DaWnntt0623")
        print("   - PW: .secrets/supabase_secrets.toml 참고")
        return 0
    else:
        print("⚠️  일부 준비가 되지 않았습니다.")

        if not master_exists:
            print("\n💡 마스터 계정 생성 방법:")
            print("1. Supabase Dashboard 접속")
            print("2. SQL Editor → New Query")
            print("3. 아래 SQL 실행:")
            print()
            print(
                "INSERT INTO admins (id, username, password_hash, full_name, role, created_at)"
            )
            print("VALUES (")
            print("  gen_random_uuid(),")
            print("  'DaWnntt0623',")
            print("  '$2b$12$HSvKXJrKap3XcNzFis8FL.3Z.XJrbHkfDW1TbtongvQWq7X5stzDq',")
            print("  'Master',")
            print("  'master',")
            print("  NOW()")
            print(");")

        return 1


if __name__ == "__main__":
    sys.exit(main())
