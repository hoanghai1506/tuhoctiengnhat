import streamlit as st
import sqlite3
import random
import time
from gtts import gTTS
import pykakasi
from deep_translator import GoogleTranslator
from io import BytesIO
import base64
import json
import uuid
import streamlit.components.v1 as components

# Khởi tạo bộ chuyển đổi
kks = pykakasi.kakasi()

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Nihongo Pink Web", page_icon="🌸", layout="centered")
st.markdown("""
    <style>
    .stApp { background-color: #FFF0F5; }
    h1, h2, h3 { color: #FF69B4; font-family: 'Arial', sans-serif; text-align: center;}
    .word-card { background-color: white; padding: 30px; border-radius: 20px; box-shadow: 0px 4px 15px rgba(0,0,0,0.1); text-align: center; margin-bottom: 20px;}
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1>✿ NIHONGO PINK MASTER WEB ✿</h1>", unsafe_allow_html=True)

def init_db():
    conn = sqlite3.connect('nihongo_web.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS vocab 
                    (id INTEGER PRIMARY KEY, kanji TEXT, hiragana TEXT, meaning TEXT)''')
    conn.commit(); conn.close()
init_db()

# --- HÀM PHÁT ÂM CHUẨN CHO IPHONE (Đã sửa lỗi TypeError) ---
def render_audio(text, autoplay=False):
    tts = gTTS(text=text, lang='ja')
    fp = BytesIO()
    tts.write_to_fp(fp)
    b64 = base64.b64encode(fp.getvalue()).decode()
    uid = str(uuid.uuid4()).replace("-", "")
    
    # Tạo nút HTML gốc để Safari ghi nhận cú chạm
    html = f"""
    <div style="text-align: center; margin-top: 10px;">
        <audio id="audio_{uid}" src="data:audio/mp3;base64,{b64}"></audio>
        <button onclick="document.getElementById('audio_{uid}').play()" 
                style="background-color: #FF69B4; color: white; border: none; padding: 12px 30px; border-radius: 50px; font-size: 18px; font-weight: bold; cursor: pointer; box-shadow: 0 4px 6px rgba(0,0,0,0.1); width: 100%;">
            🔊 BẤM ĐỂ NGHE
        </button>
        <script>
            if("{str(autoplay).lower()}" === "true") {{
                document.getElementById('audio_{uid}').play().catch(e => console.log('Chờ người dùng bấm (iOS)'));
            }}
        </script>
    </div>
    """
    components.html(html, height=75)

# --- BỘ NHỚ TRẠNG THÁI ---
if 'selected_ids' not in st.session_state: st.session_state.selected_ids = []
if 'flash_word' not in st.session_state: st.session_state.flash_word = None
if 'quiz_word' not in st.session_state: st.session_state.quiz_word = None
if 'quiz_options' not in st.session_state: st.session_state.quiz_options = []
if 'edit_id' not in st.session_state: st.session_state.edit_id = None

t_add, t_manage, t_shadow, t_flash, t_quiz = st.tabs(["📝 Thêm", "📚 Quản Lý", "🗣 Luyện Nói", "🎴 Flashcard", "🎯 Trắc Nghiệm"])

# ==========================================
# TAB 1: THÊM TỪ
# ==========================================
with t_add:
    st.markdown("<h3>TRA CỨU VÀ THÊM TỪ</h3>", unsafe_allow_html=True)
    kj_input = st.text_input("Nhập Kanji (vd: 先生):", key="in_kj")
    if st.button("Tra cứu tự động ✧", use_container_width=True):
        if kj_input:
            st.session_state.temp_hira = "".join([i['hira'] for i in kks.convert(kj_input)])
            try: st.session_state.temp_mean = GoogleTranslator(source='ja', target='vi').translate(kj_input)
            except: st.session_state.temp_mean = "Lỗi mạng"
            st.rerun()

    h_input = st.text_input("Hiragana:", value=st.session_state.get('temp_hira', ''))
    m_input = st.text_input("Nghĩa tiếng Việt:", value=st.session_state.get('temp_mean', ''))
    
    if st.button("Lưu Vào Kho", use_container_width=True):
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
    st.markdown("<h3>KHO TỪ VỰNG</h3>", unsafe_allow_html=True)
    conn = sqlite3.connect('nihongo_web.db')
    rows = conn.execute("SELECT * FROM vocab").fetchall()
    conn.close()

    if not rows: st.info("Hãy thêm từ mới ở tab bên cạnh nhé!")
    
    for r in rows:
        c1, c2, c3, c4 = st.columns([0.5, 4, 1.2, 1.2])
        is_checked = c1.checkbox("", key=f"chk_{r[0]}", value=(r[0] in st.session_state.selected_ids))
        if is_checked and r[0] not in st.session_state.selected_ids: st.session_state.selected_ids.append(r[0])
        elif not is_checked and r[0] in st.session_state.selected_ids: st.session_state.selected_ids.remove(r[0])
            
        c2.write(f"**{r[1]}** [{r[2]}] - {r[3]}")
        
        if c3.button("Sửa", key=f"edit_{r[0]}"): st.session_state.edit_id = r[0]
        if c4.button("Xóa", key=f"del_{r[0]}"):
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
# TAB 3: LUYỆN NÓI (SỬ DỤNG WEB AUDIO API ĐỂ VƯỢT RÀO APPLE)
# ==========================================
with t_shadow:
    st.markdown("<h3>LUYỆN NÓI (SHADOWING)</h3>", unsafe_allow_html=True)
    if not st.session_state.selected_ids:
        st.warning("Hãy sang tab Quản Lý và chọn ít nhất 1 từ nhé!")
    else:
        conn = sqlite3.connect('nihongo_web.db')
        ids_str = ','.join(map(str, st.session_state.selected_ids))
        shadow_words = conn.execute(f"SELECT * FROM vocab WHERE id IN ({ids_str})").fetchall()
        conn.close()

        playlist = []
        for w in shadow_words:
            tts = gTTS(text=w[1], lang='ja')
            fp = BytesIO()
            tts.write_to_fp(fp)
            b64 = base64.b64encode(fp.getvalue()).decode()
            playlist.append({"kanji": w[1], "hira": w[2], "mean": w[3], "audio": b64})
        
        js_playlist = json.dumps(playlist)
        
        html_player = f"""
        <div style="text-align: center; background: white; padding: 30px; border-radius: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); font-family: sans-serif;">
            <h1 id="p_kanji" style="font-size: 60px; color: #FF69B4; margin-bottom: 10px;">Sẵn sàng!</h1>
            <h3 id="p_hira" style="color: #34495e; margin: 5px 0;"></h3>
            <p id="p_mean" style="color: gray; font-style: italic; font-size: 18px; margin-bottom: 20px;"></p>

            <div style="display: flex; justify-content: center; gap: 15px; margin-top: 20px;">
                <button id="btn_play" onclick="startPlay()" style="background: #27ae60; color: white; border: none; padding: 15px; border-radius: 10px; font-size: 18px; font-weight: bold; width: 100%;">▶ BẮT ĐẦU</button>
                <button id="btn_stop" onclick="stopPlay()" style="background: #e74c3c; color: white; border: none; padding: 15px; border-radius: 10px; font-size: 18px; font-weight: bold; width: 100%; display: none;">■ DỪNG LẠI</button>
            </div>
        </div>
        
        <script>
            const playlist = {js_playlist};
            let idx = 0;
            let isPlaying = false;
            let audioCtx = null;
            let currentSource = null;
            let timeoutId = null;

            async function startPlay() {{
                if(isPlaying) return;
                isPlaying = true;
                document.getElementById('btn_play').style.display = 'none';
                document.getElementById('btn_stop').style.display = 'inline-block';
                
                // Mở khóa AudioContext bằng 1 cú click duy nhất
                if(!audioCtx) {{
                    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                }}
                if(audioCtx.state === 'suspended') audioCtx.resume();
                
                playLoop();
            }}

            function stopPlay() {{
                isPlaying = false;
                if(currentSource) currentSource.stop();
                clearTimeout(timeoutId);
                document.getElementById('btn_play').style.display = 'inline-block';
                document.getElementById('btn_stop').style.display = 'none';
                document.getElementById('btn_play').innerText = "▶ PHÁT TIẾP";
            }}

            async function playLoop() {{
                if(!isPlaying) return;
                if(idx >= playlist.length) {{
                    document.getElementById('p_kanji').innerText = "Hoàn thành! 🌸";
                    document.getElementById('p_hira').innerText = "";
                    document.getElementById('p_mean').innerText = "";
                    stopPlay();
                    document.getElementById('btn_play').innerText = "▶ LẶP LẠI";
                    idx = 0;
                    return;
                }}

                let word = playlist[idx];
                document.getElementById('p_kanji').innerText = word.kanji;
                document.getElementById('p_hira').innerText = word.hira;
                document.getElementById('p_mean').innerText = word.mean;

                try {{
                    let binaryString = window.atob(word.audio);
                    let len = binaryString.length;
                    let bytes = new Uint8Array(len);
                    for (let i = 0; i < len; i++) bytes[i] = binaryString.charCodeAt(i);
                    
                    let audioBuffer = await audioCtx.decodeAudioData(bytes.buffer);
                    currentSource = audioCtx.createBufferSource();
                    currentSource.buffer = audioBuffer;
                    currentSource.connect(audioCtx.destination);
                    currentSource.start();

                    currentSource.onended = () => {{
                        if(!isPlaying) return;
                        timeoutId = setTimeout(() => {{ idx++; playLoop(); }}, 3500);
                    }};
                }} catch(e) {{ idx++; playLoop(); }}
            }}
        </script>
        """
        components.html(html_player, height=350)

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
            st.session_state.flash_word = random.choice(conn.execute(f"SELECT * FROM vocab WHERE id IN ({ids_str})").fetchall())
            conn.close()
            st.session_state.show_flash_ans = False

        if st.session_state.flash_word:
            w = st.session_state.flash_word
            st.markdown(f"<div class='word-card'><h1 style='font-size: 80px;'>{w[1]}</h1></div>", unsafe_allow_html=True)
            render_audio(w[1], autoplay=True)
            
            if st.button("👁 Xem nghĩa", use_container_width=True):
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
            
            # Hàm gọi nút phát âm với tên biến đã được đồng bộ
            render_audio(q_word[1], autoplay=True)
            
            st.write("Chọn đáp án đúng:")
            opts = st.session_state.quiz_options
            
            for i in range(4):
                if st.button(opts[i], key=f"ans_{i}", use_container_width=True):
                    if opts[i] == q_word[3]:
                        st.balloons()
                        st.success("Chính xác! 🌸")
                        time.sleep(1.5)
                        generate_quiz()
                        st.rerun()
                    else:
                        st.error(f"Sai rồi! Đáp án là: {q_word[3]}")
