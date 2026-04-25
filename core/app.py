import streamlit as st
import time

from ingestion import pdf_to_text, docx_to_text, txt_to_text
from prompt_template import create_optimal_prompt
from llm_handler import Llm_handler


st.set_page_config(
    page_title="ShiftLeft.ai",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed"
)

def initialize_session_states():
    default = {
        "user_story":"",
        "user_story_text":"",
        "is_generating": False,
        "show_test_case_types": False
    }

    for k, v in default.items():
        if k not in st.session_state:
            st.session_state[k] = v

def generate_answer(user_story: str) -> str:
    st.session_state.user_story_text = user_story

    status = st.empty()

    status.info("Model is analyzing story")

    st.session_state.is_generating = True
    # time.sleep(2)

    prompt = create_optimal_prompt(user_story)
    status.info("Model is determinal optimal coverage")
    return ""


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

col1, col2, col3 = st.columns(3)

with col1:
    generate_suite = ""
    generate_suite = st.radio(
        label="Outputs", 
        options=["Gherkin", "Test cases"], 
        index=0, 
        key="radio_options", 
        help="Select if you want gherkin or test cases.", 
        label_visibility="collapsed",
        horizontal=True
    )

with col2:
    is_test_cases = "Test" in generate_suite
    
    with st.expander("Test case types", expanded=False):
        if is_test_cases:
            test_types = st.multiselect(
                "Select types",
                options=["Functional", "Edge Case", "Negative", "Regression"],
                default=["Functional"],
                key="test_types"
            )
        else:
            st.caption("⚠️ Only available for Test cases output.")

with col3:
    generate_button = st.button("Generate", use_container_width=True, type="primary")

with st.container(height=500):
    if generate_button:
        if not user_story or len(user_story) < 20:
            st.error("Enter detailed user story.")
        else:
            results = generate_answer(user_story)