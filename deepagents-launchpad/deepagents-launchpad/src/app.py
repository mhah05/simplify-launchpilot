import os
import sys
import uuid
import importlib
import streamlit as st
from dotenv import load_dotenv

# Ensure the local directory is in Python path
sys.path.append(os.path.join(os.path.dirname(__file__)))
st.set_page_config(page_title="LaunchPilot", layout="wide")

@st.cache_resource
def _load_backend(_mtime: float):
    import supervisor as supervisor_mod
    supervisor_mod = importlib.reload(supervisor_mod)
    supervisor_mod.load_aws_credentials()
    return supervisor_mod.compiled_graph

_supervisor_mtime = os.path.getmtime(os.path.join(os.path.dirname(__file__), "supervisor.py"))
compiled_graph = _load_backend(_supervisor_mtime)
load_dotenv()

st.title("🚀 LaunchPilot")
st.caption("Validating technical innovations and drafting social dispatches using AWS Bedrock.")

if "thread_id" not in st.session_state:
    st.session_state.thread_id = f"streamlit_{uuid.uuid4().hex[:8]}"

config = {"configurable": {"thread_id": st.session_state.thread_id}}

def _as_list(value) -> list:
    return value if isinstance(value, list) else []

def _as_dict(value) -> dict:
    return value if isinstance(value, dict) else {}

def _friendly_error(exc: Exception) -> str:
    text = str(exc)
    if "ExpiredTokenException" in text or "expired" in text.lower():
        return (
            "AWS session token has expired. Refresh the temporary keys in .env "
            "(Access Key, Secret Key, and Session Token) and restart the app."
        )
    if "UnrecognizedClientException" in text or "InvalidClientTokenId" in text:
        return "AWS credentials in .env were not accepted. Check the keys and region."
    if "AccessDenied" in text:
        return "These AWS credentials cannot call Bedrock in ap-southeast-1. Confirm model access in the Bedrock console."
    return text

# ==========================================
# X (TWITTER) INTEGRATION GATEWAY
# ==========================================
st.sidebar.markdown("## 🔗 Integration Center")

# Initialize X connection state in Streamlit session memory
if "x_connected" not in st.session_state:
    st.session_state.x_connected = False
if "x_username" not in st.session_state:
    st.session_state.x_username = ""

if not st.session_state.x_connected:
    st.sidebar.warning("🔴 X (Twitter) Not Connected")
    
    # Choose connection method
    link_mode = st.sidebar.radio("Link Method", ["OAuth (Quick Demo Link)", "Manual API Keys"])

    if link_mode == "OAuth (Quick Demo Link)":
        if st.sidebar.button("🐦 Log in with X", use_container_width=True):
            with st.sidebar.spinner("Establishing secure handshake..."):
                import time
                time.sleep(1.2)  # Simulate network OAuth latency
                st.session_state.x_connected = True
                st.session_state.x_username = "Robotics_Bot"
                st.sidebar.success("✅ Linked to @Robotics_Bot successfully!")
                st.rerun()
                
    elif link_mode == "Manual API Keys":
        st.sidebar.caption("Enter your developer keys. They will be securely saved to your local .env file.")
        
        # Mask inputs for secret keys to protect user data
        new_key = st.sidebar.text_input("X API Key (Consumer Key)", type="password")
        new_secret = st.sidebar.text_input("X API Secret (Consumer Secret)", type="password")
        new_token = st.sidebar.text_input("X Access Token", type="password")
        new_token_secret = st.sidebar.text_input("X Access Token Secret", type="password")
        
        if st.sidebar.button("💾 Link & Save Keys", use_container_width=True):
            if new_key and new_secret and new_token and new_token_secret:
                st.session_state.x_connected = True
                st.session_state.x_username = "DeveloperAccount"
                
                # Securely append credentials to local .env file
                with open(".env", "a", encoding="utf-8") as env_file:
                    env_file.write(f"\nX_API_KEY={new_key}")
                    env_file.write(f"\nX_API_SECRET={new_secret}")
                    env_file.write(f"\nX_ACCESS_TOKEN={new_token}")
                    env_file.write(f"\nX_ACCESS_TOKEN_SECRET={new_token_secret}")
                
                st.sidebar.success("✅ Credentials saved to .env!")
                st.rerun()
            else:
                st.sidebar.error("Please fill in all 4 key fields!")
