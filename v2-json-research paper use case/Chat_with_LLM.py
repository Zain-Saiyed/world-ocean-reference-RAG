import streamlit as st
import argparse
from langchain_community.vectorstores import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain_community.llms.ollama import Ollama

from get_embedding_function import get_embedding_function

import time
import base64 

CHROMA_PATH = "chroma"

# PROMPT_TEMPLATE = """
# Answer the question based only on the following context:

# {context}

# ---

# Answer the question based on the above context with inline citation of the paper from which reference is taken: {question}
# """

# PROMPT_TEMPLATE = """
# You are a chatbot based on the references within book "The Second World Assessment".
# DOCUMENT:
# {context}

# ---
# QUESTION:
# {question}
# ---

# Instructions:
# Answer the QUESTION using the above DOCUMENT. 
# Keep the answers ground in facts of the DOCUMENT. 
# Provide concise and informative responses tailored to the QUESTION.
# Use specific references or topics from the DOCUMENT to support your answer.
# If the DOCUMENT does not contain the facts to answer the QUESTION return {none}. 
# """
PROMPT_TEMPLATE = """
You are an expert marine scientist assistant with comprehensive knowledge of the Second World Ocean Assessment and its referenced research papers.

Context: 
{context}

User Query: {question}

Instructions:
1. Analyze the user's query carefully to understand the specific information needed.
2. Utilize the retrieved information to identify the most relevant research documents.
3. Synthesize information from the relevant abstracts to formulate a comprehensive answer.
4. Provide a clear, concise, and factual response that directly addresses the user's question.
5. Cite the relevant 'source' document IDs in your response using the format [Citations: [1] (the source), [2] (the source), etc.] and at the end list them.
6. If the question is out of context or unclear based on the available documents, respond with: "That question is out of the scope of the available documents."
7. If the information requested is not present in the available documents, respond with: "The information you're seeking is not available in the referenced documents."
8. Stick strictly to the facts presented in the documents; do not generate speculative answers.

Your response should be:
- Accurate and fact-based
- Directly relevant to the user's query
- Concise yet comprehensive
- Properly cited using the document IDs and PDF citations

Answer response:
"""
PROMPT_TEMPLATE_SUMMARY = """
You are an expert marine scientist assistant tasked with summarizing research papers related to the Second World Ocean Assessment.

Context: 
{context}

Instructions:
1. Analyze the context and synthesize their key information.
2. Create a comprehensive summary that integrates insights from all relevant papers in Context.
3. Structure your summary as follows:

   a. Overview (100-150 words)
   Provide a high-level summary of the main themes and findings across all papers.

   b. Key Findings (3-5 bullet points)
   List the most significant discoveries or conclusions from the papers.

   c. Methodologies (50-75 words)
   Briefly describe the primary research methods used across the studies.

   d. Comparative Analysis (75-100 words)
   Highlight any notable similarities or differences between the papers' approaches or results.

   e. Research Implications (50-75 words)
   Summarize the broader implications of these findings for marine science or policy.

   f. Future Directions (50-75 words)
   Identify gaps in current knowledge or areas for future research as mentioned in the papers.

   g. Key Terms and Concepts
   Define 3-5 important technical terms or concepts crucial to understanding the research.

4. Cite the relevant document Title in your summary using the format [1], [2], etc. and list them at the end from the context.
5. Aim for clarity, conciseness, and accuracy in your summary.
6. Stick strictly to the information presented in the documents; avoid speculation or external information.
7. If the question is out of context or not clear based on the available documents, respond with: "That question is out of the scope of the available documents."

Your summary should be:
- Comprehensive, covering the main points from all relevant papers
- Accurate and fact-based
- Well-structured according to the outline provided
- Properly cited using the document IDs

Summary:
"""

models = ["llama3", "phi3:14b", ]
model_names = ["model_1 - Llama3 [8B]","model_2 - Phi3 medium [14B]", ]
# models = ["llama3", "llama3"]
# model_names = [ "model_1 - Llama3 [8B]", "model_2 - Llama3 [8B]"]

if "init_status" not in st.session_state:
    st.session_state["init_status"] = False

