# Product Requirements Document: Length of Stay Histogram Visualization

## Introduction/Overview

The Animal Humane shelter dog tracking project currently provides adoption trends, weekly age group breakdowns, and shelter transfer data. However, it lacks visibility into how long individual dogs remain in the shelter before being adopted. This feature introduces a histogram visualization displaying the distribution of `length_of_stay_days` for all dogs, both currently available and previously adopted.

**Problem:** Shelter staff, administrators, and the public cannot easily identify which dogs have been waiting the longest for adoption, making it difficult to prioritize promotional efforts or understand shelter capacity trends.

**Goal:** Provide a clear, interactive histogram that shows the distribution of how long dogs have been in the shelter, enabling data-driven decisions about which animals need additional attention.

## Goals

1. **Visualize length of stay distribution** for all dogs, including both currently available and adopted dogs
2. **Enable identification of long-stay dogs** that may need priority promotion or special attention
3. **Integrate seamlessly** into the existing React-based InsightsTab component
4. **Provide actionable insights** through interactive elements that allow users to drill down into specific stay-duration ranges
5. **Automatically update** when new data is scraped from the shelter website

## User Stories

1. **As a shelter administrator**, I want to see a histogram of how long dogs have been at the shelter so that I can identify which animals have been waiting the longest and prioritize them for promotional campaigns.

2. **As a shelter staff member**, I want to click on a histogram bar to see the list of specific dogs in that length-of-stay range so that I can take action on individual cases.

3. **As a data analyst**, I want the histogram bins to be automatically calculated based on the data distribution so that the visualization adapts to varying datasets over time.

4. **As a member of the public**, I want to understand overall shelter trends so that I'm aware of how quickly dogs typically get adopted.

5. **As a shelter manager**, I want the histogram to refresh automatically when new data is available so that I always have up-to-date information without manual intervention.

## Functional Requirements

1. The system **must** display a histogram showing the distribution of `length_of_stay_days` for all dogs, including both currently available and adopted dogs.

2. The system **must** query the latest Elasticsearch index (or use the `animal-humane-latest` alias) to retrieve `length_of_stay_days` data.

