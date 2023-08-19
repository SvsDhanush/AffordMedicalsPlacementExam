from fastapi import FastAPI, Query
import requests
import concurrent.futures
from cachetools import TTLCache
from typing import List


app = FastAPI()

cache = TTLCache(maxsize=100, ttl=500)

def get_numbers_from_url(url):
    cached_numbers = cache.get(url)
    if cached_numbers is not None:
        return cached_numbers

    try:
        response = requests.get(url, timeout=0.5) 
        if response.status_code == 200:
            data = response.json()
            numbers = data.get("numbers", [])
            cache[url] = numbers  
            return numbers\
            
        else:
            return []
    except requests.Timeout:
        print("Request to URL timed out:", url)
        return []
    except Exception as e:
        print("Error fetching data from URL:", e)
        return []

@app.get("/numbers")
async def get_numbers(urls: List[str] = Query(..., description="List of URLs")):
    all_numbers = []

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_url = {executor.submit(get_numbers_from_url, url): url for url in urls}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            numbers = future.result()
            all_numbers.extend(numbers)

    unique_numbers = list(set(all_numbers))
    unique_numbers.sort()

    response_data = {"numbers": unique_numbers}
    return response_data

