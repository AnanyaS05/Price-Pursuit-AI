from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
load_dotenv()

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.documents import Document
from langchain_core.tools import tool

from agent import Agent
from custom_search import CustomSearch
from scrape import Scrape

import json

customSearch = CustomSearch()
scrapeTool = Scrape()
import database

app = FastAPI()


@tool
def web_search_tool(query: str, num: int) -> list[Document]:
    """Search the web for a query and return the top num results."""
    urls = customSearch.search(query, num)
    print("URLS:", urls)
    documents = []
    for url in urls:
        documents.append(scrapeTool.scrape(url))
    return documents

message = SystemMessage(
    content = """You are a AI Agent whose job is to compare prices of products from competitor websites.
                    You work for Comoto, a retailer of sports bikes and accessories. You are to scrape its competitor website, www.speedaddicts.com \
                    to get the prices of the given products.

                    You have access to the following tool:
                    web_search_tool - This tool would scrape the data from the competitor website and give you the scraped data. The tools takes in a query \
                    which is the search query and an integer num which is the number of results to return as inputs. It returns the scraped data from those urls as \
                    output.
                    You can call this tool either sequentially or together as well. You must call this tool enough times to gather information on all different products when asked for a category. 
                    You must call this tool as many times as required to get all the products under a category.
                    Your job is to search for the name and price of the given product or products under a given category. Display the product name and its price in the format of product name: price.

                    When asked to find products within a category, ensure the results showcase different brands and models.
                    Avoid including multiple color variations of the same product model in the results.
                    Focus on providing a diverse set of options within the specified category.

                    To achieve diversity and meet the minimum of 5 different products when searching by category, you should strategically use the `web_search_tool`.
                    Consider the following strategies:\
                    1.  Start with a broad category search (e.g., "full face helmet") with `num` set to a reasonable number (e.g., 3).
                    2.  Analyze the results. If you have fewer than 5 distinct products (different brands or models), identify promising brands from the initial results.
                    3.  Make subsequent calls to the `web_search_tool`, focusing on specific brands identified in the previous step (e.g., query="Shoei full face helmet", num=2).
                    4.  You can also try searching for different types within the category if applicable (e.g., for "motorcycle jackets", you might search for "leather motorcycle jacket" and "textile motorcycle jacket").
                    5.  Continue calling the tool until you have gathered information on at least 5 distinct products.
                    6.  If an item is on sale, mention what its original price was and what its current price is, along with the discount applied, if any.

                    If you are asked to find all the products and their prices under a category, display the list of all the products and their \
                    prices that fall under that category, ensuring variety in brands and models, and aim for different products.

                    If you get any of these tasks, you have to use the web_search_tool to \
                    search for the price of the given product or products under a given category, ensuring you find information for different products.

                    If you are asked to find the price of a particular product, search for that particular product and display its price.
                    If the task is something other than this, you have to act accordingly to give the best possible response to the user."

                    If there is no discounted price for a product, the discounted price should be the same as the original price.
                    Give the final output only in the following python dictionary format: {product1 name : [original price of product 1, discounted price of product 1], product2 name : [original price of product 2, discounted price of product 2]}.
                    Enclose the keys in the dictionary in double quotes ("").
                    Give me only the python dictionary with no other text or symbols.
                  """
)


priceAgent = Agent([web_search_tool], [message])

class PriceRequest(BaseModel):
    input : str

class PriceResponse(BaseModel):
    result : str

@app.post("/get-price", responseModel = PriceResponse)
async def get_price_endpoint(request = PriceRequest):
    try:
        # Invoke the backend  gent
        result = priceAgent.graph.invoke({"messages": [HumanMessage(content=user_input)]})

        # Extract and return the final message content
        output = result["messages"][-1].content

        print(output)
        opening_index = output.index("{")
        closing_index = output.index("}")
        formatted_output = output[opening_index:(closing_index+1)]
        
        json_output = json.loads(formatted_output)

        str_output = ""

        for i in json_output:
            database.execute_query(i, float(str(json_output[i][0]).strip("$")), float(str(json_output[i][1]).strip("$")))
            str_output+= f" The product is {i}, whose original is {json_output[i][0]} and discounted price is {json_output[i][1]}\n"

        return str_output
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


'''
# --- Main function ---
def get_product_price(user_input: str) -> str:
    """Takes a product name, queries the backend, and returns the price info."""
    # Invoke the backend  gent
    result = priceAgent.graph.invoke({"messages": [HumanMessage(content=user_input)]})

    # Extract and return the final message content
    output = result["messages"][-1].content

    print(output)
    opening_index = output.index("{")
    closing_index = output.index("}")
    formatted_output = output[opening_index:(closing_index+1)]
    
    json_output = json.loads(formatted_output)

    str_output = ""

    for i in json_output:
        database.execute_query(i, float(str(json_output[i][0]).strip("$")), float(str(json_output[i][1]).strip("$")))
        str_output+= f" The product is {i}, whose original is {json_output[i][0]} and discounted price is {json_output[i][1]}\n"

    return str_output

   
#print(get_product_price("Show me the price of the NORU Maruchi Perforated Leather Black Jacket from the competitor website."))
'''