import React, { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { fetchLengthOfStayData } from '../api';

const LengthOfStayHistogram = ({ onBarClick }) => {
    const [histogramData, setHistogramData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const loadData = async () => {
            try {
                setLoading(true);
                setError(null);
                const response = await fetchLengthOfStayData();

                // Transform API response to Recharts format
                if (response.data && response.data.bins) {
                    const chartData = response.data.bins.map(bin => ({
                        range: `${bin.min}–${bin.max} days`,
                        count: bin.count,
                        min: bin.min,
                        max: bin.max,
                        dogs: bin.dogs
                    }));

                    // Sort bins by min value ascending
                    chartData.sort((a, b) => a.min - b.min);
                    setHistogramData(chartData);
                } else {
                    setHistogramData([]);
                }
            } catch (err) {
                console.error('Error loading length of stay data:', err);
                setError('Failed to load data');
            } finally {
                setLoading(false);
            }
        };

        loadData();
    }, []);

    const CustomTooltip = ({ active, payload }) => {
        if (active && payload && payload.length) {
            const count = payload[0].value;
            return (
                <div style={{ backgroundColor: 'white', border: '1px solid #ccc', padding: '10px' }}>
                    <p><strong>Dogs:</strong> {count}</p>
                </div>
            );
        }
        return null;
    };

    const handleClick = (data) => {
        if (data && onBarClick) {
            onBarClick({
                range: data.range,
                dogs: data.dogs,
                count: data.count
            });
        }
    };

    if (loading) {
        return <div>Loading...</div>;
    }

    if (error) {
        return <div style={{ color: 'red' }}>Failed to load data</div>;
    }

    if (histogramData.length === 0) {
        return <div>No data available</div>;
    }

    return (
        <div>
            <h3 style={{ textAlign: 'center', marginTop: '30px' }}>Length of Stay Distribution - All Dogs</h3>
            <ResponsiveContainer width="100%" height={350}>
                <BarChart
                    data={histogramData}
                    margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
                >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                        dataKey="range"
                        angle={-45}
                        textAnchor="end"
                        height={80}
                        interval={0}
                        tick={{ fontSize: 12 }}
                    />
                    <YAxis
                        allowDecimals={false}
                        label={{ value: "Number of Dogs", angle: -90, position: "insideLeft", offset: 0, dy: 50 }}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar
                        dataKey="count"
                        fill="#4E79A7"
                        onClick={handleClick}
                        cursor="pointer"
                    />
                </BarChart>
            </ResponsiveContainer>
        </div>
    );
};

export default LengthOfStayHistogram;
