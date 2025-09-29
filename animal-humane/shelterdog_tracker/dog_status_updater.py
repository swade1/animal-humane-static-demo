class DogStatusUpdater:
    def __init__(self, scraper, es_handler):
        self.scraper = scraper
        self.es_handler = es_handler

    def update_dog_statuses(self, ids_to_process, indexA, indexB):
        print(f"update_dog_statuses called with ids: {ids_to_process}")
        print(f"and indices {indexA} and {indexB}")
        for dog_id in ids_to_process:
            #Retrieve current location
            url = f'https://new.shelterluv.com/embed/animal/{dog_id}'
            current_location = self.scraper.scrape_dog_location(url)
            #Compare current location with index location
            dog_doc = get_dog_by_id(self, dog_id) 
            index_location = dog_doc['location']
            if current_location != index_location:
                print(f"current_location in DogStatusUpdater class is: {current_location}")
                # Example: new_status_info = {'status': 'Adopted', 'location': 'Foster'}
                self.es_handler.update_dog_fields(indexA, dog_id, current_location)
            elif current_location == index_location:
                dog_data = dog_doc['_source']
                self.es_handler.index_dog(self, indexB, id=dog_id, document=dog_data)


#There are two (so far) cases to handle when dog is in indexA but not indexB:
#if indexA location != indexB location
#    update location (adoption, trial adoption, parasite treatment, etc)
#elif indexA location == indexB location:
#    copy entire doc from indexA to indexB so dog does not drop off radar
