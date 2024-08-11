import argparse, os, time, shutil, json
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from get_embedding_function import get_embedding_function
from langchain_community.vectorstores import Chroma

BASE_PATH = "database_cluster_pdfs"
DATA_PATH = "clustered_pdfs"
# CLUSTER_INFO_PATH = "cluster_output.json"  

# Load the PDF files
def load_documents(cluster_name):
    cluster_path = os.path.join(DATA_PATH, cluster_name)
    document_loader = PyPDFDirectoryLoader(cluster_path)
    return document_loader.load()

# Split PDF document into chunks
def split_documents(documents):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=80,
        length_function=len,
        is_separator_regex=False,
    )
    return text_splitter.split_documents(documents)

# Delete all existing databases created
def clear_all_databases():
    if os.path.exists(BASE_PATH):
        shutil.rmtree(BASE_PATH)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Reset all databases.")
    args = parser.parse_args()

    if args.reset:
        clear_all_databases()
        print("All Databases deleted!")

    # Loading cluster-PDF information
    # with open(CLUSTER_INFO_PATH, 'r') as f:
    #     cluster_info = json.load(f)

    for cluster_name in os.listdir(DATA_PATH):
        # cluster_name = "CLS_"+str(cluster['cluster'])
        cluster_path = os.path.join(BASE_PATH, cluster_name)
        
        print(f"[*] Processing cluster: {cluster_name}")
        
        # Create the data store for this cluster
        documents = load_documents(cluster_name)
        chunks = split_documents(documents)
        add_to_chroma(chunks, cluster_path, cluster_name)

# Add PDF document to chromaDB
def add_to_chroma(chunks, cluster_path, cluster_name):
    # Create the cluster directory if not exist
    os.makedirs(cluster_path, exist_ok=True)

    # Load or create the database for this cluster
    db = Chroma(
        persist_directory=cluster_path,
        embedding_function=get_embedding_function(),
        collection_name=cluster_name
    )

    # Calculate Page IDs
    chunks_with_ids = calculate_chunk_ids(chunks)

    # Add or Update the documents
    existing_items = db.get(include=[])
    existing_ids = set(existing_items["ids"])
    print(f"Number of existing documents in {cluster_name} DB: {len(existing_ids)}")

    new_chunks = [chunk for chunk in chunks_with_ids if chunk.metadata["id"] not in existing_ids]

    total_new_chunks = len(new_chunks)
    print(f"Total new chunks to add to {cluster_name}: {total_new_chunks}")

    if total_new_chunks:
        batch_size = 100
        for i in range(0, total_new_chunks, batch_size):
            start_time = time.time()

            batch = new_chunks[i:i+batch_size]
            batch_ids = [chunk.metadata["id"] for chunk in batch]
            db.add_documents(batch, ids=batch_ids)
            db.persist()
            
            chunks_added = i + len(batch)
            chunks_remaining = total_new_chunks - chunks_added

            print(f"Progress for {cluster_name}: {chunks_added}/{total_new_chunks} chunks added, {chunks_remaining} remaining | time taken: {time.time()-start_time}")

        print(f"✅ All new documents have been added to the {cluster_name} database")
    else:
        print(f"✅ No new documents to add to {cluster_name}")

# Get teh cunk IDs for each page of the pdfs 
def calculate_chunk_ids(chunks):
    last_page_id = None
    current_chunk_index = 0

    for chunk in chunks:
        source = chunk.metadata.get("source")
        page = chunk.metadata.get("page")
        current_page_id = f"{source}:{page}"

        if current_page_id == last_page_id:
            current_chunk_index += 1
        else:
            current_chunk_index = 0

        chunk_id = f"{current_page_id}:{current_chunk_index}"
        last_page_id = current_page_id

        chunk.metadata["id"] = chunk_id

    return chunks

# Main Function
if __name__ == "__main__":
    main()