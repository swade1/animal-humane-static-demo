import React, { useEffect, useState } from 'react';
import Modal from 'react-modal';  // Install via npm install react-modal if not already installed
import { fetchDiffAnalysis } from './api';

function DiffAnalysisTab() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalUrl, setModalUrl] = useState('');

  useEffect(() => {
    const loadDiffAnalysis = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await fetchDiffAnalysis();
        // Extract data from APIResponse wrapper
        setData(response.data || response);
      } catch (err) {
        setError(err.message);
        console.error('Failed to load diff analysis:', err);
      } finally {
        setLoading(false);
      }
    };

    loadDiffAnalysis();
  }, []);

  const openModal = (url) => {
    setModalUrl(url);
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setModalUrl('');
  };

  if (loading) return <div>Loading diff analysis...</div>;

  if (error) {
    return (
      <div style={{ padding: '20px' }}>
        <div style={{ color: 'red', marginBottom: '10px' }}>
          Error loading diff analysis: {error}
        </div>
        <button onClick={() => window.location.reload()}>
          Retry
        </button>
      </div>
    );
  }

  if (!data) return <div>No data available</div>;

  const renderDogList = (dogs, title) => {
    if (!dogs || dogs.length === 0) {
      return (
        <div style={{ marginBottom: '20px' }}>
          <p style={{ fontWeight: 'bold', marginBottom: '10px', fontSize: '16px' }}>{title}</p>
          <p>No dogs in this category</p>
        </div>
      );
    }

    return (
      <div style={{ marginBottom: '20px' }}>
        <p style={{ fontWeight: 'bold', marginBottom: '10px', fontSize: '16px' }}>{title}</p>
        {dogs.map((dog, index) => (
          <div key={index} style={{ marginBottom: '5px' }}>
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
      <h2 style={{ marginTop: '10px', textAlign: 'left' }}>Dog Movement Analysis</h2>
      <p style={{ marginBottom: '30px' }}>This tab shows changes in dog status between database updates.</p>

      {renderDogList(data.new_dogs, "New Dogs")}
      {renderDogList(data.returned_dogs, "Returned Dogs")}
      {renderDogList(data.adopted_dogs, "Adopted/Reclaimed Dogs")}
      {renderDogList(data.trial_adoption_dogs, "Trial Adoptions")}
      {renderDogList(data.other_unlisted_dogs, "Available but Temporarily Unlisted")}

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
