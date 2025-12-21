    def get_length_of_stay_distribution(self):
        """
        Get histogram distribution of length_of_stay_days for dogs currently available at the shelter.
        Uses fixed 30-day intervals for bin calculation.
        Calculates current length of stay from intake_date for available dogs only.
        Excludes adopted and euthanized dogs.
        Returns bins with dog lists containing minimal fields.

        Bin boundaries: [min, max] inclusive for all bins except last which is right-inclusive.
        """
        import math
        from datetime import datetime

        # First, get all unique dog IDs across all indices
        id_query = {
            "size": 0,
            "aggs": {
                "unique_ids": {
                    "terms": {
                        "field": "id",
                        "size": 10000
                    }
                }
            }
        }

        try:
            # Get all unique dog IDs from all indices
            id_response = self.es.search(index="animal-humane-*", body=id_query)
            dog_ids = [bucket["key"] for bucket in id_response["aggregations"]["unique_ids"]["buckets"]]

            # Now get the latest record for each dog
            dogs = []
            excluded_count = 0

            for dog_id in dog_ids:
                # Get the most recent record for this dog across all indices
                dog_query = {
                    "size": 1,
                    "query": {"term": {"id": dog_id}},
                    "sort": [{"_index": {"order": "desc"}}],  # Most recent index first
                    "_source": ["id", "name", "breed", "age_group", "length_of_stay_days", "intake_date", "status"]
                }

                dog_response = self.es.search(index="animal-humane-*", body=dog_query)
                if dog_response["hits"]["hits"]:
                    source = dog_response["hits"]["hits"][0]["_source"]
                    name = source.get("name", "Unknown")
                    breed = source.get("breed")
                    age_group = source.get("age_group")
                    status = source.get("status", "").lower()
                    intake_date_str = source.get("intake_date")
                    stored_los = source.get("length_of_stay_days")

                    # Skip euthanized dogs
                    if status == "euthanized":
                        excluded_count += 1
                        continue

                    # Only include dogs with status "available"
                    if status != "available":
                        excluded_count += 1
                        continue

                    # Calculate current length of stay for available dogs
                    los_days = None

                    if intake_date_str:
                        # Calculate current stay for available dogs
                        try:
                            intake_date = datetime.fromisoformat(intake_date_str.replace('Z', '+00:00')).date()
                            current_date = datetime.now().date()
                            los_days = (current_date - intake_date).days
                            if los_days < 0:  # Future date, invalid
                                los_days = None
                        except (ValueError, TypeError):
                            los_days = None

                    # Use stored length_of_stay_days if available and reasonable, otherwise use calculated
                    final_los = stored_los if stored_los is not None and stored_los >= 0 else los_days

                    # Only include dogs with valid LOS
                    if final_los is not None and final_los >= 0:
                        dogs.append({
                            "id": dog_id,
                            "name": name,
                            "breed": breed,
                            "age_group": age_group,
                            "length_of_stay_days": final_los,
                            "status": status
                        })
                    else:
                        excluded_count += 1

            n = len(dogs)
            print(f"Length of stay distribution: {n} dogs included, {excluded_count} excluded")

            # Handle edge case: no valid dogs
            if n == 0:
                return {"bins": [], "metadata": {"n": 0, "bin_algorithm": "30_day_intervals", "generated_at": datetime.now().isoformat()}}

            # Handle edge case: single dog
            if n == 1:
                dog = dogs[0]
                los_val = dog["length_of_stay_days"]
                return {
                    "bins": [{
                        "min": los_val,
                        "max": los_val,
                        "count": 1,
                        "dogs": [dog]
                    }],
                    "metadata": {"n": 1, "bin_algorithm": "30_day_intervals", "generated_at": datetime.now().isoformat()}
                }

            # Use fixed 30-day intervals
            bin_width = 30  # 30-day intervals

            # Calculate number of bins needed to cover the range with 30-day intervals
            los_values = [d["length_of_stay_days"] for d in dogs]
            min_los = min(los_values)
            max_los = max(los_values)

            # Create bins with fixed 30-day intervals: 0-30, 31-60, 61-90, etc.
            bins = []
            bin_start = 0

            while bin_start <= max_los:
                if bin_start == 0:
                    bin_end = 30
                    bin_start_next = 31
                else:
                    bin_end = bin_start + 29
                    bin_start_next = bin_end + 1

                bin_dogs = [d for d in dogs if bin_start <= d["length_of_stay_days"] <= bin_end]

                # Always add bins, even if empty (but only up to the point where we have data)
                bins.append({
                    "min": bin_start,
                    "max": bin_end,
                    "count": len(bin_dogs),
                    "dogs": bin_dogs
                })

                bin_start = bin_start_next

                # If we've exceeded the max, stop creating bins
                if bin_start > max_los:
                    break

            return {
                "bins": bins,
                "metadata": {
                    "n": n,
                    "bin_algorithm": "30_day_intervals",
                    "generated_at": datetime.now().isoformat()
                }
            }

        except Exception as e:
            print(f"Error getting length_of_stay_distribution: {e}")
            import traceback
            traceback.print_exc()
            return {"bins": [], "metadata": {"n": 0, "bin_algorithm": "30_day_intervals", "generated_at": datetime.now().isoformat(), "error": str(e)}}