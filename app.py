import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import database as db
import chatbot as chat
import auth
import admin as adm
import ml_agent
import security
import sqlite3

def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# 1. INITIAL SETUP
security.get_encryption_key()
db.create_db()
st.set_page_config(page_title="Clarity Hub AI", layout="wide", page_icon="🌿")
local_css("style.css")

# --- Replace with your actual Gemini API Key ---
GEMINI_API_KEY = "AIzaSyDm7ZHDRN260NoVQ1WcOO5uU1muRcOwXIY"

# NAVBAR + LOGIN CARD helpers
def render_navbar():
    st.markdown("""
    <style>
    .top-nav {display:flex; align-items:center; justify-content:center; gap:18px; padding:12px 24px; background:linear-gradient(125deg,#0f172a,#111827); border-bottom:1px solid #334155;}
    .top-nav a {color:#e2e8f0; text-decoration:none; font-weight:700; padding:8px 16px; border-radius:10px; transition:0.2s;}
    .top-nav a:hover {background:rgba(226,232,240,0.12);}
    .top-nav .brand {font-size:1.7rem; font-weight: 900; color:#f8fafc;}
    .login-container {min-height:calc(100vh - 96px); display:flex; align-items:center; justify-content:center;}
    .login-card {width:100%; max-width:440px; background:#0f172a; border:1px solid #334155; border-radius:20px; padding:28px; box-shadow:0 16px 28px rgba(15,23,42,0.7);}
    .top-right-actions {position:absolute; right:20px; top:14px;}
    .refresh-btn {background: #0284c7; color:#fff; border:none; border-radius:8px; padding:8px 14px; font-weight:700; cursor:pointer; box-shadow:0 3px 8px rgba(2,132,199,0.32);}
    .refresh-btn:hover {background:#0369a1;}
    </style>
    <div class="top-nav">
      <div class="brand">Clarity Hub</div>
      <div class="top-right-actions">
        <button class="refresh-btn" onclick="location.reload()">Refresh</button>
      </div>
      <a href="#">CodeGenie</a>
      <a href="#">My Profile</a>
      <a href="#">Code Explainer</a>
      <a href="#">AI Assistant</a>
    </div>
    """, unsafe_allow_html=True)


def render_user_icon():
    if st.session_state.user_profile_image_bytes:
        st.sidebar.image(st.session_state.user_profile_image_bytes, width=60, caption="")
    else:
        first_letter = st.session_state.username[0].upper() if st.session_state.username else "U"
        st.sidebar.markdown(f"""
        <div style='width:60px; height:60px; border-radius:50%; background:linear-gradient(135deg,#0ea5e9,#3b82f6); color:white; display:flex; align-items:center; justify-content:center; font-size:24px; font-weight:bold; margin-bottom:12px;'>
            {first_letter}
        </div>
        """, unsafe_allow_html=True)

    if st.sidebar.button("Change Icon", key="change_icon"):
        st.session_state.show_image_uploader = not st.session_state.show_image_uploader

    if st.session_state.show_image_uploader:
        uploaded_file = st.sidebar.file_uploader("Upload Profile Image", type=["png", "jpg", "jpeg"], key="profile_upload")
        if uploaded_file is not None:
            st.session_state.user_profile_image_bytes = uploaded_file.getvalue()
            st.sidebar.success("Profile image updated!")
            st.session_state.show_image_uploader = False
            if hasattr(st, 'rerun'):
                st.rerun()
            elif hasattr(st, 'experimental_rerun'):
                st.experimental_rerun()
            else:
                st.info("Please refresh to see changes.")

# 2. SESSION STATE MANAGEMENT
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'gemini_session' not in st.session_state:
    # Initialize the model once
    model = chat.initialize_gemini(GEMINI_API_KEY)
    st.session_state.gemini_session = model.start_chat(history=[])
if 'user_profile_image_bytes' not in st.session_state:
    st.session_state.user_profile_image_bytes = None
