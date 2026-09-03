import os
import tempfile
import datetime
import textwrap
import streamlit as st
from dotenv import load_dotenv
from fpdf import FPDF
from PIL import Image
from utils import inspect_files
from agent import process_query

# Load environment variables from .env
load_dotenv()

def generate_pdf_report(query, response, trace, output_image):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, "SatQuery AI - Execution Audit Report", ln=True, align="C")
        
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 10, f"Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
        pdf.ln(5)
        
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 10, "1. Query & Response", ln=True)
        pdf.set_font("Helvetica", "", 10)
        
        # Sanitize unicode characters that Helvetica doesn't support, then wrap
        clean_query = str(query).encode('latin-1', 'replace').decode('latin-1')
        clean_response = str(response).encode('latin-1', 'replace').decode('latin-1')
        
        # Use a conservative width (65) to ensure wide characters don't exceed page margins
        safe_query = textwrap.fill(clean_query, width=65, replace_whitespace=False, break_long_words=True)
        safe_response = textwrap.fill(clean_response, width=65, replace_whitespace=False, break_long_words=True)
        
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(pdf.epw, 8, f"Query:\n{safe_query}")
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(pdf.epw, 8, f"Agent Response:\n{safe_response}")
        pdf.ln(5)
        
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 10, "2. Execution Trace", ln=True)
        pdf.set_font("Helvetica", "", 10)
        if trace:
            for k, v in trace.items():
                clean_v = str(v).encode('latin-1', 'replace').decode('latin-1')
                safe_v = textwrap.fill(clean_v, width=65, replace_whitespace=False, break_long_words=True)
                pdf.set_x(pdf.l_margin)
                pdf.multi_cell(pdf.epw, 8, f"{str(k).replace('_', ' ').title()}:\n{safe_v}")
        pdf.ln(5)
        
        # Add Image
        if output_image is not None:
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 10, "3. Visual Spatial Output", ln=True)
            pdf.ln(5)
            
            # Save array to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                im = Image.fromarray(output_image)
                im.save(tmp.name)
                pdf.image(tmp.name, w=170)
                tmp_path = tmp.name
            
            # Clean up
            os.unlink(tmp_path)
            
        return bytes(pdf.output())
    except Exception as e:
        print(f"PDF Generation failed: {e}")
        return None

