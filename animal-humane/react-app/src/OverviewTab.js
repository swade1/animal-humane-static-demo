import React, { useEffect, useState } from 'react';
import Modal from 'react-modal';
import { fetchOverviewStats, clearCache, getApiMode } from './api';

function OverviewTab() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  // Add modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalUrl, setModalUrl] = useState('');

  useEffect(() => {
    const loadStats = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await fetchOverviewStats();
        // Extract data from APIResponse wrapper
        setStats(response.data || response);
      } catch (err) {
        setError(err.message);
        console.error('Failed to load overview stats:', err);
      } finally {
        setLoading(false);
      }
    };

    loadStats();
  }, []);

  // Add modal handlers
  const openModal = (url) => {
    setModalUrl(url);
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setModalUrl('');
  };

  const handleRefresh = async () => {
    const apiMode = getApiMode();
    if (apiMode.isStatic) {
      alert('🎯 Demo Mode: Data refresh is not available in this static portfolio demonstration.\n\nThis demo uses static data from January 1, 2026. In the live version, this button would refresh data from the live API.');
      return;
    }
    
    try {
      setRefreshing(true);
      setError(null);
      // Clear cache first
      await clearCache();
      // Then reload data
      const response = await fetchOverviewStats();
      setStats(response.data || response);
    } catch (err) {
      setError(err.message);
      console.error('Failed to refresh overview stats:', err);
    } finally {
      setRefreshing(false);
    }
  };

  if (loading) return <div>Loading overview statistics...</div>;
  
  if (error) {
    return (
      <div style={{ padding: '20px' }}>
        <div style={{ color: 'red', marginBottom: '10px' }}>
          Error loading overview: {error}
        </div>
        <button onClick={() => window.location.reload()}>
          Retry
        </button>
      </div>
    );
  }

  if (!stats) return <div>No data available</div>;

  const ageOrder = ["Puppy","Adult","Senior"];

  const labelMap = {
    "Puppy":"Puppies (0 to 1 year):",
    "Adult":"Adults:",
    "Senior":"Seniors (8+ years):"
  };

  const sortedAgeGroups = stats.ageGroups
    ? [...stats.ageGroups].sort((a, b) => {
        return ageOrder.indexOf(a.age_group) - ageOrder.indexOf(b.age_group);
      })
    : [];

  // Add modal styles
  const customStyles = {
    content: {
      top: '50%',
      left: '50%',
      right: 'auto',
      bottom: 'auto',
      marginRight: '-50%',
      transform: 'translate(-50%, -50%)',
      width: '80%',
      height: '80%',
    },
  };

  return (
    <div>
      {/* Move refresh button to the right of the heading */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '10px' }}>
        <h2 style={{ margin: 0, textAlign: 'left' }}>Shelter Overview</h2>
        <button 
          onClick={handleRefresh} 
          disabled={refreshing || loading}
          style={{ 
            display: 'none', // Hidden but not removed
            padding: '8px 16px', 
            backgroundColor: 'transparent', 
            color: '#007bff', 
            border: 'none', 
            borderRadius: '4px', 
            cursor: refreshing || loading ? 'not-allowed' : 'pointer',
            opacity: refreshing || loading ? 0.6 : 1,
            fontSize: '32px'  // Increased from 16px to make the icon larger
          }}
          title="Refresh Data"
        >
          {refreshing ? 'Refreshing...' : '🔄'}
        </button>
      </div>
      <table style={{ width: "50%", marginTop: "16px", textAlign: "left", borderCollapse: "collapse" }}>
        <tbody>
          <tr>
            <td><strong>Available Dogs:</strong></td>
            <td>{stats.total}</td>
          </tr>
          <br />  {/* Added to preserve original line spacing */}
          <tr>
            <td><strong>New this week:</strong></td>
            <td>{stats.newThisWeek}</td>
          </tr>
          <br />  {/* Added to preserve original line spacing */}
          <tr>
            <td><strong>Adopted this week:</strong></td>
            <td>{stats.adoptedThisWeek}</td>
          </tr>
          <br />  {/* Added to preserve original line spacing */}
          <tr>
            <td><strong>Trial Adoptions:</strong></td>
            <td>{stats.trialAdoptions}</td>
          </tr>
          <br />  {/* Added to preserve original line spacing */}
          <tr>
            <td><strong>Average Length of Stay:</strong></td>
            <td>{stats.avgStay} days</td>
          </tr>
          <br />  {/* Added to preserve original line spacing */}
          <tr>
            <td><strong>Longest Stay:</strong></td>
            <td>{stats.longestStay.days} days (
              <span
                onClick={() => openModal(stats.longestStay.url)}
                style={{ color: "#2a5db0", textDecoration: "underline", cursor: "pointer", fontWeight: 'bold' }}
              >
                {stats.longestStay.name}
              </span>
            )</td>
          </tr>
          <br />  {/* Added to preserve original line spacing */}
          <tr>
            <td style={{ verticalAlign: "top" }}>
              <strong>Available Dogs by Age Group:</strong>
            </td>
            <td>
              <table style={{ marginLeft: "0", borderCollapse: "separate", borderSpacing: "10px 4px" }}>
                <tbody>
                  {sortedAgeGroups.map(item =>
                    labelMap[item.age_group] ? (
                      <tr key={item.age_group}>
                        <td style={{padding: "4px 20px", textAlign:"left"}}>
                            {labelMap[item.age_group]}
                        </td>
                        <td style={{padding: "4px 20px", textAlign:"right"}}>
                          {item.count}
                        </td>
                      </tr>
                    ) : null
                  )}
                </tbody>
              </table>
            </td>
          </tr>
        </tbody>
      </table>

      {/* Add trend, alerts, small charts here */}
      {/* Add the modal */}
      <Modal
        isOpen={isModalOpen}
        onRequestClose={closeModal}
        style={customStyles}
        contentLabel="Dog Information"
      >
        <button onClick={closeModal} style={{ float: 'right' }}>Close</button>
        <iframe
          src={modalUrl}
          width="100%"
          height="100%"
          title="Dog Information"
          style={{ border: 'none' }}
        ></iframe>
      </Modal>
    </div>
  );
}

export default OverviewTab;
