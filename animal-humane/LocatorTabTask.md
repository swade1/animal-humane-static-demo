Use Case:
I'd like to let the user enter a kennel number/location and see who is in the kennel currently, regardless of if that dog is available or not. Additionally I'd like to let the user enter a dog's name and see where that dog is, whether it's in a Foster Home, at the Westside Adoption Center, etc. I'd like that functionality to be in a new tab called 'Locator' and be placed to the right of the the Insights & Spotlight tab. Give me a detailed plan with tasks and subtasks to implement this requirement.

Plan: 

1. Backend/Data Preparation
 a. Ensure up-to-date mapping of dog IDs/names to locations (kennel, foster, adoption center, etc.)
 b. Expose an API endpoint (or extend an existing one) to:
  i. Return all dogs currently in a given kennel/location
  ii. Return the current location for a given dog name (or ID)
 c. Handle cases where a dog or kennel is not found, or data is ambiguous

2. Frontend: UI/UX
 a. Add a new tab “Locator” to the right of the Insights & Spotlight tab
 b. Design the Locator tab with:
  i. A search box for kennel number/location
  ii. A search box for dog name
  iii. Display area for results (list of dogs in a kennel, or location for a dog)
 c. Show clear messages for “not found” or “no dogs in this kennel”
 d. (Optionally) Add autocomplete or suggestions for kennel numbers and dog names

3. Frontend: Logic
 a. On search, call the backend API with the entered kennel/location or dog name
 b. Display results in a user-friendly format
 c. Handle loading, error, and empty states

4. Integration & Testing
 a. Test with real and edge-case data (e.g., empty kennels, dogs with similar names)
 b. Verify the Locator tab appears in the correct position
 c. Test responsiveness and accessibility

5. Documentation & Deployment
 a. Document the new API endpoints and UI usage
 b. Deploy changes and monitor for issues

Task List

1. Backend/API
 1.1. Review data sources for kennel and dog location info
 1.2. Implement/extend API:
  - GET /locator/kennel/{kennel_id} → list dogs in kennel
  - GET /locator/dog/{dog_name} → current location of dog
 1.3. Add error handling for not found/ambiguous cases
 1.4. Write unit tests for new endpoints

2. Frontend
 2.1. Add “Locator” tab to navigation (right of Insights & Spotlight)
 2.2. Create Locator tab UI:
  - Input for kennel/location
  - Input for dog name
  - Results display area
 2.3. Connect UI to backend API
 2.4. Handle loading, error, and empty states
 2.5. (Optionally) Add autocomplete for kennels/dogs
 2.6. Write component/unit tests

3. Integration
 3.1. Test end-to-end with real data
 3.2. Verify tab placement and UI/UX
 3.3. Fix bugs and edge cases

4. Documentation & Deployment
 4.1. Update API and UI documentation
 4.2. Deploy to production
 4.3. Monitor and gather user feedback
