-- ============================================
-- participants 테이블에 Session Check-in 컬럼 추가
-- 실행: Supabase Dashboard > SQL Editor
-- ============================================

-- 체크인 관련 컬럼 추가 (이미 존재하면 무시)
ALTER TABLE public.participants
ADD COLUMN IF NOT EXISTS re_confirmed BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS alliance_entry BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS dice_purchased BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS checked_by TEXT,
ADD COLUMN IF NOT EXISTS checked_at TIMESTAMP WITH TIME ZONE;

-- 컬럼 설명 주석 추가
COMMENT ON COLUMN public.participants.re_confirmed IS '재확인 완료';
COMMENT ON COLUMN public.participants.alliance_entry IS '연맹 입장 완료';
COMMENT ON COLUMN public.participants.dice_purchased IS '주사위 구매 완료';
COMMENT ON COLUMN public.participants.checked_by IS '체크한 관리자';
COMMENT ON COLUMN public.participants.checked_at IS '체크 일시';

-- 인덱스 생성 (이미 존재하면 무시)
CREATE INDEX IF NOT EXISTS idx_participants_event_name ON public.participants(event_name);
CREATE INDEX IF NOT EXISTS idx_participants_igg_id ON public.participants(igg_id);

-- 확인 쿼리
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'participants'
ORDER BY ordinal_position;
