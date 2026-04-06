import streamlit as st
import sqlite3
import random
import time
from gtts import gTTS
import pykakasi
from deep_translator import GoogleTranslator
from io import BytesIO
import base64 # Thư viện mới để xử lý âm thanh cho Web

# Khởi tạo bộ chuyển đổi tiếng Nhật
kks = pykakasi.kakasi()

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Nihongo Pink Web", page_icon="🌸", layout="centered")
st.markdown("""
    <style>
    .stApp { background-color: #FFF0F5; }
    h1, h2, h3 { color: #FF69B4; font-family: 'Arial', sans-serif; text-align: center;}
    .stButton>button { background-color: #FF69B4; color: white; border-radius: 10px; border: none; font-weight: bold; }
    .stButton>button:hover { background-color: #FF1493; }
    .word-card { background-color: white; padding: 30px; border-radius: 20px; box-shadow: 0px 4px 15px rgba(0,0,0,0.1); text-align: center; margin-bottom: 20px;}
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1>✿ NIHONGO PINK MASTER WEB ✿</h1>", unsafe_allow_html=True)

# --- DATABASE ---
def init_db():
    conn = sqlite3.connect('nihongo_web.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS vocab 
                    (id INTEGER PRIMARY KEY, kanji TEXT, hiragana TEXT, meaning TEXT)''')
    conn.commit(); conn.close()
init_db()

# --- HÀM PHÁT ÂM CHỐNG LỖI CHO IPHONE ---
def render_audio(text, autoplay=False):
    tts = gTTS(text=text, lang='ja')
    fp = BytesIO()
    tts.write_to_fp(fp)
    b64 = base64.b64encode(fp.getvalue()).decode()
    auto_str = "autoplay" if autoplay else ""
    # Tạo trình phát HTML5 tùy chỉnh
    html = f"""
        <audio controls {auto_str} style="width: 100%; height: 40px;">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
    """
    st.markdown(html, unsafe_allow_html=True)

# --- KHỞI TẠO BỘ NHỚ TRẠNG THÁI ---
if 'selected_ids' not in st.session_state: st.session_state.selected_ids = []
if 'shadow_idx' not in st.session_state: st.session_state.shadow_idx = 0
if 'is_shadowing' not in st.session_state: st.session_state.is_shadowing = False
if 'flash_word' not in st.session_state: st.session_state.flash_word = None
if 'quiz_word' not in st.session_state: st.session_state.quiz_word = None
if 'quiz_options' not in st.session_state: st.session_state.quiz_options = []
if 'edit_id' not in st.session_state: st.session_state.edit_id = None

# --- TẠO TABS ---
t_add, t_manage, t_shadow, t_flash, t_quiz = st.tabs(["📝 Thêm", "📚 Quản Lý", "🗣 Luyện Nói", "🎴 Flashcard", "🎯 Trắc Nghiệm"])

# ==========================================
# TAB 1: THÊM TỪ
# ==========================================
with t_add:
    st.markdown("<h3>TRA CỨU VÀ THÊM TỪ</h3>", unsafe_allow_html=True)
    kj_input = st.text_input("Nhập Kanji (vd: 先生):", key="in_kj")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Tra cứu tự động ✧"):
            if kj_input:
                st.session_state.temp_hira = "".join([i['hira'] for i in kks.convert(kj_input)])
                try: st.session_state.temp_mean = GoogleTranslator(source='ja', target='vi').translate(kj_input)
                except: st.session_state.temp_mean = "Lỗi mạng"
                st.rerun()

    h_input = st.text_input("Hiragana:", value=st.session_state.get('temp_hira', ''))
    m_input = st.text_input("Nghĩa tiếng Việt:", value=st.session_state.get('temp_mean', ''))
    
    if st.button("Lưu Vào Kho Dữ Liệu", use_container_width=True):
        if kj_input and h_input and m_input:
            conn = sqlite3.connect('nihongo_web.db')
            conn.execute("INSERT INTO vocab (kanji, hiragana, meaning) VALUES (?, ?, ?)", (kj_input, h_input, m_input))
            conn.commit(); conn.close()
            st.session_state.temp_hira = ""; st.session_state.temp_mean = ""
            st.success("Đã lưu thành công!")
            time.sleep(1); st.rerun()

# ==========================================
# TAB 2: QUẢN LÝ
# ==========================================
with t_manage:
    st.markdown("<h3>QUẢN LÝ TỪ VỰNG</h3>", unsafe_allow_html=True)
    conn = sqlite3.connect('nihongo_web.db')
    rows = conn.execute("SELECT * FROM vocab").fetchall()
    conn.close()

    if not rows: st.info("Chưa có từ vựng nào. Hãy thêm ở tab bên cạnh nhé!")
    
    for r in rows:
        c1, c2, c3, c4, c5 = st.columns([0.5, 4, 1, 1, 1])
        
        is_checked = c1.checkbox("", key=f"chk_{r[0]}", value=(r[0] in st.session_state.selected_ids))
        if is_checked and r[0] not in st.session_state.selected_ids: st.session_state.selected_ids.append(r[0])
        elif not is_checked and r[0] in st.session_state.selected_ids: st.session_state.selected_ids.remove(r[0])
            
        c2.write(f"**{r[1]}** [{r[2]}] - {r[3]}")
        
        if c3.button("🔊", key=f"play_{r[0]}"): render_audio(r[1], autoplay=True)
        if c4.button("Sửa", key=f"edit_{r[0]}"): st.session_state.edit_id = r[0]
        if c5.button("Xóa", key=f"del_{r[0]}"):
            conn = sqlite3.connect('nihongo_web.db')
            conn.execute("DELETE FROM vocab WHERE id=?", (r[0],))
            conn.commit(); conn.close(); st.rerun()

        if st.session_state.edit_id == r[0]:
            new_mean = st.text_input("Nhập nghĩa mới:", value=r[3], key=f"new_m_{r[0]}")
            if st.button("Lưu thay đổi", key=f"save_{r[0]}"):
                conn = sqlite3.connect('nihongo_web.db')
                conn.execute("UPDATE vocab SET meaning=? WHERE id=?", (new_mean, r[0]))
                conn.commit(); conn.close()
                st.session_state.edit_id = None; st.rerun()
        st.divider()

# ==========================================
# TAB 3: LUYỆN NÓI
# ==========================================
with t_shadow:
    st.markdown("<h3>LUYỆN NÓI (SHADOWING)</h3>", unsafe_allow_html=True)
    if not st.session_state.selected_ids:
        st.warning("Hải hãy sang tab Quản Lý và tích chọn ít nhất 1 từ nhé!")
    else:
        conn = sqlite3.connect('nihongo_web.db')
        ids_str = ','.join(map(str, st.session_state.selected_ids))
        shadow_words = conn.execute(f"SELECT * FROM vocab WHERE id IN ({ids_str})").fetchall()
        conn.close()

        if st.button("▶ Bắt đầu / Dừng phát", use_container_width=True):
            st.session_state.is_shadowing = not st.session_state.is_shadowing
            st.session_state.shadow_idx = 0
            st.rerun()

        if st.session_state.is_shadowing:
            idx = st.session_state.shadow_idx
            if idx < len(shadow_words):
                word = shadow_words[idx]
                st.markdown(f"""
                    <div class="word-card">
                        <h1 style="font-size: 60px;">{word[1]}</h1>
                        <h3>{word[2]}</h3>
                        <p style="color: gray;">{word[3]}</p>
                    </div>
                """, unsafe_allow_html=True)
                
                render_audio(word[1], autoplay=True)
                time.sleep(4) 
                st.session_state.shadow_idx += 1
                st.rerun()
            else:
                st.session_state.is_shadowing = False
                st.success("Đã hoàn thành vòng luyện nói!")

# ==========================================
# TAB 4: FLASHCARD
# ==========================================
with t_flash:
    st.markdown("<h3>FLASHCARD LẬT THẺ</h3>", unsafe_allow_html=True)
    if not st.session_state.selected_ids:
        st.warning("Hãy chọn từ ở tab Quản lý trước!")
    else:
        if st.button("Rút thẻ mới ➔", use_container_width=True):
            conn = sqlite3.connect('nihongo_web.db')
            ids_str = ','.join(map(str, st.session_state.selected_ids))
            words = conn.execute(f"SELECT * FROM vocab WHERE id IN ({ids_str})").fetchall()
            conn.close()
            st.session_state.flash_word = random.choice(words)
            st.session_state.show_flash_ans = False

        if st.session_state.flash_word:
            w = st.session_state.flash_word
            st.markdown(f"<div class='word-card'><h1 style='font-size: 80px;'>{w[1]}</h1></div>", unsafe_allow_html=True)
            
            c1, c2 = st.columns(2)
            if c1.button("🔊 Nghe", use_container_width=True):
                render_audio(w[1], autoplay=True)
            if c2.button("👁 Xem nghĩa", use_container_width=True):
                st.session_state.show_flash_ans = True
                
            if st.session_state.get('show_flash_ans', False):
                st.markdown(f"<div class='word-card'><h3>{w[2]}</h3><p>{w[3]}</p></div>", unsafe_allow_html=True)

# ==========================================
# TAB 5: TRẮC NGHIỆM
# ==========================================
with t_quiz:
    st.markdown("<h3>TRẮC NGHIỆM PHẢN XẠ</h3>", unsafe_allow_html=True)
    if not st.session_state.selected_ids:
        st.warning("Hãy chọn từ ở tab Quản lý để làm test nhé!")
    else:
        def generate_quiz():
            conn = sqlite3.connect('nihongo_web.db')
            ids_str = ','.join(map(str, st.session_state.selected_ids))
            sel_words = conn.execute(f"SELECT * FROM vocab WHERE id IN ({ids_str})").fetchall()
            all_means = [r[0] for r in conn.execute("SELECT meaning FROM vocab").fetchall()]
            conn.close()
            
            st.session_state.quiz_word = random.choice(sel_words)
            correct = st.session_state.quiz_word[3]
            distractors = random.sample([m for m in all_means if m != correct], min(3, len(all_means)-1)) if len(all_means)>1 else ["-", "-", "-"]
            opts = distractors + [correct]
            random.shuffle(opts)
            st.session_state.quiz_options = opts

        if st.button("Câu hỏi mới ➔", use_container_width=True) or st.session_state.quiz_word is None:
            generate_quiz()

        if st.session_state.quiz_word:
            q_word = st.session_state.quiz_word
            st.markdown(f"<div class='word-card'><h1 style='font-size: 60px;'>{q_word[1]}</h1></div>", unsafe_allow_html=True)
            
            # Khung phát âm (Trên iPhone có thể ấn Play thủ công nếu bị chặn autoplay)
            render_audio(q_word[1], autoplay=True)
            
            st.write("Chọn đáp án đúng:")
            opts = st.session_state.quiz_options
            
            col1, col2 = st.columns(2)
            for i in range(4):
                col = col1 if i % 2 == 0 else col2
                if col.button(opts[i], key=f"ans_{i}", use_container_width=True):
                    if opts[i] == q_word[3]:
                        st.balloons()
                        st.success("Chính xác! 🌸")
                        time.sleep(1.5)
                        generate_quiz()
                        st.rerun()
                    else:
                        st.error(f"Sai rồi! Đáp án là: {q_word[3]}")
