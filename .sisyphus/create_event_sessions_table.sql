-- ============================================
-- event_sessions 테이블 생성 SQL
-- ============================================
-- Supabase SQL Editor에서 실행하세요

CREATE TABLE public.event_sessions (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    session_number integer NOT NULL UNIQUE,
    session_name text NOT NULL,
    session_date date NOT NULL,
    max_participants integer NOT NULL DEFAULT 180,
    is_active boolean NOT NULL DEFAULT false,
    reservation_open_time timestamp with time zone,
    reservation_close_time timestamp with time zone,
    created_by uuid,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    CONSTRAINT event_sessions_pkey PRIMARY KEY (id),
    CONSTRAINT event_sessions_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.admins(id)
);

-- 인덱스 생성
CREATE INDEX idx_event_sessions_is_active ON public.event_sessions(is_active);
CREATE INDEX idx_event_sessions_session_number ON public.event_sessions(session_number);
