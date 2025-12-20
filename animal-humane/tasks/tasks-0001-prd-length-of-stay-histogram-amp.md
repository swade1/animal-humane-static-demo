# Task List: Length of Stay Histogram Visualization

Generated from: `0001-prd-length-of-stay-histogram.md`

## Relevant Files

### Backend Files
- `models/api_models.py` - Add Pydantic models for LOS histogram response (LOSDogSummary, LOSBin, LOSHistogramData)
- `shelterdog_tracker/elasticsearch_handler.py` - Add method to query all dogs with length_of_stay_days and calculate histogram bins
- `services/elasticsearch_service.py` - Add async wrapper method for the new handler functionality
- `services/dog_service.py` - Add business logic method to orchestrate length of stay data retrieval
- `api/main.py` - Add new `/api/length-of-stay` endpoint
- `tests/test_length_of_stay.py` - Unit tests for backend functionality (new file)

### Frontend Files
- `react-app/src/api.js` - Add `fetchLengthOfStayData()` function to call the new API endpoint
- `react-app/src/components/LengthOfStayHistogram.js` - New component for the histogram visualization
- `react-app/src/components/DogListModal.js` - New component for displaying dog details on bar click
- `react-app/src/InsightsTab.js` - Integrate the new histogram component

### Notes
- The project uses FastAPI (async Python) for the backend, not Flask
- Elasticsearch is accessed via `ElasticsearchHandler` class with synchronous methods wrapped in async via `ElasticsearchService`
- Frontend uses Recharts library for visualizations (already installed)
- Backend tests use pytest framework
- No test framework is currently configured for React components, so frontend tests are out of scope for initial implementation

## Tasks

- [ ] 1.0 Define API Contract and Response Models
  - [ ] 1.1 Add Pydantic model `LOSDogSummary` to `models/api_models.py` with fields: id, name, breed, age, length_of_stay_days
  - [ ] 1.2 Add Pydantic model `LOSBin` to `models/api_models.py` with fields: min, max, count, dogs (List[LOSDogSummary])
  - [ ] 1.3 Add Pydantic model `LOSHistogramData` with fields: bins (List[LOSBin]), metadata (dict with n, bin_algorithm, generated_at)
  - [ ] 1.4 Add code comments documenting bin boundary conventions (e.g., [min, max] inclusive, or last bin right-inclusive)

- [ ] 2.0 Verify Elasticsearch Data Readiness
  - [ ] 2.1 Check that `length_of_stay_days` exists as a numeric field in the latest index mapping
  - [ ] 2.2 Add validation in ElasticsearchHandler to exclude docs where `length_of_stay_days` is null/missing
  - [ ] 2.3 Add logging to track count of included vs excluded documents
  - [ ] 2.4 Ensure queries use the `animal-humane-latest` alias (not hardcoded index names)
  - [ ] 2.5 Add fallback logic if needed: compute on-the-fly for available dogs (today - intake_date) and adopted dogs (adopted_date - intake_date)

- [ ] 3.0 Create Backend API Endpoint for Length of Stay Data
  - [ ] 3.1 Add `get_length_of_stay_distribution()` method to `ElasticsearchHandler` class that queries all dogs (available and adopted) from the latest index using `animal-humane-latest` alias
  - [ ] 3.2 Extract `length_of_stay_days` field with numeric cast, filtering out null/invalid values
  - [ ] 3.3 Log how many documents were included vs excluded
  - [ ] 3.4 Implement bin calculation logic using Sturges' formula: `num_bins = ceil(log2(n) + 1)` where n is the number of valid dogs
  - [ ] 3.5 Create histogram data structure with bins containing: bin range (min, max), count, and list of minimal dog objects (only id, name, breed, age, length_of_stay_days)
  - [ ] 3.6 Handle edge cases: empty dataset (return empty bins), single dog, all dogs with same length of stay
  - [ ] 3.7 Add async wrapper method `get_length_of_stay_distribution()` to `ElasticsearchService` class
  - [ ] 3.8 Add business logic method `get_length_of_stay_data()` to `DogService` class to call the ES service method and return LOSHistogramData model
  - [ ] 3.9 Add new FastAPI route `@app.get("/api/length-of-stay", response_model=APIResponse)` in `api/main.py` following existing pattern
  - [ ] 3.10 Return `APIResponse.success_response(histogram_data)` to match other endpoints
  - [ ] 3.11 Test the endpoint manually using curl to verify JSON response structure matches Pydantic models
  
