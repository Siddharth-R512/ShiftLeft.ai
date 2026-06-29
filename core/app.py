import streamlit as st
import time
import logging
import json
from pydantic import ValidationError

from ingestion import pdf_to_text, docx_to_text, txt_to_text
from prompt_template import create_llm_messages
from llm_handler import Llm_handler
from render import feature_to_gherkin, feature_to_csv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s -%(message)s'
)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="ShiftLeft.ai",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed"
)

def initialize_session_states():
    """
    Initialize streamlit's session state variables.
    """
    default = {
        "user_story": "",
        "user_story_text": "",
        "is_generating": False,
        "show_test_case_types": False,
        "llm_response": "",
        "test_types": "",
        "gherkin_text": "",
        "csv_text": "",
        "download_basename": "",
    }

    for k, v in default.items():
        if k not in st.session_state:
            st.session_state[k] = v

initialize_session_states()

@st.cache_resource
def get_llm_handler():
    """
    Cached initialization of the LLM handler.
    The handler and its Groq client are created once and reused across app reruns.
    """
    return Llm_handler()

def generate_answer(user_story: str, output_type: str = "Gherkin", test_types: list = None):
    """
    
    """
    st.session_state.user_story_text = user_story

    status = st.empty()

    status.info("Model is analyzing story")

    st.session_state.is_generating = True
    # time.sleep(2)

    messages = create_llm_messages(user_story, output_type, test_types)
    

    try:
        status.info("Model is determining optimal coverage")
        llm = get_llm_handler()
        status.success("Ready to generate output...")
        # Return the generator for streaming
        return status, llm.generate_output(messages, output_type)
    
    except Exception as e:
        status.error(f"Error processing output: {str(e)}")
        return None, None

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
            extracted = pdf_to_text(uploaded_file)
        elif file_extension == "docx":
            extracted = docx_to_text(uploaded_file)
        elif file_extension == "txt":
            extracted = txt_to_text(uploaded_file)

        st.session_state["user_story_text_area"] = extracted
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
            test_types_list = st.session_state.get("test_types", ["Functional"]) if is_test_cases else None
            messages = create_llm_messages(user_story, generate_suite, test_types_list)
            try:
                llm = get_llm_handler()
                with st.spinner("Generating scenarios..."):
                    feature = llm.generate_feature(messages)
                    logger.info(feature)

                st.success(f"Generated {len(feature.scenarios)} scenarios.")

                gherkin_text = feature_to_gherkin(feature)
                st.code(gherkin_text, language="gherkin")

                # Persist results so the download buttons survive reruns
                safe = feature.name.lower().replace(" ", "_")
                st.session_state["gherkin_text"] = gherkin_text
                st.session_state["csv_text"] = feature_to_csv(feature)
                st.session_state["download_basename"] = safe
            except json.JSONDecodeError:
                st.error("Model returned malformed JSON. Try again.")
            except ValidationError as e:
                st.error(f"Output didn't match schema: {e}")
            except Exception as e:
                st.error(f"Generation failed: {str(e)}")

# Download buttons live outside and below the container.
# They render whenever a result exists in session state.
if st.session_state.get("gherkin_text"):
    safe = st.session_state["download_basename"]
    dl_col1, dl_col2 = st.columns(2)
    with dl_col1:
        st.download_button(
            "Download .feature",
            st.session_state["gherkin_text"],
            file_name=f"{safe}.feature",
            mime="text/plain",
            use_container_width=True,
        )
    with dl_col2:
        st.download_button(
            "Download test cases (CSV)",
            st.session_state["csv_text"],
            file_name=f"{safe}_testcases.csv",
            mime="text/csv",
            use_container_width=True,
        )