else:
    st.sidebar.success(f"🟢 Connected: **@{st.session_state.x_username}**")
    if st.sidebar.button("🔌 Unlink Account", use_container_width=True):
        st.session_state.x_connected = False
        st.session_state.x_username = ""
        st.rerun()

st.sidebar.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.subheader("💡 Validate Your Startup Idea")
    user_idea = st.text_area(
        "Describe your deep-tech idea (e.g., Robot-arm sorting mechanism using custom YOLOv8 models):",
        height=150,
        placeholder="Enter your startup's core technology here...",
    )
    
    if st.button("Generate Pitch Angle 🤖", use_container_width=True):
        if user_idea.strip():
            with st.spinner("Processing Multi-Agent Flowchart..."):
                initial_input = {
                    "repo_raw_content": user_idea,
                    "is_post_approved": False,
                    "current_post_index": 0,
                    "content_calendar": [],
                }
                try:
                    compiled_graph.invoke(initial_input, config)
                    st.session_state["flow_started"] = True
                    st.rerun()
                except Exception as exc:
                    st.error(_friendly_error(exc))
        else:
            st.warning("Please describe your idea first!")

with col2:
    st.subheader("📋 Advisor Feedback")
    graph_state = compiled_graph.get_state(config)
    values = graph_state.values if graph_state else {}
    profile = _as_dict(values.get("repo_profile"))
    market = _as_dict(values.get("market_research"))
    strategy = _as_dict(values.get("content_strategy"))
    posts = _as_list(values.get("content_calendar"))

    if profile or market or strategy or posts:
        st.success("Analysis Complete!")

        tab1, tab2, tab3 = st.tabs(["Technical Extraction", "Market Viability", "Commercial Pillars"])

        with tab1:
            st.markdown(f"**Architecture Summary:** {profile.get('summary', 'Pending...')}")
            st.markdown(f"**Identified Stack:** {', '.join(_as_list(profile.get('tech_stack'))) or 'Pending...'}")

        with tab2:
            st.markdown(f"**Identified Competitors:** {', '.join(_as_list(market.get('competitors'))) or 'Pending...'}")
            st.markdown(f"**Differentiator:** {market.get('uniqueness', 'Pending...')}")

        with tab3:
            st.write(_as_list(strategy.get("pillars")) or "Pending...")

        st.markdown("---")
        st.subheader("🛡️ Social Publishing Gate")
        idx = values.get("current_post_index", 0) or 0

        if idx < len(posts):
            current_post = posts[idx]
            st.warning(f"**Reviewing Social Draft #{idx + 1} of {len(posts)}**")
            st.markdown(f"**Pillar:** *{current_post.get('pillar', '')}*")
            st.info(f"**Draft Caption:** '{current_post.get('caption', '')}'")
            st.caption(f"**Visual Prompt:** *{current_post.get('visual_prompt', '')}*")

            c1, c2 = st.columns(2)

            # Safety gateway checks
            if st.session_state.x_connected:
                if c1.button("✅ Approve & Publish", use_container_width=True):
                    try:
                        compiled_graph.update_state(
                            config,
                            {"is_post_approved": True},
                            as_node="content_creator",
                        )
                        compiled_graph.invoke(None, config)
                        st.toast("Demo publish completed and saved to the local log.")
                        st.rerun()
                    except Exception as exc:
                        st.error(_friendly_error(exc))
            else:
                c1.warning("⚠️ Link your X Account first!")

            if c2.button("🔄 Refine Content", use_container_width=True):
                st.session_state.thread_id = f"streamlit_{uuid.uuid4().hex[:8]}"
                st.session_state.pop("flow_started", None)
                st.rerun()
        else:
            st.success("All social posts in this session have been published!")
    else:
        st.info("Write your idea on the left and click 'Generate' to see feedback here.")