- [ ] 4.0 Implement Frontend API Client Function
  - [ ] 4.1 Add `fetchLengthOfStayData()` function to `react-app/src/api.js` following the existing pattern (fetch from `/api/length-of-stay`, handle errors)
  - [ ] 4.2 Verify the function returns the expected data structure by logging the response in browser console

- [ ] 5.0 Build Length of Stay Histogram React Component
  - [ ] 5.1 Create new file `react-app/src/components/LengthOfStayHistogram.js`
  - [ ] 5.2 Import required Recharts components: `BarChart`, `Bar`, `XAxis`, `YAxis`, `CartesianGrid`, `Tooltip`, `ResponsiveContainer`
  - [ ] 5.3 Set up component state using `useState` to hold histogram data, loading state, and error state
  - [ ] 5.4 Implement `useEffect` hook to call `fetchLengthOfStayData()` on component mount with try/catch error handling
  - [ ] 5.5 Add loading state UI (e.g., "Loading..." message) matching existing InsightsTab patterns
  - [ ] 5.6 Add error state UI (e.g., "Failed to load data" message) matching existing InsightsTab patterns
  - [ ] 5.7 Transform API response data into format suitable for Recharts (array of objects with keys for X-axis labels and Y-axis values)
  - [ ] 5.8 Create X-axis labels from bin ranges with consistent formatting (e.g., "0–10 days", "11–20 days"), sorted ascending
  - [ ] 5.9 Implement custom Tooltip component to show exact dog count (as integer) on hover with accessible text
  - [ ] 5.10 Add onClick handler to Bar component that captures clicked bin data and passes it to parent callback prop
  - [ ] 5.11 Add chart title "Length of Stay Distribution - All Dogs" above the ResponsiveContainer with proper heading markup
  - [ ] 5.12 Style the chart to match existing InsightsTab charts (use color `#4E79A7`, match margins and responsive container sizing)
  - [ ] 5.13 Handle edge cases: display "No data available" message when histogram data is empty

- [ ] 6.0 Implement Dog List Modal Component
  - [ ] 6.1 Create new file `react-app/src/components/DogListModal.js`
  - [ ] 6.2 Accept props: `isOpen` (boolean), `onClose` (function), `dogs` (array of dog objects), `binRange` (string for display)
  - [ ] 6.3 Conditionally render modal only when `isOpen` is true
  - [ ] 6.4 Create modal overlay with semi-transparent background that prevents background scroll when open
  - [ ] 6.5 Create modal content container with white background, border, and centered positioning
  - [ ] 6.6 Add accessible modal title using `aria-labelledby` and `role="dialog"`
  - [ ] 6.7 Add modal header showing the bin range (e.g., "Dogs with 0–10 Days Stay")
  - [ ] 6.8 Add close button (X icon or "Close" text) in top-right corner that calls `onClose` when clicked
  - [ ] 6.9 Render table with columns: Name, Breed, Age, Length of Stay (days)
  - [ ] 6.10 Map over `dogs` prop to create table rows with dog data
  - [ ] 6.11 Add basic CSS styling for modal (flexbox centering, z-index: 1000, padding, font styling to match app)
  - [ ] 6.12 Implement click-outside-to-close functionality
  - [ ] 6.13 Implement keyboard close on Escape key
  - [ ] 6.14 Implement focus trap to keep keyboard navigation within modal when open

