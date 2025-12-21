import React, { useEffect, useState } from 'react';
import Modal from 'react-modal';
import { fetchAdoptions } from './api';
import './AdoptionsTab.css';

function Adoptions() {
  const [adoptions, setAdoptions] = useState([]);

  // Add modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalUrl, setModalUrl] = useState('');

  useEffect(() => {
    fetchAdoptions()
      .then(response => {
        const data = response.data || response;
        setAdoptions(Array.isArray(data) ? data : []);
      })
      .catch(err => {
        console.error("Error fetching adoptions:", err);
        setAdoptions([]);
      });
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

  if (!Array.isArray(adoptions) || adoptions.length === 0) {
    return <p>No adoptions to display.</p>;
  }

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
    <>
      <table style={{ 
        width: '80%', 
        maxWidth: '800px', 
        margin: '0 0 0 25px',
        borderCollapse: 'collapse'
      }}>
        <thead>
          <tr style={{ backgroundColor: '#f2f2f2' }}>
            <th style={{ padding: '10px', textAlign: 'left', paddingLeft: '10px' }}>Name</th>
            <th style={{ padding: '10px', textAlign: 'center' }}>Date Adopted</th>
            <th style={{ padding: '10px', textAlign: 'center' }}>Days at Shelter</th>
          </tr>
        </thead>
        <tbody>
          {[...adoptions]
            .sort((a, b) => a.date.localeCompare(b.date)) 
            .map((dog) => (
              <tr key={dog.name + dog.date}>
                <td style={{ padding: '10px 20px', textAlign: 'left' }}>
                  <span
                    onClick={() => openModal(dog.url)}
                    style={{ color: '#007bff', textDecoration: 'none', cursor: 'pointer', fontWeight: 'bold' }}
                  >
                    {dog.name.trim()}
                  </span>
                </td>
                <td style={{ padding: '10px 20px', textAlign: 'center' }}>{dog.date}</td>
                <td style={{ padding: '10px 20px', textAlign: 'center' }}>{dog.los}</td>
              </tr>
            ))}
        </tbody>
      </table>

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
    </>
  );
}

export default Adoptions;