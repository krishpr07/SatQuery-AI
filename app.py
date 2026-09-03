import os
import streamlit as st
from dotenv import load_dotenv
from utils import inspect_files
from agent import process_query
from ui import set_space_theme, login_page

# Load environment variables from .env
load_dotenv()

def main():
    st.set_page_config(page_title="SatQuery AI - Vibe_coders", layout="wide")
    
    # Apply space theme
    set_space_theme()
    
    # Authentication check
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
        
    if not st.session_state["authenticated"]:
        login_page()
        return
        
    st.title("🛰️ SatQuery AI - Vibe_coders")
    st.markdown("Agentic Vision-Language Assistant for Remote Sensing Images (SIH26167)")

    # Sidebar for File Upload
    st.sidebar.header("Data Input")
    uploaded_files = st.sidebar.file_uploader(
        "Upload Satellite Imagery",
        type=["tif", "tiff", "png", "jpeg", "jpg"],
        accept_multiple_files=True
    )

    file_metadata = None
    if uploaded_files:
        st.sidebar.subheader("Uploaded Files Info")
        try:
            file_metadata = inspect_files(uploaded_files)
            if file_metadata["status"] == "valid":
                st.sidebar.success(f"Detected Modality: {file_metadata['modality']}")
                for f in uploaded_files:
                    st.sidebar.text(f"📄 {f.name}")
            else:
                st.sidebar.error(file_metadata.get("message", "Invalid configuration."))
        except Exception as e:
            st.sidebar.error(f"Error inspecting files: {e}")

    # Chat Interface
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            # Display execution trace if present
            if "trace" in message and message["trace"]:
                with st.expander("Auditable Execution Summary", expanded=False):
                    st.json(message["trace"])

    # React to user input
    if prompt := st.chat_input("Ask a question about the uploaded imagery..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate response
        if not uploaded_files:
            response = "Please upload some satellite imagery first using the sidebar."
            trace = None
        elif file_metadata and file_metadata["status"] != "valid":
            response = "Cannot process query. Uploaded files have an invalid configuration."
            trace = None
        else:
            with st.spinner("Agentic Controller is thinking..."):
                try:
                    result = process_query(prompt, file_metadata)
                    response = f"**Agent Reasoning:** {result.get('reasoning', 'No reasoning provided.')}"
                    trace = {
                        "Selected Task": result.get("selected_task", "N/A"),
                        "Tools Used": result.get("tools_used", "N/A"),
                        "Confidence Score": result.get("confidence_score", "N/A"),
                        "Input Modality": result.get("modality", "Unknown"),
                        "File Metadata": file_metadata.get("metadata", [])
                    }
                except Exception as e:
                    response = f"Error processing query: {str(e)}"
                    trace = None

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            st.markdown(response)
            if trace:
                st.info("Query successfully routed by Agentic Controller.")
                with st.expander("Auditable Execution Summary", expanded=True):
                    st.write(f"**Selected Task:** {trace['Selected Task']}")
                    st.write(f"**Tools Used:** {trace['Tools Used']}")
                    st.write(f"**Confidence:** {trace['Confidence Score']}")
                    st.write(f"**Modality:** {trace['Input Modality']}")
                    st.markdown("---")
                    st.write("**Image Metadata Extracted:**")
                    for meta in trace["File Metadata"]:
                        st.json(meta)
                    
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response, "trace": trace})

if __name__ == "__main__":
    main()
