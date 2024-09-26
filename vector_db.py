from pymilvus import MilvusClient
from pymilvus import Collection, FieldSchema, CollectionSchema, DataType
from sentence_transformers import SentenceTransformer
import mysql.connector
from configparser import ConfigParser

# Load pre-trained sentence transformer model for generating embeddings
model = SentenceTransformer('all-MiniLM-L6-v2')

# Initialize Milvus client for vector database operations
client = MilvusClient("NatureJournals.db")

# Milvus collection name and metric type for vector similarity search
COLLECTION_NAME = "Journal_Crawler"
METRIC = "COSINE"

# Load configuration from config.ini for MySQL connection details
config = ConfigParser()
config.read('config.ini')


def connect_to_mysql():
    """
    Establishes a connection to the MySQL database using credentials 
    provided in the config.ini file.
    
    Returns:
        conn: MySQL database connection object.
    """
    conn = mysql.connector.connect(
        host=config['mysql']['host'],
        user=config['mysql']['user'],
        password=config['mysql']['password'],
        database=config['mysql']['database'],
        port=config['mysql']['port']
    )
    return conn


def milvus_db_handling():
    """
    Handles Milvus database setup, including creating a collection, defining the schema, 
    inserting data from MySQL (with embeddings for article titles), and indexing fields.
    """
    
    # Define the schema for Milvus collection
    schema = MilvusClient.create_schema(
        auto_id=False,
        enable_dynamic_field=True,
    )
    
    # Add fields for the collection schema: id, vector, and title
    schema.add_field(field_name="id", datatype=DataType.VARCHAR, max_length=100, is_primary=True)
    schema.add_field(field_name="vector", datatype=DataType.FLOAT_VECTOR, dim=384)
    schema.add_field(field_name="Title", datatype=DataType.VARCHAR, max_length=1000)

    # Prepare index parameters for the collection
    index_params = client.prepare_index_params()

    # Add index for id (uncomment and define index_type if needed)
    index_params.add_index(
        field_name="id",
        # index_type="STL_SORT"  # Example, if required by Milvus
    )

    # Add index for vector field, using cosine similarity (FLAT index type)
    index_params.add_index(
        field_name="vector",
        index_type="FLAT",
        metric_type=METRIC,
    )

    # Add index for title field (optional, depending on query type)
    index_params.add_index(
        field_name="Title",
    )

    # Check if the collection exists; if so, drop it to recreate
    if client.has_collection(collection_name=COLLECTION_NAME):
        client.drop_collection(collection_name=COLLECTION_NAME)

    # Create the collection in Milvus with the defined schema and index parameters
    client.create_collection(
        collection_name=COLLECTION_NAME,
        schema=schema,
        index_params=index_params
    )

    # Fetch data from MySQL articles table
    conn = connect_to_mysql()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM articles")
    data = cursor.fetchall()

    # Insert articles data with embeddings into Milvus collection
    for row in data:
        article_id = row[0]
        article_title = row[1]
        
        # Generate embedding for the article title using the Sentence Transformer model
        article_embedding = model.encode(article_title)
        
        # Insert the article data (ID, embedding, title) into Milvus
        print(client.insert(collection_name=COLLECTION_NAME, data=[{
            "id": article_id,
            "vector": article_embedding,
            "Title": article_title
        }]))

    cursor.close()
    conn.close()


if __name__ == '__main__':
    # Start the process of handling Milvus DB setup and inserting data
    milvus_db_handling()
