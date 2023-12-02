import os
import logging
import configparser
from src.scraper.core import obtain_products, normalize_json, \
    obtain_product_details, generate_output, write_output
from src.scraper.constants import api_url, currency_equivalence, base_url
from definitions import ROOT_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("boots-web-scraper")

config = configparser.ConfigParser()
config.read(os.path.join(ROOT_DIR, 'config.ini'))
api_key = config['boots']['api']

headers = {'Accept': '*/*', 'X-Client-Id': api_key}
query = {
    "query": "",
    "indices": {
        "products": {
            "paging": {
                "index": 0,
                "size": 96
            },
            "criteria": {
                "category": [
                    "wellness",
                    "sleep"
                ],
                "brand": [
                    "Bach Rescue Remedy", "Boots"
                ]
            },
            "sortBy": "mostRelevant"}
    },
    "returnHits": True,
    "returnSuggestions": False,
    "returnFacets": True,
    "returnChanel": False,
    "searchRequired": True,
    "adRequired": True,
    "adParams": {
        "pageId": "viewCategoryApiDesktop",
        "eventType": "viewCategory",
        "environment": "desktop",
        "customerId": "",
        "category": "1860697>1595167"
    }
}

if __name__ == "__main__":
    logger.info("Starting process...")
    # Make request to products API
    products = obtain_products(api_url, query, headers)
    logger.info("Products obtained from API")

    # Normalize Dataframe according to expected output
    df_products = normalize_json(products, currency_equivalence)
    logger.info("Products normalized and transformed to DF")

    # Obtain additional fields from each product's detail
    df_products_detail = obtain_product_details(base_url, df_products)
    logger.info("Product details retrieved")

    output = generate_output(df_products_detail)
    logger.info("Output generated correctly")

    write_output(output, ROOT_DIR, 'output', 'output.json')
    logger.info("Output file written")
    logger.info("Process ended...")
