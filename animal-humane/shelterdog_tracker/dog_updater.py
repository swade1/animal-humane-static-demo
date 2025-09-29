class DogUpdater:
    def __init__(self, es_handler):
        self.es_handler = es_handler

    def process_changes(self, change_ids):
        for dog_id in change_ids:
            #What really needs to happen here is to use the id to access the shelterluv
            #page for each dog and scrape the three fields. It's possible that there are
            #no changes. Can I take advantage of the ShelterScraper class?
            dog = self.es_handler.get_dog_by_id(dog_id)
            if not dog:
                continue
            new_status, new_location, new_name  = self.determine_updates(dog)
            self.es_handler.update_dog_fields(dog_id, {
                'status': new_status,
                'location': new_location,
                'name': new_name
            })

    def determine_updates(self, dog):
        # Implement logic based on dog info, diff, or other rules
        new_status = dog.status  # example placeholder
        new_location = dog.location  # example placeholder
        new_name = dog.name
        return new_status, new_location, new_name
  
    #when id is in set b but not set a
    def process_additions(self, new_ids):
        pass
