import feedparser
import json

rss_url = 'https://anchor.fm/s/12ab1e4c/podcast/rss'

feed = feedparser.parse(rss_url)
with open('rss_feedparser.json', 'w', encoding='utf-8') as feed_json:
    json.dump(feed, feed_json, indent=4, ensure_ascii=False)

podcast_title = feed['feed']['title']
print('podcast_title')
print(podcast_title)
print()

episode_title = feed.entries[0]['title']
print('episode_title')
print(episode_title)
print()

episode_image = feed['feed']['image'].href
print('episode_image')
print(episode_image)
print()

episode_mp3 = 'Error'
for item in feed.entries[0].links:
    print('item')
    print(item)
    print()

    if item['type'] == 'audio/mpeg':
        episode_mp3 = item.href
    elif item['type'] == 'audio/x-m4a':
        episode_mp3 = item.href

print('episode_mp3')
print(episode_mp3)
for i, entry in enumerate(feed['entries']):
    for link in entry['links']:
        if link['type'] == 'audio/mpeg' and link['href'] == episode_mp3:
            entry_idx = i
            print('entry_idx')
            print(entry_idx)
        elif link['type'] == 'audio/x-m4a' and link['href'] == episode_mp3:
            entry_idx = i
            print('entry_idx')
            print(entry_idx)
