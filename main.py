import requests
import xml.etree.ElementTree as ET
import random
import sys
import pwn
from config import WEB_HOOK, GIF_URL

try:
    if sys.argv[1] == 'nodiscord':
        nodiscord = True
except:
    nodiscord = False

def save_link_to_file(link):
    with open('found_links.txt', 'a') as file:
        file.write(link + '\n')

def is_link_found(link):
    with open('found_links.txt', 'r') as file:
        found_links = file.readlines()
    return link + '\n' in found_links


class Rss:
    def __init__(self, channel=None):
        self._channel = channel
    
    @property
    def channel(self):
        return self._channel
    
    @channel.setter
    def channel(self, channel):
        self._channel = channel 

class Channel:
    def __init__(self, items=None):
        self._items = items
    
    @property
    def items(self):
        return self._items
    
    @items.setter
    def items(self, items):
        self._items = items

class Items:
    def __init__(self, title=None, link=None, pub_date=None):
        self._title = title
        self._link = link
        self._pub_date = pub_date
    
    @property
    def title(self):
        return self._title
    
    @title.setter
    def title(self, title):
        self._title = title
    
    @property
    def link(self):
        return self._link
    
    @link.setter
    def link(self, link):
        self._link = link
    
    @property
    def pub_date(self):
        return self._pub_date
    
    @pub_date.setter
    def pub_date(self, pub_date):
        self._pub_date = pub_date

def fetch_data_from_url(url):
    response = requests.get(url, headers = headers)
    headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'}
    content_type = response.headers['Content-Type'].split(';')[0]

    if 'text/xml' in content_type:
        root = ET.fromstring(response.content)
        items = []
        for item in root.findall(".//item"):
            title = item.find("title").text
            link = item.find("guid").text
            pub_date = item.find("pubDate").text
            items.append(Items(title, link, pub_date))
        channel = Channel(items)
        return Rss(channel)
    
    elif 'application/json' in content_type:
        data = response.json()
        for selected_item in data['data']:
            for item in selected_item['Links']:
                links = item['Link']
                title = item['Title']
                Authors = selected_item['Authors']
                Programs = selected_item['Programs']
                Bugs = selected_item['Bugs']
                publication_date = selected_item['PublicationDate']
                AddedDate = selected_item['AddedDate']
                if links and not is_link_found(links):
                    save_link_to_file(links)
                    pwn.log.success(f"adding Pentester.Land writeups to file: {links}")
                else:
                    return links, title, Authors, Programs, Bugs, publication_date, AddedDate
        return None

def send_to_discord_webhook(webhook_url, message, embed=None):
    payload = {"content": message, "embeds": [embed] if embed else []}
    headers = {"Content-Type": "application/json"}

    response = requests.post(webhook_url, json=payload, headers=headers)

    if response.status_code == 204:
        pwn.log.info("Message sent successfully to Discord webhook.")
    else:
        pwn.log.info("Failed to send message to Discord webhook.")


def main():
    with open('files/lists.txt', 'r') as file:
        urls = file.readlines()

    if nodiscord:
        for found in urls:
            data = fetch_data_from_url(found.strip())
            if isinstance(data, Rss):
                channel = data.channel
                if isinstance(channel, Channel):
                    for link in channel.items:
                        found_link = link.link
                        title = link.title
                        last_build_date = link.pub_date
                        if found_link and not is_link_found(found_link):
                            save_link_to_file(found_link)
                            pwn.log.success(f"adding medium writeups to file: {found_link}")

        data = fetch_data_from_url('https://pentester.land/writeups.json')
        if data:
            links, title, Authors, Programs, Bugs, publication_date, AddedDate = data
            embed = {
                "title": title,
                "description": f"[{title}]({links})",
                "color": 16777215,
                "fields": [
                    {"name": "Authors", "value": Authors[0]},
                    {"name": "Programs", "value": Programs[0]},
                    {"name": "Bugs", "value": Bugs[0]},
                    {"name": "Publication Date", "value": publication_date},
                    {"name": "Added Date", "value": AddedDate}
                ],
                "thumbnail": {"url": GIF_URL}
            }
            send_to_discord_webhook(WEB_HOOK, None, embed=embed)
            save_link_to_file(links)
            pwn.log.info("New Writeup Founded {}".format(links))

    else:
        for url in urls:
            data = fetch_data_from_url(url.strip())
            if data and isinstance(data, Rss):
                channel = data.channel
                if isinstance(channel, Channel):
                    for link in channel.items:
                        found_link = link.link
                        title = link.title
                        last_build_date = link.pub_date
                        if found_link and not is_link_found(found_link):
                            embed = {
                                "title": title,
                                "description": f"[{title}]({found_link})",
                                "color": 16777215,
                                "fields": [
                                    {"name": "Last Build Date", "value": last_build_date}
                                ],
                                "thumbnail": {"url": GIF_URL}
                            }
                            send_to_discord_webhook(WEB_HOOK, None, embed=embed)
                            save_link_to_file(found_link)
                            pwn.log.info("New Writeup Founded {}".format(found_link))
if __name__ == "__main__":
    main()
