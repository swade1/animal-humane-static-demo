import React, { useState } from 'react';
import OverviewTab from './OverviewTab';
import LivePopulationTab from './LivePopulationTab';
import AdoptionsTab from './AdoptionsTab';
import InsightsTab from './InsightsTab';
import RoadmapTab from './RoadmapTab';
import { Tabs, Tab, Box } from '@mui/material';

const tabList = [
  { label: 'Overview', component: <OverviewTab /> },
  { label: 'Current Population', component: <LivePopulationTab /> },
  { label: 'Adoptions', component: <AdoptionsTab /> },
  { label: 'Insights & Spotlight', component: <InsightsTab /> },
  { label: 'Technical Roadmap & AI', component: <RoadmapTab /> },
];

function Dashboard() {
  const [activeTab, setActiveTab] = useState(0);

  return (
    <Box sx={{ width: '100%', typography: 'body1', p: 2 }}>
      <Tabs 
        value={activeTab}
        onChange={(e, newTab) => setActiveTab(newTab)}
        indicatorColor="primary"
        textColor="primary"
        variant="scrollable"
        scrollButtons="auto"
      >
        {tabList.map((tab, idx) => (
          <Tab label={tab.label} key={tab.label} />
        ))}
      </Tabs>
      <Box sx={{ mt: 3 }}>
        {tabList[activeTab].component}
      </Box>
    </Box>
  );
}

export default Dashboard;

