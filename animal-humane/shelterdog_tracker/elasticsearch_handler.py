from datetime import datetime, timezone, timedelta
import json
import pytz
import re
import requests

from elasticsearch import Elasticsearch, helpers, exceptions as es_exceptions
from elasticsearch.helpers import scan

from shelterdog_tracker.dog import Dog

class ElasticsearchHandler:
    origin_coordinates = {
        "ABQ Animal Welfare Department":{"latitude":35.1102,"longitude":-106.5823},
        "ACTion Programs for Animals":{"latitude":32.315292,"longitude":-106.767102},
        "Artesia Animal Shelter (Paws & Claws Humane Society)":{"latitude":32.8423,"longitude":-104.4033},
        "Aztec Animal Shelter":{"latitude":36.8305,"longitude":-108.0095},
        "Bayard Animal Control":{"latitude":32.7795,"longitude":-108.1503},
        "Bernalillo County Animal Care":{"latitude":35.0561,"longitude":-106.6646},
        "Bro & Tracy Animal Welfare":{"latitude":35.2378,"longitude":-106.6067},
        "Chama Valley Humane Society":{"latitude":36.894318,"longitude":-106.581931},
        "Cindy's Hope for Precious Paws":{"latitude":34.4214,"longitude":-103.2150},
        "City of Las Vegas Animal Care Center":{"latitude":35.5939,"longitude":-105.2239},
        "Clayton":{"latitude":36.4517,"longitude":-103.1841},
        "Corrales Animal Services":{"latitude":35.2393,"longitude":-106.6054},
        "Corrales Kennels":{"latitude":35.2378,"longitude":-106.6067},
        "County of Taos Animal Control":{"latitude":36.3948,"longitude":-105.5767},
        "DAGSHIP Rescue":{"latitude":32.2655,"longitude":-107.7582},
        "Edgewood Animal Control":{"latitude":35.0913,"longitude":-106.1945},
        "Espanola Humane":{"latitude":36.0006,"longitude":-106.0373},
        "Farmington Regional Animal Shelter":{"latitude":36.7334,"longitude":-108.1681},
        "Forever Homes Animal Rescue":{"latitude":32.8985,"longitude":-105.9510},
        "Four Corners Animal League":{"latitude":36.4072,"longitude":-105.5731},
        "Gallup McKinley County Humane Society":{"latitude":35.543605,"longitude":-108.760272},
        "Humane Society of Lincoln County":{"latitude":33.3436,"longitude":-105.6650},
        "Labor of Love Project NM":{"latitude":34.1827,"longitude":-103.3245},
        "Lovelace Biomedical Research":{"latitude":35.0559,"longitude":-106.5789},
        "Moriarty Animal Control":{"latitude":34.9996,"longitude":-106.0183},
        "Mountainair Animal Control":{"latitude":34.5197,"longitude":-106.2433},
        "Otero County Animal Control":{"latitude":32.8995,"longitude":-105.9603},
        "Paws & Claws Rescue of Quay County":{"latitude":35.1911,"longitude":-103.6150},
        "Petroglyph Animal Hospital":{"latitude":35.1728,"longitude":-106.6737},
        "RezDawg Rescue":{"latitude":35.0142,"longitude":-106.0846},
        "Rio Rancho Animal Control":{"latitude":35.2748, "longitude":-106.6681},
        "Roswell Humane Society":{"latitude":33.3930,"longitude":-104.5235},
        "Sandoval County Animal Services":{"latitude":35.3515,"longitude":-106.4694},
        "Santa Clara Animal Control":{"latitude":32.776773,"longitude":-108.153132},
        "Santa Rosa Animal Control":{"latitude":34.9387,"longitude":-104.6825},
        "Sororro Animal Services":{"latitude":34.0242,"longitude":-106.8958},
        "Socorro Animal Shelter and Adoption Center":{"latitude":34.0225,"longitude":-106.9031},
        "Stray Hearts Animal Shelter":{"latitude":36.3848,"longitude":-105.5969},
        "The Animal Services Center":{"latitude":32.3128,"longitude":-106.7799},
        "Torrance County Animal Shelter":{"latitude":34.8712,"longitude":-106.0515},
        "Truth or Consequences Animal Shelter":{"latitude":33.1347,"longitude":-107.2425},
        "Tucumcari Animal Shelter":{"latitude":35.1927,"longitude":-103.7197},
        "Valencia County Animal Shelter":{"latitude":34.7945,"longitude":-106.7400}
    }
    def __init__(self, host, index_name):
        self.host = host
        self.index_name = index_name
        # Configure client for Elasticsearch 8.x compatibility
        self.es = Elasticsearch(
            host,
            request_timeout=60,
            # Disable SSL verification for local development
            verify_certs=False,
            ssl_show_warn=False
        )

    def create_index(self, index_name, mapping):
        print(f"index_name passed to create_index is: {index_name}")
        if not self.es.indices.exists(index=index_name):
            self.es.indices.create(index=index_name, body=mapping)
        else:
            print(f"Index already exists: {index_name}")

    def push_doc_to_elastic(self, index_name, doc):
        self.es.index(index=index_name, body=doc)

    def push_dogs_to_elasticsearch(self, dogs):
        bulk_lines = []
        #Convert dog objects to dictionaries for Elasticsearch all at once like this
        #dog_dicts = [dog.to_dict(include_attributes=False) for dog in all_dogs]

        for dog in dogs:
            action = {"index": {"_index": self.index_name, "_id": dog.id}}
            bulk_lines.append(json.dumps(action))
            bulk_lines.append(json.dumps(dog.to_dict(include_attributes=False)))
        bulk_data = "\n".join(bulk_lines) + "\n"
        url = f"{self.host}/_bulk"
        headers = {"Content-Type": "application/json"}

        # ...send request to Elasticsearch...
        response = requests.post(url, headers=headers, data=bulk_data)

        # Optional: Handle response
        if response.status_code == 200:
            result = response.json()
            if result.get('errors'):
                print("Some documents failed to index.")
            else:
                print("All documents indexed successfully.")
        else:
            print(f"Failed to index documents. Status code: {response.status_code}")
            print(response.text)

        print(f"Refreshing Elasticsearch to ensure doc availability")
        refresh_url = f"{self.host}/{self.index_name}/_refresh"
        response = requests.post(refresh_url)

        if response.status_code == 200:
            print("Index refreshed successfully.")
        else:
            print(f"Failed to refresh index. Status code: {response.status_code}")
            print(response.text)
        return response

    def push_dog_to_elasticsearch(self, dog: Dog, index_name: str):
        doc = dog.to_dict()
        response = self.es.index(index=index_name, id=dog.id, document=doc)
        return response

    def update_dogs(self, results):
        from shelterdog_tracker.shelter_scraper import ShelterScraper
        scraper = ShelterScraper()
        for group_name in ['adopted_dogs', 'trial_adoption_dogs', 'other_unlisted_dogs']:
            for dog in results.get(group_name, []):
                index_pattern = "animal-humane-*"
                dog_id = dog.get('dog_id')
                url = dog.get('url', None)

                if url:
                    new_location = scraper.scrape_dog_location(url) or ''
                else:
                    new_location = ''  # fallback if no URL is present

                if group_name == 'adopted_dogs':
                    new_status = 'adopted'
                    doc_update = {"location":new_location,"status":new_status}
                else:
                    doc_update = {"location": new_location}

                query_body = {
                    "query": {"term": {"id": dog_id}},
                    "sort": [{"_index": {"order": "desc"}}]
                }
                response = self.es.search(index=index_pattern,body=query_body,size=1)
                hits = response['hits']['hits']

                if hits:
                    hit = hits[0]
                    index_name = hit['_index']
                    document_id = hit['_id']

                    update_response = self.es.update(
                        index=index_name,
                        id=document_id,
                        body={
                            "doc": doc_update   #{"location": new_location}
                        }
                    )
                    print(f"Updated dog {dog.get('name')} in index {index_name}: {update_response}")
                else:
                    print(f"No documents found for dog {dog.get('name')} with dog_id {dog_id}")

    def update_metadata_from_location_info(self, dog_ids=None):
        """
        Update existing Elasticsearch documents with metadata from location_info.jsonl
        This is needed because location_info.jsonl data is only applied during initial scraping,
        not retroactively updated for existing documents.

        Args:
            dog_ids: List of specific dog IDs to update. If None, updates all dogs.
        """
        import json

        # Load location_info.jsonl data
        origin_lookup = {}
        try:
            with open('location_info.jsonl', 'r') as f:
                for lineno, line in enumerate(f, 1):
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError as e:
                        print(f"Error on line {lineno}: {e}")
                        print("Line:", line)
                        continue
                    origin_lookup[data['id']] = {
                        "origin": data.get('origin', 'Unknown'),
                        "returned": data.get('returned', 0),
                        "bite_quarantine": data.get('bite_quarantine', 0),
                        "latitude": data.get('latitude', 0) if data.get('latitude') not in (None, '') else None,
                        "longitude": data.get('longitude', 0) if data.get('longitude') not in (None, '') else None
                    }
        except FileNotFoundError:
            print("location_info.jsonl file not found")
            return

        # If specific dog_ids provided, filter the lookup
        if dog_ids:
            origin_lookup = {k: v for k, v in origin_lookup.items() if k in dog_ids}

        print(f"Updating metadata for {len(origin_lookup)} dogs from location_info.jsonl")

        # Update each dog in Elasticsearch
        index_pattern = "animal-humane-*"
        updated_count = 0

        for dog_id, metadata in origin_lookup.items():
            # Find the most recent document for this dog
            query_body = {
                "query": {"term": {"id": dog_id}},
                "sort": [{"_index": {"order": "desc"}}],
                "size": 1
            }

            try:
                response = self.es.search(index=index_pattern, body=query_body)
                hits = response['hits']['hits']

                if hits:
                    hit = hits[0]
                    index_name = hit['_index']
                    document_id = hit['_id']
                    current_doc = hit['_source']

                    # Prepare update document with metadata fields
                    doc_update = {}

                    # Only update if values are different or missing
                    if current_doc.get('bite_quarantine', 0) != metadata['bite_quarantine']:
                        doc_update['bite_quarantine'] = metadata['bite_quarantine']
                    if current_doc.get('returned', 0) != metadata['returned']:
                        doc_update['returned'] = metadata['returned']
                    if current_doc.get('origin', 'Unknown') != metadata['origin']:
                        doc_update['origin'] = metadata['origin']
                    if metadata['latitude'] is not None and current_doc.get('latitude', 0) != metadata['latitude']:
                        doc_update['latitude'] = metadata['latitude']
                    if metadata['longitude'] is not None and current_doc.get('longitude', 0) != metadata['longitude']:
                        doc_update['longitude'] = metadata['longitude']

                    # Only update if there are changes
                    if doc_update:
                        update_response = self.es.update(
                            index=index_name,
                            id=document_id,
                            body={"doc": doc_update}
                        )
                        print(f"Updated dog ID {dog_id} in index {index_name}: {doc_update}")
                        updated_count += 1
                    else:
                        print(f"Dog ID {dog_id} already has correct metadata")
                else:
                    print(f"No documents found for dog ID {dog_id}")

            except Exception as e:
                print(f"Error updating dog ID {dog_id}: {e}")

        print(f"Metadata update complete. Updated {updated_count} documents.")

    def get_dog_by_name(self, name):
        print(f"Retrieving dog with name: {name} from index: {self.index_name}")
        url = f"{self.host}/{self.index_name}/_search"
        query = {"query":{"match":{"name": name}}}
        response = requests.get(url, json=query)
        if response.status_code == 200:
            results = response.json()
            hits = results.get("hits", {}).get("hits", [])
            # Return all matching dogs as a list of dicts
            return [hit["_source"] for hit in hits]
        else:
            print(f"Search failed. Status code: {response.status_code}")
            print(response.text)
            return []

    #This doesn't identify new dogs, it identifies differences between sets of incoming and existing jobs
    #'new' dogs could be dogs that are no longer in Elasticsearch because they've been adopted.

    def non_overlapping_dogs(self, current_dog_ids):
        es_handler = ElasticsearchHandler(host="http://localhost:9200", index_name="dogs")
        #es_ids = [doc['_id'] for doc in scan(es_handler.es, index="dogs", query={"query": {"match_all": {}}}, _source=False)]
        es_docs = [
            (int(doc['_id']), doc['_source']['url'])
            for doc in scan( es_handler.es, index="dogs", query={"query": {"match_all": {}}}, _source=["url"])
        ]
        new_ids_only = [id for id, url in es_docs]
        new_ids_set = set(new_ids_only)
        current_ids_set = set(current_dog_ids)

        # IDs in newly_collected_ids but not in current_ids
        non_overlapping_ids = list(new_ids_set - current_ids_set)
        non_overlapping_tuples = [(dog_id, url) for dog_id, url in es_docs if dog_id in non_overlapping_ids]
        return non_overlapping_tuples

    def add_new_dogs(self, current_dog_ids):
        pass
    def index_dog(copy_to_idx, id, doc):
        self.es_handler.index_dog(es, indexB, id=dog_id, document=dog_data)

        #You have the IDs for non_overlapping dogs but you don't know if the dogs are really new or just
        #returned from a trial adoption or returned after a longer period of being adopted (Bella Michele)
        #or if they've been recently adopted (Kia).
        #They might have been adopted on trial before you started collecting data
        #likewise, another dog like Ramen may appear to be new, but because you've been at AH
        #for awhile, you recognize her. They're 'new', which means they're not currently in the
        #data store. You won't always know their history but if the dog is new, they should be added.
        #You're checking from one day to the next so a dog should be there or not be there. The reason
        #can be anything or nothing obvious. They could still have a location but not be on the site.
        #If nothing has changed, that's the case where you update nothing.

    def get_docs_by_key(self, index, key_field):
        docs = {}
        for doc in scan(self.es, index=index, query={"query": {"match_all": {}}}):
            key = doc['_source'][key_field]
            docs[key] = doc['_source']
        return docs

    def diff_indices(self, index_a, index_b, key_field):
        docs_a = self.get_docs_by_key(index_a, key_field)
        docs_b = self.get_docs_by_key(index_b, key_field)

        only_in_a = set(docs_a) - set(docs_b)
        only_in_b = set(docs_b) - set(docs_a)
        changed = [k for k in (set(docs_a) & set(docs_b)) if docs_a[k] != docs_b[k]]

        return {
            "only_in_a": only_in_a,
            "only_in_b": only_in_b,
            "changed": changed
        }
    def update_by_query(self, dog_id):
        body = {"script":{"source":"ctx._source.latitude = params.new_latitude;ctx._source.longitude = params.new_longitude;ctx._source.origin = params.new_origin","lang":"painless","params":{"new_latitude":latitude,"new_longitude":longitude, "new_origin":origin}},"query":{"term":{"id":dog_id}}}

        response = self.es.update_by_query(
            index="animal-humane-*",
            body=body,
            conflicts="proceed",
            refresh=True   # optionally refresh index after update
        )

        return response

    def update_dog_fields(self, index_to_update, dog_id, fields_to_update):
        #print(f"{index_to_update} will be updated with {fields_to_update} for dog {dog_id}")
        self.es.update(
            index=index_to_update,
            id=dog_id,
            doc=fields_to_update
        )
        print(f"******************  updated doc  ******************")
        self.get_dog_by_id(dog_id)

    #This function gets dog by id from Elastic.
    def get_dog_by_id(self, dog_id):
        body = {"query":{"match":{"id":dog_id}},"sort":{"_index":{"order":"desc"}}}
        response = self.es.search(index="animal-humane-*", body=body, size=1)
        hits = response.get("hits",{}).get("hits",[])
        if hits:
            hit = hits[0]
            dog_data = hit["_source"]
            dog_data["_index"] = hit["_index"]  # Add the index name to the response
            return dog_data
        return None
        #print(f"Retrieving dog with ID: {dog_id} from index: {self.index_name}")
        #url = f"{self.host}/{self.index_name}/_doc/{dog_id}"
        #print(f"url: {url}")
        #response = requests.get(url)
        #if response.status_code == 200:
        #    result = response.json()
        #    if result.get('found'):
        #        return result['_source']  # This is the stored document (dict)
        #    else:
        #        print(f"No dog found with id {dog_id}.")
        #        return None
        #else:
        #    print(f"Failed to retrieve document. Status code: {response.status_code}")
        #    print(response.text)
        #    return None

    def retrieve_trial_adoptions(self):
        #If all dogs in a trial adoption are not returned by this function, verify that locations for all
        #contain "*Trial Adoption*", not something else.
        query = {"query":{"bool":{"must":[{"wildcard":{"location.keyword":"*Trial Adoption*"}}]}}}

        response = self.es.search(index="animal-humane-*", body=query)

        results = [
            {'name': hit['_source']['name'], 'url': hit['_source']['url']}
            for hit in response['hits']['hits']
            if 'name' in hit['_source'] and 'url' in hit['_source']
        ]
        return results

    def cat_indices(self):
        indices_table = self.es.cat.indices(v=True, s="index")
        lines = indices_table.strip().split('\n')
        return '\n'.join(lines[-2:])
        #return indices_table

    def get_adoptions(self):
        pass

    def get_current_availables(self):
        # This returns ALL available dogs from recent indices, not just recent ones
        # Modified to avoid aggregation issues with mixed field types by using direct query

        # Query all indices to get complete picture, avoiding mixed type issues by processing in Python
        try:
            # Use all animal-humane indices but sort by recency for deduplication
            index_pattern = "animal-humane-*"
        except Exception as e:
            print(f"Error getting indices, falling back to wildcard: {e}")
            index_pattern = "animal-humane-*"

        # Use a simpler query without aggregations to avoid mixed type issues
        query = {
            "size": 10000,  # Get up to 10k documents
            "sort": [{"_index": {"order": "desc"}}],  # Sort by index name (most recent first)
            "_source": ["id", "name", "url", "status", "location", "origin", "intake_date", "length_of_stay_days", "birthdate", "age_group", "breed", "secondary_breed", "weight_group", "color", "bite_quarantine", "returned", "latitude", "longitude"],
            "query": {
                "match_all": {}  # Get all dogs from recent indices
            }
        }

        # Run the search on recent indices only
        response = self.es.search(index=index_pattern, body=query)

        # Process results to get unique dogs (most recent record for each ID)
        dogs_by_id = {}
        for hit in response['hits']['hits']:
            dog_data = hit['_source']
            dog_id = str(dog_data['id'])  # Ensure ID is string for consistency

            # Keep the most recent record for each dog (first in sorted results)
            if dog_id not in dogs_by_id:
                dogs_by_id[dog_id] = {
                    "name": dog_data.get("name"),
                    "dog_id": dog_data.get("id"),
                    "url": dog_data.get("url"),
                    "location": dog_data.get("location"),
                    "origin": dog_data.get("origin"),
                    "status": dog_data.get("status"),  # Make sure status is included
                    "intake_date": dog_data.get("intake_date"),
                    "length_of_stay_days": dog_data.get("length_of_stay_days"),
                    "birthdate": dog_data.get("birthdate"),
                    "age_group": dog_data.get("age_group"),
                    "breed": dog_data.get("breed"),
                    "secondary_breed": dog_data.get("secondary_breed"),
                    "weight_group": dog_data.get("weight_group"),
                    "color": dog_data.get("color"),
                    "bite_quarantine": dog_data.get("bite_quarantine"),
                    "returned": dog_data.get("returned"),
                    "latitude": dog_data.get("latitude"),
                    "longitude": dog_data.get("longitude")
                }

        # Filter for dogs with status "Available" from their most recent record
        available_dogs = [
            dog for dog in dogs_by_id.values() 
            if dog.get("status") == "Available"  # Only include dogs currently available
        ]

        # Return list of unique available dogs
        return available_dogs

    def get_all_ids(self, index_name):
        ids = []
        # Use scan helper for efficient iteration through all docs
        for hit in helpers.scan(self.es, index=index_name, query={"query": {"match_all": {}}}, _source=["id"]):
            id_value = hit['_source'].get('id')
            if id_value is not None:
                ids.append(id_value)
        return ids

    def get_unlisted_availables(self, availables, most_recent_index):
        index_ids = self.get_all_ids(most_recent_index)

        #Filter out the dogs on trial adoption even though their status still says "Available"
        unmatched_dogs = [
            d for d in availables
            if d['dog_id'] not in index_ids and "Trial Adoption" not in d.get('location', '')
        ]

        # If you just want the ids:
        unmatched_ids = [d['dog_id'] for d in unmatched_dogs]

        return unmatched_dogs

    def get_most_recent_index(self):
        try:
            resp = self.es.cat.indices(format="json")

            # Extract index names (filtering for your pattern, if desired)
            indices = [item["index"] for item in resp if item["index"].startswith("animal-humane-")]

            if not indices:
                print("No animal-humane indices found")
                return None

            pattern = re.compile(r'animal-humane-(\d{8})-(\d{4})')

            # Build a list of tuples: (datetime-str, index-name)
            index_dates = []
            for index in indices:
                match = pattern.match(index)
                if match:
                    dt_str = match.group(1) + match.group(2)  # 'YYYYMMDDHHMM'
                    index_dates.append((dt_str, index))

            if not index_dates:
                print("No valid animal-humane indices found with proper date format")
                return None

            # Sort by datetime string
            most_recent = max(index_dates)[1]
            print(f"Most recent index: {most_recent}")
            return most_recent
        except Exception as e:
            print(f"Error getting most recent index: {e}")
            return None
    def get_new_dogs(self):
        indices_info = self.es.cat.indices(format='json')
        all_indices = [index['index'] for index in indices_info if index.get('status') == 'open']

        # Get today's date in YYYYMMDD format
        current_date = datetime.now().strftime('%Y%m%d')
        indices_today = [idx for idx in all_indices if f"-{current_date}-" in idx]

        # Get all unique ids from 'indices_today'
        unique_ids_today = set()
        for doc in scan(self.es, index=indices_today, query={"_source":False}):
            unique_ids_today.add(doc['_id'])

        # Exclude system indices and today's indices
        indices_not_today = [
            idx for idx in all_indices
            if not idx.startswith('.') and f"-{current_date}-" not in idx
        ]

        # Retrieve all unique _id values from each index (or all at once)
        previous_unique_ids = set()
        for idx in indices_not_today:
            for doc in scan(self.es, index=idx, query={"_source": False}):
                previous_unique_ids.add(doc['_id'])

        new_ids_today = unique_ids_today - previous_unique_ids

        #Put new dogs in the format expected by the output_utils.py
        new_dogs_list = []
        for doc_id in new_ids_today:
            resp = self.es.search(
            index=indices_today,
            body={"query": {"ids": {"values": [doc_id]}},"_source": ["name"]}
            )
            hits = resp.get('hits', {}).get('hits', [])
            if hits:
                doc = hits[0]
                source = doc.get('_source', {})
                dog_name = source.get('name')

                if dog_name:
                    new_dogs_list.append({
                        "name": dog_name,
                        "url": f"https://new.shelterluv.com/embed/animal/{doc_id}"
                    })
                else:
                    # Handle missing name field gracefully if needed
                    new_dogs_list.append({
                        "name": "(no name found)",
                        "url": f"https://new.shelterluv.com/embed/animal/{doc_id}"
                    })
            else:
                # Handle missing document gracefully if needed
                new_dogs_list.append({
                    "name": "(document not found)",
                    "url": f"https://new.shelterluv.com/embed/animal/{doc_id}"
                })
            result = {"new_dogs": new_dogs_list}
        #If there are no new dogs, result will not exist
        if 'result' in locals() or 'result' in globals():
            return result
        else:
            return {}

    def gather_unique_ids(self, index_names, id_field='dog_id'):
        """
        Returns a set of unique IDs from all provided indices.

        :param es: Elasticsearch client instance
        :param index_names: List of Elasticsearch index names
        :param id_field: The field name to extract (default 'dog_id')
        :return: Set of unique IDs
        """
        unique_ids = set()
        print(f"Index names passed to gather_unique_ids: {index_names}")
        for index in index_names:
            # Use a query that gets only the ID field for efficiency
            resp = self.es.search(
                index=index,
                size=1000,  # adjust size if you expect more docs; for >10k use scroll API
                _source=False,
                fields=[id],
                body={
                    "query": { "match_all": {} }
                }
            )
            hits = resp.get('hits', {}).get('hits', [])
            for hit in hits:
                # Try both 'fields' and fallback to '_source' if needed
                id_value = None
                if 'fields' in hit and id in hit['fields']:
                    id_value = hit['fields'][id][0]
                elif '_source' in hit and id in hit['_source']:
                    id_value = hit['_source'][id]
                if id_value is not None:
                    unique_ids.add(id_value)
        return unique_ids
    #TODO: Finish the get_unlisted_dogs function
    def get_unlisted_dogs(self):
        #Unlisted dogs are those that are not on the site and have a non-empty location.
        #Retrieve all unique ids where status is not "adopted"
        current_date = datetime.now().strftime("%Y%m%d")
        index_pattern = f"animal-humane-{current_date}-*"
        query = {
            "size": 0,
            "aggs": {
                "unique_dogs": {
                    "terms": {
                        "field": "id",
                        "size": 1000
                    },
                    "aggs": {
                        "latest_doc": {
                            "top_hits": {
                                "size": 1,
                                "sort": [{"_index": {"order": "desc"}}],
                                "_source": ["name", "id"]
                            }
                        }
                    }
                }
            },
            "query": {
                "bool": {
                    "must_not": [{"term": {"location": ""}}]
                }
            }
        }
        response = self.es.search(index=index_pattern, body=query, size=100)
        #This gets you all the available dogs. You still need to compare with dogs on the site
        dogs = []
        if "aggregations" in response:
            for bucket in response["aggregations"]["unique_dogs"]["buckets"]:
                hits = bucket["latest_doc"]["hits"]["hits"]
                if hits:
                    source = hits[0]["_source"]
                    dogs.append(source)
        return dogs

    def get_current_listed_count(self):
        #current count includes all unique ids for the day + unlisted but available dogs
        #such as those in bite quarantine or waiting for a vet check

        """
        Count unique dogs currently listed at the shelter using `timestamp` field.
        Excludes dogs whose final status is 'adopted'.
        """
        # Mountain Time zone
        mountain_tz = pytz.timezone("US/Mountain")
        now_mt = datetime.now(mountain_tz)

        # Today's start and end
        today_start = now_mt.replace(hour=0, minute=0, second=0, microsecond=0)
        today_start_str = today_start.strftime("%Y-%m-%dT%H:%M:%S%z")
        now_str = now_mt.strftime("%Y-%m-%dT%H:%M:%S%z")

        # Try "today" first
        unique_ids_today = set()
        adopted_ids_today = set()

        query_today = {"query":{"range":{"timestamp":{"gte":today_start_str,"lte": now_str}}},"_source":["id","status"]}

        for doc in scan(self.es, index="animal-humane-*", query=query_today):
            src = doc["_source"]
            dog_id = src.get("id")
            if dog_id:
                unique_ids_today.add(dog_id)
                if src.get("status", "").lower() == "adopted":
                    adopted_ids_today.add(dog_id)

        # If we have results for today, return them
        if unique_ids_today:
            return len(unique_ids_today) - len(adopted_ids_today)

        # Otherwise, fallback to yesterday
        yesterday_start = today_start - timedelta(days=1)
        yesterday_end = today_start - timedelta(seconds=1)
        yesterday_start_str = yesterday_start.strftime("%Y-%m-%dT%H:%M:%S%z")
        yesterday_end_str = yesterday_end.strftime("%Y-%m-%dT%H:%M:%S%z")

        query_yesterday = {"query":{"range":{"timestamp":{"gte":yesterday_start_str,"lte": yesterday_end_str}}},"_source":["id","status"]}

        unique_ids_yesterday = set()
        adopted_ids_yesterday = set()

        for doc in scan(self.es, index="animal-humane-*", query=query_yesterday):
            src = doc["_source"]
            dog_id = src.get("id")
            if dog_id:
                unique_ids_yesterday.add(dog_id)
                if src.get("status", "").lower() == "adopted":
                    adopted_ids_yesterday.add(dog_id)

        return len(unique_ids_yesterday) - len(adopted_ids_yesterday)

    def extract_datetime_from_index(self, index_name: str) -> datetime:
        datetime_str = index_name.split("animal-humane-")[1]
        return datetime.strptime(datetime_str, "%Y%m%d-%H%M")
        # Find the last '-' group that starts the date string
        #parts = index_name.split('-')
        #date_str = parts[-2] + '-' + parts[-1]  # results in YYYYMMDD-HHMM
        #return datetime.strptime(date_str, "%Y%m%d-%H%M")
        #"""
        #Extract datetime from index names in format:
        #animal-humane-YYYYMMDD-HHMM (NOT logging indices).
        #"""
        # Only process if it starts with 'animal-humane-' and doesn't have 'logging'
        #if index_name.startswith("animal-humane-") and "logging" not in index_name:
            # Remove the "animal-humane-" prefix and parse
        #    datetime_str = index_name.split("animal-humane-")[1]
        #    return datetime.strptime(datetime_str, "%Y%m%d-%H%M")
        #else:
        #    raise ValueError(f"Index name '{index_name}' is not a valid animal-humane date index")

    def get_unique_ids_from_indices(self,indices):
        if not indices:
            return set()
        body = {
            "size": 0,
            "aggs": {
                "all_ids": {
                    "terms": {
                        "field": "id",
                        "size": 100000  # adjust as needed
                    }
                }
            }
        }
        resp = self.es.search(index=",".join(indices), body=body)
        return set(bucket["key"] for bucket in resp["aggregations"]["all_ids"]["buckets"])

    def get_new_dog_count_this_week(self):
        """
        Return the count of dogs that appeared in indices from the last 7 days.
        This approximates "new dogs" by counting dogs in recent scrapes.
        """
        now = datetime.utcnow().replace(microsecond=0)
        seven_days_ago = now - timedelta(days=7)

        try:
            # Get indices from the last 7 days
            cutoff_date = seven_days_ago.strftime("%Y%m%d")

            # Get all indices and filter for recent ones
            indices_response = self.es.cat.indices(index="animal-humane-*", format="json")
            all_indices = [idx['index'] for idx in indices_response]

            # Filter for indices from the last 7 days
            recent_indices = []
            for index in all_indices:
                try:
                    # Extract date from index name (animal-humane-YYYYMMDD-...)
                    date_str = index.split('-')[2]  # YYYYMMDD
                    if date_str >= cutoff_date:
                        recent_indices.append(index)
                except:
                    continue

            if not recent_indices:
                return []

            recent_pattern = ",".join(recent_indices)

            # Query for all dogs in recent indices with aggregation to get names
            query = {
                "size": 0,
                "query": {"match_all": {}},
                "aggs": {
                    "unique_dogs": {
                        "terms": {
                            "field": "id",
                            "size": 10000
                        },
                        "aggs": {
                            "dog_name": {
                                "terms": {
                                    "field": "name.keyword",
                                    "size": 1
                                }
                            }
                        }
                    }
                }
            }

            resp = self.es.search(index=recent_pattern, body=query, request_timeout=60)

            if 'aggregations' in resp and 'unique_dogs' in resp['aggregations']:
                dog_names = []
                for bucket in resp['aggregations']['unique_dogs']['buckets']:
                    if bucket['dog_name']['buckets']:
                        dog_names.append(bucket['dog_name']['buckets'][0]['key'])
                
                print(f"Found {len(dog_names)} unique dogs in indices since {seven_days_ago.date()}")
                return sorted(dog_names)
            else:
                print("No aggregation results found")
                return []

        except es_exceptions.ApiError as e:
            print(f"Error querying Elasticsearch for new dog count: {e}")
            return []

    def get_new_dog_count_this_week_accurate(self):
        """
        Return the count of dogs that first appeared in the last 7 days.
        This checks each current dog's first appearance date by finding their earliest index.
        """
        now = datetime.utcnow().replace(microsecond=0)
        seven_days_ago = now - timedelta(days=7)
        cutoff_date = seven_days_ago.strftime("%Y%m%d")

        print(f"Checking for dogs that first appeared on or after {cutoff_date}")

        try:
            # First, get all current dogs from recent indices
            current_dogs = self.get_current_availables()
            current_dog_ids = set(dog.get('dog_id') for dog in current_dogs if dog.get('dog_id'))

            new_dog_count = 0
            new_dog_names = []

            for dog_id in current_dog_ids:
                try:
                    # Query for this dog's earliest appearance
                    query = {
                        "query": {"match": {"id": dog_id}},
                        "size": 1,
                        "_source": ["name"],
                        "sort": [{"_index": {"order": "asc"}}]
                    }

                    resp = self.es.search(index="animal-humane-*", body=query, request_timeout=10)

                    if resp["hits"]["hits"]:
                        earliest_index = resp["hits"]["hits"][0]["_index"]
                        dog_name = resp["hits"]["hits"][0]["_source"].get("name", f"ID:{dog_id}")

                        # Extract date from index name (animal-humane-YYYYMMDD-...)
                        try:
                            date_str = earliest_index.split('-')[2]  # YYYYMMDD
                            if date_str >= cutoff_date:
                                new_dog_count += 1
                                new_dog_names.append(dog_name)
                        except:
                            continue

                except Exception as e:
                    print(f"Error checking dog {dog_id}: {e}")
                    continue

            print(f"Found {new_dog_count} dogs that first appeared on or after {seven_days_ago.date()}")
            return sorted(new_dog_names)

        except es_exceptions.ApiError as e:
            print(f"Error querying Elasticsearch for accurate new dog count: {e}")
            return []

    def get_adopted_dog_count_this_week(self):
        """
        Return names, adoption dates, URLs, LOS, and count of unique dogs
        adopted in the last 7 days.
        """
        now = datetime.now(timezone.utc)
        #cover the entire day on the 7th day
        seven_days_ago = (now - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)

        query_body = { "query": { "bool": { "must": [ {"term": {"status.keyword": "adopted"}}, { "range": { "timestamp": { "gte": seven_days_ago.isoformat(), "lte": now.isoformat() } } } ] } }, "_source": [ "id", "status", "location", "name", "url", "length_of_stay_days", "timestamp" ], "size": 500 }

        adopted_ids = set()
        adopted_name = []
        adopted_date = []
        adopted_url = []
        adopted_los = []

        try:
            resp = self.es.search( index="animal-humane-*", body=query_body, request_timeout=30)

            for hit in resp["hits"]["hits"]:
                source = hit.get("_source", {})
                dog_id = source.get("id")

                # Ensure each unique dog only appears once
                if dog_id and dog_id not in adopted_ids:
                    adopted_ids.add(dog_id)
                    adopted_name.append(source.get("name"))
                    adopted_url.append(source.get("url"))
                    adopted_los.append(source.get("length_of_stay_days"))
                    adopted_date.append(source.get("timestamp"))

            print(f"Dogs adopted since {seven_days_ago.date()}: {adopted_name}")
            return adopted_name, adopted_date, adopted_url, adopted_los, len(adopted_ids)

        except es_exceptions.ApiError as e:
            print(f"Error querying adopted dogs in last 7 days: {e}")
            return [], [], [], [], 0

    def get_avg_length_of_stay(self):
        #For all dogs with "status":"adopted", calculate the average length of
        #stay.

        query_body = {"size":0,"query":{"term":{"status.keyword":"adopted"}},"aggs": {"by_id": {"terms": {"field": "id","size": 100},"aggs": {"most_recent": {"top_hits":{"size":1,"sort":[{"_index":{"order":"desc"}}],"_source": ["id", "length_of_stay_days", "status"]}}}}}}

        res = self.es.search(index="animal-humane-*", body=query_body)
        total_los = 0
        count = 0
        for bucket in res["aggregations"]["by_id"]["buckets"]:
            doc = bucket["most_recent"]["hits"]["hits"][0]["_source"]
            los = doc.get("length_of_stay_days")
            if los is not None:
                total_los += los
                count += 1
        average_los = (total_los / count) if count > 0 else 0
        print(f"Average length_of_stay_days for adopted dogs: {average_los:.2f} days based on {count} dogs")
        return round(average_los)

    def has_been_seen_before(self, dog_id: str) -> bool:
        # Only check indices from the last 3 months to avoid excessive queries
        # Use a simpler query that just checks if the dog exists in historical data
        from datetime import datetime, timedelta
        three_months_ago = datetime.now() - timedelta(days=90)
        date_pattern = three_months_ago.strftime('%Y%m%d')

        # Use index pattern for recent indices only (current year)
        current_year = datetime.now().strftime('%Y')
        index_pattern = f"animal-humane-{current_year}*"
        query = {
            "size": 0,
            "query": {
                "bool": {
                    "must": [
                        {"range": {"timestamp": {"lt": "now/d"}}},
                        {"term": {"id": dog_id}}
                    ]
                }
            }
        }

        try:
            response = self.es.search(index=index_pattern, body=query)
            total_hits = response.get("hits", {}).get("total", {}).get("value", 0)
            return total_hits > 0
        except Exception as e:
            print(f"Error checking if dog {dog_id} has been seen before: {e}")
            return False

    def get_returned_dogs(self, availables, most_recent_index):
        # Extract current date from most_recent_index (e.g., "20251227" from "animal-humane-20251227-1500")
        import re
        date_match = re.search(r'animal-humane-(\d{8})-', most_recent_index)
        if not date_match:
            # Fallback if date extraction fails
            return []
        current_date = date_match.group(1)
        # Convert to YYYY-MM-DD format for timestamp comparison
        formatted_today = f"{current_date[:4]}-{current_date[4:6]}-{current_date[6:]}"

        returned_dogs = []

        # For each available dog, check if they were previously adopted AND returned today
        for available_dog in availables:
            dog_id = available_dog['dog_id']

            # First check if this dog has "status":"adopted" in historical indices (before today)
            historical_query = {
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"id": dog_id}},
                            {"term": {"status": "adopted"}},
                            {"range": {"timestamp": {"lt": formatted_today}}}  # Before today
                        ]
                    }
                },
                "_source": ["name", "id", "status", "timestamp"]
            }

            try:
                response = self.es.search(index="animal-humane-*", body=historical_query)
                if response['hits']['total']['value'] > 0:
                    # This dog was previously adopted, now check if they returned TODAY
                    # Get all records for this dog to find the return date
                    all_records_query = {
                        "query": {"term": {"id": dog_id}},
                        "_source": ["status", "timestamp"],
                        "sort": [{"timestamp": {"order": "asc"}}],
                        "size": 1000
                    }
                    all_response = self.es.search(index="animal-humane-*", body=all_records_query)

                    # Find the return date (first "Available" status after adoption)
                    adoption_found = False
                    return_date = None

                    for record in all_response['hits']['hits']:
                        status = record['_source'].get('status')
                        timestamp = record['_source'].get('timestamp')

                        if status == 'adopted':
                            adoption_found = True
                        elif status == 'Available' and adoption_found and not return_date:
                            # This is the return date
                            return_date = timestamp[:10] if timestamp else None  # YYYY-MM-DD
                            break

                    # Only include if the return date is today
                    if return_date == formatted_today:
                        returned_dogs.append({
                            'name': available_dog.get('name', 'Unknown'),
                            'dog_id': dog_id,
                            'url': available_dog.get('url', ''),
                            'location': available_dog.get('location', '')
                        })

            except Exception as e:
                print(f"Error checking returned dog {dog_id}: {e}")

        return returned_dogs

    def get_dog_groups(self, availables, most_recent_index):
        #availables is a list of dicts in this format:
        #{'name': 'Nova', 'dog_id': 208810842, 'url': 'https://new.shelterluv.com/embed/animal/208810842', 'location': 'Main Kennel North, Main Campus - MKN-18'}

        # For diff analysis, use existing location data instead of scraping
        # to avoid seleniumwire dependency

        # Extract current date from most_recent_index (e.g., "20251227" from "animal-humane-20251227-1500")
        import re
        date_match = re.search(r'animal-humane-(\d{8})-', most_recent_index)
        if not date_match:
            # Fallback to just using the most recent index if date extraction fails
            current_date = None
        else:
            current_date = date_match.group(1)

        available_ids = [dog['dog_id'] for dog in availables]

        # Find adopted dogs: dogs with status "adopted" in today's indices but not in current availables
        adopted_dogs = []
        if current_date:
            # Query all indices from today for adopted dogs
            today_index_pattern = f"animal-humane-{current_date}-*"
            query = {
                "query": {"term": {"status": "adopted"}},
                "_source": ["name", "id", "url", "location", "status"]
            }
            try:
                response = self.es.search(index=today_index_pattern, body=query)
                for hit in response['hits']['hits']:
                    dog_data = hit['_source']
                    dog_id = dog_data['id']
                    # Only include if not in current available dogs
                    if dog_id not in available_ids:
                        adopted_dogs.append({
                            'name': dog_data.get('name', 'Unknown'),
                            'dog_id': dog_id,
                            'url': dog_data.get('url', ''),
                            'location': dog_data.get('location', '')
                        })
            except Exception as e:
                print(f"Error querying today's adopted dogs: {e}")
                # Fallback to old logic if today's query fails
                index_ids = self.get_all_ids(most_recent_index)
                adopted_dog_ids = [dog_id for dog_id in index_ids if dog_id not in available_ids]
                if adopted_dog_ids:
                    query = {
                        "query": {"terms": {"id": adopted_dog_ids}},
                        "_source": ["name", "id", "url", "location", "status"]
                    }
                    response = self.es.search(index=most_recent_index, body=query)
                    for hit in response['hits']['hits']:
                        dog_data = hit['_source']
                        adopted_dogs.append({
                            'name': dog_data.get('name', 'Unknown'),
                            'dog_id': dog_data['id'],
                            'url': dog_data.get('url', ''),
                            'location': dog_data.get('location', '')
                        })
        else:
            # Fallback to old logic if date extraction fails
            index_ids = self.get_all_ids(most_recent_index)
            adopted_dog_ids = [dog_id for dog_id in index_ids if dog_id not in available_ids]
            if adopted_dog_ids:
                query = {
                    "query": {"terms": {"id": adopted_dog_ids}},
                    "_source": ["name", "id", "url", "location", "status"]
                }
                response = self.es.search(index=most_recent_index, body=query)
                for hit in response['hits']['hits']:
                    dog_data = hit['_source']
                    adopted_dogs.append({
                        'name': dog_data.get('name', 'Unknown'),
                        'dog_id': dog_data['id'],
                        'url': dog_data.get('url', ''),
                        'location': dog_data.get('location', '')
                    })

        # Get index IDs for filtering unlisted dogs (still use most recent for this)
        index_ids = self.get_all_ids(most_recent_index)
        unlisted_dogs = [dog for dog in availables if dog['dog_id'] not in index_ids]

        returned_dogs = self.get_returned_dogs(availables, most_recent_index)

        trial_adoption_dogs = []
        other_unlisted_dogs = []

        for dog in unlisted_dogs:
            # Use the location from the available dogs data instead of scraping
            location = dog.get('location', '').strip().lower()

            if 'trial adoption' in location:
                trial_adoption_dogs.append(dog)
            else:
                other_unlisted_dogs.append(dog)

        return {
            'adopted_dogs': adopted_dogs,
            'trial_adoption_dogs': trial_adoption_dogs,
            'returned_dogs': returned_dogs,
            'other_unlisted_dogs': other_unlisted_dogs
        }
    def get_adoptions_per_day(self):
        query = {"size":0, "query":{"term":{"status":"adopted"}},"aggs":{"adoptions_over_time":{"date_histogram":{"field":"timestamp","calendar_interval":"day","format":"MM/dd/yyyy","time_zone":"-07:00"},"aggs":{"dog_names":{"terms":{"field":"name.keyword","size":100}}}}}}
        # Use index pattern that only includes 2025 indices to avoid timestamp mapping conflicts
        response = self.es.search(index="animal-humane-2025*", body=query)

        #for bucket in response["aggregations"]["adoptions_over_time"]["buckets"]:
        #    print({"date": bucket["key_as_string"], "count":bucket["doc_count"]})

        chart_data = [
            {
                "date": bucket["key_as_string"],
                "count": bucket["doc_count"],
                "names":[b["key"] for b in bucket["dog_names"]["buckets"]]
            }
            for bucket in response["aggregations"]["adoptions_over_time"]["buckets"]
        ]
        print(json.dumps(chart_data, indent=2))
        return chart_data

    def get_longest_resident(self):
        """
        Get the dog with the longest length of stay, calculated dynamically
        as the difference between intake_date and today's date.
        Only considers dogs that are currently available (most recent status is "available").
        """
        from datetime import datetime

        # First, get all dogs that are currently available by finding their most recent status
        # We'll query all documents and group by dog ID, keeping only those with latest status = "available"
        current_available_query = {
            "size": 10000,  # Need to get all available dogs
            "query": {"match_all": {}},  # Get all documents
            "_source": ["id", "status", "name", "intake_date", "url"],
            "sort": [{"_index": {"order": "desc"}}]  # Most recent index first
        }

        response = self.es.search(index="animal-humane-*", body=current_available_query)

        # Group by dog ID and keep only the most recent record for each dog
        dogs_by_id = {}
        for hit in response["hits"]["hits"]:
            dog_data = hit["_source"]
            dog_id = str(dog_data.get("id"))

            # Only keep the first (most recent) record for each dog
            if dog_id not in dogs_by_id:
                dogs_by_id[dog_id] = dog_data

        # Filter to only dogs with current status "available" and valid intake_date
        available_dogs = []
        for dog_data in dogs_by_id.values():
            if (dog_data.get("status", "").lower() == "available" and
                dog_data.get("intake_date") and
                dog_data.get("name")):  # Exclude euthanized dogs
                available_dogs.append(dog_data)

        if not available_dogs:
            return {"name": None, "days": None, "url": None}

        # Calculate length of stay for each available dog and find the maximum
        longest_stay_dog = None
        max_days = 0
        today = datetime.now().date()

        for dog_data in available_dogs:
            intake_date_str = dog_data.get("intake_date")

            try:
                # Parse intake_date (assuming format like "2025-10-17")
                intake_date = datetime.fromisoformat(intake_date_str.split('T')[0]).date()
                days = (today - intake_date).days

                if days > max_days:
                    max_days = days
                    longest_stay_dog = {
                        "name": dog_data.get("name"),
                        "days": days,
                        "url": dog_data.get("url")
                    }
            except (ValueError, AttributeError) as e:
                # Skip dogs with invalid intake dates
                continue

        return longest_stay_dog if longest_stay_dog else {"name": None, "days": None, "url": None}

    def get_weekly_age_group_adoptions(self):
        # Only search indices from 2025 onwards to avoid timestamp mapping conflicts
        query_body = {
            "size": 0,
            "query": {"term": {"status": "adopted"}},
            "aggs": {
                "weekly": {
                    "date_histogram": {
                        "field": "timestamp",
                        "calendar_interval": "week",
                        "format": "MM/dd/yyyy",
                        "time_zone": "-07:00"
                    },
                    "aggs": {
                        "by_age_group": {
                            "terms": {"field": "age_group.keyword", "size": 10}
                        }
                    }
                }
            }
        }
        # Use index pattern that only includes 2025 indices to avoid mapping conflicts
        response = self.es.search(index="animal-humane-2025*", body=query_body)
        weekly_buckets=response['aggregations']['weekly']['buckets']
        result = []

        for week_bucket in weekly_buckets:
            week_str = week_bucket['key_as_string']
            age_buckets = week_bucket['by_age_group']['buckets']
            week_data = {"week":week_str}
            # Initialize counts to zero for all age groups if needed
            for age_group in ["Puppy", "Adult", "Senior"]:
                week_data[age_group] = 0
            # Fill in the counts from the buckets
            for age_bucket in age_buckets:
                age_group = age_bucket['key']
                count = age_bucket['doc_count']
                week_data[age_group] = count
            result.append(week_data)
        print(f"Returning results from get_weekly_age_group_adoptions: {result}")
        #Return the most recent 5 weeks to prevent chart crowding
        return result[-5:]

    def get_adoption_percentages_per_origin(self):
        query_body={"size":0,"aggs":{"origins":{"terms":{"field":"origin.keyword","size":10000},"aggs": {"total_count": {"cardinality": {"field": "id","precision_threshold": 10000}},"adopted_count": {"filter": {"term": {"status.keyword": "adopted"}},"aggs": {"unique_adopted": {"cardinality": {"field": "id","precision_threshold": 10000}}}},"adoption_rate": {"bucket_script": {"buckets_path": {"adopted": "adopted_count>unique_adopted","total": "total_count"},"script": "params.total > 0 ? (params.adopted / params.total) * 100 : 0"}}}}}}
        response = self.es.search(index="animal-humane-*", body=query_body)
        origin_buckets=response['aggregations']['origins']['buckets']
        transformed_data = []
        for bucket in origin_buckets:
            coords = self.origin_coordinates.get(bucket["key"])
            if coords:
                transformed_data.append({
                    "latitude": coords["latitude"],
                    "longitude": coords["longitude"],
                    "locationName": bucket["key"],
                    "adoptionRate": bucket["adoption_rate"]["value"]
                })
            else:
                print(f"Warning: Coordinates missing for origin '{bucket['key']}'")
        return transformed_data

    def get_origins(self):
        # Query ALL dogs from shelters (both available and adopted)
        # Exclude only Unknown, Stray, and Owner Surrender
        query = {
            "query": {
                "bool": {
                    "must_not": [
                        {"term": {"origin.keyword": "Unknown"}},
                        {"term": {"origin.keyword": "Stray"}},
                        {"term": {"origin.keyword": "Owner Surrender"}}
                    ]
                }
            },
            "_source": ["id", "origin", "latitude", "longitude", "status"]
        }

        # Separate query for adopted dogs only
        adoptions_per_shelter = {
            "size": 0,
            "query": {
                "bool": {
                    "must": [
                        {"term": {"status.keyword": "adopted"}}
                    ],
                    "must_not": [
                        {"term": {"origin.keyword": "Unknown"}},
                        {"term": {"origin.keyword": "Stray"}},
                        {"term": {"origin.keyword": "Owner Surrender"}}
                    ]
                }
            },
            "aggs": {
                "shelters": {
                    "terms": {"field": "origin.keyword", "size": 500},
                    "aggs": {
                        "uids": {"cardinality": {"field": "id"}}
                    }
                }
            }
        }

        # Collect unique dogs per origin using aggregation across ALL indices
        # This gets total transfers (both current and adopted)
        origins_data = {}

        # Get all unique dog IDs per origin across all indices
        agg_query = {
            "size": 0,
            "query": {
                "bool": {
                    "must_not": [
                        {"term": {"origin.keyword": "Unknown"}},
                        {"term": {"origin.keyword": "Stray"}},
                        {"term": {"origin.keyword": "Owner Surrender"}}
                    ]
                }
            },
            "aggs": {
                "origins": {
                    "terms": {"field": "origin.keyword", "size": 500},
                    "aggs": {
                        "unique_dogs": {"cardinality": {"field": "id"}}
                    }
                }
            }
        }
        
        agg_response = self.es.search(index="animal-humane-*", body=agg_query)
        origin_buckets = agg_response["aggregations"]["origins"]["buckets"]
        
        for bucket in origin_buckets:
            origin_name = bucket["key"]
            count = int(bucket["unique_dogs"]["value"])
            origins_data[origin_name] = {
                'count': count,
                'latitude': None,
                'longitude': None
            }
        
        # Now get coordinates from ALL indices (not just latest)
        query["size"] = 10000
        response = self.es.search(index="animal-humane-*", body=query)
        hits = response["hits"]["hits"]
        
        # Update coordinates from latest index data
        doc_count = 0
        for doc in hits:
            doc_count += 1
            src = doc["_source"]
            origin = src.get("origin")
            lat = src.get("latitude")
            lon = src.get("longitude")

            # Handle list values
            if isinstance(origin, list):
                origin = origin[0] if origin else None
            if isinstance(lat, list):
                lat = lat[0] if lat else None
            if isinstance(lon, list):
                lon = lon[0] if lon else None

            # Skip if no origin or not in our aggregation results
            if not origin or origin not in origins_data:
                continue

            # Update coordinates if we have them (always use latest found)
            if lat is not None:
                origins_data[origin]['latitude'] = lat
            if lon is not None:
                origins_data[origin]['longitude'] = lon

        # Convert to the expected format and ensure coordinates are available
        origins = {}
        for origin_name, data in origins_data.items():
            lat = data['latitude']
            lon = data['longitude']

            # If we still don't have coordinates, try to get them from the predefined dict
            if lat is None or lon is None:
                coords_info = self.origin_coordinates.get(origin_name, {})
                if lat is None:
                    lat = coords_info.get('latitude')
                if lon is None:
                    lon = coords_info.get('longitude')

            # Only include origins that have coordinates
            if lat is not None and lon is not None:
                key = (origin_name, lat, lon)
                origins[key] = data['count']

                # Debug specific origins
                if origin_name in ['Bayard Animal Control', 'Clayton']:
                    print(f"DEBUG: {origin_name} - {data['count']} unique dogs")
                    print(f"DEBUG: {origin_name} coordinates - lat: {lat}, lon: {lon}")
            else:
                print(f"WARNING: {origin_name} has no coordinates - lat: {lat}, lon: {lon}")

        # Instead of counting historical adoptions, we need to count dogs by their CURRENT status
        # Use Elasticsearch aggregations to efficiently count current status per origin
        # This replaces the inefficient deduplication approach that hit the 10,000 document limit
        current_status_agg_query = {
            "size": 0,  # We only need aggregations, not the actual documents
            "query": {
                "bool": {
                    "must_not": [
                        {"term": {"origin.keyword": "Unknown"}},
                        {"term": {"origin.keyword": "Stray"}},
                        {"term": {"origin.keyword": "Owner Surrender"}}
                    ]
                }
            },
            "aggs": {
                "origins": {
                    "terms": {
                        "field": "origin.keyword",
                        "size": 500  # Should be enough for all shelters
                    },
                    "aggs": {
                        "dogs": {
                            "terms": {
                                "field": "id",
                                "size": 10000  # Allow up to 10k dogs per shelter
                            },
                            "aggs": {
                                "latest_status": {
                                    "top_hits": {
                                        "size": 1,
                                        "sort": [{"_index": {"order": "desc"}}],  # Most recent index first
                                        "_source": ["status"]
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        # Execute the aggregation query
        agg_response = self.es.search(index="animal-humane-*", body=current_status_agg_query)

        # Process aggregation results
        adopted_by_origin = {}
        available_by_origin = {}

        for origin_bucket in agg_response['aggregations']['origins']['buckets']:
            origin = origin_bucket['key']

            # Count unique dogs by their latest status
            adopted_count = 0
            available_count = 0

            for dog_bucket in origin_bucket['dogs']['buckets']:
                # Get the latest status for this dog
                latest_hit = dog_bucket['latest_status']['hits']['hits'][0]
                status = latest_hit['_source'].get('status', '').lower()

                if status == 'adopted':
                    adopted_count += 1
                elif status == 'available':
                    available_count += 1

            adopted_by_origin[origin] = adopted_count
            available_by_origin[origin] = available_count

        # Debug: Print adopted dogs per shelter
        print("ADOPTED dogs per shelter:")
        for shelter_name, count in adopted_by_origin.items():
            print(f"  {shelter_name}: {count}")

        result = [
            {"origin": o[0], "latitude": o[1], "longitude": o[2], "count": count}
            for o, count in origins.items()
        ]

        # Debug: Print specific origins and final result structure
        print(f"\nDEBUG: Used Elasticsearch aggregations to process ALL records efficiently")
        print(f"DEBUG: Found {len(origins_data)} unique origins with IDs")
        print(f"FINAL RESULTS - Total origins returned (with coords): {len(result)}")
        for item in result:
            if "Bayard" in item.get('origin', '') or "Clayton" in item.get('origin', ''):
                print(f"FINAL RESULT: {item}")

        # Also check if any origins are missing coordinates
        missing_coords = [item for item in result if item.get('latitude') is None or item.get('longitude') is None]
        if missing_coords:
            print(f"WARNING: {len(missing_coords)} origins missing coordinates:")
            for item in missing_coords:
                print(f"  - {item.get('origin')}: lat={item.get('latitude')}, lon={item.get('longitude')}")

        # Add adopted and available counts to each shelter in result
        for shelter in result:
            origin = shelter.get('origin')
            adopted = adopted_by_origin.get(origin, 0)
            available = available_by_origin.get(origin, 0)
            shelter['adopted'] = adopted
            shelter['available'] = available

        # Debug: Print final results for specific origins
        print("\nCURRENT STATUS counts per shelter:")
        for shelter in result:
            origin = shelter.get('origin')
            if origin in ['Four Corners Animal League', 'Bayard Animal Control', 'Clayton']:
                print(f"  {origin}: total={shelter.get('count')}, adopted={shelter.get('adopted')}, available={shelter.get('available')}")

        return result

    def get_adoption_count_per_shelter(self):
        #{'origin': 'ABQ Animal Welfare Department', 'latitude': 35.1102, 'longitude': -106.5823, 'count': 18}
        adoptions_per_shelter_query = {"size":0,"query":{"match":{"status":"adopted"}},"aggs":{"shelters":{"terms":{"field":"origin.keyword","size":500},"aggs":{"uids":{"terms":{"field":"id","size":500}}}}}}
        adoptions_per_shelter_results = self.es.search(index="animal-humane-*", body=adoptions_per_shelter_query)
        #print(f"adoptions_per_shelter_results = {adoptions_per_shelter_results}")
        shelter_buckets=adoptions_per_shelter_results['aggregations']['shelters']['buckets']
        transformed_shelter_data = []
        for bucket in shelter_buckets:
            print(f"bucket in shelter_buckets: {bucket}")
            shelter_name = bucket["key"]
            if shelter_name == 'Unknown' or shelter_name == 'Stray' or shelter_name == 'Owner Surrender':
                continue
            adoptions_res = bucket["uids"]
            num_adoptions = len(adoptions_res['buckets'])
            transformed_shelter_data.append({shelter_name:num_adoptions})
        return transformed_shelter_data

    def get_age_groups(self, idx):
        try:
            # Check if index exists first
            if not self.es.indices.exists(index=idx):
                print(f"Index {idx} does not exist, returning empty age groups")
                return []

            query_body = {"query":{"bool":{"must":[{"match":{"status":"Available"}}]}},"aggs":{"age_groups":{"terms":{"field":"age_group.keyword"},"aggs": {"unique_dogs": {"cardinality":{"field": "id"}}}}}}
            response = self.es.search(index=idx, body=query_body)

            # Check if aggregations exist in response
            if "aggregations" not in response or "age_groups" not in response["aggregations"]:
                print(f"No aggregations found in response for index {idx}, returning empty age groups")
                return []

            age_group_data = [
                {
                    "age_group": bucket["key"],
                    "count": bucket["doc_count"],
                }
                for bucket in response["aggregations"]["age_groups"]["buckets"]
            ]
            print(f"returning age_group_data: {age_group_data}")
            return age_group_data
        except Exception as e:
            print(f"Error in get_age_groups: {e}")
            return []
    def get_length_of_stay_distribution(self, status=None, index_pattern=None):
        """
        Get histogram distribution of length_of_stay_days for dogs at the shelter.
        Uses fixed 30-day intervals for bin calculation.
        Returns bins with dog lists containing minimal fields.

        Uses the same logic as get_current_availables() to get all currently available dogs
        from all indices, deduplicating by ID and keeping the most recent record for each dog.
        
        For visualization purposes, length_of_stay_days is dynamically calculated as the 
        number of days between intake_date and current date, rather than using the stored value.

        Args:
            status: Optional status filter ('available', 'adopted', etc.). If None, defaults to 'available'.
            index_pattern: Optional index pattern to search. If None, uses all animal-humane indices.
        """
        from datetime import datetime

        # Default to 'available' if no status specified
        target_status = status if status is not None else "available"
        
        # Use the same logic as get_current_availables() to get all current available dogs
        try:
            # Use all animal-humane indices but sort by recency for deduplication
            index_pattern = index_pattern or "animal-humane-*"

            # Use a simpler query without aggregations to avoid mixed type issues
            query = {
                "size": 10000,  # Get up to 10k documents
                "sort": [{"_index": {"order": "desc"}}],  # Sort by index name (most recent first)
                "_source": ["id", "name", "breed", "age_group", "length_of_stay_days", "intake_date", "status"],
                "query": {
                    "match_all": {}  # Get all dogs from recent indices
                }
            }

            # Run the search on all indices
            response = self.es.search(index=index_pattern, body=query)

            # Process results to get unique dogs (most recent record for each ID)
            dogs_by_id = {}
            for hit in response['hits']['hits']:
                dog_data = hit['_source']
                dog_id = str(dog_data['id'])  # Ensure ID is string for consistency

                # Keep the most recent record for each dog (first in sorted results)
                if dog_id not in dogs_by_id:
                    dogs_by_id[dog_id] = {
                        "id": dog_data.get("id"),
                        "name": dog_data.get("name", "Unknown"),
                        "breed": dog_data.get("breed"),
                        "age_group": dog_data.get("age_group"),
                        "length_of_stay_days": dog_data.get("length_of_stay_days"),
                        "intake_date": dog_data.get("intake_date"),
                        "status": dog_data.get("status")
                    }

            # Filter for dogs with the target status and calculate dynamic length of stay
            from datetime import datetime
            current_date = datetime.now().date()
            
            filtered_dogs = []
            for dog in dogs_by_id.values():
                if dog.get("status") == target_status.title() and dog.get("intake_date"):
                    try:
                        # Parse intake_date and calculate dynamic length of stay
                        intake_date = datetime.fromisoformat(dog["intake_date"].replace('Z', '+00:00')).date()
                        dynamic_length_of_stay = (current_date - intake_date).days
                        
                        # Create dog record with calculated length of stay for visualization
                        dog_with_calculated_los = dog.copy()
                        dog_with_calculated_los["length_of_stay_days"] = dynamic_length_of_stay
                        dog_with_calculated_los["original_length_of_stay_days"] = dog.get("length_of_stay_days")  # Keep original for reference
                        
                        filtered_dogs.append(dog_with_calculated_los)
                    except (ValueError, TypeError) as e:
                        print(f"Error parsing intake_date for dog {dog.get('id')}: {e}")
                        continue

            # Define the bin ranges (0-30, 31-60, 61-90, etc.)
            bin_ranges = []
            bin_start = 0
            max_bins = 20  # Reasonable limit to prevent excessive bins

            for i in range(max_bins):
                if bin_start == 0:
                    bin_end = 30
                    bin_start_next = 31
                else:
                    bin_end = bin_start + 29
                    bin_start_next = bin_end + 1

                bin_ranges.append({
                    "min": bin_start,
                    "max": bin_end,
                    "from": bin_start,
                    "to": bin_end + 1  # Elasticsearch range is exclusive of 'to'
                })
                bin_start = bin_start_next

            # Build histogram from filtered dogs
            bins = []
            total_dogs = len(filtered_dogs)

            for bin_range in bin_ranges:
                # Find dogs in this bin
                dogs_in_bin = [
                    dog for dog in filtered_dogs
                    if bin_range["from"] <= dog["length_of_stay_days"] < bin_range["to"]
                ]
                
                bins.append({
                    "min": bin_range["min"],
                    "max": bin_range["max"],
                    "count": len(dogs_in_bin),
                    "dogs": dogs_in_bin
                })

                # Stop creating bins if we've gone beyond the data range
                if bin_range["min"] > 365:  # Reasonable cutoff at 1 year
                    break

            print(f"Length of stay distribution: {total_dogs} dogs from all indices with deduplication (dynamic calculation)")

            return {
                "bins": bins,
                "metadata": {
                    "n": total_dogs,
                    "bin_algorithm": "30_day_intervals_all_indices_deduplicated_dynamic_los",
                    "index_used": index_pattern,
                    "generated_at": datetime.now().isoformat(),
                    "calculation_method": "dynamic_from_intake_date"
                }
            }

        except Exception as e:
            print(f"Error getting length_of_stay_distribution: {e}")
            import traceback
            traceback.print_exc()
            return {
                "bins": [],
                "metadata": {
                    "n": 0,
                    "bin_algorithm": "30_day_intervals_all_indices_deduplicated_dynamic_los",
                    "index_used": index_pattern or "animal-humane-*",
                    "generated_at": datetime.now().isoformat(),
                    "calculation_method": "dynamic_from_intake_date",
                    "error": str(e)
                }
            }

