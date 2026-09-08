import os
import hashlib
from io import BytesIO

import streamlit as st
from PIL import Image
from google import genai
from google.genai import types
from groq import Groq


st.set_page_config(
    page_title="Multi-Agent AI Debate + Vision",
    page_icon="⚖️",
    layout="centered",
)

st.title("I might be him AI(not a scam btw)")
st.caption(
    "Upload an image or document. Agent A proposes, Agent B critiques, "
    "and Gemini delivers a synthesized consensus verdict."
)



if "messages" not in st.session_state:
    st.session_state.messages = []
if "image_caption" not in st.session_state:
    st.session_state.image_caption = ""
if "active_file_bytes" not in st.session_state:
    st.session_state.active_file_bytes = None
if "active_file_type" not in st.session_state:
    st.session_state.active_file_type = None
if "file_hash" not in st.session_state:
    st.session_state.file_hash = None
if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

# Display prior chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "image" in message and message["image"] is not None:
            st.image(message["image"], width=300)


with st.sidebar:
    st.header("📂 Multimodal Inputs")
    
    # Image / Document Upload Form
    with st.form("multimodal_form", clear_on_submit=False):
        uploaded_file = st.file_uploader(
            "Upload an image or PDF", 
            type=["png", "jpg", "jpeg", "webp", "pdf"]
        )
        custom_image_prompt = st.text_area(
            "Prompt / Instructions for the upload:",
            placeholder="e.g., 'Extract all text' or 'Summarize key metrics.'",
            height=100
        )
        submit_button = st.form_submit_button("🚀 Submit File & Prompt")
        
    if submit_button:
        if uploaded_file is not None:
            file_bytes = uploaded_file.read()
            file_type = uploaded_file.type
            current_hash = hashlib.sha256(file_bytes).hexdigest()
            
            if st.session_state.file_hash != current_hash:
                st.session_state.file_hash = current_hash
                st.session_state.active_file_bytes = file_bytes
                st.session_state.active_file_type = file_type
                st.session_state.image_caption = ""
                
            prompt_text = custom_image_prompt.strip() or "Analyze this file, extract visible text, and describe its key elements."
            st.session_state.pending_prompt = prompt_text
            
            if "image" in file_type:
                st.image(st.session_state.active_file_bytes, caption="Active Image Upload", use_container_width=True)
            else:
                st.info(f"Uploaded Document: {uploaded_file.name}")
        else:
            st.warning("Please upload a file before submitting the form.")

chat_input = st.chat_input("Ask a follow-up question or continue the debate...")


active_prompt = None

if st.session_state.pending_prompt:
    active_prompt = st.session_state.pending_prompt
    st.session_state.pending_prompt = None
elif chat_input:
    active_prompt = chat_input

if active_prompt:
    groq_key = os.environ.get("GROQ_API_KEY")
    gemini_key = os.environ.get("GEMINI_API_KEY")

    if not groq_key or not gemini_key:
        st.error("Missing API keys. Please set `GROQ_API_KEY` and `GEMINI_API_KEY` in your environment.")
        st.stop()

    groq_client = Groq(api_key=groq_key)
    gemini_client = genai.Client(api_key=gemini_key)

    media_part = None
    pil_image = None

    if st.session_state.active_file_bytes:
        mime_type = st.session_state.active_file_type or "image/jpeg"
        if "image" in mime_type:
            pil_image = Image.open(BytesIO(st.session_state.active_file_bytes)).convert("RGB")
            media_part = pil_image
        else:
            media_part = types.Part.from_bytes(
                data=st.session_state.active_file_bytes,
                mime_type=mime_type
            )

    history_context = ""
    recent_messages = st.session_state.messages[-4:] 
    for msg in recent_messages:
        role_label = "User" if msg["role"] == "user" else "Assistant (Consensus)"
        history_context += f"{role_label}: {msg['content']}\n\n"

    user_message_store = {"role": "user", "content": active_prompt}
    if pil_image and not st.session_state.image_caption:
        user_message_store["image"] = st.session_state.active_file_bytes

    st.session_state.messages.append(user_message_store)
    with st.chat_message("user"):
        st.markdown(active_prompt)
        if "image" in user_message_store:
            st.image(user_message_store["image"], width=300)


    with st.chat_message("assistant"):
        with st.status("🧠 Multi-agent debate in progress...", expanded=True) as status:
            try:
                # 1. Gemini Visual Analysis (if applicable)
                if media_part and not st.session_state.image_caption:
                    st.write("👁️ **Gemini** is analyzing media content...")

                    analysis_instructions = f"""
                    Analyze the provided file according to the user's specific request below.
                    Extract text accurately and organize details logically.

                    User Request:
                    "{active_prompt}"
                    """

                    caption_response = gemini_client.models.generate_content(
                        model="models/gemini-3.6-flash",
                        contents=[media_part, analysis_instructions]
                    )
                    st.session_state.image_caption = caption_response.text

                vision_modifier = ""
                if st.session_state.image_caption:
                    vision_modifier = f"\n\n[Visual/Document Analysis]:\n{st.session_state.image_caption}"

                full_user_prompt = f"{active_prompt}{vision_modifier}"

                
                st.write("🤖 **Agent A** is drafting a proposal...")
                chat_a = groq_client.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    messages=[
                        {
                            "role": "system",
                            "content": f"You are Agent A. Propose a rigorous, direct solution. Prior conversation context:\n{history_context}",
                        },
                        {"role": "user", "content": full_user_prompt},
                    ],
                )
                proposal_a = chat_a.choices[0].message.content

               
                st.write("🔍 **Agent B** is auditing the proposal...")
                chat_b = groq_client.chat.completions.create(
                    model="openai/gpt-oss-20b",
                    messages=[
                        {
                            "role": "system",
                            "content": f"You are Agent B. Identify any logical fallacies, edge cases, or missing constraints in this proposal:\n\n{proposal_a}",
                        },
                        {"role": "user", "content": full_user_prompt},
                    ],
                )
                critique_b = chat_b.choices[0].message.content

                
                st.write("⚖️ **Gemini Judge** is synthesizing consensus...")
                judge_prompt = f"""
You are the Lead Judge AI synthesizing a multi-agent debate into a coherent, final response.

Prior Conversation Context:
{history_context}

User Prompt:
{active_prompt}

Agent A (Proposal):
{proposal_a}

Agent B (Critique):
{critique_b}

Task:
Deliver a comprehensive, final answer addressing the user's prompt directly. Inspect the attached media content to verify claims made by Agent A and critiques made by Agent B. Resolve conflicts and deliver an ironclad consensus.
"""
                judge_contents = [judge_prompt]
                if media_part:
                    judge_contents.insert(0, media_part)

                gemini_response = gemini_client.models.generate_content(
                    model="models/gemini-3.6-flash",
                    contents=judge_contents,
                )
                final_verdict = gemini_response.text

                status.update(label="✅ Consensus reached!", state="complete", expanded=False)

            except Exception as e:
                status.update(label="❌ Error during processing", state="error", expanded=True)
                st.error(f"An error occurred: {str(e)}")
                st.stop()

        # Expandable Agent Collapsibles for review
        with st.expander("🤖 View Agent A Proposal"):
            st.markdown(proposal_a)

        with st.expander("🔍 View Agent B Critique"):
            st.markdown(critique_b)

        # Render final synthesized verdict
        st.markdown(final_verdict)

        # Save to history
        st.session_state.messages.append({
            "role": "assistant",
            "content": final_verdict
        })