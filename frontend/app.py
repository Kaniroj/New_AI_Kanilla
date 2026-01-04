# frontend/app.py
import os
import requests
import streamlit as st

st.set_page_config(page_title="YouTuber RAG Chatbot")
st.title("🎓 RAG Chatbot")

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/rag/query").strip()

# --- init chat history ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- render history ---
for msg in st.session_state.messages:
    with st.chat_message("user" if msg["role"] == "user" else "assistant"):
        st.markdown(msg["content"])

# --- new input ---
question = st.chat_input("Ask the YouTuber a question about the videos:")
if question:
    # show user message
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    # call API + show assistant message
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                resp = requests.post(API_URL, json={"prompt": question}, timeout=60)
                resp.raise_for_status()
                data = resp.json()

                # ---- normalize response ----
                # API might return:
                # 1) {"answer": "...", "sources": [...]}
                # 2) {"answer": {"answer": "...", "sources": [...]}}  (nested)
                # 3) "just a string"
                if isinstance(data, dict) and isinstance(data.get("answer"), dict):
                    data = data["answer"]

                if isinstance(data, dict):
                    answer_text = data.get("answer", "")
                    sources = data.get("sources", []) or []
                else:
                    answer_text = str(data)
                    sources = []

                if not isinstance(answer_text, str):
                    answer_text = str(answer_text)

                if not answer_text:
                    answer_text = f"Unexpected response: {data}"

                # ---- sources rendering ----
                source_info = ""
                if sources:
                    source_info = "\n\n---\n**Sources:**\n"
                    for s in sources:
                        source_info += f"- {s}\n"

                full_answer = answer_text + source_info
                st.markdown(full_answer)

                st.session_state.messages.append(
                    {"role": "assistant", "content": full_answer}
                )

            except requests.exceptions.HTTPError as e:
                st.error(
                    f"API request failed: {e}\n\nURL: {getattr(resp, 'url', API_URL)}\n\nBody: {getattr(resp, 'text', '')[:500]}"
                )
                st.session_state.messages.append(
                    {"role": "assistant", "content": f"API request failed: {e}"}
                )
            except Exception as e:
                st.error(f"Error calling API: {e}")
                st.session_state.messages.append(
                    {"role": "assistant", "content": f"Error calling API: {e}"}
                )
