import streamlit as st
import os
from pathlib import Path
import pandas as pd
from datetime import datetime
import io
import pytz

# Set page configuration
st.set_page_config(
    page_title="Cold Calling Assistant",
    page_icon="📞",
    layout="wide"
)

# Initialize session state
if 'audio_files' not in st.session_state:
    st.session_state.audio_files = {}
if 'call_log' not in st.session_state:
    st.session_state.call_log = []
if 'current_audio' not in st.session_state:
    st.session_state.current_audio = None

# Define PST timezone
pst = pytz.timezone('America/Los_Angeles')

# Custom CSS for circular buttons and other styles
st.markdown("""
    <style>
    .audio-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
        gap: 1rem;
        padding: 1rem;
    }
    .audio-button {
        background-color: #f0f2f6;
        border-radius: 50%;
        width: 120px;
        height: 120px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        transition: all 0.3s;
        margin: 10px;
        padding: 10px;
        text-align: center;
    }
    .audio-button:hover {
        background-color: #e0e2e6;
    }
    .audio-title {
        font-size: 0.8em;
        margin-top: 5px;
        word-wrap: break-word;
        max-width: 100px;
        text-align: center;
    }
    .stRadio > label {
        font-weight: bold;
        margin-bottom: 10px;
    }
    div[data-testid="stAudioPlayer"] {
        display: none;
    }
    </style>
    """, unsafe_allow_html=True)

def save_uploaded_files(uploaded_files):
    """Save multiple uploaded audio files"""
    for uploaded_file in uploaded_files:
        if uploaded_file.type == 'audio/mpeg':
            st.session_state.audio_files[uploaded_file.name] = uploaded_file

def log_call(business_name, notes, result, reason):
    """Add a new call to the call log with PST timestamp"""
    timestamp = datetime.now(pst).strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.call_log.append({
        "timestamp": timestamp,
        "business": business_name,
        "notes": notes,
        "result": result,
        "reason": reason
    })

