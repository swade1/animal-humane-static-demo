from datetime import datetime

class Dog:
    def __init__(self, timestamp, dog_id, name, location=None, origin=None, status='Available', url=None, intake_date=None, length_of_stay_days=None, birthday=None, age_group=None, breed=None, secondary_breed=None, weight_group=None, color=None, bite_quarantine=None, returned=None, latitude=None, longitude=None, **kwargs):
        self.timestamp = timestamp
        self.id = dog_id
        self.name = name
        self.location = location if location else "" 
        self.origin=origin
        self.status = status
        self.url = url
        self.intake_date = intake_date
        self.length_of_stay_days = length_of_stay_days
        self.birthday = birthday
        self.age_group = age_group
        self.breed = breed
        self.secondary_breed = secondary_breed
        self.weight_group = weight_group
        self.color = color 
        self.bite_quarantine=bite_quarantine
        self.returned=returned
        self.latitude=latitude
        self.longitude=longitude
        # all the information provided on the page is saved to attributes 
        self.attributes = kwargs
    def is_complete(self):
        # Define what "complete" means for your use case
        return self.id is not None and self.name and self.location and self.status and self.url and self.intake_date

    def update_status(self, new_status):
        self.status = new_status

    def to_dict(self, include_attributes=True):
        
        data = {
            "timestamp":self.timestamp,
            "id": self.id,
            "name": self.name,
            "location": self.location,
            "origin":self.origin,
            "status": self.status,
            "url": self.url,
            "intake_date":self.intake_date,
            "length_of_stay_days":self.length_of_stay_days,
            "birthdate":self.birthday,
            "age_group":self.age_group,
            "breed":self.breed,
            "secondary_breed":self.secondary_breed,
            "weight_group":self.weight_group,
            "color":self.color,
            "bite_quarantine":self.bite_quarantine,
            "returned":self.returned,
            "latitude":self.latitude,
            "longitude":self.longitude
        }
        if include_attributes:
            data.update(self.attributes)
        return data
