import requests
from bs4 import BeautifulSoup
import html
import json

BASE_URL = 'https://new.shelterluv.com/embed/animal/'

def get_animal_id_from_page(url):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 404:
            return None, None, 404
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        iframe_animal = soup.find('iframe-animal')
        if iframe_animal and ':animal' in iframe_animal.attrs:
            animal_attr = iframe_animal[':animal']
            animal_json_str = html.unescape(animal_attr)
            try:
                animal_data = json.loads(animal_json_str)
                unique_id = animal_data.get('uniqueId', '')
                name = animal_data.get('name', '')
                if unique_id.startswith('AHNM'):
                    return unique_id, name, response.status_code
            except Exception as e:
                print(f"Error parsing animal JSON for {url}: {e}")
        return None, None, response.status_code
    except requests.exceptions.HTTPError as e:
        if '404' in str(e):
            return None, None, 404
        print(f"Error fetching {url}: {e}")
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return None, None, None

def main():
    start = int(input("Enter the starting animal number: ").strip())
    end = int(input("Enter the ending animal number: ").strip())
    print(f"Searching for Animal IDs with prefix 'AHNM' from {start} to {end}...")
    for num in range(start, end + 1):
        url = f"{BASE_URL}{num}"
        unique_id, name, status_code = get_animal_id_from_page(url)
        if unique_id:
            print(f"Found Animal ID with prefix 'AHNM' at: {url} | uniqueId: {unique_id} | {name}.")

if __name__ == "__main__":
    main()
