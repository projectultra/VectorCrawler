#!/bin/bash
# Run the crawling script
python crawler.py

# Store vector embeddings in Milvus
python vector_db.py

# Search articles
python search.py