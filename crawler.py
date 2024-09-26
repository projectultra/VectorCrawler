import requests
from bs4 import BeautifulSoup
import mysql.connector
from configparser import ConfigParser

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

def drop_and_create_table(cursor):
    """
    Drops the articles table if it exists and recreates it in MySQL. 
    The table stores articles with fields for link, title, authors, 
    publication date, and abstract.
    
    Args:
        cursor: MySQL cursor object to execute SQL commands.
    """
    # Drop the table if it exists
    drop_table_query = "DROP TABLE IF EXISTS articles;"
    cursor.execute(drop_table_query)
    print("Table 'articles' dropped (if it existed).")

    # Create the table again
    create_table_query = """
    CREATE TABLE articles (
        link VARCHAR(100) PRIMARY KEY,
        title TEXT NOT NULL,
        authors TEXT,
        pub_date DATE,
        abstract TEXT
    );
    """
    cursor.execute(create_table_query)
    print("Table 'articles' created.")


def scrape_nature_oncology():
    """
    Scrapes the Nature Oncology page for article titles, links, authors, publication dates, 
    and abstracts, and stores this information in a MySQL database.
    """
    # Establish database connection and create table if not exists
    conn = connect_to_mysql()
    cursor = conn.cursor()

    drop_and_create_table(cursor)

    # SQL query to insert article data into the MySQL database
    query = "INSERT INTO articles (link, title, authors, pub_date, abstract) VALUES (%s, %s, %s, %s, %s)"

    # URL of the Nature Oncology page (modify page number as needed)
    url = "https://www.nature.com/search?order=date_desc&subject=oncology&article_type=research&page=1"
    response = requests.get(url, timeout=10)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Extracting all articles from the page
    articles = soup.find_all('article')

    for article in articles:
        # Extract article title and link
        title_tag = article.find('h3', class_='c-card__title')
        title = title_tag.text.strip()
        article_link = "https://www.nature.com" + title_tag.find('a')['href']

        # Visit the article's detail page
        paper_url = article_link
        response = requests.get(paper_url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        article = soup.find('article')

        # Extract detailed information from the article page
        title = article.find("h1", class_="c-article-title").text

        # Extract authors
        author_list = article.find("ul", class_="c-article-author-list")
        authors = []
        for li in author_list:
            try:
                authors.append(li.find("a").text)
            except AttributeError:
                continue

        # Extract publication date
        pub_date = article.find('time').get('datetime')

        # Extract abstract
        abstract = article.find('section', {'aria-labelledby': 'Abs1'}).find('p').text

        try:
            # Convert list of authors to a string
            authors_string = ', '.join(authors)
            
            # Insert article details into the MySQL database
            cursor.execute(query, (article_link, title, authors_string, pub_date, abstract))
        except mysql.connector.IntegrityError:
            # Skip the article if the link already exists in the database (duplicate entry)
            print(f"Duplicate link found: {article_link}. Skipping this entry.")

    # Commit changes and close the database connection
    conn.commit()
    cursor.close()
    conn.close()


if __name__ == '__main__':
    # Start scraping the Nature Oncology articles and save them to the database
    scrape_nature_oncology()
