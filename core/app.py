import streamlit as st
import time
import logging
import json
from pydantic import ValidationError

from ingestion import pdf_to_text, docx_to_text, txt_to_text
from prompt_template import create_llm_messages_ac, create_scenario_messages
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
        "ac_items":[],
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

# with col1:
#     generate_suite = ""
#     generate_suite = st.radio(
#         label="Outputs", 
#         options=["Gherkin", "Test cases"], 
#         index=0, 
#         key="radio_options", 
#         help="Select if you want gherkin or test cases.", 
#         label_visibility="collapsed",
#         horizontal=True
#     )

# with col2:
#     is_test_cases = "Test" in generate_suite
    
#     with st.expander("Test case types", expanded=False):
#         if is_test_cases:
#             test_types = st.multiselect(
#                 "Select types",
#                 options=["Functional", "Edge Case", "Negative", "Regression"],
#                 default=["Functional"],
#                 key="test_types"
#             )
#         else:
#             st.caption("⚠️ Only available for Test cases output.")

with col3:
    generate_button = st.button("Generate", use_container_width=True, type="primary")

with st.container():
    # --- Stage 1: generate ACs (only runs the rerun after "Generate" is clicked) ---
    if generate_button:
        if not user_story or len(user_story) < 20:
            st.error("Enter detailed user story.")
        else:
            messages = create_llm_messages_ac(user_story=user_story)
            try:
                llm = get_llm_handler()
                with st.spinner("Generating acceptance criteria..."):
                    ac = llm.generate_ac(messages)
                    logger.info(ac)
                st.session_state.ac_items = [item.model_dump() for item in ac.items]
                st.session_state.feature = None          # clear any stale feature
                st.session_state.user_story_saved = user_story   # keep the story for call 2
                st.success(f"Generated {len(ac.items)} acceptance criteria.")
            except json.JSONDecodeError:
                st.error("Model returned malformed JSON. Try again.")
            except ValidationError as e:
                st.error(f"Output didn't match schema: {e}")
            except Exception as e:
                st.error(f"Generation failed: {str(e)}")

    # --- Stage 2: review + scenario generation (runs whenever ACs exist in state) ---
    if st.session_state.ac_items:
        st.subheader("Review acceptance criteria")
        st.caption("Edit, add, or delete criteria before spending the second call.")

        edited = st.data_editor(
            st.session_state.ac_items,
            num_rows="dynamic",
            width="stretch",
            key="ac_editor",
            column_config={
                "id": st.column_config.TextColumn("AC ID", width="small"),
                "text": st.column_config.TextColumn("Acceptance criterion", width="large"),
            },
        )

        c1, _, c2 = st.columns(3)
        if c1.button("← Back / regenerate"):
            st.session_state.ac_items = []
            st.session_state.feature = None
            st.rerun()

        if c2.button("Generate scenarios →", type="primary", width="stretch"):
            clean = [r for r in edited if r.get("text", "").strip()]
            for i, r in enumerate(clean, start=1):
                r["id"] = f"AC{i}"
            st.session_state.ac_items = clean

            if not clean:
                st.error("Add at least one acceptance criterion before continuing.")
            else:
                try:
                    with st.spinner("Generating scenarios..."):
                        feature = get_llm_handler().generate_feature(
                            create_scenario_messages(
                                st.session_state.user_story_saved, clean
                            )
                        )
                    st.session_state.feature = feature
                    st.session_state.download_basename = (
                        feature.name.lower().replace(" ", "_") or "feature"
                    )
                    logger.info("Generated %d scenarios", len(feature.scenarios))
                except Exception as e:
                    st.error(f"Scenario generation failed: {str(e)}")

    # --- Stage 3: display the feature (runs whenever a feature exists in state) ---
    if st.session_state.get("feature"):
        st.subheader("Generated feature")
        st.write(st.session_state.feature)

            

# Download buttons live outside and below the container.
# They render whenever a result exists in session state.
# if st.session_state.get("gherkin_text"):
#     safe = st.session_state["download_basename"]
#     dl_col1, dl_col2 = st.columns(2)
#     with dl_col1:
#         st.download_button(
#             "Download .feature",
#             st.session_state["gherkin_text"],
#             file_name=f"{safe}.feature",
#             mime="text/plain",
#             use_container_width=True,
#         )
#     with dl_col2:
#         st.download_button(
#             "Download test cases (CSV)",
#             st.session_state["csv_text"],
#             file_name=f"{safe}_testcases.csv",
#             mime="text/csv",
#             use_container_width=True,
#         )