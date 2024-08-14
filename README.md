# LLM RAG-Ocean: Navigate World Ocean Assessment II PDF References


## Overview:

The Second World Ocean Assessment (WOA II) is a comprehensive evaluation of the state of the world's oceans, produced as part of the United Nations Regular Process for Global Reporting and Assessment of the State of the Marine Environment, including Socioeconomic Aspects. The volume of scientific literature related to ocean assessment is quite high, because of this researchers often struggle to find relevant studies, understand the vast corpus, and derive meaningful insights.
Hence, this project aims to tackle an important challenge which is to manage and make sense of the extensive and complex bibliography or references included in (WOA II). This involves extracting references, expanding the corpus with related literature, and providing interactive tools for users to explore and understand the data. The goal is to create a system that can cluster and categorize the data, visualize it effectively, and allow for interactive queries and summaries on the corpus using Large Language Models.

#### Deployed URLs:

* **D3.js** web application URL : http://134.190.153.189:8000/
* **Streamlit** Web application URL : http://134.190.153.189:8501/ 
* **Backend FastAPI** URL : http://134.190.153.189:8401/api

## Project structure:

There are three folders, and these are:

#### 1. Streamlit Web Application - **RAG_web_app/**
The `RAG_web_app/` folder contains the Streamlit web application which runs at port `8501`. This application is for internal testing of the RAG system and compare the responses between different Large Language Models (LLMs). 

* **Current LLMs deployed:**: `Llama3` [8B] and `Phi3-medium` [14B]. 
* **Vector Database**: `ChromaDB` database with L2 distance function.

**Folders and Files:**

1. `chroma/`: Contains the chromaDB vector database persisted/saved for later use.
2. `json to txt/`: Contains python code for reading in the json file containing abstracts and saving each paper as a `.txt` file. This is to use it for loading in the vector database.
3. `pages/` : This is for streamlit to read in any other pages to display on the home page.
4. `pdf_data/`: This folder contains all the WOA II reference documents (with their title, abstract, and other information) as a **PDF file**.
5. `txt_data/`: This folder contains all the WOA II reference documents (with their title, abstract, and other information) as a **Text file**.
6. `Chat_with_LLM.py`: The Streamlit web application.
7. `get_embedding_function.py`: Helper script for returning the Helper function.
8. `populate_database_pdf.py`: Script for saving the PDF documents into the ChromaDB database.
9. `populate_database_txt.py`: Script for saving the Text documents into the ChromaDB database.
10. `txt_to_pdf.py`: Script to convert Text file into PDF file.


#### 2. Backend Restful API - **RAG_API/**

The `RAG_API/` folder contains the FAST API Python REST API for serving the RAG system to the **D3.js web application**.

**Folders and Files:**

1. `chroma/`: Contains the chromaDB vector database persisted/saved for later use.
2. `clustered_pdfs/`: This folder contains the PDF documents for each of the clusters.
3. `database_clustered_pdfs/`: This folder contains the ChromaDB database for each of the clusters.
4. `json to txt/`: Contains python code for reading in the json file containing abstracts and saving each paper as a `.txt` file. This is to use it for loading in the vector database.
5. `pages/` : This is for streamlit to read in any other pages to display on the home page.
6. `pdf_data/`: This folder contains all the WOA II reference documents (with their title, abstract, and other information) as a **PDF file**.
7. `txt_data/`: This folder contains all the WOA II reference documents (with their title, abstract, and other information) as a **Text file**.
8. `api_chat_with_llm_v1.py`: The FastAPI Restful API.
9. `get_embedding_function.py`: Helper script for returning the Helper function.
10. `populate_database_pdf.py`: Script for saving the PDF documents into the ChromaDB database.
11. `populate_database_txt.py`: Script for saving the Text documents into the ChromaDB database.
12. `txt_to_pdf.py`: Script to convert Text file into PDF file.
13. `cluster_output.json`: JSON extracted after applying clustering on the 3000+ reference documents.
14. `create_cluster_folders.py`: Script for saving each of the different PDF documents into their respective clusters. 
15. `populate_database_by_cluster_output.py`: Script to create and populate the ChromaDB database for each of the clusters.


#### 3. D3.js web application - **viz_frontend/**

D3.js web application which gets model responses from teh FastAPI backend api.

1. `openalexworks.json`: Contains metadata about academic papers, including their titles, abstracts, authors, and related institutions.
2. `ac.py`: A Python script for clustering academic paper abstracts using TF-IDF vectorization and k-means clustering, and saving the results as JSON.
3. `cluster_output.json`: JSON file storing the results of clustering academic papers, including cluster labels, top terms, and associated paper IDs.
4. `file_convert.py`: Python script that converts cluster_output.json into a hierarchical structure for visualization.
5. `hierarchical_output.json`: Hierarchical JSON file used for creating the D3.js visualization.
6. `script.js`: JavaScript file containing D3.js code for creating an interactive circle packing visualization.
7. `index.html`: HTML file that structures the web page and includes necessary scripts and UI elements.

