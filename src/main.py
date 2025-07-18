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
from PIL import Image, ImageDraw
from streamlit_cropper import st_cropper

from constants import *


def init_directories() -> None:
    """Initialize necessary directories for storing thread history and images."""
    os.makedirs(THREADS_DIR, exist_ok=True)
    os.makedirs(UPLOADED_IMAGES_DIR, exist_ok=True)
    os.makedirs(GENERATED_IMAGES_DIR, exist_ok=True)
    os.makedirs(INPAINTING_IMAGES_DIR, exist_ok=True)


def load_threads() -> Dict[str, Dict[str, Any]]:
    """
    Load all conversation threads from the history directory.

    Returns:
        Dict[str, Dict[str, Any]]: A dictionary of thread IDs to thread data
    """
    threads = {}
    current_time = datetime.now()
    for file_path in glob(os.path.join(THREADS_DIR, "*.json")):
        with open(file_path, 'r') as f:
            thread_data = json.load(f)
            thread_id = thread_data["id"]
            last_updated = datetime.fromisoformat(thread_data["last_updated"])
            
            # Check if the thread is empty and older than 2 minutes
            if not thread_data["messages"] and (current_time - last_updated).total_seconds() > 120:
                # Delete the empty thread
                os.remove(file_path)
            else:
                threads[thread_id] = thread_data
    
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


def display_message(message: Dict[str, Any]) -> None:
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
        content (Union[str, List[Dict[str, Any]]]): The message content to prepare

    Returns:
        Union[str, List[Dict[str, Any]]]: The prepared message content
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


def setup_sidebar(threads: Dict[str, Dict[str, Any]]) -> Tuple[str, Dict[str, Dict[str, Any]], List, str, Dict[str, Any]]:
    """
    Set up the sidebar interface.

    Args:
        threads (Dict[str, Dict[str, Any]]): The current threads dictionary

    Returns:
        Tuple[str, Dict[str, Dict[str, Any]], List, str, Dict[str, Any]]:
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
                # dalle_options['n'] = st.slider("Number of Images", min_value=1, max_value=4, value=1)
                dalle_options['n'] = st.number_input("Number of Images (max 4)", min_value=1, max_value=4, value=1)

                st.divider()

                st.title("🎨 Image Generation History")
                generations = load_image_generations()
                display_image_generation_history(generations)

        elif interaction_type == INTERACTION_TYPES["inpainting"]:
            with st.container(border=True):
                st.title("🖌️ Inpainting Options")
                dalle_options['size'] = st.selectbox("Image Size", ["1024x1024"], index=0)
                
                st.divider()
                
                st.title("🎨 Inpainting History")
                inpaintings = load_inpainting_history()
                display_inpainting_history(inpaintings)

        st.write("")

        with st.container(border=True):
            st.caption(f'By Timmothy Dangeon, PharmD & Healthcare Data Scientist')
            st.caption(f'Linkedin : linkedin.com/in/timdangeon')
            st.caption(f'Github : github.com/timdgn')

    return mode, threads, uploaded_files, interaction_type, dalle_options


def display_thread_history(threads: Dict[str, Dict[str, Any]]) -> None:
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


def display_thread_button(thread_id: str, thread_data: Dict[str, Any], threads: Dict[str, Dict[str, Any]]) -> None:
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
        if st.button(f"**{last_updated}** : {preview}", key=thread_id):
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


def create_message_content(prompt: str, image_data_list: List[Dict[str, str]]) -> Union[str, List[Dict[str, Any]]]:
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


def handle_chat_input(client: OpenAI, thread: Dict[str, Any], uploaded_files, mode: str) -> None:
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


def initialize_session_state(model: str) -> None:
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


def generate_images(client: OpenAI, dalle_options: Dict[str, Any], final_prompt: str) -> None:
    """
    Generate images using DALL-E in parallel.

    Args:
        client (OpenAI): The OpenAI client
        dalle_options (Dict[str, Any]): Options for DALL-E image generation
        final_prompt (str): The final prompt including selected categories
    """
    def generate_single_image(prompt):
        response = client.images.generate(model="dall-e-3",
                                          prompt=prompt,
                                          size=dalle_options['size'],
                                          quality=dalle_options['quality'])
        return response.data[0].url

    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(generate_single_image, final_prompt) for _ in range(dalle_options['n'])]
            image_urls = [future.result() for future in concurrent.futures.as_completed(futures)]
        st.session_state["image_urls"] = image_urls

    except Exception as e:
        st.error(f"Error generating images: {str(e)}")


def save_image_generation(final_prompt: str, image_urls: List[str]) -> str:
    """
    Save an image generation to the history.

    Args:
        final_prompt (str): The final prompt including selected categories
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
        "prompt": final_prompt,
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