def set_custom_theme():
    # A beautiful, unique space background and modern sleek UI
    # We use a stunning Unsplash space image for the hero section
    custom_css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide Streamlit default header, footer, and menu */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .stApp {
        background-color: #050510;
        background-image: 
            linear-gradient(rgba(5, 5, 16, 0.65), rgba(5, 5, 16, 0.95)),
            url("https://images.unsplash.com/photo-1506318137071-a8e063b4bec0?q=80&w=2070&auto=format&fit=crop");
        background-size: cover;
        background-attachment: fixed;
        background-position: center;
        color: #FFFFFF;
    }

    /* Text Visibility and Global styles */
    h1, h2, h3, h4, h5, h6, p, label, .stMarkdown {
        color: #F8FAFC !important;
        text-shadow: 1px 1px 4px rgba(0, 0, 0, 0.9);
    }
    
    /* Hero Title styling */
    .hero-title {
        font-size: 4rem;
        font-weight: 800;
        text-align: center;
        margin-top: 2rem;
        margin-bottom: 0.5rem;
        background: -webkit-linear-gradient(45deg, #A78BFA 0%, #38BDF8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0px 4px 15px rgba(56, 189, 248, 0.4);
    }
    
    .hero-subtitle {
        font-size: 1.3rem;
        font-weight: 400;
        text-align: center;
        color: #E2E8F0;
        margin-bottom: 3rem;
        text-shadow: 1px 1px 4px rgba(0,0,0,0.9);
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
        background-color: rgba(15, 23, 42, 0.4);
        border: 2px dashed #1E293B;
        border-radius: 16px;
        padding: 2rem;
        transition: all 0.3s ease;
    }
    
    [data-testid="stFileUploadDropzone"]:hover {
        border-color: #3B82F6;
        background-color: rgba(30, 41, 59, 0.6);
        box-shadow: 0 0 15px rgba(59, 130, 246, 0.3);
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
    
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.markdown("<div class='hero-title'>SatQuery Portal</div>", unsafe_allow_html=True)
        st.markdown("<div class='hero-subtitle'>Authenticate to access advanced remote sensing intelligence</div>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.markdown("<div style='background: rgba(15, 23, 42, 0.6); padding: 2rem; border-radius: 16px; border: 1px solid #334155;'>", unsafe_allow_html=True)
            st.markdown("<h3 style='text-align: center; color: white; margin-bottom: 1.5rem;'>Login</h3>", unsafe_allow_html=True)
            
            username = st.text_input("Username", key="user_login")
            password = st.text_input("Password", type="password", key="pass_login")
            
            if st.button("Enter Portal", use_container_width=True):
                # Using a dummy check for the demo
                if username and password:
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Please enter username and password")
            st.markdown("</div>", unsafe_allow_html=True)
        return

    # Hero Section
    st.markdown("<div class='hero-title'>Discover Earth's Secrets</div>", unsafe_allow_html=True)
    st.markdown("<div class='hero-subtitle'>Advanced AI-driven remote sensing intelligence at your fingertips.</div>", unsafe_allow_html=True)

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Unified Upload Interface
    st.markdown("<h3 style='text-align: center; color: #E2E8F0; margin-bottom: 1rem;'>Upload Imagery</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #cbd5e1; font-size: 1.1rem; margin-bottom: 2rem;'>Upload one or more satellite images. The system will automatically detect the modality (Single Image, Fusion, Change Analysis) based on your files.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        uploaded_files = st.file_uploader(
            "Drag and drop your images here", 
            type=["png", "jpg", "jpeg", "tif", "tiff"], 
            accept_multiple_files=True,
            key="unified_upload"
        )

    st.markdown("<br><hr style='border: 1px solid rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
    
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
                # Confidence Gauge
                conf = trace.get("confidence_score", 0.0)
                st.metric(label="Algorithmic Confidence", value=f"{conf*100:.1f}%")
                
                with st.expander("🛠️ Execution Trace & Parameters", expanded=True):
                    for k, v in trace.items():
                        st.write(f"**{str(k).replace('_', ' ').title()}:** {v}")
                        
            # Visual Layout Logic
            if output_image is not None:
                task_type = trace.get("task_type", "") if trace else ""
                
                if task_type == "Change Detection" and len(uploaded_files) >= 2:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.image(uploaded_files[0], caption="Time 1 (Before)", use_container_width=True)
                    with col2:
                        st.image(uploaded_files[1], caption="Time 2 (After)", use_container_width=True)
                    with col3:
                        st.image(output_image, caption="Change Heatmap", use_container_width=True)
                elif task_type == "Cross-Modal Fusion" and len(uploaded_files) >= 2:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.image(uploaded_files[0], caption="Optical (RGB)", use_container_width=True)
                    with col2:
                        st.image(uploaded_files[1], caption="SAR (Texture)", use_container_width=True)
                    with col3:
                        st.image(output_image, caption="Fused Composite", use_container_width=True)
                elif task_type == "Visual Grounding" and len(uploaded_files) >= 1:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.image(uploaded_files[0], caption="Original Image", use_container_width=True)
                    with col2:
                        st.image(output_image, caption="Annotated Grounding", use_container_width=True)
                else:
                    st.image(output_image, caption="Agent Visual Output", use_container_width=True)
            
            # PDF Report Button
            if trace:
                pdf_bytes = generate_pdf_report(prompt, response, trace, output_image)
                if pdf_bytes is not None:
                    st.download_button(
                        label="📄 Download Audit Report (PDF)",
                        data=pdf_bytes,
                        file_name=f"SatQuery_Audit_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf"
                    )
                else:
                    st.error("Could not generate PDF report due to rendering constraints.")
                    
        st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
