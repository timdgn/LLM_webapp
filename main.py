from openai import OpenAI
import streamlit as st
import base64


# Load the API key from Streamlit secrets
api_key = st.secrets["openai_api_key"]
client = OpenAI(api_key=api_key)

# Side panel for mode selection
st.sidebar.title("Mode Selection")
mode = st.sidebar.radio(
    "Choisis un mode:",
    ("Default", "Data Scientist"),
    index=0)

st.title("4o mini")

if "openai_model" not in st.session_state:
    st.session_state.openai_model = "gpt-4o-mini-2024-07-18"

if "messages" not in st.session_state:
    st.session_state.messages = []

if "files_content" not in st.session_state:
    st.session_state.files_content = []
if "mode_prefix" not in st.session_state:
    st.session_state.mode_prefix = ""

# Add multiple file uploader
uploaded_files = st.file_uploader("Choose files", type=None, accept_multiple_files=True)

# Process uploaded files
if uploaded_files:
    st.session_state.files_content = []
    for uploaded_file in uploaded_files:
        # Read file content
        file_content = uploaded_file.read()

        # Try to decode as text, if not possible, encode as base64
        try:
            decoded_content = file_content.decode('utf-8')
            st.session_state.files_content.append(f"\nAttached text file '{uploaded_file.name}':\n{decoded_content}")
        except UnicodeDecodeError:
            encoded_content = base64.b64encode(file_content).decode('utf-8')
            st.session_state.files_content.append(
                f"\nAttached binary file '{uploaded_file.name}':\n[Binary content encoded in base64]")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Comment puis-je t'aider ?"):
    # Add mode prefix for the first message
    if not st.session_state.messages:
        if mode == "Data Scientist":
            st.session_state.mode_prefix = """You are an expert in Python development, including its core libraries, popular frameworks like Flask, Streamlit and FastAPI, data science libraries such as NumPy and Pandas, and testing frameworks like pytest. You excel at selecting the best tools for each task, always striving to minimize unnecessary complexity and code duplication.
            When making suggestions, you break them down into discrete steps, recommending small tests after each stage to ensure progress is on the right track.
            You provide code examples when illustrating concepts or when specifically asked. However, if you can answer without code, that is preferred. You're open to elaborating if requested.
            Before writing or suggesting code, you conduct a thorough review of the existing codebase, describing its functionality between <CODE_REVIEW> tags. After the review, you create a detailed plan for the proposed changes, enclosing it in <PLANNING> tags. You pay close attention to variable names and string literals, ensuring they remain consistent unless changes are necessary or requested. When naming something by convention, you surround it with double colons and use ::UPPERCASE::.
            Your outputs strike a balance between solving the immediate problem and maintaining flexibility for future use.
            You always seek clarification if anything is unclear or ambiguous. You pause to discuss trade-offs and implementation options when choices arise.
            It's crucial that you adhere to this approach, teaching your conversation partner about making effective decisions in Python development. You avoid unnecessary apologies and learn from previous interactions to prevent repeating mistakes.
            You are highly conscious of security concerns, ensuring that every step avoids compromising data or introducing vulnerabilities. Whenever there's a potential security risk (e.g., input handling, authentication management), you perform an additional review, presenting your reasoning between <SECURITY_REVIEW> tags.
            Lastly, you consider the operational aspects of your solutions. You think about how to deploy, manage, monitor, and maintain Python applications. You highlight relevant operational concerns at each step of the development process.
            Here's your task:"""
        else:
            st.session_state.mode_prefix = ""

    # Combine prompt with mode prefix and all file contents if available
    full_prompt = st.session_state.mode_prefix + prompt
    if st.session_state.files_content:
        for file_content in st.session_state.files_content:
            full_prompt += file_content
        st.session_state.files_content = []  # Clear files content after using them

    # Add message to chat history
    st.session_state.messages.append({"role": "user", "content": full_prompt})
    with st.chat_message("user"):
        st.markdown(prompt)  # Only show original prompt to user, not files content

    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model=st.session_state.openai_model,
            messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
            stream=True)
        response = st.write_stream(stream)
    st.session_state.messages.append({"role": "assistant", "content": response})

    # Clear mode prefix after first message
    st.session_state.mode_prefix = ""