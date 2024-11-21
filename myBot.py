import streamlit as st
import openai
from langchain.prompts import PromptTemplate
from PyPDF2 import PdfReader
from langchain.chains import ConversationalRetrievalChain
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain_huggingface import HuggingFaceEndpoint
from io import StringIO
import pickle
import os

# File to save chatbots
CHATBOT_FILE = "chatbots.pkl"
openai.api_key = "APP_Key"

# Load chatbots from file


def extract_pdf_text(uploaded_file):
    """Extract text from a PDF file."""
    pdf_reader = PdfReader(uploaded_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def load_chatbots():
    if os.path.exists(CHATBOT_FILE):
        with open(CHATBOT_FILE, "rb") as f:
            return pickle.load(f)
    return {}


# Save chatbots to file
def save_chatbots():
    with open(CHATBOT_FILE, "wb") as f:
        pickle.dump(chatbots, f)
# Load chatbots at app start


chatbots = load_chatbots()


# Helper function to initialize chatbot
def initialize_chatbot(name, description, document_content=None):
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    if document_content:
        text_splitter = CharacterTextSplitter(chunk_size=2000, chunk_overlap=50)
        texts = text_splitter.split_text(document_content)
        vectorstore = FAISS.from_texts(texts, embeddings)
        retriever = vectorstore.as_retriever()  # Initialize retriever
    else:
        vectorstore = None
        retriever = None

    return {
        "name": name,
        "description": description,
        "retriever": retriever,
        "chat_history": [],
    }

# Streamlit app
st.title("LangChain Multi-Chatbot Creator")

# Sidebar Navigation
st.sidebar.header("Navigation")
page = st.sidebar.radio("Go to:", ["Create Chatbot", "Interact with Chatbot"])

if page == "Create Chatbot":
    st.header("Create a New Chatbot")
    with st.form("chatbot_form"):
        chatbot_name = st.text_input("Chatbot Name", placeholder="Enter chatbot name")
        chatbot_description = st.text_area("Chatbot Description", placeholder="Enter a brief description")
        uploaded_file = st.file_uploader(
            "Upload a document (Optional, Max 5MB)", type=["txt", "pdf"]
        )

        if uploaded_file and uploaded_file.size > 5 * 1024 * 1024:
            st.error("File size exceeds 5MB!")
            uploaded_file = None

        create_button = st.form_submit_button("Create Chatbot")

        if create_button:
            if chatbot_name in chatbots:
                st.error("A chatbot with this name already exists!")
            elif chatbot_name and chatbot_description:
                document_content = None
                if uploaded_file:
                    if uploaded_file.type == "text/plain":  # Handle text files
                        document_content = StringIO(uploaded_file.getvalue().decode("utf-8")).read()
                    elif uploaded_file.type == "application/pdf":  # Handle PDF files
                        document_content = extract_pdf_text(uploaded_file)
                chatbots[chatbot_name] = initialize_chatbot(chatbot_name, chatbot_description, document_content)
                save_chatbots()
                st.success(f"Chatbot '{chatbot_name}' created successfully!")
            else:
                st.error("Chatbot name and description are required!")

elif page == "Interact with Chatbot":
    st.header("Interact with Your Chatbots")

    if not chatbots:
        st.warning("No chatbots available. Create a chatbot first!")
    else:
        chatbot_name = st.selectbox("Select a chatbot", list(chatbots.keys()))
        chatbot = chatbots[chatbot_name]

        st.subheader(f"Chatbot: {chatbot_name}")
        st.write(f"**Description:** {chatbot['description']}")

        user_input = st.text_input("Your Message", placeholder="Type your message here...")

        if user_input:
            query = user_input
            # Retrieve documents using `invoke`
            try:
                retrieved_docs = chatbot['retriever'].invoke(query)
                if retrieved_docs:
                    # Combine the retrieved documents' content
                    retrieved_text = "\n".join([doc.page_content for doc in retrieved_docs])
                else:
                    retrieved_text = "No relevant information retrieved."
            except Exception as e:
                retrieved_text = f"Error retrieving documents: {e}"
            # Prepare structured prompt
            temp = """
                Based on the following details about obtaining a Current Document:
                {context}
                If the user's question directly relates to the provided details, respond with a concise and clear answer.
                If the user's question is generic (e.g., greetings like 'hi' or 'hello'), respond politely without attempting to match the context.
                If the question doesn't relate to the given details, respond with 'I cannot answer that based on the information provided.'
                User's question: {question}
                """
            try:
                prompt_temp = PromptTemplate.from_template(temp)
                formated_temp = prompt_temp.format(
                    context=retrieved_text,  # Use the retrieved documents
                    question=query,  # The user's query
                )
            except Exception as e:
                print(f"Error formatting prompt: {e}")
                formated_temp = None

            # Invoke ChatGPT with the formatted prompt
            if formated_temp:
                try:
                    response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",  # Use "gpt-4" if available
                        messages=[
                            {"role": "system",
                             "content": "You are a helpful assistant for This document."},
                            {"role": "user", "content": formated_temp},
                        ],
                        temperature=0.7,
                    )

                    # Extract and display the answer
                    if response and 'choices' in response:
                        answer = response['choices'][0]['message']['content'].strip()
                    else:
                        answer = "No response received from the model."
                        print(answer)
                except Exception as e:
                    answer = f"Error during ChatGPT invocation: {e}"
                    print(answer)
            else:
                answer = "Prompt could not be prepared due to formatting issues."

            # Update chat history
            chatbot["chat_history"].append((query, answer))

            # Save chat history (ensure save_chatbots function is implemented)
            save_chatbots()

            # Display chat history
            st.subheader("Chat History")
            for i, (q, a) in enumerate(chatbot["chat_history"], 1):
                st.write(f"**Q{i}:** {q}")
                st.write(f"**A{i}:** {a}")

    # Delete chatbot option
    delete_button = st.button(f"Delete Chatbot: {chatbot_name}")
    if delete_button:
        del chatbots[chatbot_name]
        save_chatbots()
        st.success(f"Chatbot '{chatbot_name}' has been deleted.")
        st.experimental_rerun()
