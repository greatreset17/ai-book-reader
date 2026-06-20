"""
AI Book Reader - 汎用型AIブックリーダーアプリ
Streamlit + Gemini API による書籍分析・翻訳・対話アプリ
"""
import os
import streamlit as st
from dotenv import load_dotenv
from pathlib import Path

from lib.file_parser import extract_text, split_sections, truncate_for_ai
from lib.gemini_client import GeminiClient

# ---------------------------------------------------------------------------
# Page Config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Book Reader",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS (theme-aware via CSS variables)
# ---------------------------------------------------------------------------
def get_theme_css(is_dark: bool) -> str:
    if is_dark:
        return """
        :root {
            --bg: #0e1117; --bg2: #1a1f2e; --text: #e0e0e0; --text-sub: #888;
            --card-bg: rgba(26,31,46,0.7); --card-border: rgba(124,77,255,0.15);
            --card-shadow: rgba(0,0,0,0.3);
            --chat-ai-bg: rgba(255,255,255,0.06); --chat-ai-border: rgba(255,255,255,0.08);
            --sidebar-bg-start: #0e1117; --sidebar-bg-end: #151922;
            --badge-bg: linear-gradient(135deg,#667eea33,#764ba233);
            --badge-border: rgba(124,77,255,0.3); --badge-text: #b39ddb;
            --mermaid-bg: rgba(14,17,23,0.6); --mermaid-border: rgba(124,77,255,0.2);
        }"""
    else:
        return """
        :root {
            --bg: #ffffff; --bg2: #f5f5f7; --text: #1d1d1f; --text-sub: #6e6e73;
            --card-bg: rgba(255,255,255,0.85); --card-border: rgba(100,60,180,0.12);
            --card-shadow: rgba(0,0,0,0.06);
            --chat-ai-bg: rgba(0,0,0,0.03); --chat-ai-border: rgba(0,0,0,0.06);
            --sidebar-bg-start: #f5f5f7; --sidebar-bg-end: #eeeef0;
            --badge-bg: linear-gradient(135deg,#667eea18,#764ba218);
            --badge-border: rgba(100,60,180,0.2); --badge-text: #6b4fb8;
            --mermaid-bg: rgba(245,245,247,0.8); --mermaid-border: rgba(100,60,180,0.15);
        }"""


