"""
FRAME — Creator Studio | Streamlit Cloud Edition (streamlit_app.py)
====================================================================
Deploy directly on Streamlit Community Cloud (https://share.streamlit.io)
with zero local startup scripts.
"""
import hashlib
import math
import re
from datetime import datetime, date
import numpy as np
import pandas as pd
from PIL import Image
import streamlit as st

st.set_page_config(
    page_title="FRAME — Creator Studio",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Warm Editorial Styling matching FRAME Creator Studio
st.markdown("""
<style>
  .stApp { background-color: #f5f3ec; color: #20221e; }
  div[data-testid="stMetric"] {
    background-color: #ffffffb5;
    border: 1.5px solid #20221e;
    border-radius: 12px;
    padding: 14px 18px;
  }
  .frame-banner {
    background-color: #e8ed83;
    border: 1.5px solid #20221e;
    border-radius: 12px;
    padding: 18px 22px;
    margin-bottom: 18px;
  }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# SESSION STATE INITIALIZATION
# ---------------------------------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "ig_account" not in st.session_state:
    st.session_state.ig_account = {
        "handle": "@creator.frame",
        "full_name": "FRAME Creator Studio",
        "followers": 100
    }

if "reels" not in st.session_state:
    st.session_state.reels = [
        {
            "id": "reel-1",
            "title": "The 10-minute creative reset",
            "format": "Reel",
            "reach": 2450,
            "plays": 3120,
            "duration_sec": 24,
            "avg_watch_sec": 19.8,
            "retention_rate": 82.5,
            "hook_hold_3s": 91.2,
            "completion_rate": 68.4,
            "engagement": 9.2,
            "saves": 142,
            "followers_gained": 28,
            "drive_link": "https://drive.google.com/file/d/1A2B3C4D5E6F7G8H9I0J/view",
            "curve": [100, 95, 91, 88, 86, 84, 82, 79, 76, 73, 70, 68]
        }
    ]

if "follower_events" not in st.session_state:
    st.session_state.follower_events = [
        {"handle": "@maya.designlab", "name": "Maya Lin", "niche": "Art Director", "source": "Reel: The 10-minute creative reset", "time": "2 mins ago"},
        {"handle": "@kabir.edits", "name": "Kabir Sharma", "niche": "Video Editor", "source": "Reel: The 10-minute creative reset", "time": "14 mins ago"}
    ]

if "ideas" not in st.session_state:
    st.session_state.ideas = [
        {"title": "3-second visual hook breakdown with Drive raw cut", "date": "2026-11-20", "status": "Draft"},
        {"title": "How watch time compounds after 75% retention", "date": "2026-11-22", "status": "Scheduled"},
        {"title": "The 10-minute creative reset (Reel)", "date": "2026-11-14", "status": "Published"}
    ]

if "prediction_result" not in st.session_state:
    st.session_state.prediction_result = None


def extract_media_id(url: str):
    if not url:
        return None, None
    drive_match = re.search(r"(?:/file/d/|id=|/d/)([a-zA-Z0-9_-]+)", url)
    ig_match = re.search(r"(?:instagram\.com|instagr\.am)/(?:reel|reels|p|tv)/([a-zA-Z0-9_-]+)", url, re.I)
    return (drive_match.group(1) if drive_match else None, ig_match.group(1) if ig_match else None)


def analyze_cover_image(uploaded_file):
    if uploaded_file is None:
        return None
    img = Image.open(uploaded_file).convert("RGB")
    w, h = img.size
    small = img.resize((96, 96))
    arr = np.asarray(small, dtype=np.float32)
    lum = 0.2126 * arr[:, :, 0] + 0.7152 * arr[:, :, 1] + 0.0722 * arr[:, :, 2]
    brightness = int(round((float(lum.mean()) / 255.0) * 100))
    contrast = int(round(float(lum.std())))
    aspect = round(w / max(1, h), 2)
    return {
        "file_name": uploaded_file.name,
        "width": w,
        "height": h,
        "brightness": brightness,
        "contrast": contrast,
        "is_vertical_916": 0.50 <= aspect <= 0.65
    }


def compute_virality_prediction(url_str, topic_str, caption_str, hashtags_str, followers_count, hook_mult, cut_pace, audio_type, cover_sig):
    clean_url = (url_str or "").strip()
    drive_id, ig_id = extract_media_id(clean_url)

    # Match against existing library Reel if the same link is pasted
    matched_reel = None
    for r in st.session_state.reels:
        r_drive, r_ig = extract_media_id(r.get("drive_link", ""))
        if (drive_id and r_drive == drive_id) or (ig_id and r_ig == ig_id) or (clean_url and r.get("drive_link", "").strip() == clean_url):
            matched_reel = r
            break

    seed_str = f"{drive_id or ig_id or clean_url}|{topic_str.strip().lower()}|{caption_str.strip().lower()}|{cover_sig}|{hook_mult}|{cut_pace}|{audio_type}|{followers_count}"
    digest = int(hashlib.sha256(seed_str.encode("utf-8")).hexdigest()[:12], 16)

    words = re.findall(r"[a-z0-9]+", caption_str.lower())
    topic_words = re.findall(r"[a-z0-9]+", topic_str.lower())
    has_numbers = bool(re.search(r"\d+", caption_str + " " + topic_str))
    has_cta = bool(re.search(r"save|share|comment|send|follow|checklist|template|guide|link|dm", caption_str, re.I))
    has_hook_trigger = bool(re.search(r"stop|wait|how|why|secret|mistake|never|exact|reset|formula|truth", (caption_str[:110] + " " + topic_str), re.I))
    has_punct = bool(re.search(r"[?!—:]", caption_str[:95]))

    dur_sec = int(matched_reel["duration_sec"]) if matched_reel else (15 + (digest % 29))

    cover_bonus = 0
    cover_mult = 1.0
    if cover_sig:
        good_bright = 32 <= cover_sig["brightness"] <= 82
        good_contrast = cover_sig["contrast"] >= 38
        high_res = cover_sig["width"] >= 720
        cover_bonus = (3 if good_bright else -2) + (4 if good_contrast else -2) + (2 if high_res else 0) + (3 if cover_sig["is_vertical_916"] else 0)
        cover_mult = 1.0 + cover_bonus * 0.018

    pace_mult = 1.16 if cut_pace == "fast_2s" else (1.02 if cut_pace == "dynamic_4s" else 0.81)
    audio_mult = 1.14 if audio_type == "trending_original" else (1.05 if audio_type == "trending_music" else 0.88)
    dur_factor = 1.12 if 15 <= dur_sec <= 28 else (1.01 if dur_sec <= 38 else 0.90)

    hook_sub = min(30, max(6, round((18 if hook_mult >= 1.1 else 14 if hook_mult >= 1.0 else 8) + (5 if has_hook_trigger else 0) + (3 if has_punct else 0) + (3 if len(topic_words) >= 4 else 1))))
    pace_sub = min(25, max(6, round((19 if cut_pace == "fast_2s" else 14 if cut_pace == "dynamic_4s" else 8) * dur_factor)))
    copy_sub = min(25, max(4, (8 if len(words) >= 22 else 5 if len(words) >= 10 else 2) + (8 if has_cta else 1) + (4 if has_numbers else 0) + (3 if hashtags_str.strip() else 0)))
    audio_sub = min(20, max(4, (11 if audio_type == "trending_original" else 8 if audio_type == "trending_music" else 4) + (4 if (drive_id or ig_id) else 1) + max(0, cover_bonus)))

    score = min(98, max(18, hook_sub + pace_sub + copy_sub + audio_sub))
    hook_hold_3s = round(min(96.4, max(38.0, 52.0 + hook_sub * 1.15 + (5.8 if cut_pace == "fast_2s" else 2.1 if cut_pace == "dynamic_4s" else -6.2) + cover_bonus * 0.6)), 1)
    retention = round(min(92.0, max(28.0, hook_hold_3s * (0.74 + (pace_sub / 25.0) * 0.17))), 1)
    completion = round(min(85.0, max(16.0, retention * (0.83 if dur_sec <= 26 else 0.73))), 1)

    active_followers = max(1, int(followers_count))
    copy_mult = 0.78 + (copy_sub / 25.0) * 0.44
    explore_mult = (16.0 + (score - 85) * 0.85) if score >= 85 else ((7.5 + (score - 70) * 0.52) if score >= 70 else ((3.2 + (score - 55) * 0.26) if score >= 55 else 1.4))
    reach = max(round(active_followers * 0.6), round(active_followers * explore_mult * audio_mult * pace_mult * cover_mult * copy_mult))
    plays = round(reach * (1.27 if completion >= 65 else 1.18))
    avg_watch_sec = round((dur_sec * retention) / 100.0, 1)
    watch_hours = round((plays * avg_watch_sec) / 3600.0, 1)
    followers_gained = max(1, round(reach * (0.0115 if score >= 80 else 0.0062)))

    curve = [100, round(hook_hold_3s)] + [
        max(12, round(hook_hold_3s - math.pow(i / 10.0, 0.85) * (hook_hold_3s - completion)))
        for i in range(1, 11)
    ]

    return {
        "topic": topic_str or caption_str[:48],
        "caption": caption_str,
        "drive_url": clean_url,
        "score": score,
        "breakdown": {"3s Hook": f"{hook_sub}/30", "Pacing": f"{pace_sub}/25", "Caption/CTA": f"{copy_sub}/25", "Audio/Cover": f"{audio_sub}/20"},
        "reach": reach,
        "plays": plays,
        "duration_sec": dur_sec,
        "avg_watch_sec": avg_watch_sec,
        "watch_hours": watch_hours,
        "retention_rate": retention,
        "hook_hold_3s": hook_hold_3s,
        "completion_rate": completion,
        "followers_gained": followers_gained,
        "curve": curve,
        "hook_rewrite": f"\"Stop scrolling—here is the exact {topic_str.lower()[:36] or 'creator'} framework that generated {reach:,} reach from {active_followers:,} followers.\""
    }


# ---------------------------------------------------------------------------
# FRONT PAGE CATALOG & INSTAGRAM LOGIN GATE
# ---------------------------------------------------------------------------
if not st.session_state.authenticated:
    st.markdown("""
    <div class="frame-banner">
      <div style="font-size:11px;font-weight:700;letter-spacing:1.8px;text-transform:uppercase;">FRAME — Creator Studio · Streamlit Cloud Edition</div>
      <h1 style="margin:6px 0 4px;font-size:38px;">Every Reel signal, interconnected.</h1>
      <p style="margin:0;font-size:15px;">Log in with your Instagram handle below to unlock real-time follower webhooks, verified watch-hour math, retention diagnostics, and AI Reel virality predictions.</p>
    </div>
    """, unsafe_allow_html=True)

    col_left, col_right = st.columns([1.4, 1], gap="large")
    with col_left:
        st.subheader("Platform Capabilities")
        c1, c2 = st.columns(2)
        with c1:
            st.info("**01 · Real-Time Follower Webhooks**\n\nInstant follower attribution showing which specific Reel converted each new follower.")
            st.success("**03 · Second-by-Second Retention**\n\nPinpoints 3-second hook hold strength and exact viewer drop-off timestamps.")
        with c2:
            st.warning("**02 · Verified Watch-Hour Graph**\n\nComputes true Watch Hours via `∑(Plays × Avg Watch Sec) ÷ 3600`.")
            st.error("**04 · Drive & IG Reel Virality Predictor**\n\nScores Drive/IG links, captions, and cover photos before publishing.")

    with col_right:
        st.subheader("Instagram Connect")
        with st.form("ig_login_form"):
            ig_user = st.text_input("Instagram Username or Handle", value="creator.frame")
            ig_pass = st.text_input("Password", type="password", placeholder="Enter any 4+ characters")
            ig_followers_init = st.number_input("Current Followers", min_value=1, value=100)
            submitted = st.form_submit_button("Log in & Unlock Studio", use_container_width=True, type="primary")
            if submitted:
                clean_handle = "@" + ig_user.strip().lstrip("@")
                if len(ig_pass) < 4:
                    st.error("Please enter a password with at least 4 characters.")
                else:
                    st.session_state.ig_account = {
                        "handle": clean_handle,
                        "full_name": f"{clean_handle} Studio",
                        "followers": int(ig_followers_init)
                    }
                    st.session_state.authenticated = True
                    st.rerun()
    st.stop()

# ---------------------------------------------------------------------------
# AUTHENTICATED WORKSPACE
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## [F] FRAME")
    st.caption("Creator Intelligence & Retention Lab")
    st.divider()
    acc = st.session_state.ig_account
    st.markdown(f"**Account:** `{acc['handle']}`")
    st.markdown(f"**Live Followers:** `{acc['followers']:,}`")
    if st.button("⚡ Simulate New Follower Webhook", use_container_width=True):
        st.session_state.ig_account["followers"] += 1
        top_title = st.session_state.reels[0]["title"]
        st.session_state.reels[0]["followers_gained"] += 1
        st.session_state.follower_events.insert(0, {
            "handle": f"@creator_{len(st.session_state.follower_events) + 11}",
            "name": "New Instagram Follower",
            "niche": "Creator",
            "source": f"Reel: {top_title}",
            "time": "Just now"
        })
        st.toast(f"New follower on {acc['handle']}! Total: {st.session_state.ig_account['followers']}")
        st.rerun()
    st.divider()
    if st.button("← Return to Front Page Catalog", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

st.title("Make the next one count.")
tab_overview, tab_lab, tab_audience, tab_planner = st.tabs([
    "◫ Overview & Content Graph",
    "↗ Content Lab (Virality Predictor)",
    "◎ Audience & Follower Stream",
    "▤ Content Planner"
])

# TAB 1: OVERVIEW
with tab_overview:
    df_reels = pd.DataFrame(st.session_state.reels)
    df_reels["watch_hours"] = ((df_reels["plays"] * df_reels["avg_watch_sec"]) / 3600.0).round(1)
    total_reach = int(df_reels["reach"].sum())
    total_watch_hrs = round(float(df_reels["watch_hours"].sum()), 1)
    avg_retention = round(float(df_reels["retention_rate"].mean()), 1)
    live_followers = int(st.session_state.ig_account["followers"])

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Reach", f"{total_reach:,}", f"{total_reach / max(1, live_followers):.1f}× follower base")
    m2.metric("Verified Watch Hours", f"{total_watch_hrs}h", "∑(Plays × Watch Sec) ÷ 3600")
    m3.metric("Avg Retention Rate", f"{avg_retention}%", f"3s Hold: {df_reels['hook_hold_3s'].mean():.1f}%")
    m4.metric("Live IG Followers", f"{live_followers:,}", f"+{int(df_reels['followers_gained'].sum())} from Reels")

    st.divider()
    g1, g2 = st.columns([1.3, 1])
    with g1:
        st.subheader("Content Graph: Reach & Watch Hours")
        if len(df_reels) == 1:
            r0 = df_reels.iloc[0]
            chart_df = pd.DataFrame({
                "Stage": ["Day 1 Launch", "48h Hook Surge", "Explore Push", "Current Total"],
                "Reach": [round(r0["reach"] * 0.22), round(r0["reach"] * 0.58), round(r0["reach"] * 0.84), r0["reach"]],
                "Watch Hours": [round(r0["watch_hours"] * 0.22, 1), round(r0["watch_hours"] * 0.58, 1), round(r0["watch_hours"] * 0.84, 1), r0["watch_hours"]]
            }).set_index("Stage")
        else:
            chart_df = df_reels[["title", "reach", "watch_hours"]].rename(columns={"title": "Reel", "reach": "Reach", "watch_hours": "Watch Hours"}).set_index("Reel")
        st.line_chart(chart_df)

    with g2:
        st.subheader("Second-by-Second Retention Curve")
        selected_title = st.selectbox("Select Reel to Inspect", df_reels["title"].tolist())
        sel_row = df_reels[df_reels["title"] == selected_title].iloc[0]
        curve_df = pd.DataFrame({
            "Timestamp": [f"{int(round((i / 11) * sel_row['duration_sec']))}s" for i in range(len(sel_row["curve"]))],
            "Viewer Retention (%)": sel_row["curve"]
        }).set_index("Timestamp")
        st.area_chart(curve_df)
        st.caption(f"3s Hook Hold: {sel_row['hook_hold_3s']}% · Avg Watch: {sel_row['avg_watch_sec']}s / {sel_row['duration_sec']}s")

    st.subheader("Content Graph Library")
    display_cols = ["title", "format", "reach", "plays", "watch_hours", "retention_rate", "hook_hold_3s", "followers_gained"]
    st.dataframe(df_reels[display_cols], use_container_width=True, hide_index=True)

# TAB 2: CONTENT LAB (VIRALITY PREDICTOR)
with tab_lab:
    left_lab, right_lab = st.columns([1.25, 1], gap="large")
    with left_lab:
        st.subheader("Google Drive & Instagram Reel Virality Predictor")
        st.caption("No virality score is shown until you paste a link/upload and run the prediction.")
        drive_url = st.text_input("1. Google Drive Link OR Instagram Reel Link", placeholder="https://drive.google.com/file/d/... or https://www.instagram.com/reel/...")
        followers_input = st.number_input("Current Instagram Followers", min_value=1, value=int(st.session_state.ig_account["followers"]))
        reel_topic = st.text_input("2. Visual Summary (What happens in 0–3 seconds?)", placeholder="e.g., Showing the finished edit before the 3-step breakdown")
        caption_input = st.text_area("3. Caption & Spoken Hook Script", placeholder="Write your Reel caption and opening hook here...")
        hashtags_input = st.text_input("Hashtags", placeholder="#reelsgrowth #creatortips")

        s1, s2, s3 = st.columns(3)
        hook_choice = s1.selectbox("3s Hook Structure", [("Visual payoff + contrarian (0–2s)", 1.15), ("Clear benefit / result", 1.05), ("Curiosity question", 0.94), ("Slow intro", 0.74)], format_func=lambda x: x[0])
        pace_choice = s2.selectbox("Scene Cut Pacing", [("Fast cuts (1.5–2.5s)", "fast_2s"), ("Balanced cuts (3–5s)", "dynamic_4s"), ("Single static take", "single_take")], format_func=lambda x: x[0])
        audio_choice = s3.selectbox("Audio Signal", [("Voiceover + trending audio", "trending_original"), ("Trending music", "trending_music"), ("Raw camera audio", "raw_audio")], format_func=lambda x: x[0])

        cover_file = st.file_uploader("4. Upload Cover Photo / Thumbnail (PNG, JPG, WebP)", type=["png", "jpg", "jpeg", "webp"])
        cover_sig = analyze_cover_image(cover_file)
        if cover_sig:
            st.image(cover_file, width=180, caption=f"{cover_sig['width']}×{cover_sig['height']}px · Brightness {cover_sig['brightness']}% · Contrast {cover_sig['contrast']}/128")

        if st.button("Predict Virality & Analyze Reel ↗", type="primary", use_container_width=True):
            if not drive_url.strip() and not cover_sig:
                st.warning("Paste a Google Drive / Instagram Reel link or upload a cover photo first.")
            elif not caption_input.strip():
                st.warning("Enter your Reel caption & spoken hook script first.")
            else:
                st.session_state.prediction_result = compute_virality_prediction(
                    drive_url, reel_topic, caption_input, hashtags_input,
                    followers_input, hook_choice[1], pace_choice[1], audio_choice[1], cover_sig
                )

    with right_lab:
        st.subheader("Virality Predictor Report")
        res = st.session_state.prediction_result
        if res is None:
            st.info("Ready when you are. Paste your Reel link, enter your caption, and click **Predict Virality**.")
        else:
            st.metric("Predicted Virality Score", f"{res['score']} / 100", f"{res['reach'] / max(1, followers_input):.1f}× follower reach")
            r1, r2 = st.columns(2)
            r1.metric("Predicted Reach", f"{res['reach']:,}")
            r2.metric("Predicted Plays", f"{res['plays']:,}")
            r3, r4 = st.columns(2)
            r3.metric("Predicted Watch Hours", f"{res['watch_hours']} hrs")
            r4.metric("Retention / 3s Hold", f"{res['retention_rate']}% / {res['hook_hold_3s']}%")
            st.write("**Score Breakdown:**", res["breakdown"])
            st.success(f"**Recommended 3s Hook Rewrite:** {res['hook_rewrite']}")
            if st.button("Push Predicted Reel to Content Graph ↗", use_container_width=True):
                st.session_state.reels.insert(0, {
                    "id": f"reel-{len(st.session_state.reels) + 1}",
                    "title": res["topic"],
                    "format": "Reel",
                    "reach": res["reach"],
                    "plays": res["plays"],
                    "duration_sec": res["duration_sec"],
                    "avg_watch_sec": res["avg_watch_sec"],
                    "retention_rate": res["retention_rate"],
                    "hook_hold_3s": res["hook_hold_3s"],
                    "completion_rate": res["completion_rate"],
                    "engagement": 9.4,
                    "saves": round(res["reach"] * 0.045),
                    "followers_gained": res["followers_gained"],
                    "drive_link": res["drive_url"],
                    "curve": res["curve"]
                })
                st.success("Added to Content Graph! Switch to the Overview tab to inspect.")

# TAB 3: AUDIENCE & FOLLOWER STREAM
with tab_audience:
    st.subheader(f"Real-Time Follower Attribution ({st.session_state.ig_account['followers']:,} Followers)")
    with st.form("follower_sim_form"):
        fc1, fc2, fc3 = st.columns(3)
        f_handle = fc1.text_input("Follower Handle", placeholder="@new.creator")
        f_name = fc2.text_input("Display Name", placeholder="Alex Rivera")
        f_source = fc3.selectbox("Converted From Reel", [f"Reel: {r['title']}" for r in st.session_state.reels])
        if st.form_submit_button("＋ Log Follower Attribution Event"):
            if f_handle.strip():
                clean_h = f_handle.strip() if f_handle.strip().startswith("@") else "@" + f_handle.strip()
                st.session_state.ig_account["followers"] += 1
                st.session_state.follower_events.insert(0, {
                    "handle": clean_h,
                    "name": f_name.strip() or "New Follower",
                    "niche": "Creator",
                    "source": f_source,
                    "time": "Just now"
                })
                st.rerun()
    st.dataframe(pd.DataFrame(st.session_state.follower_events), use_container_width=True, hide_index=True)

# TAB 4: PLANNER
with tab_planner:
    st.subheader("Content Planner")
    with st.form("planner_form"):
        pc1, pc2, pc3 = st.columns([2, 1, 1])
        new_idea_title = pc1.text_input("Reel Idea or Drive Draft", placeholder="An idea worth making...")
        new_idea_date = pc2.date_input("Target Date", value=date(2026, 11, 25))
        new_idea_status = pc3.selectbox("Status", ["Draft", "Scheduled", "Published"])
        if st.form_submit_button("＋ Add to Planner"):
            if new_idea_title.strip():
                st.session_state.ideas.insert(0, {
                    "title": new_idea_title.strip(),
                    "date": str(new_idea_date),
                    "status": new_idea_status
                })
                st.rerun()
    st.dataframe(pd.DataFrame(st.session_state.ideas), use_container_width=True, hide_index=True)
