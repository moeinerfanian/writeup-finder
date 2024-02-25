import requests
import xml.etree.ElementTree as ET
from config import WEB_HOOK,GIF_URL
import random

def fetch_data(url):
    response = requests.get(url)
    content_type = response.headers['Content-Type'].split(';')[0]

    if 'text/xml' in content_type:
        data = response.text
    elif 'application/json' in content_type:
        data = response.json()
    else:
        data = None

    return data

def fetch_xml_data(url):
    response = requests.get(url)
    if response.status_code == 200: 
        root = ET.fromstring(response.content)
        link = root.find(".//link").text
        title = root.find(".//title").text
        last_build_date = root.find(".//lastBuildDate").text
        return link, title, last_build_date
    else:
        return None, None, None

def fetch_json_data(url):
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        
        selected_item = random.choice(data['data'])
        
        link = selected_item['Links'][0]['Link']
        title = selected_item['Links'][0]['Title']
        Authors = selected_item['Authors']
        Programs = selected_item['Programs']
        Bugs = selected_item['Bugs']
        publication_date = selected_item['PublicationDate']
        AddedDate = selected_item['AddedDate']
        return link, title, Authors, Programs, Bugs, publication_date, AddedDate
    else:
        return None, None, None

def send_to_discord_webhook(webhook_url, message, embed=None):
    payload = {"content": message, "embeds": [embed] if embed else []}
    headers = {"Content-Type": "application/json"}

    response = requests.post(webhook_url, json=payload, headers=headers)

    if response.status_code == 200:
        print("Message sent successfully to Discord webhook.")
    else:
        print("Failed to send message to Discord webhook.")

def save_link_to_file(link):
    with open('found_links.txt', 'a') as file:
        file.write(link + '\n')

def is_link_found(link):
    with open('found_links.txt', 'r') as file:
        found_links = file.readlines()
    return link + '\n' in found_links

def main():
    with open('files/lists.txt', 'r') as file:  
        urls = file.readlines()  
    
    urls = [url.strip() for url in urls if url.strip()]

    random_url = random.choice(urls)

    data = fetch_data(random_url)
    if data is not None:
        if isinstance(data, str): 
            link, title, last_build_date = fetch_xml_data(random_url)
            if link and title and last_build_date and not is_link_found(link):
                embed = {
                    "title": title,
                    "description": f"[{title}]({link})",
                    "color": 16777215,  
                    "fields": [
                        {"name": "Last Build Date", "value": last_build_date}
                    ],
                    "thumbnail": {"url": GIF_URL}  
                }
                send_to_discord_webhook(WEB_HOOK, None, embed=embed)
                save_link_to_file(link)
                
            link, title, Authors, Programs, Bugs, publication_date, AddedDate = fetch_json_data("https://pentester.land/writeups.json") 
            if link and title and publication_date and not is_link_found(link):
                embed = {
                    "title": title,
                    "description": f"[{title}]({link})",
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
                save_link_to_file(link)
        else:
            print(f"Unsupported content type for URL: {random_url}")

if __name__ == "__main__":
    main()
