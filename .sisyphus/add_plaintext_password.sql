-- ============================================
-- users 테이블에 plaintext_password 컬럼 추가
-- ============================================
-- 이 SQL은 Supabase SQL Editor에서 실행하세요

-- 컬럼 추가 (이미 존재하면 무시)
ALTER TABLE public.users
ADD COLUMN IF NOT EXISTS plaintext_password text;

-- 컬럼 설명 주석 추가
COMMENT ON COLUMN public.users.plaintext_password IS '초기 비밀번호 (평문) - 관리자가 열람 가능';

-- 인덱스 생성 (필요시)
-- CREATE INDEX idx_users_plaintext_password ON public.users(plaintext_password);
