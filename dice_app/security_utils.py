#!/usr/bin/env python3
"""
보안 유틸리티 - 개발자 모드 방지
"""

import streamlit as st


def inject_devtools_block():
    """개발자 도구(F12) 방지 JavaScript를 주입합니다."""
    # 관리자인 경우 개발자 모드 허용
    import auth

    if auth.is_admin():
        return

    # 개발자 도구 방지 JavaScript
    js_code = """
    <script>
    // F12 키 방지
    document.addEventListener('keydown', function(e) {
        if (e.key === 'F12' ||
            e.key === 'f12' ||
            (e.ctrlKey && e.shiftKey && (e.key === 'I' || e.key === 'i')) ||
            (e.ctrlKey && e.shiftKey && (e.key === 'C' || e.key === 'c')) ||
            (e.ctrlKey && e.shiftKey && (e.key === 'J' || e.key === 'j')) ||
            (e.ctrlKey && e.key === 'U' || e.key === 'u')) {
            e.preventDefault();
            e.stopPropagation();
            return false;
        }
    });

    // 마우스 우클릭 방지
    document.addEventListener('contextmenu', function(e) {
        e.preventDefault();
        return false;
    });

    // 개발자 도구 감지
    const devtools = {
        open: false,
        orientation: null
    };

    const threshold = 160;

    setInterval(() => {
        const widthThreshold = window.outerWidth - window.innerWidth > threshold;
        const heightThreshold = window.outerHeight - window.innerHeight > threshold;
        const orientation = widthThreshold ? 'vertical' : 'horizontal';

        if ((heightThreshold && orientation !== devtools.orientation) ||
            (widthThreshold && orientation !== devtools.orientation) ||
            (heightThreshold && widthThreshold && orientation !== devtools.orientation)) {
            if (!devtools.open) {
                devtools.open = true;
                devtools.orientation = orientation;

                // 개발자 도구가 열리면 페이지 리로드
                alert('개발자 도구 사용이 감지되었습니다.\\n보안 정책에 따라 페이지가 리로드됩니다.');
                location.reload();
            }
        } else {
            if (!devtools.open) {
                devtools.open = false;
                devtools.orientation = null;
            }
        }
    }, 500);

    // 콘솔 감지
    const element = new Image();
    Object.defineProperty(element, 'id', {
        get: function() {
            alert('개발자 도구 사용이 감지되었습니다.\\n보안 정책에 따라 페이지가 리로드됩니다.');
            location.reload();
        }
    });
    console.log(element);
    console.clear();
    </script>
    """

    # JavaScript 주입
    st.markdown(js_code, unsafe_allow_html=True)


def show_security_warning():
    """보안 경고 메시지를 표시합니다."""
    st.warning("""
    ⚠️ **보안 안내**

    - 개발자 도구(F12) 사용은 보안 정책상 제한됩니다.
    - 관리자는 이 제한을 해제할 수 있습니다.
    - 불필요한 페이지 수정 시도는 감지될 수 있습니다.
    """)