def calculate_statistics(df):
    """Calculate call statistics including time-based metrics in PST"""
    total_calls = len(df)
    if total_calls == 0:
        return None
    
    # Convert timestamp strings to datetime objects in PST
    df['datetime'] = pd.to_datetime(df['timestamp']).dt.tz_localize(pst)
    
    # Calculate time-based metrics
    time_diff = df['datetime'].max() - df['datetime'].min()
    total_hours = time_diff.total_seconds() / 3600
    calls_per_hour = total_calls / total_hours if total_hours > 0 else total_calls
    
    # Format time difference for display
    hours = int(time_diff.total_seconds() // 3600)
    minutes = int((time_diff.total_seconds() % 3600) // 60)
    
    # Calculate percentages
    interested_pct = (df['result'] == 'Interested').mean() * 100
    rejected_pct = (df['result'] == 'Rejected').mean() * 100
    
    # Calculate reason percentages
    reason_counts = df['reason'].value_counts()
    reason_pcts = {
        reason: (count / total_calls * 100)
        for reason, count in reason_counts.items()
    }
    
    stats = {
        'total_calls': total_calls,
        'interested_pct': interested_pct,
        'rejected_pct': rejected_pct,
        'reason_pcts': reason_pcts,
        'duration_hours': hours,
        'duration_minutes': minutes,
        'calls_per_hour': calls_per_hour,
        'start_time': df['datetime'].min().strftime('%I:%M %p PST'),
        'end_time': df['datetime'].max().strftime('%I:%M %p PST')
    }
    
    return stats

def create_report_text(stats, date):
    """Create a text report with statistics including time metrics"""
    report = f"""Cold Calling Report - {date}
{'='*50}

TIME STATISTICS
--------------
Session Duration: {stats['duration_hours']} hours, {stats['duration_minutes']} minutes
Start Time: {stats['start_time']}
End Time: {stats['end_time']}
Calls Per Hour: {stats['calls_per_hour']:.1f}

CALL STATISTICS SUMMARY
----------------------
Total Calls: {stats['total_calls']}
Interested: {stats['interested_pct']:.1f}%
Rejected: {stats['rejected_pct']:.1f}%

REASON BREAKDOWN
--------------"""
    
    for reason, pct in stats['reason_pcts'].items():
        report += f"\n{reason}: {pct:.1f}%"
    
    return report

# Main app layout
st.title("Cold Calling Assistant 📞")

# Create two columns for the main layout
col1, col2 = st.columns([2, 1])

with col1:
    st.header("Audio Controls")
    
    # Multiple file upload section
    uploaded_files = st.file_uploader(
        "Drop all your audio files here",
        type=['mp3'],
        accept_multiple_files=True,
        key="file_uploader"
    )
    
    if uploaded_files:
        save_uploaded_files(uploaded_files)
    
    # Audio playback section
    st.subheader("Play Audio Clips")
    if st.session_state.audio_files:
        cols = st.columns(4)
        for idx, (filename, audio_file) in enumerate(st.session_state.audio_files.items()):
            col = cols[idx % 4]
            with col:
                button_label = os.path.splitext(filename)[0]
                if st.button(
                    f"▶️\n{button_label}",
                    key=f"btn_{filename}",
                    help=f"Play {button_label}"
                ):
                    if st.session_state.current_audio != filename:
                        st.session_state.current_audio = filename
                        st.audio(audio_file, format='audio/mp3')
    else:
        st.info("👆 Drop your audio files above to get started!")

with col2:
    st.header("Call Logger")
    
    # Call logging form
    with st.form("call_log_form"):
        business_name = st.text_input("Business Name", placeholder="Enter business name")
        
        # Radio buttons for Result
        result = st.radio(
            "Call Result",
            options=['Interested', 'Rejected'],
            horizontal=True
        )
        
        # Radio buttons for Reason
        reason = st.radio(
            "Reason",
            options=['No answer', 'Owner not there', 'Not Interested', 'N/A'],
            horizontal=True
        )
        
        notes = st.text_area("Call Notes (Optional)", placeholder="Enter any additional notes")
        
        submitted = st.form_submit_button("Log Call 📝")
        
        if submitted and business_name:
            log_call(business_name, notes, result, reason)
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
                "result": "Result",
                "reason": "Reason",
                "notes": "Notes"
            }
        )
        
        # Calculate and display statistics
        stats = calculate_statistics(df)
        if stats:
            st.subheader("Statistics")
            
            # Time metrics
            st.write("⏱️ Time Statistics")
            st.write(f"Session Duration: {stats['duration_hours']} hours, {stats['duration_minutes']} minutes")
            st.write(f"Start Time: {stats['start_time']}")
            st.write(f"End Time: {stats['end_time']}")
            st.write(f"Calls Per Hour: {stats['calls_per_hour']:.1f}")
            
            # Call metrics
            st.write("📊 Call Statistics")
            st.write(f"Total Calls: {stats['total_calls']}")
            st.write(f"Interested: {stats['interested_pct']:.1f}%")
            st.write(f"Rejected: {stats['rejected_pct']:.1f}%")
            
            st.write("📋 Reason Breakdown:")
            for reason, pct in stats['reason_pcts'].items():
                st.write(f"{reason}: {pct:.1f}%")
            
            # Export functionality
            col1, col2 = st.columns(2)
            
            current_date = datetime.now(pst).strftime("%Y-%m-%d")
            
            # CSV Export
            with col1:
                csv_filename = f"call_log_{current_date}.csv"
                st.download_button(
                    label="Download Call Log (CSV)",
                    data=df.to_csv(index=False),
                    file_name=csv_filename,
                    mime="text/csv"
                )
            
            # Text Report Export
            with col2:
                report_filename = f"call_report_{current_date}.txt"
                report_text = create_report_text(stats, current_date)
                st.download_button(
                    label="Download Report (TXT)",
                    data=report_text,
                    file_name=report_filename,
                    mime="text/plain"
                )

# Footer
st.markdown("---")
st.markdown("*💡 Tip: Keep your audio clips short and clear for the best results*")