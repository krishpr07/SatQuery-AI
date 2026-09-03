import os
import streamlit as st
from dotenv import load_dotenv
from utils import inspect_files
from agent import process_query

# Load environment variables from .env
load_dotenv()

def set_custom_theme():
    # A beautiful, unique space background and modern sleek UI
    # We use a stunning Unsplash space image for the hero section
    custom_css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;500;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background-color: #0B0E14;
        background-image: 
            linear-gradient(rgba(11, 14, 20, 0.85), rgba(11, 14, 20, 1.0)),
            url("https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072&auto=format&fit=crop");
        background-size: cover;
        background-attachment: fixed;
        background-position: center;
        color: #E2E8F0;
    }
    
    /* Hero Title styling */
    .hero-title {
        font-size: 3.5rem;
        font-weight: 700;
        text-align: center;
        margin-top: 2rem;
        margin-bottom: 0.5rem;
        background: -webkit-linear-gradient(45deg, #4facfe 0%, #00f2fe 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .hero-subtitle {
        font-size: 1.2rem;
        font-weight: 300;
        text-align: center;
        color: #94A3B8;
        margin-bottom: 3rem;
    }
    
    /* Custom Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        justify-content: center;
        background-color: rgba(30, 41, 59, 0.5);
        border-radius: 12px;
        padding: 10px;
        border: 1px solid #334155;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 8px;
        color: #94A3B8;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #3B82F6 !important;
        color: white !important;
    }
    
    /* Upload Box styling */
    [data-testid="stFileUploadDropzone"] {
        background-color: rgba(15, 23, 42, 0.6);
        border: 2px dashed #475569;
        border-radius: 16px;
        padding: 2rem;
    }
    
    [data-testid="stFileUploadDropzone"]:hover {
        border-color: #3B82F6;
        background-color: rgba(30, 41, 59, 0.8);
    }
    
    /* Chat Input styling */
    .stChatInputContainer {
        border-radius: 12px;
        border: 1px solid #334155;
        background-color: rgba(15, 23, 42, 0.8);
    }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

def main():
    st.set_page_config(page_title="SatQuery AI", layout="wide", initial_sidebar_state="collapsed")
    set_custom_theme()
    
    # Hero Section
    st.markdown("<div class='hero-title'>Discover Earth's Secrets</div>", unsafe_allow_html=True)
    st.markdown("<div class='hero-subtitle'>Advanced AI-driven remote sensing intelligence at your fingertips.</div>", unsafe_allow_html=True)

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Main Analysis Interface (Tabs)
    st.markdown("<h3 style='text-align: center; color: white;'>Analyze a Scene</h3>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["🖼️ Single Image", "🌐 Optical + SAR Fusion", "🔄 Change Analysis"])
    
    uploaded_files = []
    
    with tab1:
        st.markdown("<p style='text-align: center; color: #94A3B8;'>Upload a single satellite image for Visual Grounding or QA.</p>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            file = st.file_uploader("Drop image here", type=["png", "jpg", "jpeg", "tif", "tiff"], key="single")
            if file: uploaded_files.append(file)
            
    with tab2:
        st.markdown("<p style='text-align: center; color: #94A3B8;'>Upload one Optical and one SAR image for structural fusion.</p>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            opt = st.file_uploader("Optical Image", type=["png", "jpg", "jpeg", "tif", "tiff"], key="opt")
            if opt: uploaded_files.append(opt)
        with col2:
            sar = st.file_uploader("SAR Image", type=["png", "jpg", "jpeg", "tif", "tiff"], key="sar")
            if sar: uploaded_files.append(sar)

    with tab3:
        st.markdown("<p style='text-align: center; color: #94A3B8;'>Upload two images of the same area over time to detect changes.</p>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            t1 = st.file_uploader("Time 1 (Before)", type=["png", "jpg", "jpeg", "tif", "tiff"], key="t1")
            if t1: uploaded_files.append(t1)
        with col2:
            t2 = st.file_uploader("Time 2 (After)", type=["png", "jpg", "jpeg", "tif", "tiff"], key="t2")
            if t2: uploaded_files.append(t2)

    st.markdown("---")
    
    # Process Files
    file_metadata = None
    if uploaded_files:
        try:
            file_metadata = inspect_files(uploaded_files)
            if file_metadata["status"] == "valid":
                st.success(f"✅ Ready for analysis: {file_metadata['modality']}")
                if file_metadata.get("compatibility_warnings"):
                    for warn in file_metadata["compatibility_warnings"]:
                        st.warning(f"⚠️ {warn}")
            else:
                st.error(file_metadata.get("message", "Invalid configuration."))
        except Exception as e:
            st.error(f"Error inspecting files: {e}")

    # Chat Interface
    st.markdown("### Ask about this scene")
    
    # Display chat messages from history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # React to user input
    if prompt := st.chat_input("E.g., 'Find all the buildings' or 'Run change detection'"):
        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Generate response
        if not uploaded_files:
            response = "Please upload imagery in the tabs above first."
            trace = None
            output_image = None
        elif file_metadata and file_metadata["status"] != "valid":
            response = "Cannot process query. Uploaded files have an invalid configuration."
            trace = None
            output_image = None
        else:
            with st.spinner("Agentic Controller is analyzing..."):
                try:
                    result = process_query(prompt, file_metadata, st.session_state.messages)
                    response = result.get('response', 'No response provided.')
                    trace = result.get('trace', {})
                    output_image = result.get('output_image', None)
                except Exception as e:
                    response = f"An error occurred: {e}"
                    trace = None
                    output_image = None

        # Display assistant response
        with st.chat_message("assistant"):
            st.markdown(response)
            if trace:
                with st.expander("🛠️ Execution Trace & Parameters"):
                    for k, v in trace.items():
                        st.write(f"**{k.replace('_', ' ').title()}:** {v}")
                        
            if output_image is not None:
                st.image(output_image, caption="Agent Output", use_container_width=True)
                    
        st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
