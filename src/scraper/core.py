import os
import sys
import json
import requests
import pandas as pd
from bs4 import BeautifulSoup

def obtain_products(url, query, headers):
    products_response = requests.post(url, json=query, headers=headers).text
    return json.loads(products_response)


def request_product_details(url):
    product_details_response = requests.get(url)

    return product_details_response


def get_short_description(details):
    try:
        soup = BeautifulSoup(details.text, 'html.parser')
        short_desc = (soup.find(class_='product_text')).text.strip()
    except:
        short_desc = ''
    return short_desc


def normalize_json(input_json, currency_equivalence):
    products_necessary_fields = []
    # List with all the products and the corresponding attributes
    product_details = input_json['products']['hits']

    for product in product_details:
        product_to_create = {}
        product_to_create['Title'] = product['title']
        product_to_create['Rating'] = product['reviews']['average']
        product_to_create['Price'] = product['pricing']['regular']['value']
        product_to_create['Price_Unit'] = currency_equivalence[product['pricing']['regular']['currency']]
        product_to_create['ReferenceUri'] = product['referenceUri']
        products_necessary_fields.append(product_to_create)

    return pd.json_normalize(products_necessary_fields)


def get_size_in_kb(details):
    size_in_bytes = sys.getsizeof(details.content)

    return size_in_bytes / 1000


def obtain_product_details(url, df):
    # Request product details for each product and store them on a temporary field
    df['details'] = df.apply(lambda x: request_product_details(url + x['ReferenceUri']), axis=1)
    # Obtain page size for each product
    df['Page_Size'] = df.apply(lambda x: get_size_in_kb(x['details']), axis=1)
    # Obtain short description if available for each product
    df['Short_Desc'] = df.apply(lambda x: get_short_description(x['details']), axis=1)
    # Delete unnecessary field
    df_details = df.drop(['details', 'ReferenceUri'], axis=1)

    return df_details


def generate_output(df):
    final_output = {}
    # Calculate median price
    median_price = df['Price'].median()

    records = df.to_dict('records')

    final_output['Products'] = records
    final_output['Median'] = median_price

    return final_output


def write_output(output, ROOT_DIR, desired_dir, output_name):
    output_dir = os.path.join(ROOT_DIR, desired_dir)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(os.path.join(output_dir, output_name), "w+", encoding='utf-8') as file_path:
        json.dump(output, file_path)