def display_image_generation_history(generations: List[Dict[str, Any]]) -> None:
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
                st.markdown(f"**Prompt**: {generation['prompt']}")

                st.markdown(f"##### {len(generation['image_paths'])} images generated :" if len(generation['image_paths']) > 1 else "##### 1 image generated :")
                captions_list = [f"Image {i+1}" for i in range(len(generation['image_paths']))]
                st.image(generation["image_paths"], caption=captions_list, width=300)
                
                # Boutons de téléchargement en dessous des images
                for i, image_path in enumerate(generation["image_paths"]):
                    with open(image_path, "rb") as file:
                        image_bytes = file.read()
                        st.download_button(
                            label=f"Download image ({i+1}/{len(generation['image_paths'])})",
                            icon="💾",
                            data=image_bytes,
                            file_name=f"{generation['id']}_image_{i}.png",
                            mime="image/png",
                            key=f"export_{generation['id']}_{i}")
                st.markdown("#")
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

def download_thread_export(thread_data: Dict[str, Any], format: str) -> None:
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

def create_mask(image: Image.Image) -> Image.Image:
    """
    Create a mask by allowing the user to crop a rectangle on the image using st_cropper.
    The mask will be black (0) in the selected area and white (255) elsewhere.
    
    Args:
        image (Image.Image): The original image
    
    Returns:
        Image.Image: The inverted mask image
    """
    # Display the image and allow the user to crop a rectangle
    crop_coordinates = st_cropper(
        image, 
        realtime_update=True, 
        box_color="#00ff00", 
        aspect_ratio=None,
        return_type="box"
    )
    
    # Create a white mask (255 everywhere)
    mask = Image.new("L", image.size, 255)
    draw = ImageDraw.Draw(mask)
    
    # Convert width/height to right/bottom coordinates and convert to integers
    left = int(crop_coordinates['left'])
    top = int(crop_coordinates['top'])
    right = int(crop_coordinates['left'] + crop_coordinates['width'])
    bottom = int(crop_coordinates['top'] + crop_coordinates['height'])
    
    # Draw black rectangle (0) on the selected area
    draw.rectangle([left, top, right, bottom], fill=0)
    
    return mask

def generate_inpainting(client: OpenAI, original_image: Image.Image, mask: Image.Image, prompt: str, dalle_options: Dict[str, Any]) -> Image.Image:
    """
    Generate an inpainting using DALL-E.
    
    Args:
        client (OpenAI): The OpenAI client
        original_image (Image.Image): The original image
        mask (Image.Image): The mask image
        prompt (str): The prompt for inpainting
        dalle_options (Dict[str, Any]): Options for DALL-E image generation
    
    Returns:
        Image.Image: The inpainted image
    """
    original_image_bytes = io.BytesIO()
    original_image.save(original_image_bytes, format="PNG")
    original_image_bytes = original_image_bytes.getvalue()
    
    mask_bytes = io.BytesIO()
    mask.save(mask_bytes, format="PNG")
    mask_bytes = mask_bytes.getvalue()
    
    response = client.images.edit(
        model="dall-e-2",
        image=original_image_bytes,
        mask=mask_bytes,
        prompt=prompt,
        size=dalle_options['size']
    )
    
    inpainted_image_url = response.data[0].url
    inpainted_image_response = requests.get(inpainted_image_url)
    inpainted_image = Image.open(io.BytesIO(inpainted_image_response.content))
    
    return inpainted_image

