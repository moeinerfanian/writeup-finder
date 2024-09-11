import requests, pwn, os, psycopg2, time
import xml.etree.ElementTree as ET
from datetime import datetime
from config import *
from bs4 import BeautifulSoup
from datetime import datetime
# Database connection setup
def get_db_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    return conn

def is_link_processed(conn, table_name, link):
    with conn.cursor() as cursor:
        cursor.execute(f"SELECT 1 FROM {table_name} WHERE link = %s", (link,))
        return cursor.fetchone() is not None

def save_processed_link(conn, table_name, link, title, pub_date):
    with conn.cursor() as cursor:
        cursor.execute(
            f"INSERT INTO {table_name} (link, title, pub_date) VALUES (%s, %s, %s)",
            (link, title, pub_date)
        )
        conn.commit()

def fetch_rss_data(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0'}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        pwn.log.error(f"Failed to fetch data from {url}. Status code: {response.status_code}")
        return []

    response_content = response.content.decode('utf-8')

    try:
        root = ET.fromstring(response_content)
    except ET.ParseError as e:
        pwn.log.error(f"Failed to parse XML: {e}")
        return []

    namespace = {'atom': 'http://www.w3.org/2005/Atom'}

    items = []
    for item in root.findall(".//atom:entry", namespace):
        title_element = item.find("atom:title", namespace)
        link_element = item.find("atom:link", namespace)
        pub_date_element = item.find("atom:published", namespace)

        title = title_element.text if title_element is not None else 'No Title'
        link = link_element.attrib['href'] if link_element is not None else 'No Link'
        pub_date = pub_date_element.text if pub_date_element is not None else 'No Date'

        items.append({"title": title, "link": link, "pub_date": pub_date})
        pwn.log.info(f"Video found: {title} - {link}")

    return items

def fetch_medium_writeups(file_path):
    items = []
    headers = {'User-Agent': 'curl/7.81.0', 'accept': '*/*'}

    with open(file_path, 'r') as file:
        urls = file.readlines()

    for url in urls:
        url = url.strip()
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                try:
                    root = ET.fromstring(response.content)
                    namespace = {
                        '': 'http://purl.org/rss/1.0/',
                        'atom': 'http://www.w3.org/2005/Atom'
                    }
                    channel = root.find('channel')
                    if channel is not None:
                        items_list = channel.findall('item')
                        for item in items_list:
                            title = item.find('title').text if item.find('title') is not None else 'No Title'
                            link = item.find('link').text if item.find('link') is not None else 'No Link'
                            pub_date = item.find('pubDate').text if item.find('pubDate') is not None else str(datetime.now())

                            items.append({
                                "title": title,
                                "link": link,
                                "pub_date": pub_date
                            })
                except ET.ParseError as e:
                    pwn.log.error(f"Error parsing RSS feed from {url}: {e}")
            elif response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))  # Default to 60 seconds
                pwn.log.info(f"Rate limit exceeded for {url}. Waiting for {retry_after} seconds before retrying...")
                time.sleep(retry_after)
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    try:
                        root = ET.fromstring(response.content)
                        namespace = {
                            '': 'http://purl.org/rss/1.0/',
                            'atom': 'http://www.w3.org/2005/Atom'
                        }
                        channel = root.find('channel')
                        if channel is not None:
                            items_list = channel.findall('item')
                            for item in items_list:
                                title = item.find('title').text if item.find('title') is not None else 'No Title'
                                link = item.find('link').text if item.find('link') is not None else 'No Link'
                                pub_date = item.find('pubDate').text if item.find('pubDate') is not None else str(datetime.now())

                                items.append({
                                    "title": title,
                                    "link": link,
                                    "pub_date": pub_date
                                })
                    except ET.ParseError as e:
                        pwn.log.error(f"Error parsing RSS feed from {url} after retry: {e}")
                else:
                    pwn.log.error(f"Failed to fetch Medium writeup from {url} after retry. Status code: {response.status_code}")
            elif response.status_code == 404:
                pwn.log.info(f"URL {url} returned 404. Skipping...")
            else:
                pwn.log.error(f"Failed to fetch Medium writeup from {url}. Status code: {response.status_code}")
        except Exception as e:
            pwn.log.error(f"Error fetching Medium writeup from {url}: {e}")

    pwn.log.info(f"Fetched items: {items}")
    return items

