import os
from googleapiclient.discovery import build
from authorization import authorization

class CustomSearch:
    def __init__(self):
        self.__auth = authorization()
        self.__creds = self.__auth.cred_token_auth()
        self.__service = build("customsearch", "v1", credentials=self.__creds)
    
    def search(self, query: str, num: int) -> list[str]:
        try:
            search = self.__service.cse().list(
                cx=os.getenv("SEARCH_ENGINE_ID"),
                lr="lang_en", # To search in English language
                num=num, # Number of search results
                q=query, # Search query
                c2coff=1, # To disable search results in chinese
                hl="en" # To search in English language
            ).execute()
            
            items = search["items"]
            urls = [item["link"] for item in items] # Extracting URLs from search results
            return urls
        
        except Exception as error:
            raise error