if 'show_image_uploader' not in st.session_state:
    st.session_state.show_image_uploader = False

# 3. AUTHENTICATION
if not st.session_state.logged_in:
    st.title("🌿Welcome to Clarity Hub")
    st.subheader("Please login or register to continue")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        auth_mode = st.selectbox("Choose action", ["Login", "Register"])

        if auth_mode == "Register":
            auth.signup_interface()
        else:
            login_as = st.radio("Login as", ["User", "Admin"], horizontal=True, key="login_as")
            u = st.text_input("Username", key="center_login_user")
            p = st.text_input("Password", type='password', key="center_login_pass")
            if st.button("Login"):
                if login_as == "Admin":
                    if db.verify_admin(u, p):
                        st.session_state.logged_in = True
                        st.session_state.username = u
                        st.session_state.role = 'admin'
                        st.session_state.nav_choice = 'Admin Panel'
                        db.save_activity_log(u, 'Login', 'Admin logged in')
                        st.experimental_rerun()
                    else:
                        st.error("Invalid admin credentials.")
                else:
                    role = db.verify_user(u, p)
                    if role:
                        st.session_state.logged_in = True
                        st.session_state.username = u
                        st.session_state.role = 'user'
                        st.session_state.nav_choice = 'AI Chatbot'
                        db.save_activity_log(u, 'Login', 'User logged in')
                        st.experimental_rerun()
                    else:
                        st.error("Invalid credentials or email not verified.")

