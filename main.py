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
from typing import Dict, List, Union, Any, Tuple

# Constants
HISTORY_DIR = Path("thread_history")
IMAGE_DIR = Path("uploaded_images")
AVATARS = {"user": "🧑‍⚕️", "assistant": "🤖"}

# System prompts
SYSTEM_PROMPTS = {
    "Data Scientist": """<SYSTEM PROMPT>
        You are an expert in Python development, including its core libraries, popular frameworks like Flask, Streamlit and FastAPI, data science libraries such as NumPy and Pandas, and testing frameworks like pytest. You excel at selecting the best tools for each task, always striving to minimize unnecessary complexity and code duplication.
        When making suggestions, you break them down into discrete steps, recommending small tests after each stage to ensure progress is on the right track.
        You provide code examples when illustrating concepts or when specifically asked. However, if you can answer without code, that is preferred. You're open to elaborating if requested.
        Before writing or suggesting code, you conduct a thorough review of the existing codebase, describing its functionality between <CODE_REVIEW> tags. After the review, you create a detailed plan for the proposed changes, enclosing it in <PLANNING> tags. You pay close attention to variable names and string literals, ensuring they remain consistent unless changes are necessary or requested. When naming something by convention, you surround it with double colons and use ::UPPERCASE::.
        Your outputs strike a balance between solving the immediate problem and maintaining flexibility for future use.
        You always seek clarification if anything is unclear or ambiguous. You pause to discuss trade-offs and implementation options when choices arise.
        It's crucial that you adhere to this approach, teaching your conversation partner about making effective decisions in Python development. You avoid unnecessary apologies and learn from previous interactions to prevent repeating mistakes.
        You are highly conscious of security concerns, ensuring that every step avoids compromising data or introducing vulnerabilities. Whenever there's a potential security risk (e.g., input handling, authentication management), you perform an additional review, presenting your reasoning between <SECURITY_REVIEW> tags.
        Lastly, you consider the operational aspects of your solutions. You think about how to deploy, manage, monitor, and maintain Python applications. You highlight relevant operational concerns at each step of the development process. Answer in the language of the following user prompt.
        <END OF SYSTEM PROMPT>""",
    "Default": ""}


def init_directories():
    """Initialize necessary directories for storing thread history and images."""
    HISTORY_DIR.mkdir(exist_ok=True)
    IMAGE_DIR.mkdir(exist_ok=True)


def load_threads() -> Dict[str, Dict[str, Any]]:
    """
    Load all conversation threads from the history directory.

    Returns:
        Dict[str, Dict[str, Any]]: A dictionary of thread IDs to thread data
    """
    threads = {}
    for file_path in HISTORY_DIR.glob("*.json"):
        with open(str(file_path), 'r') as f:
            thread_data = json.load(f)
            threads[thread_data["id"]] = thread_data
    return threads


def save_thread(thread_id: str, messages: List[Dict[str, Any]]) -> None:
    """
    Save a conversation thread to disk.

    Args:
        thread_id (str): The unique identifier for the thread
        messages (List[Dict[str, Any]]): The messages in the thread
    """
    thread_data = {
        "id": thread_id,
        "last_updated": datetime.now().isoformat(),
        "messages": messages
    }
    file_path = HISTORY_DIR / f"{thread_id}.json"
    with open(str(file_path), 'w') as f:
        json.dump(thread_data, f)


def create_new_thread() -> Tuple[str, Dict[str, Any]]:
    """
    Create a new conversation thread.

    Returns:
        Tuple[str, Dict[str, Any]]: The thread ID and thread data
    """
    thread_id = str(uuid.uuid4())
    thread_data = {
        "id": thread_id,
        "last_updated": datetime.now().isoformat(),
        "messages": []
    }
    save_thread(thread_id, [])
    return thread_id, thread_data


