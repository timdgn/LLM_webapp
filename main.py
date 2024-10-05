from openai import OpenAI
import streamlit as st
import base64
import json
import os
from datetime import datetime
import uuid
from pathlib import Path
import hashlib
from PIL import Image
import io

# Create directories for storing thread history and images
HISTORY_DIR = Path("thread_history")
IMAGE_DIR = Path("uploaded_images")
HISTORY_DIR.mkdir(exist_ok=True)
IMAGE_DIR.mkdir(exist_ok=True)

st.set_page_config(page_title="Tim LLM", page_icon="✨")

# Load the API key from Streamlit secrets
api_key = st.secrets["openai_api_key"]
client = OpenAI(api_key=api_key)

# Initialize session state variables
if "openai_model" not in st.session_state:
    st.session_state.openai_model = "gpt-4o-mini"
if "current_thread_id" not in st.session_state:
    st.session_state.current_thread_id = None
if "threads" not in st.session_state:
    st.session_state.threads = {}

def save_uploaded_image(image_file):
    image_bytes = image_file.getvalue()
    image_hash = hashlib.md5(image_bytes).hexdigest()
    image_ext = image_file.type.split('/')[-1]
    image_filename = f"{image_hash}.{image_ext}"
    image_path = IMAGE_DIR / image_filename
    if not image_path.exists():
        Image.open(io.BytesIO(image_bytes)).save(str(image_path))
    return image_filename  # Return just the filename, not the full path

def save_thread(thread_id, messages):
    thread_data = {
        "id": thread_id,
        "last_updated": datetime.now().isoformat(),
        "messages": messages
    }
    file_path = HISTORY_DIR / f"{thread_id}.json"
    with open(str(file_path), 'w') as f:
        json.dump(thread_data, f)

def load_threads():
    threads = {}
    for file_path in HISTORY_DIR.glob("*.json"):
        with open(str(file_path), 'r') as f:
            thread_data = json.load(f)
            threads[thread_data["id"]] = thread_data
    return threads

def display_message(message):
    if isinstance(message["content"], list):
        for content in message["content"]:
            if isinstance(content, dict):
                if content["type"] == "text":
                    st.markdown(content["text"])
                elif content["type"] == "image_url" and "filename" in content:
                    image_path = str(IMAGE_DIR / content["filename"])
                    if os.path.exists(image_path):
                        st.image(image_path)
    else:
        st.markdown(message["content"])

# Load existing threads
st.session_state.threads = load_threads()

# Sidebar for thread management and mode selection
with st.sidebar:
    # Mode selection
    st.title("Mode Selection")
    mode = st.radio(
        "Choose a mode:",
        ("Default", "Data Scientist"),
        index=0)

    st.divider()

    st.title("Thread history")

    # New thread button
    if st.button("New Thread"):
        st.session_state.current_thread_id = str(uuid.uuid4())
        st.session_state.threads[st.session_state.current_thread_id] = {
            "id": st.session_state.current_thread_id,
            "last_updated": datetime.now().isoformat(),
            "messages": []
        }
        save_thread(st.session_state.current_thread_id, [])

    # Thread selection
    st.subheader("Previous Threads")
    for thread_id, thread_data in sorted(
            st.session_state.threads.items(),
            key=lambda x: x[1]["last_updated"],
            reverse=True):
        last_updated = datetime.fromisoformat(thread_data["last_updated"]).strftime("%Y-%m-%d %H:%M")

        if thread_data["messages"]:
            if isinstance(thread_data["messages"][0]["content"], str):
                preview = thread_data["messages"][0]["content"][:30] + "..."
            else:
                preview = "Image thread"
        else:
            preview = "Empty thread"

        col1, col2 = st.columns([3, 1])

        with col1:
            if st.button(f"{last_updated}: {preview}", key=thread_id):
                st.session_state.current_thread_id = thread_id

        with col2:
            if st.button("❌", key=f"delete_{thread_id}"):
                del st.session_state.threads[thread_id]
                file_path = HISTORY_DIR / f"{thread_id}.json"
                if os.path.exists(str(file_path)):
                    os.remove(str(file_path))
                st.rerun()

# Main chat interface
st.title(f"🤖 4o mini")

# File uploaders
text_files = st.file_uploader("Choose text files", type=None, accept_multiple_files=True)
image_files = st.file_uploader("Choose image files", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

# Process uploaded files
if text_files:
    st.session_state.files_content = []
    for uploaded_file in text_files:
        file_content = uploaded_file.read()
        try:
            decoded_content = file_content.decode('utf-8')
            st.session_state.files_content.append(f"\nAttached text file '{uploaded_file.name}':\n{decoded_content}")
        except UnicodeDecodeError:
            encoded_content = base64.b64encode(file_content).decode('utf-8')
            st.session_state.files_content.append(
                f"\nAttached binary file '{uploaded_file.name}':\n[Binary content encoded in base64]")

# Process uploaded images
image_data_list = []
if image_files:
    for image_file in image_files:
        image_filename = save_uploaded_image(image_file)
        image_path = str(IMAGE_DIR / image_filename)
        st.image(image_path)
        image_data_list.append({"filename": image_filename, "original_name": image_file.name})

# Ensure we have a current thread
if st.session_state.current_thread_id is None:
    st.session_state.current_thread_id = str(uuid.uuid4())
    st.session_state.threads[st.session_state.current_thread_id] = {
        "id": st.session_state.current_thread_id,
        "last_updated": datetime.now().isoformat(),
        "messages": []}
    save_thread(st.session_state.current_thread_id, [])

# Display current thread messages
current_thread = st.session_state.threads[st.session_state.current_thread_id]
for message in current_thread["messages"]:
    with st.chat_message(message["role"]):
        display_message(message)

# Chat input
if prompt := st.chat_input("Comment puis-je t'aider ?"):
    # Prepare mode prefix
    mode_prefix = ""
    if not current_thread["messages"] and mode == "Data Scientist":
        mode_prefix = """You are an expert in Python development..."""  # Add your full prefix here

    # Combine prompt with mode prefix and file contents
    full_prompt = mode_prefix + prompt
    if hasattr(st.session_state, 'files_content') and st.session_state.files_content:
        for file_content in st.session_state.files_content:
            full_prompt += file_content
        st.session_state.files_content = []

    # Prepare API message content
    if image_data_list:
        new_message_content = [{"type": "text", "text": full_prompt}]
        for image_data in image_data_list:
            image_path = str(IMAGE_DIR / image_data["filename"])
            with open(image_path, "rb") as img_file:
                image_bytes = img_file.read()
                image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            new_message_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
                "filename": image_data["filename"]})
    else:
        new_message_content = full_prompt

    # Add user message to thread
    current_thread["messages"].append({"role": "user", "content": new_message_content})

    # Display user message
    with st.chat_message("user"):
        display_message({"content": new_message_content})

    # Get and display assistant response
    with st.chat_message("assistant"):
        messages = [
            {"role": m["role"], "content": m["content"] if isinstance(m["content"], str) else next((item["text"] for item in m["content"] if isinstance(item, dict) and "text" in item), "")}
            for m in current_thread["messages"]]
        stream = client.chat.completions.create(
            model=st.session_state.openai_model,
            messages=messages,
            stream=True)
        response = st.write_stream(stream)

    # Add assistant response to thread
    current_thread["messages"].append({"role": "assistant", "content": response})

    # Update thread timestamp and save
    current_thread["last_updated"] = datetime.now().isoformat()
    save_thread(st.session_state.current_thread_id, current_thread["messages"])