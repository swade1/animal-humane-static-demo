import React, { useEffect, useState } from 'react';
import Modal from 'react-modal';
import { fetchRecentPupdates, getApiMode } from './api';

function DiffAnalysisTab() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalUrl, setModalUrl] = useState('');

  useEffect(() => {
    const loadRecentPupdates = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await fetchRecentPupdates(); // Use correct API endpoint
        // Extract data from APIResponse wrapper
        const pupdatesData = response.data || response;
        setData(pupdatesData);
      } catch (err) {
        setError(err.message);
        console.error('Failed to load recent pupdates:', err);
      } finally {
        setLoading(false);
      }
    };

    loadRecentPupdates();
  }, []);

  const openModal = (url) => {
    setModalUrl(url);
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setModalUrl('');
  };

  const renderDogList = (dogs, title, description = null) => {
    if (!dogs || dogs.length === 0) {
      return (
        <div style={{ marginBottom: '20px' }}>
          <p style={{ fontWeight: 'bold', marginBottom: '10px', fontSize: '16px' }}>{title}</p>
          {description && <p style={{ fontSize: '14px', color: '#666', marginBottom: '10px' }}>{description}</p>}
          <p>No dogs in this category</p>
        </div>
      );
    }

    return (
      <div style={{ marginBottom: '20px' }}>
        <p style={{ fontWeight: 'bold', marginBottom: '10px', fontSize: '16px' }}>{title}</p>
        {description && <p style={{ fontSize: '14px', color: '#666', marginBottom: '10px' }}>{description}</p>}
        {dogs.map((dog, index) => (
          <div key={dog.id || index} style={{ marginBottom: '5px' }}>
            <span
              onClick={() => openModal(dog.url || '#')}
              style={{ color: '#007bff', textDecoration: 'none', cursor: 'pointer', fontWeight: 'bold' }}
            >
              {dog.name || 'Unnamed Dog'}
            </span>
          </div>
        ))}
      </div>
    );
  };

  const renderDataQualityIndicator = () => {
    if (!data?.metadata?.data_quality_score) return null;
    
    const score = data.metadata.data_quality_score;
    const color = score >= 0.8 ? '#28a745' : score >= 0.5 ? '#ffc107' : '#dc3545';
    
    return (
      <div style={{ 
        marginBottom: '20px', 
        padding: '10px', 
        backgroundColor: '#f8f9fa', 
        borderRadius: '5px',
        border: `1px solid ${color}`
      }}>
        <div style={{ fontSize: '14px', color: '#666' }}>
          Data Quality Score: <span style={{ color, fontWeight: 'bold' }}>{Math.round(score * 100)}%</span>
          {data.metadata.warnings && data.metadata.warnings.length > 0 && (
            <div style={{ marginTop: '5px' }}>
              <strong>Warnings:</strong>
              <ul style={{ margin: '5px 0', paddingLeft: '20px' }}>
                {data.metadata.warnings.map((warning, idx) => (
                  <li key={idx} style={{ color: '#856404' }}>{warning}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderDataFreshness = () => {
    if (!data?.metadata?.data_freshness) return null;
    
    const freshness = data.metadata.data_freshness;
    return (
      <div style={{ 
        marginBottom: '20px', 
        padding: '10px', 
        backgroundColor: '#e9ecef', 
        borderRadius: '5px',
        fontSize: '12px',
        color: '#6c757d'
      }}>
        <div><strong>Data Freshness:</strong></div>
        {freshness.analysis_timestamp && (
          <div>Analysis: {new Date(freshness.analysis_timestamp).toLocaleString()}</div>
        )}
        {freshness.elasticsearch_last_update && (
          <div>Database: {new Date(freshness.elasticsearch_last_update).toLocaleString()}</div>
        )}
      </div>
    );
  };

  if (loading) return <div>Loading recent pupdates...</div>;

  if (error) {
    return (
      <div style={{ padding: '20px' }}>
        <div style={{ color: 'red', marginBottom: '10px' }}>
          Error loading recent pupdates: {error}
        </div>
        <button onClick={() => {
          const apiMode = getApiMode();
          if (apiMode.isStatic) {
            alert('🎯 Demo Mode: Page reload is not recommended in this static portfolio demonstration.\n\nThis demo uses static data from January 1, 2026. In the live version, this would reload data from the live API.');
          } else {
            window.location.reload();
          }
        }}>
          Retry
        </button>
      </div>
    );
  }

  if (!data) return <div>No data available</div>;

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
      <h2 style={{ marginTop: '10px', textAlign: 'left' }}>Recent Pupdates</h2>
      <p style={{ marginBottom: '20px' }}>
        This tab shows recent changes in dog status and availability. 
        {data.metadata?.total_dogs && <span> • Total: {data.metadata.total_dogs} dogs</span>}
      </p>

      {renderDogList(data.new_dogs, "New Dogs", "We're new and making our debut!")}
      {renderDogList(data.returned_dogs, "Returned Dogs", "We're Back!")}
      {renderDogList(data.adopted_dogs, "Adopted/Reclaimed Dogs", "We've been adopted!!!")}
      {renderDogList(data.trial_dogs, "Trial Adoptions", "We're checking out a potential new home and evaluating the quality of the treats and toys")}
      {renderDogList(data.unlisted_dogs, "Available but Temporarily Unlisted", "We're taking a short break but we'll be back soon!")}
      {renderDogList(data.available_soon, "Available Soon", "We're settling in and getting ready for our close-ups!")}

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

export default DiffAnalysisTab;
