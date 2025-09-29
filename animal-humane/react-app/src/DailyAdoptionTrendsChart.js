import React, { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

function DailyAdoptionTrendsChart() {
  const [data, setData] = useState([]);

  useEffect(() => {
    async function fetchDailyAdoptions() {
      try {
        // Example API endpoint for your daily adoptions data
        const response = await fetch("/api/daily_adoptions");
        const result = await response.json();

        // Assume result is like:
        // [
        //   { date: "08/01/2025", count: 3 },
        //   { date: "08/02/2025", count: 5 },
        //   ...
        // ]

        // Optionally sort by date, if not sorted
        const sortedData = result.sort((a, b) =>
          new Date(a.date) - new Date(b.date)
        );

        setData(sortedData);
      } catch (error) {
        console.error("Error fetching daily adoptions data:", error);
      }
    }

    fetchDailyAdoptions();
  }, []);

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart
        data={data}
        margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis
          dataKey="date"
          tick={{ fontSize: 12 }}
          angle={-45}
          textAnchor="end"
          height={60}
          interval={3} // show every 3rd tick to avoid overcrowding
        />
        <YAxis allowDecimals={false} />
        <Tooltip />
        <Line
          type="monotone"
          dataKey="count"
          stroke="#8884d8"
          strokeWidth={2}
          dot={{ r: 4 }}
          activeDot={{ r: 6 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

export default DailyAdoptionTrendsChart;

