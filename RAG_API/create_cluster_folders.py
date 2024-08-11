import os
import shutil
import json

# Path configurations
SOURCE_PDF_PATH = "pdf_data"
CLUSTER_JSON_PATH = "cluster_output.json"
DESTINATION_BASE_PATH = "clustered_pdfs"

# Function to copy pdf files into their respective cluster name 
def copy_pdfs_to_clusters():
    # Load cluster output information
    with open(CLUSTER_JSON_PATH, 'r') as f:
        cluster_info = json.load(f)

    # Create the destination directory if not exist
    os.makedirs(DESTINATION_BASE_PATH, exist_ok=True)

    for cluster in cluster_info:
        # Get cluster ID and abstract IDs
        cluster_id = cluster['cluster']
        abstract_ids = cluster['abstract_ids']

        # Creating folder for this cluster
        cluster_folder = os.path.join(DESTINATION_BASE_PATH, f"CLS_{cluster_id}")
        os.makedirs(cluster_folder, exist_ok=True)

        for abstract_id in abstract_ids:
            # Extract filename from abstract_id
            filename = abstract_id.split('/')[-1] + ".pdf"
            source_path = os.path.join(SOURCE_PDF_PATH, filename)
            destination_path = os.path.join(cluster_folder, filename)

            # If source file not exists then copy pdf file into folder else Warn
            if os.path.exists(source_path):
                shutil.copy2(source_path, destination_path)
                print(f"Copied {filename} to {cluster_folder}")
            else:
                print(f"Warning: {filename} not found in {SOURCE_PDF_PATH}")

    print("PDF copying process completed.")

# Main function
if __name__ == "__main__":
    copy_pdfs_to_clusters()