def save_inpainting(original_image: Image.Image, prompt: str, inpainted_image: Image.Image) -> None:
    """
    Save an inpainting to the history.
    
    Args:
        original_image (Image.Image): The original image
        prompt (str): The prompt used for inpainting
        inpainted_image (Image.Image): The inpainted image
    """
    inpainting_id = str(uuid.uuid4())
    
    inpainting_folder = os.path.join(INPAINTING_IMAGES_DIR, inpainting_id)
    os.makedirs(inpainting_folder, exist_ok=True)

    original_image_path = os.path.join(inpainting_folder, "original.png")
    original_image.save(original_image_path)
    
    inpainted_image_path = os.path.join(inpainting_folder, "inpainted.png")
    inpainted_image.save(inpainted_image_path)
    
    inpainting_data = {
        "id": inpainting_id,
        "prompt": prompt,
        "original_image_path": original_image_path,
        "inpainted_image_path": inpainted_image_path,
        "timestamp": datetime.now().isoformat()
    }
    file_path = os.path.join(INPAINTING_IMAGES_DIR, f"{inpainting_id}.json")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(inpainting_data, f, indent=4, ensure_ascii=False)

def load_inpainting_history() -> List[Dict[str, Any]]:
    """
    Load all inpaintings from the history directory.
    
    Returns:
        List[Dict[str, Any]]: A list of inpainting data
    """
    inpaintings = []
    for file_path in glob(os.path.join(INPAINTING_IMAGES_DIR, "*.json")):
        with open(file_path, 'r') as f:
            inpainting_data = json.load(f)
            inpaintings.append(inpainting_data)
    return sorted(inpaintings, key=lambda x: x["timestamp"], reverse=True)

def display_inpainting_history(inpaintings: List[Dict[str, Any]]) -> None:
    """
    Display the inpainting history.
    
    Args:
        inpaintings (List[Dict[str, Any]]): The inpaintings to display
    """
    for inpainting in inpaintings:
        timestamp = datetime.fromisoformat(inpainting["timestamp"]).strftime("%Y-%m-%d %H:%M")
        preview = inpainting["prompt"][:30] + "..."
        
        col1, col2, col3 = st.columns([3, 1, 0.5])
        with col1:
            with st.popover(f"{timestamp}: {preview}"):
                st.markdown(f"**Prompt**: {inpainting['prompt']}")

                st.image([inpainting["original_image_path"], inpainting["inpainted_image_path"]],
                         caption=["Original Image", "Inpainted Image"],
                         width=300)
                
                with open(inpainting["inpainted_image_path"], "rb") as file:
                    image_bytes = file.read()
                    st.download_button(
                        label="Download Inpainted Image",
                        icon="💾",
                        data=image_bytes,
                        file_name=f"inpainted_image_{inpainting['id']}.png",
                        mime="image/png")
        
        with col2:
            st.image(inpainting["inpainted_image_path"], width=75)
        
        with col3:
            if st.button("❌", key=f"delete_{inpainting['id']}"):
                delete_inpainting(inpainting['id'])
                st.rerun()

def delete_inpainting(inpainting_id: str) -> None:
    """
    Delete an inpainting from the history.
    
    Args:
        inpainting_id (str): The ID of the inpainting to delete
    """
    file_path = os.path.join(INPAINTING_IMAGES_DIR, f"{inpainting_id}.json")
    if os.path.exists(file_path):
        os.remove(file_path)
    
    inpainting_folder = os.path.join(INPAINTING_IMAGES_DIR, inpainting_id)
    if os.path.exists(inpainting_folder):
        shutil.rmtree(inpainting_folder)

