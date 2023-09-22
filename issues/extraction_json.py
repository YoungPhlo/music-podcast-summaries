from bs4 import BeautifulSoup
import json
import requests
import re

# Apple Podcast URL
pod = 'https://podcasts.apple.com/us/podcast/being-a-gangsta-gets-you-to-jail-dj-akademiks-keeps/id1495188313?i=1000566535963'


def extract_json_from_url(url):
    response = requests.get(url)
    if response.status_code != 200:
        return None, f"Failed to fetch URL with status code: {response.status_code}"
    return extract_json_from_content(response.text)


def extract_json_from_content(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    potential_json_strings = []
    for script in soup.find_all('script'):
        if script.string:
            script_str = script.string.strip()
            if script_str.startswith('{') and script_str.endswith('}'):
                potential_json_strings.append(script_str)
    successfully_parsed_json = []
    failed_to_parse_json = []
    for json_str in potential_json_strings:
        try:
            parsed_dict = json.loads(json_str)
            successfully_parsed_json.append(parsed_dict)
        except json.JSONDecodeError:
            failed_to_parse_json.append(json_str)
    return successfully_parsed_json, failed_to_parse_json


successful_json, failed_json = extract_json_from_url(pod)

asset_json = None
catalog_value = None

# Search for the dictionary containing 'catalog.us.podcast-episodes' key
for json_obj in successful_json:
    for key in json_obj.keys():
        if 'catalog.us.podcast-episodes' in key:
            asset_json = json_obj
            catalog_value = json_obj[key]
            break
    if asset_json:
        break


# Convert the JSON string to a Python dictionary
catalog_value = json.loads(catalog_value)

asset_url = None
# Check if 'd' key exists and that it's a list
if 'd' in catalog_value and isinstance(catalog_value['d'], list):
    # Iterate through the list to find the dictionary containing 'assetUrl'
    for item in catalog_value['d']:
        if 'attributes' in item and 'assetUrl' in item['attributes']:
            asset_url = item['attributes']['assetUrl']
            break


with open('pod.json', 'w', encoding='utf-8') as scraped_json:
    json.dump(successful_json, scraped_json, indent=4, ensure_ascii=False)

with open('catalog_value.json', 'w', encoding='utf-8') as catalog:
    json.dump(catalog_value, catalog, indent=4, ensure_ascii=False)

print(asset_url)

