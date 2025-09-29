from bs4 import BeautifulSoup
import csv
from datetime import datetime
from shelterdog_tracker.dog import Dog
import html
import json
import pytz
import re
import requests
# Selenium imports - only import if actually used
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.support.ui import WebDriverWait
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("Warning: Selenium not available. Some scraping features may not work.")
# from seleniumwire import webdriver  # pip install selenium-wire
import time
from shelterdog_tracker.elasticsearch_handler import ElasticsearchHandler
# Encapsulates all scraping and data extraction logic.
class ShelterScraper:
    def __init__(self, main_url=None):
        self.main_url = main_url

    #TODO move this to test/ directory
    def verify_dogs_complete(self, dogs):
        for dog in dogs:
            if dog.is_complete():
                #print(f"Dog {dog.name} is complete.")
                continue
            else:
                print(f"Dog {dog.name if dog.name else '[No Name]'} is incomplete.")

        

    def scrape_all_dogs(self):
        urls = self.fetch_iframe_urls()
        return self.scrape_dogs_from_urls(urls)
            
    def fetch_iframe_urls(self):
        """
        Launches a headless Chrome browser, navigates to the main URL,
        and extracts all relevant iframe src URLs.
        Returns a list of URLs.
        """
        if not SELENIUM_AVAILABLE:
            print("Selenium not available, using fallback method")
            return self.fetch_iframe_urls_fallback()
            
        try:
            options = Options()
            options.add_argument("--headless")  # Run Chrome in headless mode
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")

            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(120)
            driver.get(self.main_url)
            #wait for all links to be collected 
            WebDriverWait(driver, 60).until(
                lambda d: len(d.find_elements(By.CLASS_NAME, "shelterluv")) >= 4
            )
            time.sleep(60)
            #Iterate over all captured requests
            filtered_urls = []
            for request in driver.requests:
                if request.response and "available-animals" in request.url:
                    filtered_urls.append(request.url)
                    print(f"url: {request.url}")
            driver.quit()
            return filtered_urls
        except Exception as e:
            print(f"Selenium scraping failed: {e}, falling back to alternative method")
            return self.fetch_iframe_urls_fallback()
    
    def fetch_iframe_urls_fallback(self):
        """
        Fallback method when Selenium is not available.
        Uses requests to get the page and parse iframes with BeautifulSoup.
        """
        try:
            response = requests.get(self.main_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for iframe elements with shelterluv URLs
            iframes = soup.find_all('iframe')
            filtered_urls = []
            
            print(f"DEBUG: Found {len(iframes)} iframes on the page")
            
            for iframe in iframes:
                src = iframe.get('src', '')
                print(f"DEBUG: Found iframe src: {src}")
                
                if 'shelterluv.com' in src:
                    if not src.startswith('http'):
                        src = 'https:' + src if src.startswith('//') else 'https://new.shelterluv.com' + src
                    filtered_urls.append(src)
                    print(f"Found ShelterLuv iframe URL: {src}")
            
            # Also look for any links or scripts that might contain API URLs
            if not filtered_urls:
                print("No ShelterLuv iframes found, looking for other patterns...")
                
                # Look for any mention of shelterluv in the page content
                page_text = soup.get_text()
                if 'shelterluv' in page_text.lower():
                    print("Found 'shelterluv' mentioned in page content")
                
                # Look for script tags that might contain API calls
                scripts = soup.find_all('script')
                for script in scripts:
                    if script.string and 'shelterluv' in script.string.lower():
                        print(f"Found shelterluv reference in script: {script.string[:200]}...")
            
            # If no iframe URLs found, try to construct URLs from JavaScript embed calls
            if not filtered_urls:
                print("No iframe URLs found, looking for JavaScript embed patterns...")
                
                # Look for EmbedAvailablePets calls in script tags
                scripts = soup.find_all('script')
                gid = None
                saved_queries = []
                
                print(f"DEBUG: Checking {len(scripts)} script tags for EmbedAvailablePets...")
                
                for i, script in enumerate(scripts):
                    if script.string and 'EmbedAvailablePets' in script.string:
                        print(f"DEBUG: Found EmbedAvailablePets in script {i}")
                        script_content = script.string
                        
                        # Extract GID
                        import re
                        gid_match = re.search(r'var GID = (\d+)', script_content)
                        if gid_match:
                            gid = gid_match.group(1)
                            print(f"DEBUG: Found GID: {gid}")
                        
                        # Extract saved_query values
                        query_matches = re.findall(r'"saved_query":(\d+)', script_content)
                        saved_queries.extend(query_matches)
                        print(f"DEBUG: Found saved_queries in this script: {query_matches}")
                
                print(f"DEBUG: Final GID: {gid}, Final saved_queries: {saved_queries}")
                
                if gid and saved_queries:
                    print(f"Found GID: {gid}, Saved queries: {saved_queries}")
                    
                    # Try different endpoint formats that might not require API keys
                    for query_id in saved_queries:
                        # Try the embed endpoint format (public)
                        embed_url = f"https://new.shelterluv.com/embed/available-animals/{gid}?saved_query={query_id}"
                        filtered_urls.append(embed_url)
                        print(f"Constructed embed URL: {embed_url}")
                        
                        # Also try the API endpoint in case we can make it work later
                        # api_url = f"https://new.shelterluv.com/api/v1/animals?organization_id={gid}&saved_query={query_id}"
                        # filtered_urls.append(api_url)
                        # print(f"Constructed API URL: {api_url}")
                else:
                    print(f"DEBUG: Could not extract GID and saved_queries. GID: {gid}, saved_queries: {saved_queries}")
                
                if not filtered_urls:
                    print("Could not construct API URLs from JavaScript patterns")
                    return []
            
            return filtered_urls
            
        except Exception as e:
            print(f"Fallback scraping also failed: {e}")
            return []

    def scrape_dog_location(self, url):
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        iframe_animal = soup.find('iframe-animal')
        animal_attr = iframe_animal.get(':animal')
        animal_data = json.loads(animal_attr)
        location = animal_data.get('location')
        print(f"location returned from scrape_dog_status is: {location}")
        return location 

    #This function may be a duplicate attempt at a function that's already 
    #been created called scrape_shelter_luv.
    def scrape_shelterluv_from_url_list(self, url_list):
        print(f"scrape_shelterluv_from_url_list has been called with: {url_list}")
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36'
        }
        id_url_map = {int(url.rstrip('/').split('/')[-1]): url for url in url_list}

        all_dogs = []
        #origin_lookup is a dict created to hold data in location_info.jsonl that is not available online
        origin_lookup = {}
        with open('location_info.jsonl', 'r') as f:
            for lineno, line in enumerate(f, 1):
                try:
                    data = json.loads(line)
                except json.JSONDecodeError as e:
                    print(f"Error on line {lineno}: {e}")
                    print("Line:", line)
                    continue
                origin_lookup[data['id']] = {
                    "origin":data.get('origin', 'Unknown'),
                    "returned": data.get('returned', 0),
                    "bite_quarantine": data.get('bite_quarantine', 0),
                    "latitude":data.get('latitude', 0),
                    "longitude":data.get('longitude', 0)
                }
            for url in url_list:
                dog_id = int(url.rstrip('/').split('/')[-1])
                extra = origin_lookup.get(dog_id, {})
                origin = extra.get('origin', 'Unknown')
                returned = extra.get('returned', 0)
                bite_quarantine = extra.get('bite_quarantine', 0)
                latitude = extra.get('latitude', 0)
                longitude = extra.get('longitude', 0)

                response = requests.get(url, headers=headers)
                content = response.text
                # 1. Extract the :animal="..." attribute's content
                match = re.search(r':animal="([^"]+)"', content)
                if match:
                    animal_str = match.group(1)
                    # 2. Unescape HTML entities
                    animal_json_str = html.unescape(animal_str)
                    # 3. Load the string as JSON
                    animal_data = json.loads(animal_json_str)
                    # 4. Access the location
                    current_location = animal_data.get('location', 'Unknown')
                    print(f"Current location: {current_location}, Id: {dog_id}, Origin: {origin}")
                else:
                    print("Could not extract animal data from page.")
                
                #If location info has changed, update the most recent document in Elasticsearch
                #1. doc = get_dog_by_id()
                #2. if current_location == "":
                #3.     update most current doc status to "adopted"
                #4.     update most current doc location to ""
                #5. elif current_location != doc location:
                #6.     update most current doc location to current_location


    def scrape_dogs_from_urls(self, urls):
        #print(f"urls passed to scrape_dogs_from_urls are: {urls}")
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36'
        }
        mountain_tz = pytz.timezone('US/Mountain')
        now_utc = datetime.utcnow()
        now_mt = now_utc.replace(tzinfo=pytz.utc).astimezone(mountain_tz)
        timestamp_mt = now_mt.strftime("%Y-%m-%dT%H:%M:%S%z")
        timestamp_mt_iso = timestamp_mt[:-2] + ":" + timestamp_mt[-2:]

        all_dogs = []
       
        #origin_lookup is a dict created to hold data in location_info.jsonl that is not available online
        origin_lookup = {}
        with open('location_info.jsonl', 'r') as f:
            for lineno, line in enumerate(f, 1):
                try:
                    data = json.loads(line)
                except json.JSONDecodeError as e:
                    print(f"Error on line {lineno}: {e}")
                    print("Line:", line)
                    continue
                origin_lookup[data['id']] = {
                    "origin":data.get('origin', 'Unknown'),
                    "returned": data.get('returned', 0),
                    "bite_quarantine": data.get('bite_quarantine', 0)
                }
                
                if 'latitude' in data and data['latitude'] not in (None, ''):
                    origin_lookup[data['id']]["latitude"] = float(data['latitude'])
                
                if 'longitude' in data and data['longitude'] not in (None, ''):
                    origin_lookup[data['id']]["longitude"] = float(data['longitude'])
        for url in urls:
            response = requests.get(url, headers=headers)
            parsed_data = response.json()
            
            # Debug: print the structure of the response
            print(f"DEBUG: Response keys: {list(parsed_data.keys())}")
            if 'animals' not in parsed_data:
                print(f"DEBUG: 'animals' key not found. Available keys: {list(parsed_data.keys())}")
                print(f"DEBUG: Sample response structure: {str(parsed_data)[:500]}...")
                continue
                
            for dog_dict in parsed_data['animals']:
                dog_dict['timestamp'] = timestamp_mt_iso
                dog_id = dog_dict['nid'] 
                extra = origin_lookup.get(dog_id, {})
                origin = extra.get('origin', 'Unknown')
                returned = extra.get('returned', 0)
                bite_quarantine = extra.get('bite_quarantine', 0)
                latitude = extra.get('latitude', 0)
                longitude = extra.get('longitude', 0)

                    
                dog_kwargs = dict(
                    timestamp=dog_dict['timestamp'],
                    dog_id=dog_id,
                    name=dog_dict['name'],
                    location=dog_dict['location'],
                    status=dog_dict.get('status', 'Available'),
                    url = f'https://new.shelterluv.com/embed/animal/{dog_dict["nid"]}',
                    intake_date=datetime.utcfromtimestamp(int(float(dog_dict['intake_date']))).strftime('%Y-%m-%d'),
                    length_of_stay_days=(datetime.utcnow().date() - datetime.utcfromtimestamp(int(float(dog_dict['intake_date']))).date()).days,
                    birthday=datetime.utcfromtimestamp(int(float(dog_dict['birthday']))).strftime('%Y-%m-%d'),
                    age_group=("Puppy" if (datetime.utcnow().date() - datetime.utcfromtimestamp(int(float(dog_dict['birthday']))).date()).days < 365 else "Adult" if (datetime.utcnow().date() - datetime.utcfromtimestamp(int(float(dog_dict['birthday']))).date()).days < 365*7 else "Senior"),
                    breed=dog_dict['breed'],
                    secondary_breed=dog_dict['secondary_breed'],
                    weight_group=dog_dict['weight_group'],
                    color = " and ".join(filter(None, [dog_dict.get('primary_color', ''),dog_dict.get('secondary_color', '')])),
                    origin=extra.get('origin', 'Unknown'),
                    bite_quarantine=extra.get('bite_quarantine',0),
                    returned=extra.get('returned', 0),
                    **{k: v for k, v in dog_dict.items() if k not in ['timestamp', 'nid', 'name', 'location', 'status', 'intake_date','length_of_stay', 'birthday', 'age_group', 'breed','secondary_breed','weight_group','color']}
                )
                if latitude is not None:
                    dog_kwargs['latitude'] = latitude
                if longitude is not None:
                    dog_kwargs['longitude'] = longitude
                dog = Dog(**dog_kwargs)
                all_dogs.append(dog)
        return all_dogs


    #get_data takes a source argument and based on that value, calls scrape() or load_from_csv()
    def get_data(self, source='web', csv_file_path=None):
        """
        Unified interface to get dog data from the web or a CSV file.

        Args:
            source (str): 'web' to scrape live, 'csv' to load from file.
            csv_file_path (str): Path to CSV file (required if source='csv').

        Returns:
            list: List of dog data dictionaries.
        """
        if source == 'web':
            return self.scrape()
        elif source == 'csv':
            if not csv_file_path:
                raise ValueError("csv_file_path must be provided when source='csv'")
            return self.load_from_csv(csv_file_path)
        else:
            raise ValueError("source must be 'web' or 'csv'")
 
       
    def load_from_csv(self, csv_file_path):
        """
        Load dog data from a CSV file and return a list of dicts.
        """
        with open(csv_file_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            all_dogs = []
            for row in reader:
                dog = Dog (
                    dog_id=int(row['id']),                    
                    name=row['name'],
                    location=row['location'],
                    status=row.get('status','Available'),
                    url=f'https://new.shelterluv.com/embed/animal/{row["id"]}'
                )
                # Optional: split location if it's a semicolon-separated string
                if 'location' in row:
                    row['location'] = row['location'].split(';')
                all_dogs.append(dog)
            return all_dogs 

    #TODO: Periodically run an update on dogs that have been trial adopted and update status when appropriate
    def scrape_shelterluv(self, delisted_dog_id, idxA):
        """
        Scrape location from public url and update
        """
        base_url = "https://new.shelterluv.com/embed/animal/"

        #Declare a handler so you can call functions in the ElasticsearchHandler class
        handler = ElasticsearchHandler("http://localhost:9200", idxA) 
        #dog_doc = handler.get_dog_by_id(dog_id) 
        #print(f"document returned from Elastic is: {dog_doc}")

        url = f"{base_url}{delisted_dog_id}"
        try: 
            response = requests.get(url, timeout=10)
            response.raise_for_status()
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")

        soup = BeautifulSoup(response.text, "html.parser")
        iframe_animal_tag = soup.find("iframe-animal")

        if iframe_animal_tag and ":animal" in iframe_animal_tag.attrs:
            animal_attr = iframe_animal_tag[":animal"]
            animal_json_str = html.unescape(animal_attr)
            animal_data = json.loads(animal_json_str)
            location = animal_data.get("location","")
            #print(f"extracted location: {location}")
            
        if not location:
            fields_to_update = {"status":"adopted", "location":""}
            handler.update_dog_fields(idxA, delisted_dog_id, fields_to_update)
        else:
            fields_to_update = {"location":location}
            handler.update_dog_fields(idxA, delisted_dog_id, fields_to_update)

    def scrape_dog_location(self, url):
        try: 
            response = requests.get(url, timeout=10)
            response.raise_for_status()
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")
        
        soup = BeautifulSoup(response.text, "html.parser")
        iframe_animal_tag = soup.find("iframe-animal")
    
        if iframe_animal_tag and ":animal" in iframe_animal_tag.attrs:
            animal_attr = iframe_animal_tag[":animal"]
            animal_json_str = html.unescape(animal_attr)
            animal_data = json.loads(animal_json_str)
            location = animal_data.get("location","")
        return location
