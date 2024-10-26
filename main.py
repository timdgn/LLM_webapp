from openai import OpenAI
import streamlit as st
import base64
import json
from datetime import datetime
import uuid
import hashlib
from PIL import Image
import io
from typing import Dict, List, Union, Any, Tuple
import fitz
from glob import glob
import os
import requests
import shutil
import concurrent.futures

from constants import *


def init_directories():
    """Initialize necessary directories for storing thread history and images."""
    os.makedirs(THREADS_DIR, exist_ok=True)
    os.makedirs(UPLOADED_IMAGES_DIR, exist_ok=True)
    os.makedirs(GENERATED_IMAGES_DIR, exist_ok=True)


def load_threads() -> Dict[str, Dict[str, Any]]:
    """
    Load all conversation threads from the history directory.

    Returns:
        Dict[str, Dict[str, Any]]: A dictionary of thread IDs to thread data
    """
    threads = {}
    for file_path in glob(os.path.join(THREADS_DIR, "*.json")):
        with open(file_path, 'r') as f:
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
    file_path = os.path.join(THREADS_DIR, f"{thread_id}.json")
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(thread_data, f, indent=4, ensure_ascii=False)


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
    Delete a conversation thread and its associated files.

    Args:
        thread_id (str): The ID of the thread to delete
        threads (Dict[str, Dict[str, Any]]): The current threads dictionary

    Returns:
        Dict[str, Dict[str, Any]]: The updated threads dictionary
    """
    if thread_id in threads:
        thread_data = threads[thread_id]
        
        # Delete associated files
        for message in thread_data["messages"]:
            if isinstance(message["content"], list):
                for content in message["content"]:
                    if content["type"] == "image_url" and "filename" in content:
                        image_path = os.path.join(UPLOADED_IMAGES_DIR, content["filename"])
                        if os.path.exists(image_path):
                            os.remove(image_path)

        # Delete the thread data
        del threads[thread_id]
        
        # Delete the thread JSON file
        file_path = os.path.join(THREADS_DIR, f"{thread_id}.json")
        if os.path.exists(file_path):
            os.remove(file_path)

    return threads


def save_uploaded_image(image_file, thread_id: str) -> str:
    """
    Save an uploaded image and return its filename.

    Args:
        image_file: The uploaded image file
        thread_id (str): The ID of the current thread

    Returns:
        str: The filename of the saved image
    """
    image_bytes = image_file.getvalue()
    image_hash = hashlib.md5(image_bytes).hexdigest()
    image_ext = image_file.type.split('/')[-1]
    image_filename = f"{thread_id}_{image_hash}.{image_ext}"
    image_path = os.path.join(UPLOADED_IMAGES_DIR, image_filename)

    if not os.path.exists(image_path):
        Image.open(io.BytesIO(image_bytes)).save(image_path)

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
                image_path = os.path.join(UPLOADED_IMAGES_DIR, content["filename"])
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
            image_path = os.path.join(UPLOADED_IMAGES_DIR, item["filename"])
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


def setup_sidebar(threads: Dict[str, Dict[str, Any]]) -> Tuple[str, Dict[str, Dict[str, Any]], list, str, Dict[str, Any]]:
    """
    Set up the sidebar interface.

    Args:
        threads (Dict[str, Dict[str, Any]]): The current threads dictionary

    Returns:
        Tuple[str, Dict[str, Dict[str, Any]], list, str, Dict[str, Any]]:
        The selected mode, updated threads dictionary, uploaded files, selected tab, and DALL-E options
    """
    with st.sidebar:
        st.title("✨ Choose interaction type")
        interaction_type = st.radio("Interaction Type", list(INTERACTION_TYPES.values()), index=0, label_visibility="collapsed")
        
        st.write("")

        mode = list(SYSTEM_PROMPTS.keys())[0]
        uploaded_files = None
        dalle_options = {"size": "1024x1024",
                         "quality": "standard",
                         "n": 1}

        if interaction_type == INTERACTION_TYPES["chat"]:
            with st.container(border=True):
                st.title("⚙️ Select a mode")
                mode = st.radio(
                    "Mode", 
                    list(SYSTEM_PROMPTS.keys()),
                    index=0,
                    label_visibility="collapsed",
                    captions=["Perfect for conversations without specific expertise",
                             "Specialized in Python, data science and code review", 
                             "Specialized in generating detailed DALL-E prompts"])

                st.divider()

                st.title("📄🌆 Upload text, pdf or image files")
                uploaded_files = st.file_uploader("Upload files",
                                                  type=None,
                                                  accept_multiple_files=True,
                                                  key=st.session_state.file_uploader_key,
                                                  label_visibility="collapsed")

                st.divider()

                st.title("⏳ Thread history")
                if st.button("New Thread"):
                    thread_id, thread_data = create_new_thread()
                    threads[thread_id] = thread_data
                    st.session_state.current_thread_id = thread_id
                    st.rerun()
                display_thread_history(threads)

        elif interaction_type == INTERACTION_TYPES["image"]:
            with st.container(border=True):
                st.title("🖼️ DALL-E Options")
                dalle_options['size'] = st.selectbox("Image Size", ["1024x1024"], index=0)
                dalle_options['quality'] = st.selectbox("Image Quality", ["Standard", "HD"], index=0).lower()
                dalle_options['n'] = st.slider("Number of Images", min_value=1, max_value=4, value=1)

                st.title("🎨 Image Generation History")
                generations = load_image_generations()
                display_image_generation_history(generations)

        st.write("")

        with st.container(border=True):
            st.caption(f'By Timmothy Dangeon, PharmD & Healthcare Machine Learning Engineer')
            st.caption(f'Linkedin : linkedin.com/in/timdangeon')
            st.caption(f'Github : github.com/timdgn')

    return mode, threads, uploaded_files, interaction_type, dalle_options


def display_thread_history(threads: Dict[str, Dict[str, Any]]):
    """
    Display the thread history in the sidebar.

    Args:
        threads (Dict[str, Dict[str, Any]]): The threads to display
    """
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

    col1, col2, col3 = st.columns([0.6, 0.12, 0.1])
    with col1:
        if st.button(f"{last_updated}: {preview}", key=thread_id):
            st.session_state.current_thread_id = thread_id
    with col2:
        with st.popover("⬇️"):
            download_thread_export(thread_data, "txt")
            download_thread_export(thread_data, "json")
            download_thread_export(thread_data, "md")
            download_thread_export(thread_data, "csv")
    with col3:
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


def process_files(prompt: str, uploaded_files, thread_id: str) -> Tuple[str, List[Dict[str, str]]]:
    """
    Process uploaded files of all types.

    Args:
        prompt (str): The user's prompt
        uploaded_files: Uploaded files of any type
        thread_id (str): The ID of the current thread

    Returns:
        Tuple[str, List[Dict[str, str]]]: The processed prompt and image data
    """
    display_prompt = prompt
    image_data_list = []

    for uploaded_file in uploaded_files:
        if uploaded_file.type == "application/pdf":
            # Process PDF files
            pdf_document = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            pdf_text = ""
            for page in pdf_document:
                pdf_text += page.get_text()
            pdf_document.close()
            display_prompt += f"\nAttached PDF file '{uploaded_file.name}':\n{pdf_text}"

        elif uploaded_file.type.startswith("image/"):
            # Process image files
            image_filename = save_uploaded_image(uploaded_file, thread_id)
            image_data_list.append({
                "filename": image_filename,
                "original_name": uploaded_file.name})

        elif uploaded_file.type.startswith("text/"):
            # Process text files
            file_content = uploaded_file.read()
            try:
                decoded_content = file_content.decode('utf-8')
                display_prompt += f"\nAttached text file '{uploaded_file.name}':\n{decoded_content}"
            except UnicodeDecodeError:
                display_prompt += f"\nAttached binary file '{uploaded_file.name}':\n[Binary content encoded in base64]"

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


def handle_chat_input(client: OpenAI, thread: Dict[str, Any], uploaded_files, mode: str):
    """
    Handle the chat input and generate a response.

    Args:
        client (OpenAI): The OpenAI client
        thread (Dict[str, Any]): The current thread
        uploaded_files: Uploaded files
        mode (str): The current chat mode
    """
    if prompt := st.chat_input("What's on your mind ? 🤔"):

        st.session_state["file_uploader_key"] += 1  # To remove the files items after rerun

        display_prompt, image_data_list = process_files(prompt, uploaded_files, thread["id"])
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
        st.rerun()  # Rerun to remove the files items


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
    if "file_uploader_key" not in st.session_state:
        st.session_state["file_uploader_key"] = 0  # To remove the files items after rerun


def generate_images(client: OpenAI, dalle_options: Dict[str, Any]):
    """
    Generate images using DALL-E in parallel.

    Args:
        client (OpenAI): The OpenAI client
        dalle_options (Dict[str, Any]): Options for DALL-E image generation
    """

    prompt = st.session_state.prompt
    def generate_single_image(prompt):
        response = client.images.generate(model="dall-e-3",
                                          prompt=prompt,
                                          size=dalle_options['size'],
                                          quality=dalle_options['quality'])
        return response.data[0].url

    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(generate_single_image, prompt) for _ in range(dalle_options['n'])]
            image_urls = [future.result() for future in concurrent.futures.as_completed(futures)]
        st.session_state["image_urls"] = image_urls

    except Exception as e:
        st.error(f"Error generating images: {str(e)}")


def save_image_generation(prompt: str, image_urls: List[str]) -> str:
    """
    Save an image generation to the history.

    Args:
        prompt (str): The prompt used for generation
        image_urls (List[str]): List of generated image URLs

    Returns:
        str: The ID of the saved generation
    """
    generation_id = str(uuid.uuid4())
    
    # Create a folder for the images
    image_folder = os.path.join(GENERATED_IMAGES_DIR, generation_id)
    os.makedirs(image_folder, exist_ok=True)
    
    # Download and save the images
    image_paths = []
    for i, url in enumerate(image_urls):
        response = requests.get(url)
        image_path = os.path.join(image_folder, f"{i}.png")
        with open(image_path, "wb") as f:
            f.write(response.content)
        image_paths.append(image_path)

    generation_data = {
        "id": generation_id,
        "prompt": prompt,
        "image_paths": image_paths,  # Save local image paths instead of URLs
        "timestamp": datetime.now().isoformat()
    }
    file_path = os.path.join(GENERATED_IMAGES_DIR, f"{generation_id}.json")

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(generation_data, f, indent=4, ensure_ascii=False)
        
    return generation_id


def load_image_generations() -> List[Dict[str, Any]]:
    """
    Load all image generations from the history directory.

    Returns:
        List[Dict[str, Any]]: A list of image generation data
    """
    generations = []
    for file_path in glob(os.path.join(GENERATED_IMAGES_DIR, "*.json")):
        with open(file_path, 'r') as f:
            generation_data = json.load(f)
            generations.append(generation_data)
    return sorted(generations, key=lambda x: x["timestamp"], reverse=True)


def delete_image_generation(generation_id: str) -> None:
    """
    Delete an image generation from the history.

    Args:
        generation_id (str): The ID of the generation to delete
    """
    file_path = os.path.join(GENERATED_IMAGES_DIR, f"{generation_id}.json")
    if os.path.exists(file_path):
        os.remove(file_path)
        
    # Delete the image folder
    image_folder = os.path.join(GENERATED_IMAGES_DIR, generation_id)
    if os.path.exists(image_folder):
        shutil.rmtree(image_folder)


def display_image_generation_history(generations: List[Dict[str, Any]]):
    """
    Display the image generation history in the sidebar.

    Args:
        generations (List[Dict[str, Any]]): The generations to display
    """
    for generation in generations:
        timestamp = datetime.fromisoformat(generation["timestamp"]).strftime("%Y-%m-%d %H:%M")
        preview = generation["prompt"][:30] + "..."

        col1, col2, col3 = st.columns([3, 1, 0.5])
        with col1:
            with st.popover(f"{timestamp}: {preview}"):
                st.write(generation["prompt"])
                for image_path in generation["image_paths"]:
                    st.image(image_path, width=500)
        with col2:
            st.image(generation["image_paths"][0], width=75)
        with col3:
            if st.button("❌", key=f"delete_{generation['id']}"):
                delete_image_generation(generation['id'])
                st.rerun()


def export_thread(thread_data: Dict[str, Any], format: str = "txt") -> Tuple[str, str]:
    """
    Export thread data to various formats.
    
    Args:
        thread_data (Dict[str, Any]): The thread data to export
        format (str): Export format ('txt', 'json', 'md', or 'csv')
    
    Returns:
        Tuple[str, str]: (content, filename)
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"chat_export_{timestamp}.{format}"
    
    if format == "txt":
        content = "=== Chat Export ===\n"
        content += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        for msg in thread_data["messages"]:
            content += f"[{msg['role'].upper()}]\n"
            if isinstance(msg['content'], list):
                for item in msg['content']:
                    if item['type'] == 'text':
                        content += f"{item['text']}\n"
                    elif item['type'] == 'image_url':
                        content += f"[Image: {item.get('original_name', 'uploaded_image')}]\n"
            else:
                content += f"{msg['content']}\n"
            content += "\n" + "-"*50 + "\n\n"
    
    elif format == "json":
        content = json.dumps(thread_data, indent=2, ensure_ascii=False)
    
    elif format == "md":
        content = "# Chat Export\n\n"
        content += f"*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
        
        for msg in thread_data["messages"]:
            content += f"### {msg['role'].title()}\n\n"
            if isinstance(msg['content'], list):
                for item in msg['content']:
                    if item['type'] == 'text':
                        content += f"{item['text']}\n\n"
                    elif item['type'] == 'image_url':
                        content += f"![{item.get('original_name', 'uploaded_image')}]\n\n"
            else:
                content += f"{msg['content']}\n\n"
            content += "---\n\n"
    
    elif format == "csv":
        content = "Timestamp,Role,Content\n"
        for msg in thread_data["messages"]:
            if isinstance(msg['content'], list):
                msg_content = " ".join(
                    item['text'] if item['type'] == 'text' 
                    else f"[Image: {item.get('original_name', 'uploaded_image')}]"
                    for item in msg['content']
                )
            else:
                msg_content = msg['content']
            # Escape quotes and newlines for CSV
            msg_content = msg_content.replace('"', '""').replace('\n', ' ')
            content += f"{thread_data['last_updated']},{msg['role']},\"{msg_content}\"\n"
    
    else:
        raise ValueError(f"Unsupported export format: {format}")
        
    return content, filename

