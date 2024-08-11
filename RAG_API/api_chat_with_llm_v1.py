from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel

from langchain_community.vectorstores import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain_community.llms.ollama import Ollama

from get_embedding_function import get_embedding_function
import uvicorn, base64, logging, os

# Setup logging 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# Models available for querying
models = ["llama3", "phi3:14b"]
# main database dump path
CHROMA_PATH = "chroma"
DB_CLUSTER_PATH = "database_cluster_pdfs"
cluster_categories = os.listdir(DB_CLUSTER_PATH)
# Get embedding function
embedding_function = get_embedding_function()
# Iniitalise the ChromaDB handler
# Initialize the models
model_llama3 = Ollama(model=models[0])
model_phi3 = Ollama(model=models[1])

# Initialise FastAPI app
app = FastAPI(title="LLM RAG-Ocean: Navigate World Ocean Assessment PDF References")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
)


# PROMPT Templates for chat and summary modes 
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
 
class UserRequest(BaseModel):
    cluster_name: str
    user_query: str
    mode: str
    modelName: str #Because model_name is protected by Pydantic
 
class ModelResponse(BaseModel):
    cluster_name: str
    pdf_citations: list
    llm_response: dict
    pdf_citations: dict
    chat_mode: str
 
# Function to get the base64 version of the PDF for easy display 
def get_pdf_document(file_path: str):
  with open(file_path, "rb") as f:
    base64_pdf = base64.b64encode(f.read()).decode('utf-8')
  return base64_pdf
 
# Function to retrieve chunks from vector DB
async def query_chroma(cluster_name: str, query_text: str):
    cluster_path = os.path.join(DB_CLUSTER_PATH, cluster_name)
    # logger.info(f"persist_directory: {cluster_path}")

    db = Chroma(persist_directory=cluster_path, embedding_function=embedding_function, collection_name=cluster_name)

    results = db.similarity_search_with_score(query_text, k=5)
    context_entries = []
    for idx, (doc, _score) in enumerate(results):
        document_id = doc.metadata['source']  
        page_content = doc.page_content
        context_entries.append(f"{idx+1}. {page_content}\n   (PDF: {document_id})")  # Adjust citation format as needed
 
    context_text = "\n\n---\n\n".join(context_entries)
    
    # logger.info(f"results: {results}")
    # logger.info(f"context_text: {context_text}")
 
    sources_with_scores = [(doc.metadata.get("id", None), score) for doc, score in results]
    # logger.info(f"sources_with_scores: {sources_with_scores}")
    sorted_sources = sorted(sources_with_scores, key=lambda x: x[1], reverse=False)
 
    pdf_sources = [source.split(":")[0] for source, _ in sorted_sources]
    scores = [round(score,2) for _, score in sorted_sources]
   
    pdf_citations = {}
 
    for idx, (pdf_file, score) in enumerate(zip(pdf_sources,scores)):
    #   logger.info(f"pdf_file: {pdf_file}")
      pdf_citations[idx]={}
    #   pdf_citations[idx]["file_name"] = f"{cluster_path}/{pdf_file.split('\\')[-1]}"
      pdf_citations[idx]["file_name"] = pdf_file
      pdf_citations[idx]["score"] = score
      pdf_citations[idx]["pdf_document"] = get_pdf_document(pdf_file)

    #   logger.info(f"pdf_citations: {pdf_citations}")
    # logger.info(f"pdf_citations: {pdf_citations}")
    return {"context": context_text, "pdf_citations":pdf_citations}
 
# Function to get response from LLM
async def generate_ollama_response(mode: str, query_text: str, context_text: str, model_name:str):
    if mode == "summary":
        prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE_SUMMARY)
    elif mode == "chat":
        prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=context_text, question=query_text, none="I do not know about this one!")

    if model_name == "llama3":
        response_text = model_llama3.invoke(prompt)
        return {"llama3": response_text}
    
    elif model_name == "phi3":
        response_text = model_phi3.invoke(prompt)
        return {"phi3":response_text}
 
 # POST API - for chat and summary modes
@app.post("/api", response_model=ModelResponse)
async def chat(request: UserRequest):
    if request.mode not in ["chat", "summary"]:
        raise HTTPException(status_code=400, detail="Invalid mode. Possible modes: 'chat' or 'summary'.")
    if request.modelName not in ["llama3", "phi3"]:
        raise HTTPException(status_code=400, detail="Invalid model_name. LLMs: 'llama3' or 'phi3'.")
    if request.cluster_name not in cluster_categories:
        raise HTTPException(status_code=400, detail="Invalid cluster_name. Possible clusters: "+str(cluster_categories))


    try:
        # Querying the ChromaDB for chunks
        chroma_db_results = await query_chroma(request.cluster_name, request.user_query)
 
        # Use Ollama to get model results
        ollama_response = await generate_ollama_response(request.mode, request.user_query, chroma_db_results['context'], request.modelName)
 
        # Format the response
        response = ModelResponse(
            cluster_name=request.cluster_name,
            pdf_citations=chroma_db_results["pdf_citations"],
            llm_response=ollama_response,
            chat_mode=request.mode
        )
 
        return response
 
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))
 
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8401)