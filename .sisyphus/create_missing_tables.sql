-- DaWn Dice Party - Supabase 테이블 생성 SQL
-- 생성일: 2026-02-04

-- =====================================================
-- 1. participants 테이블 (참여자 목록)
-- =====================================================
CREATE TABLE participants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    number INTEGER,
    nickname TEXT,
    affiliation TEXT,
    igg_id TEXT,  -- 사령관번호
    alliance TEXT,
    wait_confirmed BOOLEAN DEFAULT FALSE,
    confirmed BOOLEAN DEFAULT FALSE,
    notes TEXT,
    completed BOOLEAN DEFAULT FALSE,
    participation_record TEXT,
    event_name TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_participants_igg_id ON participants(igg_id);
CREATE INDEX idx_participants_event_name ON participants(event_name);

-- =====================================================
-- 2. announcements 테이블 (공지사항)
-- =====================================================
CREATE TABLE announcements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    content TEXT NOT NULL,  -- Markdown 지원
    category TEXT DEFAULT '공지',
    is_pinned BOOLEAN DEFAULT FALSE,
    created_by UUID,  -- admins.id 참조
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (created_by) REFERENCES admins(id)
);

CREATE INDEX idx_announcements_is_active ON announcements(is_active);
CREATE INDEX idx_announcements_is_pinned ON announcements(is_pinned);
