import React, { useEffect, useState } from 'react';
import Modal from 'react-modal';  // Install via npm install react-modal if not already installed
import { fetchDiffAnalysis } from './api';

function DiffAnalysisTab() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalUrl, setModalUrl] = useState('');
  const [missingDogs, setMissingDogs] = useState([]);

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

  useEffect(() => {
    const loadMissingDogs = async () => {
      try {
        // Try API JSON endpoint first
        const res = await fetch('/api/missing-dogs');
        if (res.ok) {
          const apiResp = await res.json();
          // APIResponse wrapper => {data: [...]}
          const dogs = apiResp && apiResp.data ? apiResp.data : apiResp;
          if (Array.isArray(dogs)) {
            // Normalize to include URL used by modal links
            const normalized = dogs.map(d => ({ id: d.id, name: d.name, url: `https://new.shelterluv.com/embed/animal/${d.id}` }));
            setMissingDogs(normalized);
            return;
          }
        }

        // Fallback to legacy text file if API fails or returns unexpected format
        const response = await fetch('/missing_dogs.txt');
        if (!response.ok) {
          throw new Error('Failed to load missing dogs file');
        }
        const text = await response.text();
        const dogs = parseMissingDogs(text);
        setMissingDogs(dogs);
      } catch (err) {
        console.error('Failed to load missing dogs:', err);
        setMissingDogs([]);
      }
    };

    loadMissingDogs();
  }, []);

  // Compute display lists and ensure mutual exclusivity with "Available Soon"
  const {
    displayNewDogs,
    displayReturnedDogs,
    displayAdoptedDogs,
    displayTrialDogs,
    displayOtherUnlistedDogs,
    filteredMissingDogs
  } = React.useMemo(() => {
    // If no data or no missing dogs, default to original lists
    if (!data) {
      return {
        displayNewDogs: data ? (data.new_dogs || []) : [],
        displayReturnedDogs: data ? (data.returned_dogs || []) : [],
        displayAdoptedDogs: data ? (data.adopted_dogs || []) : [],
        displayTrialDogs: data ? (data.trial_adoption_dogs || []) : [],
        displayOtherUnlistedDogs: data ? (data.other_unlisted_dogs || []) : [],
        filteredMissingDogs: missingDogs || []
      };
    }

    // Helper: extract numeric ID from a Shelterluv embed URL
    const extractIdFromUrl = (url) => {
      const match = (url || '').match(/\/animal\/(\d+)$/);
      return match ? parseInt(match[1], 10) : null;
    };

    const missingIds = new Set((missingDogs || []).map(d => d.id));

    // Build sets of IDs from backend lists
    const newIds = new Set((data.new_dogs || []).map(d => extractIdFromUrl(d.url)).filter(Boolean));
    const returnedIds = new Set((data.returned_dogs || []).map(d => d.dog_id));
    const adoptedIds = new Set((data.adopted_dogs || []).map(d => d.dog_id));
    const trialIds = new Set((data.trial_adoption_dogs || []).map(d => d.dog_id));
    const otherUnlistedIds = new Set((data.other_unlisted_dogs || []).map(d => d.dog_id));

    // Union of IDs that should exclude missing dogs from appearing in "Available Soon"
    const occupiedIds = new Set([
      ...Array.from(newIds),
      ...Array.from(returnedIds),
      ...Array.from(adoptedIds),
      ...Array.from(trialIds),
      ...Array.from(otherUnlistedIds)
    ].filter(Boolean));

    // Now produce display lists by removing any missing-dog IDs from the other lists
    const displayNew = (data.new_dogs || []).filter(dog => {
      const id = extractIdFromUrl(dog.url);
      return id && !missingIds.has(id);
    });

    const displayReturned = (data.returned_dogs || []).filter(dog => !missingIds.has(dog.dog_id));
    const displayAdopted = (data.adopted_dogs || []).filter(dog => !missingIds.has(dog.dog_id));
    const displayTrial = (data.trial_adoption_dogs || []).filter(dog => !missingIds.has(dog.dog_id));

    // For other unlisted dogs also avoid duplicates with new_dogs
    const displayOther = (data.other_unlisted_dogs || []).filter(dog => {
      const id = dog.dog_id;
      return id && !missingIds.has(id) && !newIds.has(id);
    });

    // Filter missing dogs to exclude any ID that appears in other lists
    const filteredMissing = (missingDogs || []).filter(dog => !occupiedIds.has(dog.id));

    return {
      displayNewDogs: displayNew,
      displayReturnedDogs: displayReturned,
      displayAdoptedDogs: displayAdopted,
      displayTrialDogs: displayTrial,
      displayOtherUnlistedDogs: displayOther,
      filteredMissingDogs: filteredMissing
    };
  }, [data, missingDogs]);

  const openModal = (url) => {
    setModalUrl(url);
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setModalUrl('');
  };

  const parseMissingDogs = (textOrArray) => {
    // Accept either raw text from legacy file or an array from the API
    if (Array.isArray(textOrArray)) {
      return textOrArray.map(d => ({
        id: d.id,
        name: d.name,
        url: d.url || `https://new.shelterluv.com/embed/animal/${d.id}`
      }));
    }

    const dogs = [];
    const lines = textOrArray.split('\n').filter(line => line.trim() && !line.startsWith('Missing dogs'));

    lines.forEach(line => {
      const match = line.match(/^(\d+):\s*(.+)$/);
      if (match) {
        const [, id, name] = match;
        dogs.push({
          id: parseInt(id),
          name: name.trim(),
          url: `https://new.shelterluv.com/embed/animal/${id}`
        });
      }
    });

    return dogs;
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

      {renderDogList(displayNewDogs, "New Dogs")}
      {renderDogList(displayReturnedDogs, "Returned Dogs")}
      {renderDogList(displayAdoptedDogs, "Adopted/Reclaimed Dogs")}
      {renderDogList(displayTrialDogs, "Trial Adoptions")}
      {renderDogList(displayOtherUnlistedDogs, "Available but Temporarily Unlisted")}
      {renderDogList(filteredMissingDogs, "Available Soon")}

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
