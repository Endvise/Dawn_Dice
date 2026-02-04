#!/usr/bin/env python3
"""
Supabase 연결 테스트 스크립트

사용법:
    python test_supabase_connection.py

이 스크립트는 다음을 테스트합니다:
1. Supabase 연결 (GET)
2. 데이터 쓰기 테스트 (INSERT)
3. 데이터 수정 테스트 (UPDATE)
4. 데이터 삭제 테스트 (DELETE)
"""

import sys
import requests

# Supabase 설정 (secrets.toml에서 가져옴)
SUPABASE_URL = "https://gticuuzplbemivfturuz.supabase.co"


def test_connection(supabase_key, key_name=""):
    """연결 테스트 실행"""
    print(f"\n{'=' * 60}")
    print(f"테스트: {key_name}")
    print(f"{'=' * 60}")

    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
        "Content-Type": "application/json",
    }

    # 1. 연결 테스트 (GET)
    print("\n1. 연결 테스트 (users 테이블 읽기)...")
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/users?select=id&limit=1",
            headers=headers,
            timeout=10,
        )
        print(f"   상태 코드: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ 연결 성공")
        elif response.status_code == 401:
            print("   ❌ 401 Unauthorized - 키가 유효하지 않음")
            return False
        else:
            print(f"   ⚠️  응답: {response.text[:100]}")
    except Exception as e:
        print(f"   ❌ 연결 실패: {e}")
        return False

    # 2. INSERT 테스트 (테스트용 사용자 생성)
    print("\n2. 쓰기 테스트 (테스트용 사용자 INSERT)...")
    test_user = {
        "username": "__test_user__",
        "commander_number": "TEST1234567890",
        "password_hash": "test_hash_only",
        "role": "user",
        "nickname": "Test User",
    }
    try:
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/users", headers=headers, json=test_user, timeout=10
        )
        print(f"   상태 코드: {response.status_code}")
        if response.status_code in [200, 201]:
            print("   ✅ INSERT 성공")
            insert_success = True
        elif response.status_code == 401:
            print("   ❌ 쓰기 권한 없음 - service_role key 필요")
            insert_success = False
        else:
            print(f"   ⚠️  응답: {response.text[:200]}")
            insert_success = False
    except Exception as e:
        print(f"   ❌ INSERT 실패: {e}")
        insert_success = False

    # 3. UPDATE 테스트 (테스트용 사용자 수정)
    print("\n3. 수정 테스트 (테스트용 사용자 UPDATE)...")
    if insert_success:
        try:
            response = requests.patch(
                f"{SUPABASE_URL}/rest/v1/users?commander_number=eq.TEST1234567890",
                headers=headers,
                json={"nickname": "Test User Updated"},
                timeout=10,
            )
            print(f"   상태 코드: {response.status_code}")
            if response.status_code in [200, 204]:
                print("   ✅ UPDATE 성공")
            else:
                print(f"   ⚠️  응답: {response.text[:200]}")
        except Exception as e:
            print(f"   ❌ UPDATE 실패: {e}")
    else:
        print("   ⏭️  INSERT 실패로 스킵")

    # 4. DELETE 테스트 (테스트용 사용자 삭제)
    print("\n4. 삭제 테스트 (테스트용 사용자 DELETE)...")
    if insert_success:
        try:
            response = requests.delete(
                f"{SUPABASE_URL}/rest/v1/users?commander_number=eq.TEST1234567890",
                headers=headers,
                timeout=10,
            )
            print(f"   상태 코드: {response.status_code}")
            if response.status_code in [200, 204]:
                print("   ✅ DELETE 성공")
            else:
                print(f"   ⚠️  응답: {response.text[:200]}")
        except Exception as e:
            print(f"   ❌ DELETE 실패: {e}")
    else:
        print("   ⏭️  INSERT 실패로 스킵")

    return insert_success


def main():
    """메인 함수"""
    print("\n" + "=" * 60)
    print("Supabase 연결 테스트")
    print("=" * 60)

    # anon key로 테스트
    anon_key = "sb_publishable_Z53hNS_FW1c4Bi5BVwDxfQ_mMH1wP0-"
    print("\n📌 anon key (현재 설정값)로 테스트...")
    result1 = test_connection(anon_key, "anon key (읽기 전용)")

    # service_role key로 테스트 (사용자 입력)
    print("\n" + "-" * 60)
    service_role_key = input("service_role key를 입력하세요 (없으면 엔터): ").strip()

    result2 = False
    if service_role_key:
        print("\n📌 service_role key로 테스트...")
        result2 = test_connection(service_role_key, "service_role key (전체 권한)")

    # 요약
    print("\n" + "=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)

    if result1:
        print("✅ anon key: 읽기/쓰기 모두 가능 (이상함 - RLS 비활성화?)")
    else:
        print("❌ anon key: 쓰기 권한 없음 (정상)")

    if result2:
        print("✅ service_role key: 모든 작업 가능 (정상)")
        print("\n🎉 Supabase 설정 완료!")
    else:
        print("❌ service_role key: 테스트되지 않음 또는 실패")

    if not result1 and not result2:
        print("\n📋 해결 방법:")
        print("1. Supabase Dashboard 접속: https://supabase.com/dashboard")
        print("2. 프로젝트 'gticuuzplbemivfturuz' 선택")
        print("3. Settings → API → service_role 섹션")
        print("4. service_role key 복사")
        print("5. .streamlit/secrets.toml의 SERVICE_ROLE_KEY에 붙여넣기")

    return 0 if (result1 or result2) else 1


if __name__ == "__main__":
    sys.exit(main())
