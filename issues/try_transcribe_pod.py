from bs4 import BeautifulSoup
import feedparser
import requests
import json
import re

pod = 'https://podcasts.apple.com/us/podcast/being-a-gangsta-gets-you-to-jail-dj-akademiks-keeps/id1495188313?i=1000566535963'


def get_transcribe_podcast(apple_link, local_path):
    # Extract the podcast ID and episode ID (if available) from the Apple Podcast link using regular expression
    podcast_id = re.search(r'id(\d+)', apple_link).group(1)
    episode_id = re.search(r'i=(\d+)', apple_link)

    if episode_id:
        episode_id = episode_id.group(1)

    lookup_url = f"https://itunes.apple.com/lookup?id={podcast_id}"
    lookup_response = requests.get(lookup_url)
    lookup_data = lookup_response.json()

    rss_feed = None
    if "results" in lookup_data and len(lookup_data["results"]) > 0:
        podcast_json = lookup_data["results"][0]
        rss_feed = podcast_json.get("feedUrl")

    else:
        print("\n\nRSS feed URL not found!")

    print("Starting Podcast Transcription Function")
    print("Feed URL: ", rss_feed)
    print("Local Path:", local_path)
    entry_idx = 0

    if episode_id:
        apple_response = requests.get(apple_link)
        if apple_response.status_code != 200:
            f"Failed to fetch {apple_link} with status code: {apple_response.status_code}"
        apple_html = apple_response.text

        soup = BeautifulSoup(apple_html, 'html.parser')
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

        successful_json = successfully_parsed_json

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

        mp3_url = None
        # Check if 'd' key exists and that it's a list
        if 'd' in catalog_value and isinstance(catalog_value['d'], list):
            # Iterate through the list to find the dictionary containing 'assetUrl'
            for item in catalog_value['d']:
                if 'attributes' in item and 'assetUrl' in item['attributes']:
                    mp3_url = item['attributes']['assetUrl']
                    break

        parsed_rss = feedparser.parse(rss_feed)
        for i, entry in enumerate(parsed_rss['entries']):
            for link in entry['links']:
                if link['type'] == 'audio/mpeg' and link['href'] == mp3_url:
                    entry_idx = i
                elif link['type'] == 'audio/x-m4a' and link['href'] == mp3_url:
                    entry_idx = i

    else:
        parsed_rss = feedparser.parse(rss_feed)

    # Read from the RSS Feed URL
    podcast_title = parsed_rss['feed']['title']
    episode_title = parsed_rss.entries[entry_idx]['title']
    episode_image = parsed_rss['feed']['image'].href
    print("Podcast Title: ", podcast_title)
    print("Episode Title: ", episode_title)
    episode_mp3 = 'Error'
    for item in parsed_rss.entries[entry_idx].links:
        if item['type'] == 'audio/mpeg':
            episode_mp3 = item.href
        elif item['type'] == 'audio/x-m4a':
            episode_mp3 = item.href
    episode_name = "full_podcast_episode.mp3"
    print("Episode URL: ", episode_mp3)


get_transcribe_podcast(pod, '/content/podcast/')
