# Publication Impact Tracker

Automatically finds and categorizes external references to a given article or publication.

## What it does
- Processes manually collected seed URLs and classifies them by platform and usage type
- Searches Reddit via public JSON API for additional mentions
- Exports results to CSV for further analysis

## How to run
pip install requests beautifulsoup4
python publication_tracker.py

## Built with
- Python 3
- requests
- BeautifulSoup4
- Reddit public JSON API