def delete_thread(thread_id: str, threads: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Delete a conversation thread.

    Args:
        thread_id (str): The ID of the thread to delete
        threads (Dict[str, Dict[str, Any]]): The current threads dictionary

    Returns:
        Dict[str, Dict[str, Any]]: The updated threads dictionary
    """
    if thread_id in threads:
        del threads[thread_id]
        file_path = HISTORY_DIR / f"{thread_id}.json"
        if os.path.exists(str(file_path)):
            os.remove(str(file_path))
    return threads


def save_uploaded_image(image_file) -> str:
    """
    Save an uploaded image and return its filename.

    Args:
        image_file: The uploaded image file

    Returns:
        str: The filename of the saved image
    """
    image_bytes = image_file.getvalue()
    image_hash = hashlib.md5(image_bytes).hexdigest()
    image_ext = image_file.type.split('/')[-1]
    image_filename = f"{image_hash}.{image_ext}"
    image_path = IMAGE_DIR / image_filename

    if not image_path.exists():
        Image.open(io.BytesIO(image_bytes)).save(str(image_path))

    return image_filename


def display_message(message: Dict[str, Any]):
    """
    Display a chat message in the Streamlit interface.

    Args:
        message (Dict[str, Any]): The message to display
    """
    if isinstance(message["content"], list):
        for content in message["content"]:
            if content["type"] == "text":
                st.markdown(content["text"])
            elif content["type"] == "image_url" and "filename" in content:
                image_path = str(IMAGE_DIR / content["filename"])
                if os.path.exists(image_path):
                    st.image(image_path)
    else:
        st.markdown(message["content"])


def prepare_message_content(content: Union[str, List[Dict[str, Any]]]) -> Union[str, List[Dict[str, Any]]]:
    """
    Prepare message content for the API request.

    Args:
        content: The message content to prepare

    Returns:
        The prepared message content
    """
    if not isinstance(content, list):
        return content

    api_content = []
    for item in content:
        if item["type"] == "text":
            api_content.append({"type": "text", "text": item["text"]})
        elif item["type"] == "image_url" and "filename" in item:
            image_path = str(IMAGE_DIR / item["filename"])
            if os.path.exists(image_path):
                with open(image_path, "rb") as img_file:
                    image_bytes = img_file.read()
                    image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                api_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
                })
    return api_content


def prepare_messages(thread_messages: List[Dict[str, Any]], mode: str) -> List[Dict[str, Any]]:
    """
    Prepare messages for the API request.

    Args:
        thread_messages (List[Dict[str, Any]]): The messages in the thread
        mode (str): The current chat mode

    Returns:
        List[Dict[str, Any]]: The prepared messages
    """
    messages = []
    system_prompt = SYSTEM_PROMPTS.get(mode, "")
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    for msg in thread_messages:
        api_message = {"role": msg["role"]}
        api_message["content"] = prepare_message_content(msg["content"])
        messages.append(api_message)

    return messages


def setup_sidebar(threads: Dict[str, Dict[str, Any]]) -> Tuple[str, Dict[str, Dict[str, Any]]]:
    """
    Set up the sidebar interface.

    Args:
        threads (Dict[str, Dict[str, Any]]): The current threads dictionary

    Returns:
        Tuple[str, Dict[str, Dict[str, Any]]]: The selected mode and updated threads
    """
    with st.sidebar:
        mode = st.radio("Choose a mode:", ("Default", "Data Scientist"), index=0)

        st.divider()
        st.title("Thread history")

        if st.button("New Thread"):
            thread_id, thread_data = create_new_thread()
            threads[thread_id] = thread_data
            st.session_state.current_thread_id = thread_id
            st.rerun()

        display_thread_history(threads)

    return mode, threads


def display_thread_history(threads: Dict[str, Dict[str, Any]]):
    """
    Display the thread history in the sidebar.

    Args:
        threads (Dict[str, Dict[str, Any]]): The threads to display
    """
    st.subheader("Previous Threads")
    for thread_id, thread_data in sorted(
            threads.items(),
            key=lambda x: x[1]["last_updated"],
            reverse=True):
        display_thread_button(thread_id, thread_data, threads)


def display_thread_button(thread_id: str, thread_data: Dict[str, Any], threads: Dict[str, Dict[str, Any]]):
    """
    Display a button for a thread in the sidebar.

    Args:
        thread_id (str): The ID of the thread
        thread_data (Dict[str, Any]): The thread data
        threads (Dict[str, Dict[str, Any]]): The current threads dictionary
    """
    last_updated = datetime.fromisoformat(thread_data["last_updated"]).strftime("%Y-%m-%d %H:%M")
    preview = get_thread_preview(thread_data)

    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button(f"{last_updated}: {preview}", key=thread_id):
            st.session_state.current_thread_id = thread_id
    with col2:
        if st.button("❌", key=f"delete_{thread_id}"):
            threads = delete_thread(thread_id, threads)
            st.rerun()


def get_thread_preview(thread_data: Dict[str, Any]) -> str:
    """
    Get a preview of the thread content.

    Args:
        thread_data (Dict[str, Any]): The thread data

    Returns:
        str: A preview of the thread content
    """
    if not thread_data["messages"]:
        return "Empty thread"

    first_message = thread_data["messages"][0]["content"]
    if isinstance(first_message, str):
        return first_message[:30] + "..."
    return "Image thread"


def process_files(prompt: str, text_files, image_files) -> Tuple[str, List[Dict[str, str]]]:
    """
    Process uploaded text and image files.

    Args:
        prompt (str): The user's prompt
        text_files: Uploaded text files
        image_files: Uploaded image files

    Returns:
        Tuple[str, List[Dict[str, str]]]: The processed prompt and image data
    """
    display_prompt = process_text_files(prompt, text_files)
    image_data_list = process_image_files(image_files)
    return display_prompt, image_data_list


def process_text_files(prompt: str, text_files) -> str:
    """
    Process uploaded text files and append their content to the prompt.

    Args:
        prompt (str): The original prompt
        text_files: The uploaded text files

    Returns:
        str: The prompt with appended file content
    """
    if not text_files:
        return prompt

    display_prompt = prompt
    for uploaded_file in text_files:
        file_content = uploaded_file.read()
        try:
            decoded_content = file_content.decode('utf-8')
            display_prompt += f"\nAttached text file '{uploaded_file.name}':\n{decoded_content}"
        except UnicodeDecodeError:
            display_prompt += f"\nAttached binary file '{uploaded_file.name}':\n[Binary content encoded in base64]"

    return display_prompt


def process_image_files(image_files) -> List[Dict[str, str]]:
    """
    Process uploaded image files.

    Args:
        image_files: The uploaded image files

    Returns:
        List[Dict[str, str]]: A list of processed image data
    """
    image_data_list = []
    if image_files:
        for image_file in image_files:
            image_filename = save_uploaded_image(image_file)
            image_data_list.append({
                "filename": image_filename,
                "original_name": image_file.name
            })
    return image_data_list


def create_message_content(prompt: str, image_data_list: List[Dict[str, str]]):
    """
    Create the message content combining text and images.

    Args:
        prompt (str): The text prompt
        image_data_list (List[Dict[str, str]]): The list of image data

    Returns:
        Union[str, List[Dict[str, Any]]]: The created message content
    """
    if not image_data_list:
        return prompt

    message_content = [{"type": "text", "text": prompt}]
    for image_data in image_data_list:
        message_content.append({
            "type": "image_url",
            "filename": image_data["filename"]
        })
    return message_content


def handle_chat_input(client: OpenAI, thread: Dict[str, Any], text_files, image_files, mode: str):
    """
    Handle the chat input and generate a response.

    Args:
        client (OpenAI): The OpenAI client
        thread (Dict[str, Any]): The current thread
        text_files: Uploaded text files
        image_files: Uploaded image files
        mode (str): The current chat mode
    """
    if prompt := st.chat_input("What's on your mind ? 🤔"):
        display_prompt, image_data_list = process_files(prompt, text_files, image_files)
        message_content = create_message_content(display_prompt, image_data_list)

        thread["messages"].append({"role": "user", "content": message_content})

        with st.chat_message("user", avatar=AVATARS["user"]):
            display_message({"content": message_content})

        messages = prepare_messages(thread["messages"], mode)

        with st.chat_message("assistant", avatar=AVATARS["assistant"]):
            stream = client.chat.completions.create(
                model=st.session_state.openai_model,
                messages=messages,
                stream=True)
            response = st.write_stream(stream)

        thread["messages"].append({"role": "assistant", "content": response})
        thread["last_updated"] = datetime.now().isoformat()
        save_thread(thread["id"], thread["messages"])


def initialize_session_state(model: str):
    """
    Initialize the session state variables.

    Args:
        model (str): The OpenAI model to use
    """
    if "current_thread_id" not in st.session_state:
        st.session_state.current_thread_id = None
    if "openai_model" not in st.session_state:
        st.session_state.openai_model = model


def main():
    """Main function to run the Streamlit app."""
    st.set_page_config(page_title="Tim LLM", page_icon="✨")
    api_key = st.secrets["openai_api_key"]
    model = "gpt-4o-mini"

    init_directories()
    initialize_session_state(model)

    client = OpenAI(api_key=api_key)
    threads = load_threads()

    mode, threads = setup_sidebar(threads)

    st.title(f"🤖 {model}")

    text_files = st.file_uploader("📄 Choose text files", type=None, accept_multiple_files=True)
    image_files = st.file_uploader("🌆 Choose image files", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

    if st.session_state.current_thread_id is None:
        thread_id, thread_data = create_new_thread()
        st.session_state.current_thread_id = thread_id
        threads[thread_id] = thread_data

    current_thread = threads[st.session_state.current_thread_id]

    # Display current thread messages
    for message in current_thread["messages"]:
        with st.chat_message(message["role"], avatar=AVATARS[message["role"]]):
            display_message(message)

    # Handle chat input
    handle_chat_input(client, current_thread, text_files, image_files, mode)


if __name__ == "__main__":
    main()