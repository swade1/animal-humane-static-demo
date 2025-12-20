import React, { useState } from 'react';
import OverviewTab from './OverviewTab';
import LivePopulationTab from './LivePopulationTab';
import AdoptionsTab from './AdoptionsTab';
import InsightsTab from './InsightsTab';
import DiffAnalysisTab from './DiffAnalysisTab';

const tabs = [
  { label: 'Overview', Component: OverviewTab },
  { label: 'Recent Pupdates', Component: DiffAnalysisTab },
  { label: 'Current Population', Component: LivePopulationTab },
  { label: 'Adoptions', Component: AdoptionsTab },
  { label: 'Insights & Spotlight', Component: InsightsTab },
];

export default function Tabs() {
  const [activeIndex, setActiveIndex] = useState(0);
  const ActiveComponent = tabs[activeIndex].Component;

  return (
    <div style={{ padding: 20 }}>
      {/* Tab buttons */}
      <div style={{ marginBottom: 12 }}>
        {tabs.map((tab, index) => (
          <button
            key={tab.label}
            onClick={() => setActiveIndex(index)}
            style={{
              padding: '8px 16px',
              marginRight: 8,
              cursor: 'pointer',
              backgroundColor: activeIndex === index ? '#007bff' : '#f0f0f0',
              color: activeIndex === index ? 'white' : 'black',
              border: 'none',
              borderRadius: 4,
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Render the active tab component */}
      <div
        style={{
          border: '1px solid #ccc',
          padding: 16,
          borderRadius: 4,
          backgroundColor: '#fafafa',
        }}
      >
        <ActiveComponent />
      </div>
    </div>
  );
}

