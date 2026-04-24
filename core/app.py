import streamlit as st
from ingestion import pdf_to_text, docx_to_text, txt_to_text

st.set_page_config(
    page_title="ShiftLeft.ai",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed"
)

def initialize_session_states():
    default = {
        "user_story":""
    }

    for k, v in default.items():
        if k not in st.session_state:
            st.session_state[k] = v


# Main App
st.header("Shift-Left.ai")

tab1, tab2 = st.tabs(["Text", "Upload File"])

with tab1:
    user_story =""

with tab2:
    uploaded_file = st.file_uploader(
        "Upload docx, pdf or txt file",
        type=["docx", "pdf", "txt"]
    )
if uploaded_file is not None:
    file_extension = uploaded_file.name.split(".")[-1].lower()
    try:
        if file_extension == "pdf":
            user_story = pdf_to_text(uploaded_file)
        elif file_extension == "docx":
            user_story = docx_to_text(uploaded_file)
        elif file_extension == "txt":
            user_story = txt_to_text(uploaded_file)

        user_story = st.text_area("Enter user story", value=user_story, height=300, key="user_story_text_area")
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        user_story = ""
else:
    user_story = st.text_area(
        "Enter user story",
        value=st.session_state.get("user_story_text_area", ""),
        height=300,
        key="user_story_text_area",
        placeholder="Enter any feature or story you want." \
        ""
    )

