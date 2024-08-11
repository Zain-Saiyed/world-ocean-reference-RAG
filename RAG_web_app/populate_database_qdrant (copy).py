from langchain.vectorstores import Qdrant
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import CollectionStatus
from qdrant_client.models import PointStruct
from qdrant_client.models import Distance, VectorParams

import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm.notebook import tqdm

import os

# sudo docker pull qdrant/qdrant
# sudo docker run -p 6333:6333 qdrant/qdrant

COLLECTION_NAME = "paper_data"
DATA_PATH = "txt_data"

# eventual list of books
TEXTS = [DATA_PATH+"/"+file_name for file_name in os.listdir(DATA_PATH)]

vectors = []
batch_size = 100
batch = []

model = SentenceTransformer( "msmarco-MiniLM-L-6-v3" )

# Client
client = QdrantClient(host="localhost", port=6333, prefer_grpc=False)


def make_collection(client, collection_name: str):
    """
    Use 1st time on project
    :param client: qdrant client obj
    :type client: client
    :param collection_name: name of collection
    :type collection_name: str
    """
    client.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE),
    )


#
# make_collection(client,COLLECTION_NAME)


# Load Our Text File and split into chunks
def make_chunks(inptext: str):
    """
    Split text into chunks
    :param inptext: the source file
    :type inptext: str
    :return: chunks of text
    :rtype: qd1.texts
    """
    text_splitter = RecursiveCharacterTextSplitter(
        # Set a really small chunk size, just to show.
        separators="\n",
        chunk_size=1000,
        chunk_overlap=20,
        length_function=len,
        add_start_index=True,
    )

    # This is a long document we can split up
    with open(inptext) as f:
        alice = f.read()

    chunks = text_splitter.create_documents([alice])
    return chunks


texts = make_chunks(TEXTS[0])


# Create the VECTORS
# -----------------------------------------
def gen_vectors(texts, model, batch, batch_size, vectors):
    """
    Create payload, encode vectors
    :return vectors : numpy.ndarray
    :return payload : list
    """
    for part in tqdm(texts):
        batch.append(part.page_content)

        if len(batch) >= batch_size:
            vectors.append(model.encode(batch))
            batch = []

    if len(batch) > 0:
        vectors.append(model.encode(batch))
        batch = []
    vectors = np.concatenate(vectors)

    payload = [item for item in texts]
    payload = list(payload)
    vectors = [v.tolist() for v in vectors]
    return vectors, payload


fin_vectors, fin_payload = gen_vectors(
    texts=texts, model=model, batch=batch, batch_size=batch_size, vectors=vectors
)


# Upsert
# -----------------------------------------
def upsert_to_qdrant(fin_vectors, fin_payload):
    """
    Add our vectors and meta into the Vector Database
    :param fin_vectors: _description_
    :type fin_vectors: generator
    :param fin_payload: _description_
    :type fin_payload: list
    """
    collection_info = client.get_collection(collection_name=COLLECTION_NAME)

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            PointStruct(
                id=collection_info.vectors_count + idx, 
                vector=vector, 
                payload=fin_payload[idx]
            )
            for idx, vector in enumerate(fin_vectors)
        ],
    )


# Perform the Upsert !
upsert_to_qdrant(fin_vectors, fin_payload)