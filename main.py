from dotenv import load_dotenv
load_dotenv()

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.documents import Document
from langchain_core.tools import tool

from agent import Agent
from custom_search_sa import CustomSearch
from scrape import Scrape

from playwright.async_api import async_playwright

import json
import asyncio

customSearch = CustomSearch()
import database


@tool
async def web_search_tool(query: str, num: int) -> list[Document]:
    """Search the web for a query and return the top num results asynchronously.
    
    The search is done synchronously, but scraping each URL is done in parallel."""

    urls = customSearch.search(query, num, "www.speedaddicts.com")
    print("URLS:", urls)

    if urls == ['No results found.']:
        print(f"No URLs found for query: {query}. Falling back to database.")
        # Fallback: query from your local database
        database.fallback_query(query)
        return []

    # Create tasks for scraping each URL concurrently.
    tasks = [scrapeTool.ascrape(url) for url in urls]
    
    # Await all scraping tasks concurrently.
    documents = await asyncio.gather(*tasks)

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




# --- Main function ---
async def get_product_price_async(product_names: list[str], user_query: str) -> str:
    """Takes a list of product names and a query, invokes the agent, 
    writes prices or fallbacks to the database, and returns a summary."""
    
    # Invoke the agent
    result = await priceAgent.graph.ainvoke({
        "messages": [HumanMessage(content=user_query)]
    })
    output = result["messages"][-1].content

    # Check for JSON payload
    if "{" not in output or "}" not in output:
        # No JSON at all: fallback for every product
        for name in product_names:
            database.fallback_query(name)
        return "No prices returned—logged fallback for all products."

    # Extract the JSON substring
    start = output.index("{")
    end   = output.rindex("}") + 1
    try:
        prices_dict = json.loads(output[start:end])
        print(prices_dict)
    except json.JSONDecodeError:
        # Bad JSON: fallback for all
        for name in product_names:
            database.fallback_query(name)
        return "Malformed JSON—logged fallback for all products."

    found = set(prices_dict.keys())
    lines = []

    # Insert valid prices or fallback on invalid
    for name, (orig, disc) in prices_dict.items():
        orig_str = str(orig).lstrip("$")
        disc_str = str(disc).lstrip("$")
        try:
            orig_val = float(orig_str)
            disc_val = float(disc_str)
            database.execute_query(name, orig_val, disc_val)
            lines.append(f"✔ {name}: original={orig}, discounted={disc}")
        except ValueError:
            database.fallback_query(name)
            lines.append(f"⚠ {name}: invalid price (‘{orig}/{disc}’), logged fallback")

    # Fallback for any names not returned
    for name in product_names:
        if name not in found:
            database.fallback_query(name)
            lines.append(f"⚠ {name}: not found, logged fallback")

    return "\n".join(lines)

async def main():
    product_names = ["DBK Recking Crew Premium T-Shirt", "Klim Kaos Youth Pants", "Continental ContiStreet Tires",
        "Dainese Druid 4 Gloves"]
    query = "Show me the price of the DBK Recking Crew Premium T-Shirt, Klim Kaos Youth Pants, Continental ContiStreet Tires and the Dainese Druid 4 Gloves from the competitor website."
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        global scrapeTool
        scrapeTool = Scrape(browser)
        result_str = await get_product_price_async(product_names, query)
        print(result_str)

if __name__ == "__main__":
    asyncio.run(main())