def initialize():
    # Get embedding function
    embedding_function = get_embedding_function()
    # st.session_state["embedding_function"] = embedding_function

    # Prepare the DB.
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
    st.session_state["db"] = db
    
    # Prepare the models
    for idx, model_name in enumerate(models):
        st.session_state[f"model_{idx+1}"] = Ollama(model=model_name)
        print(f"...Loaded {model_name}")
    
def query_rag(query_text: str, model_name:str, summary:bool):
    # embedding_function = st.session_state["embedding_function"]
    db = st.session_state["db"] 
    model = st.session_state[model_name]
    
    with st.spinner('Retrieving relevant chunks from database...'):
        # Search the DB.
        results = db.similarity_search_with_score(query_text, k=5)
        # st.write(results)
        
        # context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
        context_entries = []
        for idx, (doc, _score) in enumerate(results):
            document_id = doc.metadata['source']  # Adjust this based on how document IDs are stored
            page_content = doc.page_content
            # OPTION-1
            # context_entries.append(f"Document(page_content='{page_content}', metadata={{'id': '{document_id}'}})")
            
            # OPTION-2
            context_entries.append(f"{idx+1}. {page_content}\n   (PDF: {document_id})")  # Adjust citation format as needed


        context_text = "\n\n---\n\n".join(context_entries)
        
        if summary:
            prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE_SUMMARY)
        else:
            prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
        prompt = prompt_template.format(context=context_text, question=query_text, none="I do not know about this one!")

    with st.spinner(f"{model_name.replace('_',' ')} is processing query..."):
        # Invoke the model
        start_time = time.time()
        response_text = model.invoke(prompt)
        end_time = round((time.time() - start_time),2)

    sources_with_scores = [(doc.metadata.get("id", None), score) for doc, score in results]

    sorted_sources = sorted(sources_with_scores, key=lambda x: x[1], reverse=False)

    return response_text, sorted_sources, end_time

# Function to display PDF
def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    
    # Display PDF
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="500" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

def display_sources( sources ):
        # st.write(f"Sources: {sources}")

        # Display the links in your Streamlit app
        # st.markdown("## Source PDFs:")
        # pdf_files = list(set([re.search(r'pdf_data/(.*?\.pdf)', source).group(1) for source, _score in sources if re.search(r'pdf_data/(.*?\.pdf)', source)]))
        pdf_sources = [source.split(":")[0].split("/")[1] for source, _ in sources]
        scores = [round(score,2) for _, score in sources]

        for idx, (pdf_file, score) in enumerate(zip(pdf_sources,scores)):
            st.write(f"{idx+1}◦ {pdf_file} [score: {score}]")

        st.write("---")

        # Display PDFs
        num_columns = 2  # Adjust the number of columns as needed
        col1, col2 = st.columns(num_columns)
        for idx, (pdf_file, score) in enumerate(zip(pdf_sources,scores)):
            if idx % 2 == 0:
                col = col1
            else:
                col = col2
            with col:
                st.write(f"{idx+1}◦ {pdf_file} [score: {score}]")
                show_pdf(f"pdf_data/{pdf_file}")

def display_sample_prompts():
    with st.sidebar:
        st.subheader("Try it out:")
        
        prompt_category = st.radio(
            "Choose prompt category:",
            ("Relevant", "Incorrect/Off-topic")
        )
        
        if prompt_category == "Relevant":
            relevant_prompts = [
                "What are the main threats to marine biodiversity?",
                "How does climate change affect ocean ecosystems?",
                "What are the impacts of ocean acidification on marine life?",
                "Describe the current state of global fish stocks.",
                "What are the major sources of marine pollution?"
            ]
            selected_prompt = st.selectbox(
                "Select a relevant prompt:",
                relevant_prompts,
                index=None,
                placeholder="Choose a prompt..."
            )
        else:
            incorrect_prompts = [
                "Can you give me a recipe for making cheesecake in bullet points?",
                "What is the importance of COVID-19 vaccines in technology?",
                "How do I train my dog to do tricks?",
                "What are the best tourist attractions in Paris?",
                "Explain the rules of cricket in simple terms."
            ]
            selected_prompt = st.selectbox(
                "Select an incorrect/off-topic prompt:",
                incorrect_prompts,
                index=None,
                placeholder="Choose a prompt..."
            )
        
        if selected_prompt:
            if st.button("Use Selected Prompt"):
                st.session_state.query_text = selected_prompt

                return selected_prompt
    
    return None