3. The system **must** dynamically calculate histogram bin sizes based on the distribution of the data (e.g., using statistical methods like Sturges' rule or Freedman-Diaconis rule).

4. The system **must** display bin labels on the X-axis (e.g., "0-10 days", "11-20 days") and counts on the Y-axis.

5. The system **must** allow users to click on individual histogram bars to view a list of dogs whose length of stay falls within that bin range.

6. The dog list displayed on click **must** include at minimum: dog name, breed, age, and exact length of stay in days.

7. The system **must** integrate this visualization into the existing `InsightsTab.js` component in the React app.

8. The system **must** use the existing charting library (Recharts, already used in the project) for consistency.

9. The system **must** include hover tooltips showing the exact count of dogs in each bin.

10. The system **must** refresh the histogram data automatically when new scraping occurs (triggered by updates to the Elasticsearch index).

11. The system **must** handle edge cases such as:
    - Zero dogs in the shelter (display "No data available" message)
    - All dogs having the same length of stay (single bar histogram)
    - Missing or invalid `length_of_stay_days` values (exclude from histogram)

12. The system **must** provide a title and brief description above the histogram (e.g., "Length of Stay Distribution - All Dogs").

## Non-Goals (Out of Scope)

1. **Historical comparisons** - This feature will not compare length of stay across different time periods or show trends over months/years.

2. **Filtering by dog attributes** - Initial version will not include filters for breed, size, age, or other dog characteristics.

3. **Custom bin configuration** - Users will not be able to manually adjust histogram bin sizes in the initial release.

4. **Export functionality** - The feature will not include CSV/PDF export of the histogram or underlying data.

5. **Alerts/notifications** - The system will not send automated alerts when dogs exceed certain stay durations.

6. **Separate visualizations by status** - The initial version will not provide separate histograms for available vs. adopted dogs; all dogs will be shown in a single combined histogram.

## Design Considerations

### UI/UX Requirements

- **Location:** Add the histogram as a new section within the existing `InsightsTab.js` component, positioned below the "Shelter Transfers Bar Chart" section.

- **Styling:** Match the existing chart styling in InsightsTab (consistent use of Recharts components, color palette, margins, and responsive containers).

- **Chart Type:** Vertical bar chart (histogram) with:
  - X-axis: Length of stay ranges (bins)
  - Y-axis: Number of dogs
  - Bars: Solid color (suggest using project's existing color scheme, e.g., `#4E79A7` from the adoption charts)

- **Interactive Elements:**
  - Hover tooltips showing exact counts
  - Clickable bars that open a modal or expandable section showing the list of dogs in that range
  
- **Dog List Modal/Section:** When a bar is clicked, display:
  - Modal or collapsible panel
  - Table or list showing: Name, Breed, Age, Length of Stay (days)
  - Close/dismiss button

### Component Structure

```
InsightsTab.js
  ├── LengthOfStayHistogram (new component)
  │     ├── ResponsiveContainer (Recharts)
  │     ├── BarChart (Recharts)
  │     └── DogListModal (new sub-component for click interaction)
  └── [existing charts and components]
```

## Technical Considerations

1. **Data Source:** Query Elasticsearch using the existing `fetchInsights` pattern or create a new API endpoint `fetchLengthOfStayData()` in `api.js`.

2. **Backend API:** May require a new Flask API endpoint (e.g., `/api/length-of-stay`) that:
   - Queries the latest Elasticsearch index
   - Calculates histogram bins (can be done on backend or frontend)
   - Returns JSON with bin ranges and counts

3. **Bin Calculation:** Use a standard algorithm for dynamic binning:
   - Freedman-Diaconis rule: bin width = 2 × IQR × n^(-1/3)
   - Or Sturges' formula: number of bins = ceil(log2(n) + 1)
   - Can leverage JavaScript libraries like `d3-array` if needed

4. **State Management:** Use React `useState` and `useEffect` hooks consistent with the existing `InsightsTab` implementation.

5. **Dependencies:**
   - Already using Recharts (BarChart, XAxis, YAxis, Tooltip, etc.)
   - May need modal library (e.g., react-modal) or create a custom modal component

6. **Data Refresh:** Leverage the existing `useEffect` pattern that runs on component mount. If real-time updates are needed, consider polling or WebSocket integration (future enhancement).

7. **Error Handling:** Handle Elasticsearch query failures gracefully with error messages to the user.

## Success Metrics

1. **Primary Metric:** Shelter staff identify and prioritize at least 5 long-stay dogs within the first week of deployment.

2. **Engagement:** 70% of weekly active users interact with the histogram (hover or click) within the first month.

3. **Data Accuracy:** 100% of all dogs (available and adopted) with valid `length_of_stay_days` data are represented in the histogram.

4. **Performance:** Histogram loads within 2 seconds of navigating to the Insights tab.

5. **User Satisfaction:** Positive feedback from at least 3 shelter staff members in user testing regarding the usefulness of the feature.

## Open Questions

1. **Bin calculation location:** Should dynamic bin calculation happen on the backend (Python) or frontend (JavaScript)? Recommendation: Backend for consistency and to reduce frontend complexity.

2. **Modal vs. Inline Expansion:** When a user clicks a histogram bar, should the dog list appear in a modal popup or expand inline below the chart? Recommendation: Modal for better focus and mobile responsiveness.

3. **Empty bins:** Should the histogram show bins with zero dogs, or only bins that have at least one dog? Recommendation: Show all bins for better understanding of distribution.

4. **Color coding:** Should bars be color-coded by stay duration (e.g., green for short stays, red for long stays) or uniform? Recommendation: Consider gradient from green to red for immediate visual feedback.

5. **Integration with existing filters:** If/when filtering by breed or size is added in the future, should this histogram also update based on those filters? Note for future consideration.