def inject_css(is_dark: bool):
    theme_vars = get_theme_css(is_dark)
    st.markdown(
        f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Noto+Sans+JP:wght@300;400;500;700&display=swap');
    {theme_vars}
    html, body, [class*="css"] {{ font-family: 'Inter', 'Noto Sans JP', sans-serif; }}

    /* ===== Streamlit core overrides ===== */
    .stApp, [data-testid="stAppViewContainer"],
    [data-testid="stMain"], [data-testid="stMainBlockContainer"],
    [data-testid="stVerticalBlock"], [data-testid="stBottom"],
    .main .block-container {{
        background-color: var(--bg) !important;
        color: var(--text) !important;
    }}
    [data-testid="stSidebar"], [data-testid="stSidebar"] > div {{
        background: linear-gradient(180deg, var(--sidebar-bg-start), var(--sidebar-bg-end)) !important;
        color: var(--text) !important;
    }}
    [data-testid="stHeader"] {{
        display: none !important;
    }}

    /* Text elements */
    .stMarkdown, .stMarkdown p, .stMarkdown li,
    .stText, h1, h2, h3, h4, h5, h6,
    [data-testid="stCaptionContainer"],
    label, .stSelectbox label, .stTextInput label {{
        color: var(--text) !important;
    }}
    small, .stCaption, [data-testid="stCaptionContainer"] p {{
        color: var(--text-sub) !important;
    }}

    /* Inputs, selects, buttons */
    [data-testid="stFileUploader"],
    [data-testid="stFileUploader"] > div,
    [data-testid="stFileUploader"] section,
    [data-testid="stFileUploaderDropzone"],
    [data-baseweb="select"] > div,
    [data-baseweb="input"] > div,
    .stTextInput > div > div,
    .stSelectbox > div > div {{
        background-color: var(--bg2) !important;
        color: var(--text) !important;
        border-color: var(--card-border) !important;
    }}
    [data-testid="stFileUploaderDropzone"] span,
    [data-testid="stFileUploaderDropzone"] small,
    [data-testid="stFileUploaderDropzone"] p {{
        color: var(--text-sub) !important;
    }}
    [data-baseweb="select"] span,
    [data-baseweb="input"] input {{
        color: var(--text) !important;
    }}

    /* Chat Input */
    [data-testid="stChatInput"],
    [data-testid="stChatInput"] > div,
    [data-testid="stChatInput"] textarea,
    .stChatInput > div,
    .stChatInput textarea {{
        background-color: var(--bg2) !important;
        color: var(--text) !important;
        -webkit-text-fill-color: var(--text) !important;
        border-color: var(--card-border) !important;
    }}
    [data-testid="stChatInput"] svg {{
        fill: var(--text) !important;
    }}

    /* Buttons */
    .stButton > button,
    [data-testid="stBaseButton-secondary"] {{
        background-color: var(--bg2) !important;
        color: var(--text) !important;
        border-color: var(--card-border) !important;
    }}
    .stButton > button:hover,
    [data-testid="stBaseButton-secondary"]:hover {{
        border-color: var(--badge-text) !important;
    }}

    /* Popover / dropdown menus */
    [data-baseweb="popover"] > div,
    [data-baseweb="menu"],
    [data-baseweb="menu"] li,
    ul[role="listbox"],
    ul[role="listbox"] li {{
        background-color: var(--bg2) !important;
        color: var(--text) !important;
    }}
    ul[role="listbox"] li:hover,
    [data-baseweb="menu"] li:hover {{
        background-color: var(--card-border) !important;
    }}

    /* Containers & cards */
    [data-testid="stVerticalBlockBorderWrapper"],
    [data-testid="stExpander"],
    [data-testid="stExpander"] details {{
        background-color: var(--bg2) !important;
        border-color: var(--card-border) !important;
    }}
    [data-testid="stExpander"] summary span {{
        color: var(--text) !important;
    }}

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{ gap: 4px; background-color: transparent !important; }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 8px 8px 0 0; padding: 8px 20px; font-weight: 500;
        color: var(--text-sub) !important;
    }}
    .stTabs [data-baseweb="tab"][aria-selected="true"] {{
        color: var(--badge-text) !important;
    }}
    .stTabs [data-baseweb="tab-panel"] {{
        background-color: transparent !important;
    }}

    /* Toggle */
    [data-testid="stToggle"] label span {{
        color: var(--text) !important;
    }}

    /* Divider */
    [data-testid="stHorizontalRule"], hr {{
        border-color: var(--card-border) !important;
    }}

    /* Alerts */
    [data-testid="stAlert"] {{
        background-color: var(--bg2) !important;
        color: var(--text) !important;
    }}

    /* Scrollable containers */
    [data-testid="stScrollableContainer"] {{
        background-color: var(--bg2) !important;
        border-color: var(--card-border) !important;
    }}

    /* Code blocks */
    .stCodeBlock, code {{
        background-color: var(--bg2) !important;
    }}

    /* ===== Custom classes ===== */
    .main-header {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text; font-size: 2.2rem; font-weight: 700;
        margin-bottom: 0.2rem; letter-spacing: -0.02em;
    }}
    .sub-header {{ color: var(--text-sub) !important; font-size: 0.95rem; margin-bottom: 1.5rem; }}
    .glass-card {{
        background: var(--card-bg); backdrop-filter: blur(12px);
        border: 1px solid var(--card-border); border-radius: 16px;
        padding: 1.5rem; margin-bottom: 1rem; box-shadow: 0 8px 32px var(--card-shadow);
    }}
    .glass-card h4 {{ color: var(--badge-text) !important; }}
    .glass-card p {{ color: var(--text-sub) !important; font-size: 0.85rem; }}
    .mermaid-container {{
        background: var(--mermaid-bg); border: 1px solid var(--mermaid-border);
        border-radius: 12px; padding: 1rem; min-height: 300px;
        display: flex; align-items: center; justify-content: center;
    }}
    .mermaid-container p {{ color: var(--text-sub) !important; }}
    .chat-user {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white !important;
        padding: 0.8rem 1.2rem; border-radius: 16px 16px 4px 16px;
        margin: 0.5rem 0; margin-left: 20%; font-size: 0.9rem;
    }}
    .chat-ai {{
        background: var(--chat-ai-bg); border: 1px solid var(--chat-ai-border);
        color: var(--text) !important; padding: 0.8rem 1.2rem;
        border-radius: 16px 16px 16px 4px; margin: 0.5rem 0; margin-right: 20%; font-size: 0.9rem;
    }}
    .sidebar-title {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text; font-size: 1.3rem; font-weight: 700;
    }}
    .model-badge {{
        display: inline-block; background: var(--badge-bg);
        border: 1px solid var(--badge-border); color: var(--badge-text) !important;
        padding: 0.2rem 0.8rem; border-radius: 20px; font-size: 0.75rem; font-weight: 500;
    }}
    </style>
    """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Mermaid rendering helper
# ---------------------------------------------------------------------------
def render_mermaid(mermaid_code: str, height: int = 500, dark_mode: bool = True):
    """Render Mermaid diagram with zoom & pan controls"""
    import streamlit.components.v1 as components
    mermaid_theme = 'dark' if dark_mode else 'default'
    ctrl_bg = 'rgba(26,31,46,0.9)' if dark_mode else 'rgba(255,255,255,0.92)'
    ctrl_border = 'rgba(124,77,255,0.3)' if dark_mode else 'rgba(100,60,180,0.2)'
    ctrl_color = '#b39ddb' if dark_mode else '#6b4fb8'
    ctrl_hover_bg = 'rgba(124,77,255,0.25)' if dark_mode else 'rgba(100,60,180,0.1)'
    label_color = '#888' if dark_mode else '#666'

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                background: transparent;
                overflow: hidden;
                width: 100%;
                height: 100vh;
                font-family: 'Inter', 'Noto Sans JP', sans-serif;
            }}
            #viewport {{
                width: 100%;
                height: 100%;
                overflow: hidden;
                cursor: grab;
                position: relative;
            }}
            #viewport:active {{ cursor: grabbing; }}
            #canvas {{
                transform-origin: 0 0;
                position: absolute;
                top: 0; left: 0;
                display: inline-block;
                padding: 24px;
            }}
            .mermaid {{
                font-family: 'Inter', 'Noto Sans JP', sans-serif;
            }}
            /* Zoom controls */
            .controls {{
                position: fixed;
                bottom: 12px;
                right: 12px;
                display: flex;
                gap: 4px;
                z-index: 100;
            }}
            .controls button {{
                width: 32px; height: 32px;
                border: 1px solid {ctrl_border};
                background: {ctrl_bg};
                color: {ctrl_color};
                border-radius: 8px;
                font-size: 16px;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                backdrop-filter: blur(8px);
                transition: all 0.15s;
            }}
            .controls button:hover {{
                background: {ctrl_hover_bg};
                border-color: #7c4dff;
            }}
            .zoom-label {{
                color: {label_color};
                font-size: 11px;
                line-height: 32px;
                padding: 0 6px;
                user-select: none;
            }}
        </style>
    </head>
    <body>
        <div id="viewport">
            <div id="canvas">
                <div class="mermaid">
{mermaid_code}
                </div>
            </div>
        </div>
        <div class="controls">
            <span class="zoom-label" id="zoomLabel">100%</span>
            <button id="zoomIn" title="拡大">+</button>
            <button id="zoomOut" title="縮小">−</button>
            <button id="zoomReset" title="リセット">⟲</button>
            <button id="zoomFit" title="フィット">⊞</button>
        </div>
        <script>
            mermaid.initialize({{
                startOnLoad: true,
                theme: '{mermaid_theme}',
                themeVariables: {{
                    primaryColor: '#7c4dff',
                    primaryTextColor: '{'#e0e0e0' if dark_mode else '#1d1d1f'}',
                    primaryBorderColor: '#9575cd',
                    lineColor: '{'#b39ddb' if dark_mode else '#8e73c7'}',
                    secondaryColor: '#1a1f2e',
                    tertiaryColor: '#0e1117',
                    fontSize: '14px'
                }},
                flowchart: {{ curve: 'basis', padding: 20 }}
            }});

            // --- Zoom & Pan ---
            const viewport = document.getElementById('viewport');
            const canvas = document.getElementById('canvas');
            const zoomLabel = document.getElementById('zoomLabel');
            let scale = 1, panX = 0, panY = 0;
            let isDragging = false, startX, startY;
            const MIN_SCALE = 0.2, MAX_SCALE = 5;

            function applyTransform() {{
                canvas.style.transform = `translate(${{panX}}px, ${{panY}}px) scale(${{scale}})`;
                zoomLabel.textContent = Math.round(scale * 100) + '%';
            }}

            // Center diagram after render
            setTimeout(() => {{
                const svg = canvas.querySelector('svg');
                if (svg) {{
                    const vw = viewport.clientWidth, vh = viewport.clientHeight;
                    const sw = svg.scrollWidth, sh = svg.scrollHeight;
                    scale = Math.min(vw / (sw + 48), vh / (sh + 48), 1.5);
                    scale = Math.max(scale, MIN_SCALE);
                    panX = (vw - sw * scale) / 2;
                    panY = (vh - sh * scale) / 2;
                    applyTransform();
                }}
            }}, 500);

            // Mouse wheel zoom
            viewport.addEventListener('wheel', (e) => {{
                e.preventDefault();
                const rect = viewport.getBoundingClientRect();
                const mx = e.clientX - rect.left;
                const my = e.clientY - rect.top;
                const delta = e.deltaY > 0 ? 0.9 : 1.1;
                const newScale = Math.min(Math.max(scale * delta, MIN_SCALE), MAX_SCALE);
                panX = mx - (mx - panX) * (newScale / scale);
                panY = my - (my - panY) * (newScale / scale);
                scale = newScale;
                applyTransform();
            }}, {{ passive: false }});

            // Drag pan
            viewport.addEventListener('mousedown', (e) => {{
                isDragging = true;
                startX = e.clientX - panX;
                startY = e.clientY - panY;
            }});
            window.addEventListener('mousemove', (e) => {{
                if (!isDragging) return;
                panX = e.clientX - startX;
                panY = e.clientY - startY;
                applyTransform();
            }});
            window.addEventListener('mouseup', () => {{ isDragging = false; }});

            // Button controls
            document.getElementById('zoomIn').onclick = () => {{
                scale = Math.min(scale * 1.25, MAX_SCALE);
                applyTransform();
            }};
            document.getElementById('zoomOut').onclick = () => {{
                scale = Math.max(scale * 0.8, MIN_SCALE);
                applyTransform();
            }};
            document.getElementById('zoomReset').onclick = () => {{
                scale = 1; panX = 0; panY = 0;
                applyTransform();
            }};
            document.getElementById('zoomFit').onclick = () => {{
                const svg = canvas.querySelector('svg');
                if (svg) {{
                    const vw = viewport.clientWidth, vh = viewport.clientHeight;
                    const sw = svg.scrollWidth, sh = svg.scrollHeight;
                    scale = Math.min(vw / (sw + 48), vh / (sh + 48), 1.5);
                    scale = Math.max(scale, MIN_SCALE);
                    panX = (vw - sw * scale) / 2;
                    panY = (vh - sh * scale) / 2;
                    applyTransform();
                }}
            }};
        </script>
    </body>
    </html>
    """
    components.html(html, height=height, scrolling=False)


