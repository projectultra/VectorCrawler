from sentence_transformers import SentenceTransformer
from pymilvus import MilvusClient

# Initialize the Milvus client and the sentence transformer model
client = MilvusClient("NatureJournals.db")
model = SentenceTransformer('all-MiniLM-L6-v2')

# Metric type used for searching in Milvus (COSINE similarity)
METRIC = "COSINE"


def search_articles(query_text):
    """
    Searches for articles in the Milvus vector database based on the user's free-text query.
    
    Args:
        query_text (str): Free-text input from the user to search for relevant articles.

    Returns:
        res: The search results containing the article IDs and titles that match the query.
    """
    # Convert the user's query into an embedding vector
    query_embedding = [model.encode(query_text).tolist()]

    # Perform the search in Milvus using cosine similarity and return the top 2 results
    res = client.search(
        collection_name="Journal_Crawler",  # Name of the Milvus collection
        data=query_embedding,  # Embedding vector for the query
        limit=2,  # Return top 2 search results
        search_params={"metric_type": METRIC, "params": {}},  # Use cosine similarity
        output_fields=[
            "id",   # Article ID field
            "Title" # Article Title field
        ],
    )

    return res


if __name__ == '__main__':
    # User input: Example query to search for relevant journal articles
    user_query = "Give me the journals published about neuropathy and antibodies"
    
    # Get the search results from Milvus
    results = search_articles(user_query)
    
    # Print out the search results (IDs and Titles of the articles)
    print(results)
