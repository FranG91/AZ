import os
import json
import requests
import pandas as pd
import requests_mock
from definitions import ROOT_DIR
from src.scraper.constants import currency_equivalence
from src.scraper.core import obtain_products, request_product_details, get_short_description, normalize_json, \
    obtain_product_details, get_size_in_kb, generate_output, write_output


class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

def test_obtain_products(requests_mock):
    fake_url = 'https://some-url/'
    fake_headers = {'token': '123456789'}
    fake_query = {"some_query": "query"}

    requests_mock.post(url=fake_url, headers=fake_headers, json={'mock_response': 'mock'})
    fake_response = obtain_products(fake_url, fake_query, fake_headers)

    assert fake_response == {'mock_response': 'mock'}


def test_request_product_details(requests_mock):
    fake_url = 'https://some-url/'

    requests_mock.get(url=fake_url)
    fake_response = request_product_details(fake_url)

    assert fake_response.status_code == 200


def test_get_short_description():
    input = {
        "text": """<!DOCTYPE html>
<html>
  <head>
    <title>Photos</title>
  </head>
  <body>
    <h1>Photos</h1>
    <div class="photo">
      <img src="photos/IMG_5115.jpg">
    </div>
<div class="product_text">
	<p itemprop="description" id="product_shortdescription_2264934">This is a test!</p>
	<div class="clear_float"></div>		
</div>
  </body>
</html>"""
    }

    short_desc = get_short_description(dotdict(input))

    assert short_desc == 'This is a test!'


def test_normalize_json():

    input_test = {
        'products': {
            'hits': [{
                'title': 'This is a test title',
                'referenceUri': 'fake1',
                'reviews': {
                    'average': 4.5
                    },
                'pricing': {
                    'regular': {
                        'value': 15,
                        'currency': 'EUR'
                    }
                }
            },
            {
                'title': 'This is another test title',
                'referenceUri': 'fake2',
                'reviews': {
                    'average': 5
                },
                'pricing': {
                    'regular': {
                        'value': 10,
                        'currency': 'GBP'
                    }
                }
            }]
        }
    }

    normalized_test_df = normalize_json(input_test, currency_equivalence)

    assert not normalized_test_df.empty


def test_get_size_in_kb():
    test_data = dotdict({'content': {
        "text": """<!DOCTYPE html>
    <html>
      <head>
        <title>Photos</title>
      </head>
      <body>
        <h1>Photos</h1>
        <div class="photo">
          <img src="photos/IMG_5115.jpg">
        </div>
    <div class="product_text">
    	<p itemprop="description" id="product_shortdescription_2264934">This is a test!</p>
    	<div class="clear_float"></div>		
    </div>
      </body>
    </html>"""
    }
        })
    size_kb = get_size_in_kb(test_data)

    assert size_kb > 0

def test_obtain_product_details(requests_mock):
    fake_url = 'https://some-url/'
    # Test data without short description
    test_data = {'product': ['x', 'y'], 'ReferenceUri': ['fake1', 'fake2'], 'details': [{
        "text": """<!DOCTYPE html>
<html>
  <head>
    <title>Photos</title>
  </head>
  <body>
    <h1>Photos</h1>
    <div class="photo">
      <img src="photos/IMG_5115.jpg">
    </div>
  </body>
</html>"""
    },         {"text": """<!DOCTYPE html>
<html>
  <head>
    <title>Photos</title>
  </head>
  <body>
    <h1>Photos</h1>
    <div class="photo">
      <img src="photos/IMG_5115.jpg">
    </div>
  </body>
</html>"""}]
                 }
    test_df = pd.DataFrame(data=test_data)
    test_df.apply(lambda x: requests_mock.get(fake_url + x['ReferenceUri']), axis=1)

    df_details = obtain_product_details(fake_url, test_df)

    assert not df_details.empty


def test_generate_output():
    test_data = {'Product': ['x', 'y', 'z'], 'Price': [4, 6, 8]}
    test_df = pd.DataFrame(data=test_data)

    output = generate_output(test_df)

    assert bool(output)
    assert output['Median'] == 6


def test_write_output():
    test_output = {
        'Median': 6.0,
        'Products': [
            {
                'Price': 4,
                'Product': 'x'
            },
            {
                'Price': 6,
                'Product': 'y'
            },
            {
                'Price': 8,
                'Product': 'z'
            }
        ]
    }

    test_desired_dir = 'tests\\output'
    test_output_name = 'output_test.json'

    write_output(test_output, ROOT_DIR, test_desired_dir, test_output_name)

    test_file_name = os.path.join(ROOT_DIR, test_desired_dir, test_output_name)

    with open(test_file_name) as file_path:
        test_output_data = json.load(file_path)
    # Check that the data is the same as the one being written
    assert test_output_data == test_output