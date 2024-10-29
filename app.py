import streamlit as st
import os
from pathlib import Path
import time
from pygame import mixer
import pandas as pd
from datetime import datetime

# Set page configuration
st.set_page_config(
    page_title="Cold Calling Assistant",
    page_icon="📞",
    layout="wide"
)

# Initialize session state
if 'audio_files' not in st.session_state:
    st.session_state.audio_files = {}  # Dictionary to store {button_name: file_path}
if 'call_log' not in st.session_state:
    st.session_state.call_log = []

# Custom CSS to improve button appearance
st.markdown("""
    <style>
    .stButton>button {
        height: 100px;
        white-space: normal;
        padding: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

def save_uploaded_file(uploaded_file):
    """Save uploaded audio file and return the file path"""
    save_dir = Path("uploads")
    save_dir.mkdir(exist_ok=True)
    
    file_path = save_dir / uploaded_file.name
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return str(file_path)

def play_audio(file_path):
    """Play audio file using pygame mixer"""
    try:
        mixer.init()
        mixer.music.load(file_path)
        mixer.music.play()
        while mixer.music.get_busy():
            time.sleep(0.1)
    except Exception as e:
        st.error(f"Error playing audio: {str(e)}")
    finally:
        mixer.music.unload()
        mixer.quit()

def log_call(business_name, notes):
    """Add a new call to the call log"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.call_log.append({
        "timestamp": timestamp,
        "business": business_name,
        "notes": notes
    })

# Main app layout
st.title("Cold Calling Assistant 📞")

# Create two columns for the main layout
col1, col2 = st.columns([2, 1])

with col1:
    st.header("Audio Controls")
    
    # File upload section
    with st.expander("Upload New Audio Clip", expanded=True):
        uploaded_file = st.file_uploader(
            "Choose an MP3 file",
            type=['mp3'],
            key="file_uploader"
        )
        
        if uploaded_file:
            button_name = st.text_input(
                "Enter a name for this audio clip",
                value=uploaded_file.name.replace('.mp3', ''),
                placeholder="e.g., Initial Pitch, Follow Up, Close"
            )
            
            if st.button("Add Audio Clip"):
                file_path = save_uploaded_file(uploaded_file)
                st.session_state.audio_files[button_name] = file_path
                st.success(f"✅ Added audio clip: {button_name}")
                st.rerun()
    
    # Audio playback section
    st.subheader("Play Audio Clips")
    if st.session_state.audio_files:
        # Create a grid of buttons
        cols = st.columns(2)  # 2 buttons per row
        for idx, (button_name, file_path) in enumerate(st.session_state.audio_files.items()):
            with cols[idx % 2]:
                if st.button(f"▶️ {button_name}", key=f"btn_{button_name}", use_container_width=True):
                    play_audio(file_path)
    else:
        st.info("👆 Start by uploading some audio clips above!")

with col2:
    st.header("Call Logger")
    
    # Call logging form
    with st.form("call_log_form"):
        business_name = st.text_input("Business Name", placeholder="Enter business name")
        notes = st.text_area("Call Notes", placeholder="Enter call notes, outcomes, or follow-up items")
        submitted = st.form_submit_button("Log Call 📝")
        
        if submitted and business_name:
            log_call(business_name, notes)
            st.success("✅ Call logged successfully!")
    
    # Display call log
    if st.session_state.call_log:
        st.subheader("Recent Calls")
        df = pd.DataFrame(st.session_state.call_log)
        st.dataframe(
            df,
            hide_index=True,
            column_config={
                "timestamp": "Time",
                "business": "Business",
                "notes": "Notes"
            }
        )
        
        # Export functionality
        if st.button("Export Call Log 📊"):
            df.to_csv("call_log.csv", index=False)
            st.success("✅ Call log exported to call_log.csv!")
            
            # Provide download button
            st.download_button(
                label="Download Call Log",
                data=df.to_csv(index=False),
                file_name="call_log.csv",
                mime="text/csv"
            )

# Footer
st.markdown("---")
st.markdown("*💡 Tip: Keep your audio clips short and clear for the best results*")