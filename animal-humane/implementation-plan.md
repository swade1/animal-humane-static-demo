# Implementation Plan for Length of Stay Histogram

## Backend Changes

### 1. Update ElasticsearchHandler
Add a method to get length_of_stay_days data for both adopted and currently sheltered dogs.

```python
def get_length_of_stay_distribution(self):
    """
    Get distribution of length_of_stay_days for both adopted and currently sheltered dogs.
    Returns a dictionary with two keys: 'adopted' and 'currently_sheltered', each containing
    a list of objects with 'range' and 'count' properties.
    """
    # Define the ranges for the histogram bins
    ranges = [
        {"from": 0, "to": 7},
        {"from": 8, "to": 14},
        {"from": 15, "to": 30},
        {"from": 31, "to": 60},
        {"from": 61, "to": 90},
        {"from": 91, "to": None}  # No upper limit
    ]

    # Initialize the result structure
    result = {
        "adopted": [],
        "currently_sheltered": []
    }

    # Helper function to calculate the range index for a given length_of_stay_days
    def get_range_index(los):
        for i, r in enumerate(ranges):
            if (r["from"] <= los < r["to"]) or (r["to"] is None and los >= r["from"]):
                return i
        return len(ranges) - 1

    # Process adopted dogs
    query = {
        "query": {
            "term": {"status.keyword": "adopted"}
        },
        "_source": ["length_of_stay_days"]
    }

    response = self.es.search(index="animal-humane-*", body=query)

    # Initialize range counts
    adopted_counts = [0] * len(ranges)

    for hit in response["hits"]["hits"]:
        source = hit.get("_source", {})
        los = source.get("length_of_stay_days")
        if los is not None:
            index = get_range_index(los)
            adopted_counts[index] += 1

    # Populate the result for adopted dogs
    for i, count in enumerate(adopted_counts):
        result["adopted"].append({
            "range": f"{ranges[i]['from']}-{ranges[i]['to'] or '∞'}",
            "count": count
        })

    # Process currently sheltered dogs
    query = {
        "query": {
            "term": {"status.keyword": "Available"}
        },
        "_source": ["length_of_stay_days"]
    }

    response = self.es.search(index="animal-humane-*", body=query)

    # Initialize range counts
    current_counts = [0] * len(ranges)

    for hit in response["hits"]["hits"]:
        source = hit.get("_source", {})
        los = source.get("length_of_stay_days")
        if los is not None:
            index = get_range_index(los)
            current_counts[index] += 1

    # Populate the result for currently sheltered dogs
    for i, count in enumerate(current_counts):
        result["currently_sheltered"].append({
            "range": f"{ranges[i]['from']}-{ranges[i]['to'] or '∞'}",
            "count": count
        })

    return result
```

### 2. Update ElasticsearchService
Add a method to get length_of_stay_days data.

```python
async def get_length_of_stay_distribution(self):
    """Get length_of_stay_days distribution for both adopted and currently sheltered dogs"""
    return await self._run_in_executor(self.handler.get_length_of_stay_distribution)
```

### 3. Update DogService
Add a method to get length_of_stay_days data.

```python
async def get_length_of_stay_distribution(self):
    """Get length_of_stay_days distribution for both adopted and currently sheltered dogs"""
    try:
        return await self.es_service.get_length_of_stay_distribution()
    except Exception as e:
        logger.error(f"Error getting length_of_stay_distribution: {e}")
        raise
```

### 4. Update API (main.py)
Add a new endpoint to get length_of_stay_days data.

```python
@app.get("/api/length-of-stay-distribution", response_model=APIResponse)
async def get_length_of_stay_distribution(dog_service: DogService = Depends(get_dog_service)):
    """Get length_of_stay_days distribution for both adopted and currently sheltered dogs"""
    try:
        data = await dog_service.get_length_of_stay_distribution()
        return APIResponse.success_response(data)
    except Exception as e:
        logger.error(f"Error getting length_of_stay_distribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

## Frontend Changes

### 1. Create HistogramChart Component
Create a new component for the histogram chart.

```jsx
// src/LengthOfStayHistogram.js
import React from 'react';
import { BarChart, Bar, Legend, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const LengthOfStayHistogram = ({ data }) => {
  return (
    <div>
      <h3>Length of Stay Distribution</h3>
      <ResponsiveContainer width="100%" height={400}>
        <BarChart
          data={data}
          margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="range" interval={0} />
          <YAxis allowDecimals={false} label={{ value: "Number of Dogs", angle: -90, position: "insideLeft" }} />
          <Tooltip />
          <Legend />
          <Bar dataKey="adopted" fill="#8884d8" name="Adopted Dogs" />
          <Bar dataKey="currently_sheltered" fill="#82ca9d" name="Currently Sheltered Dogs" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default LengthOfStayHistogram;
```

### 2. Update InsightsTab Component
Add the new histogram visualization to the Insights tab.

```jsx
// src/InsightsTab.js
import React, { useEffect, useState } from 'react';
import { fetchInsights, fetchLengthOfStayDistribution } from './api';
import LengthOfStayHistogram from './LengthOfStayHistogram';
// ... other imports

function InsightsTab() {
  const [insights, setInsights] = useState(null);
  const [lengthOfStayData, setLengthOfStayData] = useState([]);

  useEffect(() => {
    // Fetch insights data
    fetchInsights().then(setInsights).catch(err => {
      console.error("Error loading insights:", err);
    });

    // Fetch length of stay distribution data
    fetchLengthOfStayDistribution()
      .then(data => {
        // Transform data for the histogram
        const transformedData = data.map(item => ({
          range: item.range,
          adopted: item.adopted,
          currently_sheltered: item.currently_sheltered
        }));
        setLengthOfStayData(transformedData);
      })
      .catch(err => {
        console.error("Error loading length of stay data:", err);
      });
  }, []);

  if (!insights) return <div>Loading...</div>;

  return (
    <div>
      {/* Other visualizations */}

      {/* Length of Stay Histogram */}
      <LengthOfStayHistogram data={lengthOfStayData} />

      {/* Other content */}
    </div>
  );
}

export default InsightsTab;
```

### 3. Update API Module
Add a new function to fetch length_of_stay_distribution data.

```jsx
// src/api.js
export async function fetchLengthOfStayDistribution() {
  const res = await fetch('/api/length-of-stay-distribution');
  if (!res.ok) {
    throw new Error('Failed to fetch length of stay distribution');
  }
  return res.json();
}
```

## Styling
Ensure the histogram chart is styled to match existing visualizations in the Insights tab. This includes:
1. Consistent font sizes and colors
2. Proper spacing and margins
3. Responsive design that works well on different screen sizes

## Testing
1. Test the new API endpoint to ensure it returns the correct data.
2. Test the frontend implementation to ensure the histogram displays correctly.
3. Verify that the visualization is responsive and works well on different screen sizes.