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
        "stage": "input",
        "user_story": "",
        "user_story_text": "",
        "test_types": "",
        "ac_items": [],
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
    generate_button = st.button("Generate", width="stretch", type="primary")

def _go(stage: str):
    st.session_state.stage = stage
    st.rerun()

with st.container():

    # --- STAGE 1: input -> call 1 (story -> AC) ---
    if st.session_state.stage == "input":
        if generate_button:
            if not user_story or len(user_story) < 20:
                st.error("Enter a detailed user story (at least 20 characters).")
            else:
                st.session_state.user_story_text = user_story
                try:
                    llm = get_llm_handler()
                    with st.spinner("Enumerating acceptance criteria..."):
                        messages = create_llm_messages_ac(user_story=user_story)
                        ac = llm.generate_ac(message=messages)
                    st.session_state.ac_items = [c.model_dump() for c in ac.items]
                    logger.info("Generated %d acceptance criteria", len(ac.items))
                    _go("review")
                except Exception as e:
                        st.error(f"AC generation failed: {str(e)}")

    elif st.session_state.stage == "review":
        st.subheader("Review acceptance criteria")
        st.caption(
            "Edit, add, or delete criteria before spending the second call. "
        )
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
        c1, c2 = st.columns(2)
        if c1.button("← Back / regenerate", width="stretch"):
            st.session_state.ac_items = []
            _go("input")

        if c2.button("Generate scenarios →", type="primary", width="stretch"):
            # Drop empty rows, then renumber so ids stay contiguous after edits/deletes.
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
                                st.session_state.user_story_text, clean
                            )
                        )
                    st.session_state.feature = feature
                    st.session_state.download_basename = (
                        feature.name.lower().replace(" ", "_") or "feature"
                    )
                    logger.info("Generated %d scenarios", len(feature.scenarios))
                    _go("output")
                except Exception as e:
                    st.error(f"Scenario generation failed: {str(e)}")

    # --- STAGE 3: output + coverage check ---
    elif st.session_state.stage == "output":
        feature = st.session_state.feature
        ac_ids = {a["id"] for a in st.session_state.ac_items}
        covered = {v for sc in feature.scenarios for v in sc.verifies}

        gaps = sorted(ac_ids - covered, key=lambda x: (len(x), x))
        if gaps:
            st.warning(f"No scenario covers: {', '.join(gaps)}")
        else:
            st.success(
                f"All {len(ac_ids)} criteria covered by {len(feature.scenarios)} scenarios."
            )

        # Flag any verifies pointing at ids the user did not approve.
        stray = sorted({v for v in covered if v not in ac_ids})
        if stray:
            st.info(f"Scenarios reference unknown AC ids: {', '.join(stray)}")

        st.code(feature_to_gherkin(feature), language="gherkin")

        if st.button("<- Start over", width="stretch"):
            st.session_state.feature = None
            st.session_state.ac_items = []
            _go("input")



# Download buttons live outside and below the container.
# They render whenever a result exists in session state.
if st.session_state.stage == "output" and st.session_state.feature is not None:
    feature = st.session_state.feature
    safe = st.session_state.download_basename or "feature"
    dl1, dl2, dl3 = st.columns(3)
    with dl1:
        st.download_button(
            "Download .feature",
            feature_to_gherkin(feature),
            file_name=f"{safe}.feature",
            mime="text/plain",
            width="stretch",
        )
    with dl3:
        st.download_button(
            "Download test cases (CSV)",
            feature_to_csv(feature),
            file_name=f"{safe}_testcases.csv",
            mime="text/csv",
            width="stretch",
        )
