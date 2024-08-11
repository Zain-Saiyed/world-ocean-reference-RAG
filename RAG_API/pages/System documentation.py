import streamlit as st

st.set_page_config(page_title="Model Details", page_icon="🦙")

models = [
    "• Phi-3 Medium [14B][⇗](https://ollama.com/library/phi3:14b)",
    "• Llama3 [8B][⇗](https://ollama.com/library/llama3)"
    ]
modes  = ["• Summarize", "• Chat"]

table_data = f"""
| Component | Details |
|-----------|---------|
| Supported Modes | {' <br> '.join(modes)} |
| Models | {' <br> '.join(models)} |
| Embeddings | • nomic-embed-text |
| Vector Database | • ChromaDB  |
| Vector DB Distance Function | • L2 |
| Total Research Papers in DB | • 3131 |
"""

st.header("Current System details")
st.markdown(table_data, unsafe_allow_html=True)

st.header("LLM Model selection links")
st.markdown("1. Llama 3 vs Llama 2 Comparison: [Click here to read about Llama 3 vs Llama 2](https://www.apps4rent.com/blog/llama-3-vs-llama-2/)")
