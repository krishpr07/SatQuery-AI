import streamlit as st

def set_space_theme():
    """Applies a space-themed CSS styling to the Streamlit app."""
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #0b0c10;
            color: #c5c6c7;
            background-image: url('https://images.unsplash.com/photo-1462331940025-496dfbfc7564?q=80&w=2048&auto=format&fit=crop');
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }
        h1, h2, h3, p, span {
            color: #ffffff !important;
            text-shadow: 0px 0px 5px rgba(102,252,241,0.8);
        }
        /* Glassmorphism for the form */
        [data-testid="stForm"] {
            background: rgba(11, 12, 16, 0.5);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-radius: 15px;
            border: 1px solid rgba(102, 252, 241, 0.3);
            padding: 2rem;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        }
        .stButton>button {
            background: rgba(102, 252, 241, 0.1);
            color: #66fcf1 !important;
            border-radius: 8px;
            border: 1px solid #66fcf1;
            font-weight: bold;
            transition: all 0.3s ease 0s;
            text-shadow: none;
        }
        .stButton>button:hover {
            background-color: #66fcf1;
            color: #0b0c10 !important;
            box-shadow: 0px 0px 15px rgba(102,252,241,0.6);
            transform: translateY(-2px);
        }
        .stTextInput>div>div>input {
            background-color: rgba(31, 40, 51, 0.6);
            color: #ffffff;
            border: 1px solid #45a29e;
            border-radius: 5px;
        }
        .stTextInput>div>div>input:focus {
            box-shadow: 0px 0px 10px rgba(102,252,241,0.4);
            border-color: #66fcf1;
        }
        .stFileUploader>div>div>div>button {
            color: #66fcf1;
        }
        /* Style the sidebar */
        [data-testid="stSidebar"] {
            background-color: rgba(18, 21, 28, 0.85);
            backdrop-filter: blur(10px);
            border-right: 1px solid rgba(69, 162, 158, 0.5);
        }
        /* Chat messages */
        .stChatMessage {
            background: rgba(31, 40, 51, 0.6);
            backdrop-filter: blur(10px);
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
            border: 1px solid rgba(69, 162, 158, 0.4);
            box-shadow: 0 4px 15px 0 rgba(0, 0, 0, 0.2);
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def login_page():
    """Displays the login page."""
    st.title("🚀 SatQuery Space Portal Login")
    st.markdown("Welcome to the SatQuery Space Station. Please authenticate to continue.")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            username = st.text_input("Astronaut ID (Username)", placeholder="Enter 'admin'")
            password = st.text_input("Access Code (Password)", type="password", placeholder="Enter 'admin'")
            submitted = st.form_submit_button("Engage Thrusters (Login)")
            
            if submitted:
                if username == "admin" and password == "admin":
                    st.session_state["authenticated"] = True
                    st.rerun()
                else:
                    st.error("Authentication failed. Invalid ID or Code. Try admin/admin")
