
# Writeup Finder A writeup every day
  
**Writeup Finder** is an automated script that fetches and processes security-related writeups from multiple sources including YouTube channels, Medium, and Pentester.land. The script supports integration with PostgreSQL for storing data and can send notifications to a Discord webhook.

## Features
  

-  **YouTube Videos**: Retrieve and process video data from specified YouTube channels.
-  **Medium Writeups**: Fetch and process writeups from Medium using RSS feeds.
-  **Pentester.land Writeups**: Collect writeups from Pentester.land’s JSON feed.
-  **PostgreSQL Database**: Store data in a PostgreSQL database for efficient management.
-  **Discord Notifications**: Optionally send notifications about new content to a Discord webhook.

## Setup

### Prerequisites

- Python 3.x
- PostgreSQL
- Docker (for PostgreSQL)
- Required Python packages: `requests`, `psycopg2`

### Installation

1.  **Clone the Repository**

```bash
git clone https://github.com/moeinerfanian/writeup-finder.git
cd writeup-finder
```
2.  **Set Up PostgreSQL with Docker**

```bash
docker compose up -d
```

3.  **Install Python Dependencies**
```bash
pip3 install -r requirements.txt
```

4.  **Configure the Script**
- Edit ```config.py``` to include your PostgreSQL database credentials and Discord webhook URL.

5. **Create Database Tables**
- Initialize the database schema with:
```bash 
python3 main.py db
```
## Usage
1.  **Run the Script**
    - Do in order
    - Create DB:
    `python3 main.py db` 
    - To skip sending Discord notifications, use the `nodiscord` flag:
    `python3 main.py nodiscord` 
    - Normally Run:
    `python3 main.py`

## Improvements

-   **PostgreSQL Integration**: Enhanced database handling and connectivity.
-   **RSS Feed Handling**: Improved fetching and parsing of YouTube and Medium RSS feeds.
-   **Error Handling**: Better management of rate limits and parsing errors.

## Scheduling with Crontab

To run the script automatically every 5 hours, add the following line to your crontab:
```bash
0 */5 * * * /usr/bin/python3 /path/to/your/repo/main.py
``` 
- Replace `/path/to/your/repo/` with the path to your cloned repository.

## Author

Moein Erfanian (Electro0ne)

![Screenshot from 2024-02-24 17-06-40](https://github.com/moeinerfanian/writeup-finder/assets/122752399/f505f5a6-3176-4c19-8766-5eeecd8950eb)