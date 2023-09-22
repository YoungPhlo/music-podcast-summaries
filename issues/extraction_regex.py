import requests
import re

# Test the function with sample URLs
sample_podcast_url = "https://podcasts.apple.com/us/podcast/latent-space-the-ai-engineer-podcast-codegen-agents/id1674008350"
sample_episode_url = 'https://podcasts.apple.com/us/podcast/rwkv-reinventing-rnns-for-the-transformer-era-with/id1674008350?i=1000626225028'


def asset_url(html_content):
    # Step 1: Find the JSON dictionary within the HTML
    match = re.search(r'\\"assetUrl\\":\\"(.*?)\\"', html_content)
    print(match)

    if match:
        print("Match found in html_content")
        # Step 2: Clean and decode the JSON
        raw_asset_url = match.group(1)
        real_asset_url = raw_asset_url.encode().decode('unicode_escape')

        return real_asset_url
    return None


def podcast_info(apple_podcast_link):
    # Extract the podcast ID and episode ID (if available) from the Apple Podcast link using regular expression
    podcast_match = re.search(r'id(\d+)', apple_podcast_link)
    episode_match = re.search(r'i=(\d+)', apple_podcast_link)

    podcast_id = podcast_match.group(1) if podcast_match else None
    episode_id = episode_match.group(1) if episode_match else None

    print(podcast_id)
    print(episode_id)

    if episode_id:
        response = requests.get(apple_podcast_link)

        html_content = response.text
        mp3_file = asset_url(html_content)

        return mp3_file


def anti_regex(apple_podcast_link):
    # Function to find next occurrence of non-digit character position
    def find_next_non_digit_pos(s, start):
        for i, c in enumerate(s[start:]):
            if not c.isdigit():
                return start + i
        return len(s)

    # Find position of 'id' and 'i='
    start_podcast_id = apple_podcast_link.find('id') + 2
    start_episode_id = apple_podcast_link.find('i=') + 2

    # Find next occurrence of non-digit character for both ids
    end_podcast_id = find_next_non_digit_pos(apple_podcast_link, start_podcast_id)
    end_episode_id = find_next_non_digit_pos(apple_podcast_link, start_episode_id)

    # Slice the string to get the ids
    podcast_id = apple_podcast_link[start_podcast_id:end_podcast_id]
    episode_id = apple_podcast_link[start_episode_id:end_episode_id]


with_ep = podcast_info(sample_episode_url)
print(with_ep)
