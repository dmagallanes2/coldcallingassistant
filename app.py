import streamlit as st
import os
from pathlib import Path
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import numpy as np

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

# Custom CSS
st.markdown("""
    <style>
    .stButton>button {
        height: 100px;
        white-space: normal;
        padding: 15px;
    }
    .stRadio > label {
        font-weight: bold;
        margin-bottom: 10px;
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
    return uploaded_file

def log_call(business_name, notes, result, reason):
    """Add a new call to the call log"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.call_log.append({
        "timestamp": timestamp,
        "business": business_name,
        "notes": notes,
        "result": result,
        "reason": reason
    })

def calculate_statistics(df):
    """Calculate call statistics"""
    total_calls = len(df)
    if total_calls == 0:
        return "No calls logged yet."
    
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
        'reason_pcts': reason_pcts
    }
    
    return stats

def create_pdf_report(stats, date):
    """Create PDF report with statistics"""
    pdf = FPDF()
    pdf.add_page()
    
    # Set up the PDF
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, f'Cold Calling Report - {date}', ln=True, align='C')
    pdf.ln(10)
    
    # Add statistics
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Call Statistics Summary:', ln=True)
    pdf.ln(5)
    
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, f'Total Calls: {stats["total_calls"]}', ln=True)
    pdf.cell(0, 10, f'Interested: {stats["interested_pct"]:.1f}%', ln=True)
    pdf.cell(0, 10, f'Rejected: {stats["rejected_pct"]:.1f}%', ln=True)
    
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Reason Breakdown:', ln=True)
    pdf.ln(5)
    
    pdf.set_font('Arial', '', 12)
    for reason, pct in stats['reason_pcts'].items():
        pdf.cell(0, 10, f'{reason}: {pct:.1f}%', ln=True)
    
    return pdf

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
                audio_file = save_uploaded_file(uploaded_file)
                st.session_state.audio_files[button_name] = audio_file
                st.success(f"✅ Added audio clip: {button_name}")
                st.rerun()
    
    # Audio playback section
    st.subheader("Play Audio Clips")
    if st.session_state.audio_files:
        for button_name, audio_file in st.session_state.audio_files.items():
            st.write(f"**{button_name}**")
            st.audio(audio_file, format='audio/mp3')
    else:
        st.info("👆 Start by uploading some audio clips above!")

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
        
        # Display statistics
        st.subheader("Statistics")
        stats = calculate_statistics(df)
        
        # Show live statistics in the app
        st.write(f"Total Calls: {stats['total_calls']}")
        st.write(f"Interested: {stats['interested_pct']:.1f}%")
        st.write(f"Rejected: {stats['rejected_pct']:.1f}%")
        st.write("Reason Breakdown:")
        for reason, pct in stats['reason_pcts'].items():
            st.write(f"{reason}: {pct:.1f}%")
        
        # Export functionality
        col1, col2 = st.columns(2)
        
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # CSV Export
        with col1:
            csv_filename = f"call_log_{current_date}.csv"
            st.download_button(
                label="Download Call Log (CSV)",
                data=df.to_csv(index=False),
                file_name=csv_filename,
                mime="text/csv"
            )
        
        # PDF Export
        with col2:
            pdf_filename = f"call_report_{current_date}.pdf"
            pdf = create_pdf_report(stats, current_date)
            st.download_button(
                label="Download Report (PDF)",
                data=pdf.output(dest='S').encode('latin-1'),
                file_name=pdf_filename,
                mime="application/pdf"
            )

# Footer
st.markdown("---")
st.markdown("*💡 Tip: Keep your audio clips short and clear for the best results*")