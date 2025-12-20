# 0001-PRD-Length-of-Stay-Histogram

## Introduction/Overview
This PRD outlines the requirements for adding a histogram visualization to the Insights tab of the Animal Humane application. The histogram will display the distribution of length_of_stay_days for dogs that have been adopted and dogs that are still at the shelter.

## Goals
1. Provide a visual representation of the length_of_stay_days distribution for both adopted and currently sheltered dogs.
2. Help shelter staff understand patterns in dog adoption and length of stay.
3. Enhance the Insights tab with additional data visualization.

## User Stories
1. As a shelter manager, I want to see the distribution of days dogs spend at the shelter before adoption so that I can identify trends and optimize care.
2. As a data analyst, I want to compare the length of stay between adopted dogs and those still at the shelter so that I can identify potential issues in the adoption process.

## Functional Requirements
1. The histogram must display two data series:
   - Dogs that have been adopted (filtered by status="adopted")
   - Dogs currently at the shelter (filtered by status="Available")
2. The x-axis should represent length_of_stay_days in ranges (e.g., 0-7 days, 8-14 days, etc.)
3. The y-axis should represent the count of dogs in each range.
4. The histogram must be styled to match existing visualizations in the Insights tab.
5. The visualization should be responsive and work well on different screen sizes.

## Non-Goals (Out of Scope)
1. This feature will not include any interactive filtering or drill-down capabilities.
2. This feature will not modify any existing data or business logic.

## Design Considerations
1. The histogram should use the Recharts library, consistent with other charts in the application.
2. Include a legend to differentiate between adopted dogs and currently sheltered dogs.

## Technical Considerations
1. The data for this visualization will come from the Elasticsearch service.
2. The API should expose a new endpoint to get length_of_stay_days data for both adopted and currently sheltered dogs.

## Success Metrics
1. The histogram should accurately display the distribution of length_of_stay_days for both groups.
2. The visualization should be easy to understand and interpret.

## Open Questions
1. Are there any specific length_of_stay_days ranges that should be used for the histogram bins?
2. Should the histogram include any additional data points or annotations?