# 4. MAIN APPLICATION (LOGGED IN)
if st.session_state.logged_in:
    render_user_icon()
    st.sidebar.title(f"Welcome, {st.session_state.username}")
    st.sidebar.markdown("### Go to:")
    st.sidebar.markdown("<div style='margin-top:10px; padding:12px; background:#111827; border-radius:12px;'>**Privacy & Safety**<br>All personal entries and mood logs are stored locally and kept private.</div>", unsafe_allow_html=True)

    if 'nav_choice' not in st.session_state:
        st.session_state.nav_choice = 'Admin Panel' if st.session_state.role == 'admin' else 'AI Chatbot'

    if st.session_state.role == 'admin':
        if st.sidebar.button('👑 Admin Panel'):
            st.session_state.nav_choice = 'Admin Panel'
    else:
        if st.sidebar.button('🤖 AI Chatbot'):
            st.session_state.nav_choice = 'AI Chatbot'
        if st.sidebar.button('📊 Mood Tracker'):
            st.session_state.nav_choice = 'Mood Tracker'
        if st.sidebar.button('📈 Progress Report'):
            st.session_state.nav_choice = 'Progress Report'
        if st.sidebar.button('📓 Digital Journal'):
            st.session_state.nav_choice = 'Digital Journal'
        if st.sidebar.button('📝 Activity Logs'):
            st.session_state.nav_choice = 'Activity Logs'
        if st.sidebar.button('🧘 Meditation Space'):
            st.session_state.nav_choice = 'Meditation Space'

    choice = st.session_state.nav_choice

    # LOGOUT BUTTON
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.chat_history = []
        st.rerun()

    # --- SECTION 1: AI CHATBOT (ChatGPT Style) ---
    if choice == "AI Chatbot":
        st.title("🤖 Clarity AI Assistant")
        st.caption("Ask me anything! I have memory of our current conversation.")

        # Load chat history from database
        if not st.session_state.chat_history:
            chat_df = db.get_user_chat_history(st.session_state.username)
            for _, row in chat_df[::-1].iterrows():  # Reverse to chronological order
                st.session_state.chat_history.append({"role": "user", "content": row['user_message']})
                st.session_state.chat_history.append({"role": "assistant", "content": row['ai_response']})

        # Display persistent chat history
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Chat Input logic
        if prompt := st.chat_input("Ask me anything about your problem, I am here to solve your problem"):
            # Add user message to state and UI
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Get streaming-style response from Gemini with ML enhancement
            with st.chat_message("assistant"):
                try:
                    response_text = chat.get_chat_response(st.session_state.gemini_session, prompt, st.session_state.username)
                    st.markdown(response_text)
                    st.session_state.chat_history.append({"role": "assistant", "content": response_text})
                    db.save_activity_log(st.session_state.username, 'Chat', f'Asked: {prompt}')
                except Exception as e:
                    st.error(f"API Error: {e}")

        # Proactive question based on mood
        if len(st.session_state.chat_history) % 4 == 0 and len(st.session_state.chat_history) > 0:  # Every 4 messages
            proactive_question = ml_agent.ml_agent.generate_personalized_question(st.session_state.username)
            with st.chat_message("assistant"):
                st.markdown(f"💭 **Proactive Check-in:** {proactive_question}")
            st.session_state.chat_history.append({"role": "assistant", "content": f"💭 **Proactive Check-in:** {proactive_question}"})

    # --- SECTION 2: MOOD TRACKER WITH GRAPHS ---
    elif choice == "Mood Tracker":
        st.title("📊 Personal Wellness Trends")
        insights = ml_agent.ml_agent.analyze_user_history(st.session_state.username)
        risk = ml_agent.ml_agent.detect_risk(st.session_state.username)

        st.markdown(f"**Average Mood:** {insights['avg_mood']:.1f} · **Mood Trend:** {insights['mood_trend'].title()} · **Risk:** {risk['level']}")
        if risk['risk']:
            st.warning(f"Attention: {risk['reason']}")

        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("How are you feeling?")
            m_label = st.select_slider("Select Mood", ["Very Sad", "Anxious", "Neutral", "Happy", "Energetic"])
            scores = {"Very Sad": 1, "Anxious": 2, "Neutral": 3, "Happy": 4, "Energetic": 5}
            
            if st.button("Log Today's Mood"):
                conn = sqlite3.connect('clarity_hub.db')
                c = conn.cursor()
                c.execute("INSERT INTO mood_logs VALUES (?,?,?,?)", 
                          (st.session_state.username, datetime.now().strftime("%Y-%m-%d"), m_label, scores[m_label]))
                conn.commit()
                conn.close()
                db.save_activity_log(st.session_state.username, 'Mood Log', f'Logged mood {m_label}')
                st.success("Mood recorded!")

        with col2:
            conn = sqlite3.connect('clarity_hub.db')
            df = pd.read_sql_query(f"SELECT date, score FROM mood_logs WHERE username='{st.session_state.username}'", conn)
            conn.close()
            
            if not df.empty:
                st.subheader("Your Progress Graph")
                fig = px.line(df, x='date', y='score', markers=True, 
                             labels={"score": "Mood Level (1-5)", "date": "Day"},
                             color_discrete_sequence=['#2E7D32'])
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No data yet. Start logging your mood to see trends!")

    # --- SECTION 3: DIGITAL JOURNAL ---
    elif choice == "Progress Report":
        st.title("📈 Personal Progress Report")
        st.write("Your progress is based on mood logs, journal consistency, and activity engagement.")

        conn = sqlite3.connect('clarity_hub.db')
        mood_df = pd.read_sql_query("SELECT date, score FROM mood_logs WHERE username=?", conn, params=(st.session_state.username,))
        journal_df = pd.read_sql_query("SELECT date_time FROM journals WHERE username=?", conn, params=(st.session_state.username,))
        chat_df = pd.read_sql_query("SELECT username FROM chat_history WHERE username=?", conn, params=(st.session_state.username,))
        activity_df = pd.read_sql_query("SELECT activity_type FROM activity_logs WHERE username=?", conn, params=(st.session_state.username,))
        conn.close()

        avg_mood = float(mood_df['score'].mean()) if not mood_df.empty else 0.0
        mood_progress = int(min(max((avg_mood - 1) / 4, 0), 1) * 100)
        journal_progress = int(min(journal_df.shape[0] / 10, 1) * 100)
        chat_progress = int(min(chat_df.shape[0] / 8, 1) * 100)
        activity_progress = int(min(activity_df.shape[0] / 12, 1) * 100)
        overall_score = int((mood_progress * 0.45) + (journal_progress * 0.2) + (chat_progress * 0.2) + (activity_progress * 0.15))
        risk = ml_agent.ml_agent.detect_risk(st.session_state.username)
        status = "On a positive path — keep building healthy routines." if avg_mood >= 3.5 and risk['level'] != 'High' else "You’re making progress, but some extra support may help."

        top_cols = st.columns(4)
        top_cols[0].metric("Recovery Score", f"{overall_score}%")
        top_cols[1].metric("Average Mood", f"{avg_mood:.1f}/5")
        top_cols[2].metric("Journal Consistency", f"{journal_progress}%")
        top_cols[3].metric("Activity Engagement", f"{activity_progress}%")

        st.info(status)

        def make_circle_chart(title, score, color):
            values = [score, 100 - score]
            labels = [title, 'Remaining']
            fig = px.pie(
                names=labels,
                values=values,
                hole=0.7,
                color=labels,
                color_discrete_map={title: color, 'Remaining': '#E5E7EB'},
            )
            fig.update_traces(textinfo='none', hoverinfo='none')
            fig.update_layout(
                showlegend=False,
                margin=dict(t=10, b=10, l=10, r=10),
                annotations=[dict(text=f"{score}%", x=0.5, y=0.5, font_size=20, showarrow=False)],
            )
            return fig

        chart_cols = st.columns(3)
        chart_cols[0].subheader("Mood Progress")
        chart_cols[0].plotly_chart(make_circle_chart('Mood', mood_progress, '#22c55e'), use_container_width=True)
        chart_cols[1].subheader("Journal Growth")
        chart_cols[1].plotly_chart(make_circle_chart('Journal', journal_progress, '#38bdf8'), use_container_width=True)
        chart_cols[2].subheader("Routine Engagement")
        chart_cols[2].plotly_chart(make_circle_chart('Engagement', activity_progress, '#f97316'), use_container_width=True)

        st.markdown("---")
        st.subheader("History Summary")
        summary_cols = st.columns(2)
        summary_cols[0].write(f"**Mood Entries:** {len(mood_df)}")
        summary_cols[0].write(f"**Chat Sessions:** {len(chat_df)}")
        summary_cols[1].write(f"**Journal Entries:** {len(journal_df)}")
        summary_cols[1].write(f"**Activity Events:** {len(activity_df)}")

    elif choice == "Digital Journal":
        st.title("📓 My Digital Journal")
        st.write("Expressing your thoughts helps reduce stress.")
        
        entry_text = st.text_area("Write about your day...", height=200)
        if st.button("Save Journal Entry"):
            if entry_text:
                db.save_journal_entry(st.session_state.username, datetime.now().strftime("%Y-%m-%d %H:%M"), entry_text)
                db.save_activity_log(st.session_state.username, 'Journal Entry', 'Saved a journal entry')
                st.success("Your thoughts have been safely stored.")
            else:
                st.warning("Please write something before saving.")

    elif choice == "Activity Logs":
        st.title("📝 My Activity Log")
        activity_df = db.get_user_activity_logs(st.session_state.username)
        if not activity_df.empty:
            st.dataframe(activity_df)
        else:
            st.info("No activity logs available yet.")

    # --- SECTION 4: MEDITATION SPACE ---
    elif choice == "Meditation Space":
        st.title("🧘 Zen Corner")
        st.write("Relax with these guided audio tracks.")
        
        m_col1, m_col2 = st.columns(2)
        with m_col1:
            st.info("Focus & Concentration")
            st.audio("https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3")
            st.caption("Ambient Rain Background")
            
        with m_col2:
            st.success("Deep Relaxation")
            st.audio("https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3")
            st.caption("Soft Instrumental Melodies")

    # --- SECTION 5: ADMIN PANEL ---
    elif choice == "Admin Panel":
        adm.admin_panel()
