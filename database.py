import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()


# Function to establish the MySQL connection and execute a query
def execute_query(product_name : str, original_price : float, discounted_price : float):
    password = os.getenv("MYSQL_PASSWORD")
    # Get MySQL connection details from environment variables
    host = "localhost"
    user = "root"
    password = password
    database = "price_pursuit_ai"

    try:
        # Establish a connection
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        
        # Create a cursor object to interact with the database
        cursor = conn.cursor()

        query = f"INSERT INTO SPEED_ADDICTS_PRODUCTS (PRODUCT_NAME, ORIGINAL_PRICE_USD, RUN_TIMESTAMP, DISCOUNTED_PRICE_USD) VALUES ('{product_name}', {original_price}, NOW(), {discounted_price});"

        # Execute the query
        cursor.execute(query)

     
        conn.commit()
        print("Query executed successfully!")

    except mysql.connector.Error as err:
        print(f"Error: {err}")
    
    finally:
        # Close the cursor and connection
        cursor.close()
        conn.close()

def fallback_query(product_name: str):
    password = os.getenv("MYSQL_PASSWORD")
    password = password
    host = "localhost"
    user = "root"
    database = "price_pursuit_ai"

    try:
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )

        cursor = conn.cursor()

        query = f"""
            INSERT INTO SPEED_ADDICTS_PRODUCTS (PRODUCT_NAME, ORIGINAL_PRICE_USD, RUN_TIMESTAMP, DISCOUNTED_PRICE_USD)
            VALUES (%s, NULL, NOW(), NULL);
        """

        cursor.execute(query, (product_name,))
        conn.commit()
        print(f"Fallback query inserted for: {product_name}")

    except mysql.connector.Error as err:
        print(f"Error: {err}")

    finally:
        cursor.close()
        conn.close()