def download_thread_export(thread_data: Dict[str, Any], format: str):
    """
    Create a download button for thread export.
    
    Args:
        thread_data (Dict[str, Any]): The thread data to export
        format (str): Export format
    """
    content, filename = export_thread(thread_data, format)
    
    # Convert content to bytes
    if format == "json":
        bytes_data = content.encode('utf-8')
        mime = "application/json"
    elif format == "csv":
        bytes_data = content.encode('utf-8')
        mime = "text/csv"
    elif format == "md":
        bytes_data = content.encode('utf-8')
        mime = "text/markdown"
    else:  # txt
        bytes_data = content.encode('utf-8')
        mime = "text/plain"
    
    # Add a unique key using thread ID and format
    button_key = f"download_{thread_data['id']}_{format}"
    
    st.download_button(
        label=f"Download as {format.upper()}",
        data=bytes_data,
        file_name=filename,
        mime=mime,
        key=button_key  # Add the unique key here
    )


def main():
    """Main function to run the Streamlit app."""
    st.set_page_config(page_title="LLM Chat", page_icon="✨")
    api_key = st.secrets["openai_api_key"]
    model = "gpt-4o-mini"

    init_directories()
    initialize_session_state(model)

    client = OpenAI(api_key=api_key)
    threads = load_threads()

    mode, threads, uploaded_files, interaction_type, dalle_options = setup_sidebar(threads)

    if interaction_type == INTERACTION_TYPES["chat"]:
        st.title(f"🤖 {interaction_type}")

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
        handle_chat_input(client, current_thread, uploaded_files, mode)

    elif interaction_type == INTERACTION_TYPES["image"]:
        st.title(f"🎨 {interaction_type}")

        st.session_state.prompt = st.text_area("What do you want to create?", height=150, key="new_prompt")

        if st.button("Let's go ✨") and st.session_state.prompt:
            with st.spinner("Generating ..."):
                generate_images(client, dalle_options)
            if "image_urls" in st.session_state:
                save_image_generation(st.session_state.prompt, st.session_state.image_urls)
                st.rerun()  # Rerun to update the history immediately

        if "image_urls" in st.session_state:
            st.markdown("###")
            for url in st.session_state.image_urls:
                st.image(url, use_column_width=True)


if __name__ == "__main__":
    main()