- [ ] 7.0 Integrate Histogram into InsightsTab
  - [ ] 7.1 Import `LengthOfStayHistogram` and `DogListModal` components at the top of `InsightsTab.js`
  - [ ] 7.2 Add state variable `selectedBin` using `useState` to track which bin was clicked (initially null)
  - [ ] 7.3 Add `handleBarClick` callback function that sets `selectedBin` state with clicked bin data
  - [ ] 7.4 Add `handleModalClose` callback function that resets `selectedBin` to null
  - [ ] 7.5 Position the `<LengthOfStayHistogram>` component below the `<ShelterTransfersBarChart>` component (after line 299)
  - [ ] 7.6 Pass `onBarClick={handleBarClick}` prop to LengthOfStayHistogram
  - [ ] 7.7 Add `<DogListModal>` component with props: `isOpen={!!selectedBin}`, `onClose={handleModalClose}`, `dogs={selectedBin?.dogs || []}`, `binRange={selectedBin?.range || ""}`
  - [ ] 7.8 Add section heading `<h3>` above the histogram component (e.g., "Length of Stay Analysis")
  - [ ] 7.9 Test the full integration: navigate to Insights tab, verify histogram renders, click a bar, verify modal opens with correct dogs, close modal
  - [ ] 7.10 Verify histogram data updates when new scraping occurs (test by running main.py and checking for updated data)

- [ ] 8.0 Write Backend Automated Tests
  - [ ] 8.1 Create new file `tests/test_length_of_stay.py`
  - [ ] 8.2 Write unit test for Sturges binning algorithm with small synthetic dataset (e.g., 10 dogs with known LOS values)
  - [ ] 8.3 Write test for edge case: empty dataset (0 dogs) - should return empty bins array
  - [ ] 8.4 Write test for edge case: single dog - should return single bin
  - [ ] 8.5 Write test for edge case: all dogs with same length of stay - should return single bin with all dogs
  - [ ] 8.6 Write test for mixed valid/invalid LOS values - should exclude null/missing and only bin valid values
  - [ ] 8.7 Write test for bin boundary inclusivity (values at exact bin edges fall into correct bins)
  - [ ] 8.8 Write test to verify dogs-per-bin lists contain only minimal fields (id, name, breed, age, length_of_stay_days)
  - [ ] 8.9 Write integration test for GET `/api/length-of-stay` endpoint - should return APIResponse with expected payload shape
  - [ ] 8.10 Write integration test for error path - should return 500 with APIResponse error format
  - [ ] 8.11 Run all tests with `pytest tests/test_length_of_stay.py` and verify they pass

- [ ] 9.0 Deployment and Configuration Verification
  - [ ] 9.1 Verify CORS configuration in `api/main.py` allows frontend to access `/api/length-of-stay` endpoint
  - [ ] 9.2 If reverse proxy is used, add `/api/length-of-stay` to allowed paths
  - [ ] 9.3 Add smoke test to CI or manual checklist: `curl http://localhost:8000/api/length-of-stay` should return valid JSON
  - [ ] 9.4 Test in local development environment end-to-end before deployment

- [ ] 10.0 Documentation and PRD Closure
  - [ ] 10.1 Update README or API documentation with new `/api/length-of-stay` endpoint schema and sample response
  - [ ] 10.2 Document the Pydantic models (LOSDogSummary, LOSBin, LOSHistogramData) in API docs
  - [ ] 10.3 Add note in PRD or changelog documenting resolved open questions: "Bin calculation on backend (Sturges)" and "Modal over inline expansion"
  - [ ] 10.4 Add comment in code explaining Sturges formula choice for v1 with note on when to revisit (e.g., for large datasets)
  - [ ] 10.5 Update component documentation for LengthOfStayHistogram and DogListModal with props and usage examples

## Testing & Verification

After completing all tasks:
- [ ] Test backend endpoint directly: `curl http://localhost:8000/api/length-of-stay` should return valid JSON with bins
- [ ] Test frontend integration: Navigate to Insights tab and verify histogram displays
- [ ] Test interactivity: Hover over bars (tooltip appears), click bars (modal opens with dog list), close modal
- [ ] Test edge cases: Empty shelter, all dogs with same length of stay, null/missing LOS values
- [ ] Verify styling matches existing charts in InsightsTab
- [ ] Test keyboard accessibility: Tab navigation through modal, Escape to close, focus trap
- [ ] Check browser console for any errors or warnings
- [ ] Verify data updates when new scraping occurs (run main.py and refresh)