def update_query_text():
    st.session_state.query_text = st.session_state.query_input


def main():
    if st.session_state["init_status"] == False:
        initialize()
        st.session_state["off-topic-prompts"] = [
            "Can you give me recipe of making cheese cake in bullet points?",
            "Can you give me importance of covid 19 vaccine in technology?",
            "How do I train my dog to do tricks?",
            "What are the best tourist attractions in Paris?",
            "Explain the rules of cricket in simple terms."
        ]
        
        st.session_state["relevant-prompts"] = [
            "What are the main threats to marine biodiversity?",
            "How does climate change affect ocean ecosystems?",
            "What are the impacts of ocean acidification on marine life?",
            "Describe the current state of global fish stocks.",
            "What are the major sources of marine pollution?"
        ]

        if 'query_text' not in st.session_state:
            st.session_state.query_text = ""

        with st.sidebar:
            mode = st.radio("Select Mode:", ["Summarization", "Chat"])


    # Streamlit UI
    st.title("LLM RAG-Ocean: Navigate World Ocean Assessment PDF References")
    st.write('Explore PDF references from the World Ocean Assessment book in an interactive application powered by LLMs.')

    selected_prompt = display_sample_prompts()

    # Main content area
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # st.write(st.session_state.query_text or selected_prompt)
        query_text = st.text_area("Enter your query:", 
                                value= st.session_state.query_text,
                                placeholder= "Type your question here...",          
                                help= "Press Enter to add a new line. Use Shift+Enter to submit.", 
                                key= "query_input",
                                # on_change=update_query_text,
                                max_chars= 1000, height= 100)
        if st.session_state.query_text != query_text:
            st.session_state.query_text = query_text
            
    with col2:
        st.write('<div style="display: flex; justify-content: center; align-items: center; height: 55px;">', unsafe_allow_html=True)
        ask_button = st.button("Summarize" if mode=="Summarization" else "Ask", type="primary", use_container_width=True,)
        st.write('</div>', unsafe_allow_html=True)

    
    if ask_button:
        query_to_ask_model = st.session_state.query_text
        print(query_to_ask_model)
        if query_to_ask_model: 
            for model_name in model_names:
                response, sources, response_time = query_rag(query_to_ask_model, model_name.split('-')[0].strip(),summary=(mode == "Summarization"))
                with st.expander(f"Response - {model_name.replace('_',' ')}"):
                    
                    st.write(f"*Generated in {response_time:.2f} seconds.*")
                    st.write(f"{response}")

            with st.expander("Retrieved Sources (chunks):"):
                display_sources(sources)
        else:
            st.warning("Please enter a query or select a sample prompt.")

if __name__ == "__main__":
    main()


##################################################### BACKUP PROMPT:

# PROMPT_TEMPLATE = """
# You are an expert marine scientist assistant with comprehensive knowledge of the Second World Ocean Assessment and its referenced research papers. Your task is to provide accurate, concise, and relevant answers to user queries based on the abstracts and information from the referenced papers.

# Context: 
# {context}

# User Query: {question}

# Instructions:
# 1. Analyze the user's query carefully to understand the specific information needed.
# 2. Identify the most relevant research documents and their abstracts based on the query.
# 3. Synthesize information from the relevant abstracts to formulate a comprehensive answer.
# 4. Provide a clear, concise, and factual response that directly addresses the user's question.
# 5. Cite the relevant document IDs in your response using the format [document ID].
# 6. Include citations from the context of the specific PDFs from which the information is drawn in the format (PDF: [PDF file name]).
# 7. If the question is out of context or unclear based on the available documents, respond with: "That question is out of the scope of the available documents."
# 8. If the information requested is not present in the available documents, respond with: "The information you're seeking is not available in the referenced documents."
# 9. Stick strictly to the facts presented in the documents; do not generate speculative answers.

# Your response should be:
# - Accurate and fact-based
# - Directly relevant to the user's query
# - Concise yet comprehensive
# - Properly cited using the document IDs

# Answer response:
# """