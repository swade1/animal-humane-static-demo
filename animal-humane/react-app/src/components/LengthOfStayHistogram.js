import React, { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { fetchLengthOfStayData } from '../api';

const LengthOfStayHistogram = ({ onBarClick, refreshTrigger }) => {
    const [histogramData, setHistogramData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [dataLoaded, setDataLoaded] = useState(false);

    // Load data from sessionStorage on mount
    useEffect(() => {
        const storedData = sessionStorage.getItem('lengthOfStayData');
        const storedTimestamp = sessionStorage.getItem('lengthOfStayTimestamp');
        
        if (storedData && storedTimestamp) {
            const age = Date.now() - parseInt(storedTimestamp);
            // Use cached data if it's less than 5 minutes old
            if (age < 5 * 60 * 1000) {
                try {
                    const parsedData = JSON.parse(storedData);
                    setHistogramData(parsedData);
                    setDataLoaded(true);
                    setLoading(false);
                    return;
                } catch (e) {
                    // Invalid cached data, continue with fresh load
                }
            }
        }
    }, []);

    useEffect(() => {
        const loadData = async () => {
            // Only load data if it hasn't been loaded yet or if refresh is triggered
            if (dataLoaded && !refreshTrigger) {
                return;
            }
            
            try {
                setLoading(true);
                setError(null);
                const response = await fetchLengthOfStayData();

                // Transform API response to Recharts format
                if (response.data && response.data.bins) {
                    const chartData = response.data.bins.map(bin => {
                        // Display ranges directly from bin min-max
                        const rangeLabel = `${bin.min}-${bin.max} days`;
                        
                        return {
                            range: rangeLabel,
                            count: bin.count,
                            min: bin.min,
                            max: bin.max,
                            dogs: bin.dogs
                        };
                    });

                    // Sort bins by min value ascending
                    chartData.sort((a, b) => a.min - b.min);
                    setHistogramData(chartData);
                    
                    // Cache the data in sessionStorage
                    sessionStorage.setItem('lengthOfStayData', JSON.stringify(chartData));
                    sessionStorage.setItem('lengthOfStayTimestamp', Date.now().toString());
                    
                    setDataLoaded(true);
                } else {
                    setHistogramData([]);
                    setDataLoaded(true);
                }
            } catch (err) {
                console.error('Error loading length of stay data:', err);
                setError('Failed to load data');
                setDataLoaded(false); // Allow retry on error
            } finally {
                setLoading(false);
            }
        };

        loadData();
    }, [dataLoaded, refreshTrigger]);

    const CustomTooltip = ({ active, payload, label }) => {
        if (active && payload && payload.length) {
            const data = payload[0].payload; // Get the full data object
            const count = payload[0].value;
            
            // Show dog names for all bins since we're only showing available dogs
            const showDogNames = true;
            
            return (
                <div style={{ backgroundColor: 'white', border: '1px solid #ccc', padding: '10px', maxWidth: '300px' }}>
                    <p><strong>Dogs:</strong> {count}</p>
                    <p><strong>Range:</strong> {label}</p>
                    {showDogNames && data.dogs && data.dogs.length > 0 && (
                        <div>
                            <p><strong>Dog Names:</strong></p>
                            <div style={{ maxHeight: '150px', overflowY: 'auto' }}>
                                {data.dogs.map((dog, index) => (
                                    <div key={index} style={{ fontSize: '12px', marginBottom: '2px' }}>
                                        • {dog.name} ({dog.length_of_stay_days} days)
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
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

    const refreshData = () => {
        setDataLoaded(false);
    };

    if (loading && !dataLoaded) {
        return <div>Loading...</div>;
    }

    if (error) {
        return (
            <div>
                <div style={{ color: 'red', marginBottom: '10px' }}>Failed to load data</div>
                <button onClick={refreshData} style={{ display: 'none', padding: '5px 10px', cursor: 'pointer' }}>
                    Retry
                </button>
            </div>
        );
    }

    if (histogramData.length === 0) {
        return <div>No data available</div>;
    }

    return (
        <div>
            <div style={{ marginTop: '30px', marginBottom: '10px' }}>
                <h3 style={{ margin: 0 }}>Length of Stay Distribution - Available Dogs</h3>
                <p style={{ margin: '5px 0 0 0', fontSize: '14px', color: '#666' }}>
                    Click on each bar to see detailed information about each dog.
                </p>
            </div>
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
