import React, { useEffect, useState } from 'react';
import { fetchInsights, fetchWeeklyAgeGroupAdoptions, fetchDogOrigins } from './api';
import { BarChart, Bar, Legend, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LabelList } from 'recharts';
import { getLast5Weeks } from './utils/dateUtils';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';
import LengthOfStayHistogram from './components/LengthOfStayHistogram';
import DogListModal from './components/DogListModal';

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconUrl: markerIcon,
    shadowUrl: markerShadow,
    iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png')
});

const chartLabels = getLast5Weeks();
// Adjusted to better center all New Mexico shelters including southwestern ones
const MAP_CENTER = [34.5, -106.5];
const MAP_ZOOM = 6;

/* -------------------- */
/*    Custom Tooltip    */
/* -------------------- */
const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
        const { count, names } = payload[0].payload;
        return (
            <div style={{ backgroundColor: 'white', border: '1px solid #ccc', padding: '10px' }}>
                <p><strong>Date:</strong> {label}</p>
                <p><strong>Adoptions:</strong> {count}</p>
                {names && names.length > 0 && (
                    <>
                        <p><strong>Dogs Adopted:</strong></p>
                        <ul style={{ margin: 0, paddingLeft: '20px' }}>
                            {names.map((name, i) => (
                                <li key={i}>{name}</li>
                            ))}
                        </ul>
                    </>
                )}
            </div>
        );
    }
    return null;
};
const CustomLegend = (props) => {
    const { payload } = props;
    const order = ["Puppies", "Adults", "Seniors"];
    // Sort payload by the order array
    const sortedPayload = order.map(name =>
        payload.find(item => item.value === name)
    ).filter(Boolean);
    return (
        <ul style={{ listStyle: 'none', display: 'flex', justifyContent: "center", alignItems: "center", padding: 0, margin: 0, width: "100%" }}>
            {sortedPayload.map((entry, index) => (
                <li key={`item-${index}`} style={{ marginRight: 10, display: 'flex', alignItems: 'center' }}>
                    <span style={{
                        display: 'inline-block',
                        width: 10,
                        height: 10,
                        backgroundColor: entry.color,
                        marginRight: 5,
                    }}></span>
                    {entry.value}
                </li>
            ))}
        </ul>
    );
};

/* ------------------------------- */
/*            Main Tab             */
/* ------------------------------- */
function WeeklyAdoptionsBarChart({ data }) {
    return (
        <div>
            <div className="overview-text" style={{ marginTop: "20px" }}>
                <strong>Weekly Adoption Totals per Age Group</strong>
            </div>
            <ResponsiveContainer width="100%" height={350}>
                <BarChart
                    labels={chartLabels}
                    data={data}
                    margin={{ top: 20, right: 30, left: 20, bottom: 30 }}
                    barCategoryGap="16%"
                >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="week" />
                    <YAxis allowDecimals={false} label={{ value: "Adopted Dogs", angle: -90, position: "insideLeft", offset: 0, dy: 50 }} />
                    <Tooltip />
                    <Legend content={CustomLegend} />
                    <Bar dataKey="Puppy" fill="#7DD181" name="Puppies" />
                    <Bar dataKey="Adult" fill="#4E79A7" name="Adults" />
                    <Bar dataKey="Senior" fill="#F28E2B" name="Seniors" />
                </BarChart>
            </ResponsiveContainer>
        </div>
    );
}

