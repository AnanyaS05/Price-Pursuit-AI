from dotenv import load_dotenv
load_dotenv()

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.documents import Document
from langchain_core.tools import tool

from agent import Agent
from custom_search import CustomSearch
from scrape import Scrape

customSearch = CustomSearch()
scrapeTool = Scrape()

@tool
def web_search_tool(query: str, num: int) -> list[Document]:
    """Search the web for a query and return the top num results."""
    urls = customSearch.search(query, num)
    print(f"Scraping {len(urls)} URLs")
    print(urls)
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
                You can call this tool either sequentially or together as well. You can call this tool multiple times as well.
                Your job is to search for the name and price of the given product in the scraped data and display it along with the product name. \
                If you get this task, \
                you have to use the web_search_tool to \
                search for the price of the given product.
                If the task is something other than this, you have to act accordingly to give the best possible response to the user."""
)
priceAgent = Agent([web_search_tool], [message])

user_input = "Give me the price of the AlpineStars Helmets from the competitor website."

result = priceAgent.graph.invoke({"messages": [HumanMessage(content=user_input)]})

print(result["messages"][-1].content)