def main() -> None:
    """Main function to run the Streamlit app."""
    st.set_page_config(page_title="LLM Chat", page_icon="✨")
    api_key = st.secrets["openai_api_key"]

    init_directories()
    initialize_session_state(MODEL)

    client = OpenAI(api_key=api_key)
    threads = load_threads()

    mode, threads, uploaded_files, interaction_type, dalle_options = setup_sidebar(threads)

    if interaction_type == INTERACTION_TYPES["chat"]:
        st.title(f"🤖 {interaction_type}")

        if st.session_state.current_thread_id is None or st.session_state.current_thread_id not in threads:
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

        st.session_state['prompt'] = st.text_area("What do you want to create ?", height=150, key="new_prompt")

        with st.expander("Advanced prompt modifiers", icon="🚀"):
            selected_categories = {
                "categories": st.multiselect("Select categories to add to the prompt", CATEGORIES),
                "styles": st.multiselect("Select styles to add to the prompt", STYLES),
                "lighting": st.multiselect("Select lighting to add to the prompt", LIGHTING),
                "camera_angles": st.multiselect("Select camera angles to add to the prompt", CAMERA_ANGLES),
                "colors": st.multiselect("Select colors to add to the prompt", COLORS),
                "textures": st.multiselect("Select textures to add to the prompt", TEXTURES)}

        if st.button("Let's go ✨") and st.session_state.prompt:
            with st.spinner("Generating ..."):
                st.session_state.final_prompt = st.session_state.prompt
                
                for category, selections in selected_categories.items():
                    if selections:
                        st.session_state.final_prompt += ", " + ", ".join(selections)
                
                generate_images(client, dalle_options, st.session_state.final_prompt)
            
            if "image_urls" in st.session_state:
                save_image_generation(st.session_state.final_prompt, st.session_state.image_urls)
                st.rerun()  # Rerun to update the history immediately

        if "image_urls" in st.session_state:
            st.markdown("###")

            for i, url in enumerate(st.session_state.image_urls):
                st.image(url, use_column_width=True)
                response = requests.get(url)
                image_bytes = response.content
                st.download_button(
                    label=f"Download image ({i+1}/{len(st.session_state.image_urls)})",
                    icon="💾",
                    data=image_bytes,
                    file_name=f"generated_image_{i}.png",
                    mime="image/png",
                    key=f"download_{i}")
                st.markdown("###")

    elif interaction_type == INTERACTION_TYPES["inpainting"]:
        st.title(f"🖌️ {interaction_type}")
        
        uploaded_image = st.file_uploader("Upload an image to inpaint", type=["jpg", "jpeg", "png"])
        
        if uploaded_image is not None:
            original_image = Image.open(uploaded_image)
            
            mask = create_mask(original_image)
            
            if mask is not None:
                prompt = st.text_input("Enter a prompt for inpainting")
                
                if "inpainted_result" not in st.session_state:
                    st.session_state.inpainted_result = None
                
                if st.button("Generate Inpainting"):
                    with st.spinner("Generating inpainting..."):
                        inpainted_image = generate_inpainting(client, original_image, mask, prompt, dalle_options)
                        st.session_state.inpainted_result = inpainted_image
                        save_inpainting(original_image, prompt, inpainted_image)
                        st.rerun()
                
                if st.session_state.inpainted_result is not None:
                    st.markdown("###")
                    st.image(st.session_state.inpainted_result, caption="Inpainted Image", use_column_width=True)
                    
                    # Convert image to bytes only once and store in session state
                    if "download_bytes" not in st.session_state:
                        buffered = io.BytesIO()
                        st.session_state.inpainted_result.save(buffered, format="PNG")
                        st.session_state.download_bytes = buffered.getvalue()
                    
                    st.download_button(
                        label="Download Inpainted Image",
                        icon="💾",
                        data=st.session_state.download_bytes,
                        file_name="inpainted_image.png",
                        mime="image/png",
                        key="inpaint_download"  # Add a unique key
                    )


if __name__ == "__main__":
    main()