// ----------- NEW: Shelter Transfers BarChart -----------
function ShelterTransfersBarChart({ originData }) {
    // Group shelters by count, then sort alphabetically within each count group
    const groupedData = [...originData]
        .filter(item => typeof item.count === 'number' && item.count > 0 && item.origin)
        .reduce((groups, item) => {
            if (!groups[item.count]) {
                groups[item.count] = [];
            }
            groups[item.count].push(item);
            return groups;
        }, {});

    // Sort each group alphabetically by origin name, then flatten
    const sortedData = Object.keys(groupedData)
        .sort((a, b) => parseInt(a) - parseInt(b)) // Sort count groups from lowest to highest
        .flatMap(count => 
            groupedData[count].sort((a, b) => a.origin.localeCompare(b.origin))
        )
        .map(item => ({
            ...item,
            not_adopted: item.available || (item.count - item.adopted) // use available field if present, fallback to calculation
        }));

    return (
        <div style={{ marginTop: '60px' }}>
            <h3>Transfers and Adoptions per Shelter or Rescue</h3>
            <ResponsiveContainer width="100%" height={400}>
                <BarChart
                    data={sortedData}
                    margin={{ top: 50, right: 30, left: 20, bottom: 120 }}
                >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                        dataKey="origin"
                        angle={-45}
                        textAnchor="end"
                        interval={0}
                        tick={{ fontSize: 14 }}
                        height={100}
                    />
                    <YAxis allowDecimals={false} label={{ value: "Transferred Dogs", angle: -90, position: "insideLeft", offset: 0, dy: 50 }} />
                    <Tooltip />
                    {/* Orange (adopted) on bottom, purple (not adopted) on top */}
                    <Bar dataKey="adopted" fill="#009688" stackId="a" name="Adopted" />
                    <Bar dataKey="not_adopted" fill="#8884d8" stackId="a" name="Available">
                        <LabelList dataKey="count" position="top" />
                    </Bar>
                </BarChart>
            </ResponsiveContainer>
        </div>
    );
}

