import csv
import json

import feedparser
import hashlib
import os
import re
import requests
from apscheduler.schedulers.blocking import BlockingScheduler
from bs4 import BeautifulSoup
from dotenv import dotenv_values
from json import loads
from twitchAPI.twitch import Twitch
from urllib.parse import urljoin, urlparse

config = {
    **dotenv_values(".env"),
    **os.environ,
}

items = []


def remove_html_tags(text):
    import re
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)


def get_data(type, uid, label):
    twitch = Twitch(config['TWITCH_CLIENT_ID'], config['TWITCH_CLIENT_SECRET'])
    youtube_playlist = 'https://www.googleapis.com/youtube/v3/playlistItems'

    print(type + ' : ' + label)

    """
    Twitch
    """

    if type == 'twitch':
        stream = twitch.get_streams(user_login=[uid])

        if stream['data']:
            data = stream['data'][0]
            if data['game_name'] == 'Guild Wars 2' and data['type'] == 'live':
                item = {
                    'uid': data['id'],
                    'type': 'twitch',
                    'title': data['title'],
                    'text': '',
                    'thumbnail': data['thumbnail_url'].replace('{width}', '1280').replace('{height}', '720'),
                    'user_id': data['user_login'],
                    'user_name': data['user_name'],
                    'url': '',
                    'published_at': data['started_at']
                }
                items.append(item)

    """
    YouTube
    """

    if type == 'youtube':
        youtube = youtube_playlist + '?part=snippet&playlistId=' + uid + '&key=' + config['YOUTUBE_API_KEY'] + '&maxResults=10'
        r = requests.get(url=youtube)
        data = loads(r.text)
        for data in data['items']:

            pattern = r"(#guildwars2?|#gw2?)"
            title_match = len(re.findall(pattern, data['snippet']['title'], re.MULTILINE | re.IGNORECASE))
            description_match = len(re.findall(pattern, data['snippet']['description'], re.MULTILINE | re.IGNORECASE))

            if title_match or description_match:
                if 'maxres' in data['snippet']['thumbnails']:
                    thumbnail = data['snippet']['thumbnails']['maxres']['url']
                elif 'standard' in data['snippet']['thumbnails']:
                    thumbnail = data['snippet']['thumbnails']['standard']['url']
                else:
                    thumbnail = data['snippet']['thumbnails']['high']['url']

                item = {
                    'uid': data['snippet']['resourceId']['videoId'],
                    'type': 'youtube',
                    'title': data['snippet']['title'],
                    'text': data['snippet']['description'],
                    'thumbnail': thumbnail,
                    'user_id': data['snippet']['videoOwnerChannelId'],
                    'user_name': data['snippet']['videoOwnerChannelTitle'],
                    'url': '',
                    'published_at': data['snippet']['publishedAt']
                }
                items.append(item)

    """
    RSS
    """

    if type == 'rss':
        feed = feedparser.parse(uid)

        for entry in feed.entries:

            image = ''

            if 'content' in entry:
                content = entry.content[0].value
            else:
                content = entry.summary

            if content:
                tree = BeautifulSoup(content, 'html.parser')
                img_link = tree.find('img')
                if img_link:
                    image = urljoin(img_link.get('src'), urlparse(img_link.get('src')).path)

            if not image:
                req = requests.get(entry.link)
                soup = BeautifulSoup(req.content, 'html.parser')
                thumbnail = soup.find("meta", property="og:image")

                if thumbnail:
                    image = thumbnail['content']
            item = {
                'uid': hashlib.md5(str(entry.link).encode('utf-8')).hexdigest(),
                'type': 'rss',
                'title': entry.title,
                'text': remove_html_tags(entry.summary),
                'thumbnail': image,
                'user_id': '',
                'user_name': label,
                'url': entry.link,
                'published_at': entry.published
            }
            items.append(item)


def get_feeds():
    print("Vérification des nouveaux contenus")

    with open('feeds.csv', encoding="utf-8") as file:

        reader = csv.DictReader(file, delimiter=',')

        for line in reader:
            get_data(line['type'], line['uid'], line['label'])

        if items:
            print('Enregistrement des données...')
            r = requests.post(config['LBM_API_FEED_URL'], data={'items': json.dumps(items, separators=(',', ':'))})
            print(r.text)


scheduler = BlockingScheduler()
get_feeds()
scheduler.add_job(get_feeds, 'interval', minutes=15, id='get_feeds')
scheduler.start()
