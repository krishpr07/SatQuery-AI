import os
import tempfile
import datetime
import streamlit as st
from dotenv import load_dotenv
from fpdf import FPDF
from PIL import Image
from streamlit_option_menu import option_menu
from utils import inspect_files
from agent import process_query

# Load environment variables from .env
load_dotenv()

def generate_pdf_report(query, response, trace, output_image):
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
    pdf.multi_cell(0, 8, f"Query: {query}")
    pdf.multi_cell(0, 8, f"Agent Response: {response}")
    pdf.ln(5)
    
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "2. Execution Trace", ln=True)
    pdf.set_font("Helvetica", "", 10)
    if trace:
        for k, v in trace.items():
            pdf.cell(0, 8, f"{str(k).replace('_', ' ').title()}: {v}", ln=True)
    pdf.ln(5)
    
    # Add Image
    if output_image is not None:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 10, "3. Visual Spatial Output", ln=True)
        
        # Save array to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            im = Image.fromarray(output_image)
            im.save(tmp.name)
            pdf.image(tmp.name, w=170)
            tmp_path = tmp.name
        
        # Clean up
        os.unlink(tmp_path)
        
    return bytes(pdf.output())

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
        background-color: #090D16;
        background-image: 
            linear-gradient(rgba(9, 13, 22, 0.90), rgba(9, 13, 22, 1.0)),
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
    
    # Hero Section
    st.markdown("<div class='hero-title'>Discover Earth's Secrets</div>", unsafe_allow_html=True)
    st.markdown("<div class='hero-subtitle'>Advanced AI-driven remote sensing intelligence at your fingertips.</div>", unsafe_allow_html=True)

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Main Analysis Interface (Pill Navbar)
    st.markdown("<h3 style='text-align: center; color: white;'>Analyze a Scene</h3>", unsafe_allow_html=True)
    
    selected_mode = option_menu(
        menu_title=None,
        options=["Single Image", "Optical + SAR Fusion", "Change Analysis"],
        icons=["image", "layers", "arrow-repeat"],
        default_index=0,
        orientation="horizontal",
        styles={
            "container": {"padding": "0!important", "background-color": "rgba(30, 41, 59, 0.3)", "border-radius": "100px", "border": "1px solid #1E293B", "max-width": "700px", "margin": "0 auto 30px auto"},
            "icon": {"color": "#94A3B8", "font-size": "16px"}, 
            "nav-link": {"font-size": "14px", "text-align": "center", "margin": "0px", "color": "#94A3B8", "border-radius": "100px", "padding": "10px 20px"},
            "nav-link-selected": {"background-color": "rgba(59, 130, 246, 0.8)", "color": "white", "box-shadow": "0 0 15px rgba(59,130,246,0.3)"},
        }
    )
    
    uploaded_files = []
    
    if selected_mode == "Single Image":
        st.markdown("<p style='text-align: center; color: #94A3B8;'>Upload a single satellite image for Visual Grounding or QA.</p>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            file = st.file_uploader("Drop image here", type=["png", "jpg", "jpeg", "tif", "tiff"], key="single")
            if file: uploaded_files.append(file)
            
    elif selected_mode == "Optical + SAR Fusion":
        st.markdown("<p style='text-align: center; color: #94A3B8;'>Upload one Optical and one SAR image for structural fusion.</p>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            opt = st.file_uploader("Optical Image", type=["png", "jpg", "jpeg", "tif", "tiff"], key="opt")
            if opt: uploaded_files.append(opt)
        with col2:
            sar = st.file_uploader("SAR Image", type=["png", "jpg", "jpeg", "tif", "tiff"], key="sar")
            if sar: uploaded_files.append(sar)

    elif selected_mode == "Change Analysis":
        st.markdown("<p style='text-align: center; color: #94A3B8;'>Upload two images of the same area over time to detect changes.</p>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            t1 = st.file_uploader("Before (T1)", type=["png", "jpg", "jpeg", "tif", "tiff"], key="t1")
            if t1: uploaded_files.append(t1)
        with col2:
            t2 = st.file_uploader("After (T2)", type=["png", "jpg", "jpeg", "tif", "tiff"], key="t2")
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
                st.download_button(
                    label="📄 Download Audit Report (PDF)",
                    data=pdf_bytes,
                    file_name=f"SatQuery_Audit_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf"
                )
                    
        st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