// ------------------------------------------------------
function InsightsTab() {
    const [origins, setOrigins] = useState([]);
    const [insights, setInsights] = useState(null);
    const lengthOfStayData = insights && insights.lengthOfStayData ? insights.lengthOfStayData : [];
    const [weeklyAgeGroupData, setWeeklyAgeGroupData] = useState([]);
    const [selectedBin, setSelectedBin] = useState(null);

    useEffect(() => {
        console.log("InsightsTab useEffect triggered");
        //fetchInsights().then(setInsights).catch(err => {
        fetchInsights().then(response => {
            // Extract data from APIResponse wrapper
            setInsights(response.data || response);
        }).catch(err => {
                      console.error("Error loading insights:", err);
        });
        fetchWeeklyAgeGroupAdoptions()
        //    .then(data => setWeeklyAgeGroupData(Array.isArray(data) ? data : []))
         .then(response => {
                const data = response.data || response;
                setWeeklyAgeGroupData(Array.isArray(data) ? data : []);
            })     
            .catch(err => {
                console.error("Error loading weekly age group data:", err);
                setWeeklyAgeGroupData([]);
            });
        fetchDogOrigins()
            .then(response => {
                const data = response.data || response;

                console.log('Raw dog origins data:', data);
                const validOrigins = Array.isArray(data) ? data : [];

                // Debug: Check for Bayard specifically
                const bayardData = validOrigins.find(origin => origin.origin && origin.origin.includes('Bayard'));
                if (bayardData) {
                    console.log('Bayard Animal Control data:', bayardData);
                } else {
                    console.log('Bayard Animal Control NOT FOUND in origins data');
                }

                // Debug: Check for origins missing coordinates
                const missingCoords = validOrigins.filter(origin => !origin.latitude || !origin.longitude);
                if (missingCoords.length > 0) {
                    console.log('Origins missing coordinates:', missingCoords);
                }

                // Debug: Count how many markers will be rendered
                const validMarkers = validOrigins.filter(origin => origin.latitude && origin.longitude);
                console.log(`Total origins: ${validOrigins.length}, Valid markers: ${validMarkers.length}`);

                // Debug: List all valid markers
                console.log('Valid markers:', validMarkers.map(o => o.origin));

                setOrigins(validOrigins);
            })
            .catch((error) => {
                console.error('Error fetching dog origins:', error);
                setOrigins([]);
            })
    }, []);

    const handleBarClick = (binData) => {
        setSelectedBin(binData);
    };

    const handleModalClose = () => {
        setSelectedBin(null);
    };

    if (!insights || !insights.dailyAdoptions || !Array.isArray(insights.dailyAdoptions)) {
        return <div>Loading...</div>;
    }

    const maxCount = Math.max(...insights.dailyAdoptions.map(d => d.count));
    const maxIndex = insights.dailyAdoptions.findIndex(d => d.count === maxCount);

    const CustomDot = (props) => {
        const { cx, cy, index } = props;
        if (index === maxIndex) {
            return (
                <circle cx={cx} cy={cy} r={6} fill="#FF4136" stroke="#fff" strokeWidth={2} />
            );
        }
        return (
            <circle cx={cx} cy={cy} r={4} fill="#8884d8" />
        );
    };

    return (
        <div>
            {/* Adoption Trends */}
            <h3 style={{ marginTop: '30px', textAlign: 'center' }}>Adoption Trends</h3>
            <div className="overview-text">
                <strong>Daily Adoption Totals</strong>
            </div>

            <ResponsiveContainer width="100%" height={300}>
                <LineChart
                    data={insights.dailyAdoptions}
                    margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
                >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                        dataKey="date"
                        angle={-45}
                        textAnchor="end"
                        height={60}
                        interval={3}
                        tick={{ fontSize: 12 }}
                    />
                    <YAxis allowDecimals={false} />
                    <Tooltip content={<CustomTooltip />} />
                    <Line
                        type="monotone"
                        dataKey="count"
                        stroke="#8884d8"
                        strokeWidth={2}
                        dot={CustomDot}
                        activeDot={{ r: 8, stroke: "#FF4136", strokeWidth: 2, fill: '#FF4136' }}
                    >
                        <LabelList
                            dataKey="count"
                            position="top"
                            formatter={(value, entry) =>
                                entry && entry.index === maxIndex ? `${value} (max)` : ''
                            }
                            style={{ fill: '#FF4136', fontWeight: 'bold' }}
                        />
                    </Line>
                </LineChart>
            </ResponsiveContainer>

            {/* Weekly Adoptions Bar Chart */}
            <div className="overview-text">
                <WeeklyAdoptionsBarChart data={weeklyAgeGroupData} />
            </div>

            {/* Map showing Dog Origins */}
            <h3 style={{ marginTop: "30px", textAlign: 'center' }}>Origination of Dogs at Animal Humane</h3>
            <h2 style={{ marginTop: "40px" }}>Shelters and Rescues Transferring Dogs to Animal Humane</h2>
            <div style={{ textAlign: 'left', marginBottom: '20px', padding: '10px', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
                <p style={{ margin: '0', color: '#495057', fontSize: '14px' }}>
                    <strong>{origins.length} shelters and rescues</strong> throughout New Mexico have partnered with Animal Humane to find homes for their dogs
                </p>
                <p style={{ margin: '5px 0 0 0', color: '#6c757d', fontSize: '13px' }}>
                    Each pin represents a shelter that has transferred at least one dog to our care
                </p>
                <p style={{ margin: '3px 0 0 0', color: '#6c757d', fontSize: '12px' }}>
                    Click on each pin to view shelter/rescue name and the number of dogs transferred from that location
                </p>
            </div>
            <MapContainer center={MAP_CENTER} zoom={MAP_ZOOM} style={{ height: '800px', width: '100%' }}>
                <TileLayer
                    url='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
                    attribution='&copy; OpenStreetMap contributors'
                />
                {origins.map(({ latitude, longitude, origin, count }, idx) => {
                    // Debug logging for Bayard specifically
                    if (origin && origin.includes('Bayard')) {
                        console.log(`Bayard marker check - lat: ${latitude}, lon: ${longitude}, origin: ${origin}, count: ${count}`);
                        console.log(`Bayard marker will render: ${!!(latitude && longitude)}`);
                        console.log(`Bayard position array: [${latitude}, ${longitude}]`);
                    }

                    if (latitude && longitude) {
                        // Additional debug for Bayard
                        if (origin && origin.includes('Bayard')) {
                            console.log(`Creating Bayard marker at position [${latitude}, ${longitude}]`);
                        }

                        return (
                            <Marker key={idx} position={[latitude, longitude]}>
                                <Popup>
                                    <strong>{origin}</strong><br />
                                    Dogs: {count}
                                </Popup>
                            </Marker>
                        );
                    } else {
                        // Debug: Log markers that are being filtered out
                        console.log(`Marker filtered out - origin: ${origin}, lat: ${latitude}, lon: ${longitude}`);
                        return null;
                    }
                })}
            </MapContainer>

            {/* ----------- NEW: Shelter Transfers Bar Chart Below the Map ----------- */}
            <ShelterTransfersBarChart originData={origins} />

            {/* ----------- Length of Stay Histogram ----------- */}
            <LengthOfStayHistogram onBarClick={handleBarClick} />

            {/* Dog List Modal */}
            <DogListModal
                isOpen={!!selectedBin}
                onClose={handleModalClose}
                dogs={selectedBin?.dogs || []}
                binRange={selectedBin?.range || ""}
            />
        </div>
    );
}

export default InsightsTab;