def fetch_pentesterland_writeups():
    pentesterland_url = 'https://pentester.land/writeups.json'
    response = requests.get(pentesterland_url)
    if response.status_code == 200:
        data = response.json()
        writeups = []
        for selected_item in data['data']:
            for item in selected_item['Links']:
                writeup_link = item['Link']
                writeup_title = item['Title']
                authors = selected_item['Authors']
                programs = selected_item['Programs']
                bugs = selected_item['Bugs']
                pub_date = selected_item['PublicationDate']
                added_date = selected_item['AddedDate']
                writeups.append({
                    "title": writeup_title,
                    "link": writeup_link,
                    "pub_date": pub_date,
                    "authors": authors,
                    "programs": programs,
                    "bugs": bugs,
                    "added_date": added_date
                })
        return writeups
    return []

def send_to_discord(webhook_url, title, link, pub_date, extra_fields=None):
    embed = {
        "title": title,
        "description": f"[{title}]({link})",
        "color": 16777215,
        "fields": [{"name": "Published on", "value": pub_date}]
    }

    if extra_fields:
        embed['fields'].extend(extra_fields)
        payload = {"content": None, "embeds": [embed]}
        headers = {"Content-Type": "application/json"}
        response = requests.post(webhook_url, json=payload, headers=headers)
        
    if response.status_code == 204:
        pwn.log.info(f"New item sent to Discord: {title}")
    else:
        pwn.log.info("Failed to send item to Discord.")
        
def setup_database():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS youtube_videos (
            id SERIAL PRIMARY KEY,
            link TEXT UNIQUE NOT NULL,
            title TEXT,
            pub_date TIMESTAMP
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS medium_writeups (
            id SERIAL PRIMARY KEY,
            link TEXT UNIQUE NOT NULL,
            title TEXT,
            pub_date TIMESTAMP
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS pentesterland_writeups (
            id SERIAL PRIMARY KEY,
            link TEXT UNIQUE NOT NULL,
            title TEXT,
            pub_date TIMESTAMP,
            authors TEXT[],
            programs TEXT[],
            bugs TEXT[],
            added_date TIMESTAMP
        );
        """)
        conn.commit()
    conn.close()

def main():
    conn = get_db_connection()
    import sys
    nodiscord = False
    if len(sys.argv) > 1 and sys.argv[1] == 'nodiscord':
        nodiscord = True
        if len(sys.argv) > 1 and sys.argv[1] == 'db':
            setup_database()
            pwn.log.info("Database setup completed.")
            return
        
    youtube_file = 'files/youtube_channels.txt'
    medium_file = 'files/lists.txt'

    if os.path.exists(youtube_file):
        with open(youtube_file, 'r') as file:
            youtube_channels = file.readlines()

        for line in youtube_channels:
            channel_name, channel_id = line.strip().split(',')
            rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
            videos = fetch_rss_data(rss_url)
            if videos:
                for video in videos:
                    video_link = video['link']
                    video_title = video['title']
                    pub_date = video['pub_date']
                    pub_date_dt = datetime.strptime(pub_date, '%Y-%m-%dT%H:%M:%S+00:00')

                    if not is_link_processed(conn, 'youtube_videos', video_link):
                        if not nodiscord:
                            send_to_discord(WEB_HOOK, video_title, video_link, pub_date)
                        save_processed_link(conn, 'youtube_videos', video_link, video_title, pub_date)
                        pwn.log.info(f"New YouTube video found: {video_title}")

    medium_writeups = fetch_medium_writeups(medium_file)
    for writeup in medium_writeups:
        writeup_link = writeup['link']
        writeup_title = writeup['title']
        pub_date = writeup['pub_date']

        if not is_link_processed(conn, 'medium_writeups', writeup_link):
            if not nodiscord:
                send_to_discord(WEB_HOOK, writeup_title, writeup_link, pub_date)
            save_processed_link(conn, 'medium_writeups', writeup_link, writeup_title, pub_date)
            pwn.log.info(f"New Medium writeup found: {writeup_title}")

    pentesterland_writeups = fetch_pentesterland_writeups()
    for writeup in pentesterland_writeups:
        writeup_link = writeup['link']
        writeup_title = writeup['title']
        pub_date = writeup['pub_date']
        authors = writeup['authors']
        programs = writeup['programs']
        bugs = writeup['bugs']
        added_date = writeup['added_date']

        if not is_link_processed(conn, 'pentesterland_writeups', writeup_link):
            if not nodiscord:
                send_to_discord(WEB_HOOK, writeup_title, writeup_link, pub_date, [
                    {"name": "Authors", "value": ", ".join(authors)},
                    {"name": "Programs", "value": ", ".join(programs)},
                    {"name": "Bugs", "value": ", ".join(bugs)},
                    {"name": "Added Date", "value": added_date}
                ])
            save_processed_link(conn, 'pentesterland_writeups', writeup_link, writeup_title, pub_date)
            pwn.log.info(f"New Pentester.land writeup found: {writeup_title}")

    conn.close()

if __name__ == '__main__':
    main()