# ---------------------------------------------------------------------------
# Initialize session state
# ---------------------------------------------------------------------------
def init_state():
    defaults = {
        "book_text": "",
        "sections": [],
        "selected_section_idx": 0,
        "translation_cache": {},
        "mermaid_cache": {},
        "summary_cache": {},
        "chat_history": [],
        "gemini_client": None,
        "file_name": "",
        "dark_mode": True,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


init_state()

# ---------------------------------------------------------------------------
# Initialize Gemini client from .env or st.secrets
# ---------------------------------------------------------------------------
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

# 1. Check OS environment variables
_api_key = os.getenv("GEMINI_API_KEY", "")
# 2. Check Streamlit Secrets if not found
if not _api_key:
    try:
        _api_key = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        pass

if _api_key and st.session_state.gemini_client is None:
    try:
        st.session_state.gemini_client = GeminiClient(_api_key)
    except Exception as e:
        st.error(f"Gemini API 初期化エラー: {e}")

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="sidebar-title">📚 AI Book Reader</div>', unsafe_allow_html=True)
    st.caption("AI-powered reading companion")

    # Theme toggle
    st.session_state.dark_mode = not st.toggle(
        "☀️ ライトモード",
        value=not st.session_state.dark_mode,
    )

    st.divider()

# Inject theme CSS (must be after toggle so state is up-to-date)
inject_css(st.session_state.dark_mode)

with st.sidebar:

    # Fallback API Key Input if not set in secrets
    if st.session_state.gemini_client is None:
        user_api_key = st.text_input("🔑 Gemini API Key", type="password", help="Settingsから保存できない場合はここに入力してください。")
        if user_api_key:
            try:
                st.session_state.gemini_client = GeminiClient(user_api_key)
                st.rerun()
            except Exception as e:
                st.error(f"APIキーエラー: {e}")
        st.divider()

    # File upload
    uploaded_file = st.file_uploader(
        "📄 書籍ファイルをアップロード",
        type=["pdf", "txt", "md"],
        help="PDF, TXT, MD形式に対応。最大50MB。",
    )

    # Load preset book button
    sample_book_path = Path(__file__).parent / "books" / "wealth_of_nations.md"
    if sample_book_path.exists():
        st.divider()
        st.caption("📖 収録書籍")
        if st.button("国富論 (The Wealth of Nations)", use_container_width=True):
            with open(sample_book_path, "r", encoding="utf-8") as f:
                st.session_state.book_text = f.read()
            st.session_state.sections = split_sections(st.session_state.book_text)
            st.session_state.selected_section_idx = 0
            st.session_state.file_name = "wealth_of_nations.md"
            # Clear caches for new book
            st.session_state.translation_cache = {}
            st.session_state.mermaid_cache = {}
            st.session_state.summary_cache = {}
            st.session_state.chat_history = []
            st.rerun()

    # Process uploaded file
    if uploaded_file is not None:
        current_name = uploaded_file.name
        if current_name != st.session_state.file_name:
            with st.spinner("テキスト抽出中..."):
                text = extract_text(uploaded_file)
                st.session_state.book_text = text
                st.session_state.sections = split_sections(text)
                st.session_state.selected_section_idx = 0
                st.session_state.file_name = current_name
                # Clear caches for new book
                st.session_state.translation_cache = {}
                st.session_state.mermaid_cache = {}
                st.session_state.summary_cache = {}
                st.session_state.chat_history = []
            st.success(f"✅ {current_name} を読み込みました")

    # Section selector
    if st.session_state.sections:
        st.divider()
        section_titles = [
            f"{'　' * (s['level'] - 1)}{s['title'][:50]}"
            for s in st.session_state.sections
        ]
        selected = st.selectbox(
            "📑 セクション選択",
            range(len(section_titles)),
            format_func=lambda i: section_titles[i],
            index=st.session_state.selected_section_idx,
        )
        st.session_state.selected_section_idx = selected

        # Section info
        current_section = st.session_state.sections[selected]
        char_count = len(current_section["content"])
        st.caption(f"文字数: {char_count:,}")

    # Model info
    if st.session_state.gemini_client:
        st.divider()
        model = st.session_state.gemini_client.current_model
        st.markdown(
            f'<span class="model-badge">🤖 {model}</span>',
            unsafe_allow_html=True,
        )

# ---------------------------------------------------------------------------
# Main Content
# ---------------------------------------------------------------------------
st.markdown('<div class="main-header">📚 AI Book Reader</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Upload a book and explore it with AI — translation, structural analysis, and interactive chat</div>',
    unsafe_allow_html=True,
)

if not st.session_state.book_text:
    # Landing state
    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            """
        <div class="glass-card" style="text-align:center;">
            <div style="font-size:2.5rem; margin-bottom:0.5rem;">📖</div>
            <h4 style="color:#b39ddb;">現代語訳</h4>
            <p style="color:#888; font-size:0.85rem;">AIがテキストをわかりやすい現代日本語に翻訳</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            """
        <div class="glass-card" style="text-align:center;">
            <div style="font-size:2.5rem; margin-bottom:0.5rem;">🔗</div>
            <h4 style="color:#b39ddb;">構造図</h4>
            <p style="color:#888; font-size:0.85rem;">因果関係・相関図をMermaid.jsで自動生成</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            """
        <div class="glass-card" style="text-align:center;">
            <div style="font-size:2.5rem; margin-bottom:0.5rem;">💬</div>
            <h4 style="color:#b39ddb;">対話</h4>
            <p style="color:#888; font-size:0.85rem;">テキストについてAIと自由にチャット</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.info("👈 サイドバーからファイルをアップロード、またはサンプル書籍を選択してください。")

else:
    # Book loaded - two column layout
    sections = st.session_state.sections
    idx = st.session_state.selected_section_idx
    current_section = sections[idx] if sections else {"title": "全文", "content": st.session_state.book_text, "level": 1}
    section_text = current_section["content"]
    section_title = current_section["title"]

    left_col, right_col = st.columns([1, 1], gap="large")

    # ===== LEFT COLUMN: Text Display =====
    with left_col:
        st.markdown(f"#### 📖 {section_title}")

        show_translation = st.toggle("🌏 AI現代語訳を表示", value=False)

        if show_translation:
            client = st.session_state.gemini_client
            if client is None:
                st.warning("⚠️ Gemini API Keyが設定されていません。")
            else:
                cache_key = f"translate_{idx}"
                if cache_key not in st.session_state.translation_cache:
                    with st.spinner("🔄 翻訳中..."):
                        try:
                            truncated = truncate_for_ai(section_text)
                            result = client.translate(truncated)
                            st.session_state.translation_cache[cache_key] = result
                        except Exception as e:
                            st.error(f"翻訳エラー: {e}")
                            st.session_state.translation_cache[cache_key] = None

                translation = st.session_state.translation_cache.get(cache_key)
                if translation:
                    with st.container(height=550):
                        st.markdown(translation)
        else:
            # Show original text immediately
            with st.container(height=550):
                st.markdown(section_text)

    # ===== RIGHT COLUMN: Tabs =====
    with right_col:
        tab_mermaid, tab_summary, tab_chat = st.tabs(
            ["🔗 Mermaid構造図", "📊 AI要約・応用", "💬 チャット対話"]
        )

        client = st.session_state.gemini_client

        # ----- Mermaid Tab -----
        with tab_mermaid:
            st.markdown(f"##### 因果関係・相関図: {section_title[:40]}")

            if client is None:
                st.warning("⚠️ API Keyを入力してください。")
            else:
                cache_key = f"mermaid_{idx}"
                if st.button("🔄 構造図を生成", key="gen_mermaid"):
                    with st.spinner("🔄 構造図を生成中..."):
                        try:
                            truncated = truncate_for_ai(section_text)
                            mermaid_code = client.generate_mermaid(truncated)
                            st.session_state.mermaid_cache[cache_key] = mermaid_code
                        except Exception as e:
                            st.error(f"生成エラー: {e}")

                mermaid_code = st.session_state.mermaid_cache.get(cache_key)
                if mermaid_code:
                    render_mermaid(mermaid_code, height=450, dark_mode=st.session_state.dark_mode)

                    with st.expander("📝 Mermaidコードを表示"):
                        st.code(mermaid_code, language="mermaid")
                else:
                    st.markdown(
                        """
                    <div class="mermaid-container">
                        <div style="text-align:center; color:#666;">
                            <div style="font-size:3rem; margin-bottom:1rem;">🔗</div>
                            <p>「構造図を生成」ボタンを押すと<br>AIが因果関係図を作成します</p>
                        </div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

        # ----- Summary Tab -----
        with tab_summary:
            st.markdown(f"##### AI要約・応用: {section_title[:40]}")

            if client is None:
                st.warning("⚠️ API Keyを入力してください。")
            else:
                cache_key = f"summary_{idx}"
                if st.button("📊 要約を生成", key="gen_summary"):
                    with st.spinner("🔄 要約を生成中..."):
                        try:
                            truncated = truncate_for_ai(section_text)
                            summary = client.summarize(truncated)
                            st.session_state.summary_cache[cache_key] = summary
                        except Exception as e:
                            st.error(f"生成エラー: {e}")

                summary = st.session_state.summary_cache.get(cache_key)
                if summary:
                    st.markdown(summary)
                else:
                    st.markdown(
                        """
                    <div class="glass-card" style="text-align:center; padding:3rem;">
                        <div style="font-size:3rem; margin-bottom:1rem;">📊</div>
                        <p style="color:#888;">「要約を生成」ボタンを押すと<br>AIが現代の視点で分析します</p>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

        # ----- Chat Tab -----
        with tab_chat:
            st.markdown(f"##### 💬 テキストについて質問")

            if client is None:
                st.warning("⚠️ API Keyを入力してください。")
            else:
                # Display chat history
                chat_container = st.container(height=400)
                with chat_container:
                    if not st.session_state.chat_history:
                        st.markdown(
                            """
                        <div style="text-align:center; padding:2rem; color:#666;">
                            <div style="font-size:2.5rem; margin-bottom:0.5rem;">💬</div>
                            <p>テキストについて何でも質問してください。<br>
                            例: 「この章の主要な論点は？」「現代ではどう適用できる？」</p>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )
                    else:
                        for msg in st.session_state.chat_history:
                            if msg["role"] == "user":
                                st.markdown(
                                    f'<div class="chat-user">{msg["content"]}</div>',
                                    unsafe_allow_html=True,
                                )
                            else:
                                st.markdown(msg["content"])

                # Chat input
                user_input = st.chat_input(
                    "テキストについて質問...",
                    key="chat_input",
                )
                if user_input:
                    st.session_state.chat_history.append(
                        {"role": "user", "content": user_input}
                    )
                    with st.spinner("🤔 考え中..."):
                        try:
                            context = truncate_for_ai(section_text, max_chars=10000)
                            response = client.chat(
                                user_input,
                                context,
                                st.session_state.chat_history[:-1],
                            )
                            st.session_state.chat_history.append(
                                {"role": "assistant", "content": response}
                            )
                        except Exception as e:
                            st.session_state.chat_history.append(
                                {
                                    "role": "assistant",
                                    "content": f"⚠️ エラーが発生しました: {e}",
                                }
                            )
                    st.rerun()

    # Footer
    st.markdown("---")
    st.caption(
        f"📚 {st.session_state.file_name} | "
        f"セクション {idx + 1}/{len(sections)} | "
        f"文字数: {len(section_text):,}"
    )
