import React, { useEffect } from 'react';

const DogListModal = ({ isOpen, onClose, dogs, binRange }) => {
    useEffect(() => {
        const handleEscape = (e) => {
            if (e.key === 'Escape' && isOpen) {
                onClose();
            }
        };

        if (isOpen) {
            document.addEventListener('keydown', handleEscape);
            document.body.style.overflow = 'hidden'; // Prevent background scroll
        }

        return () => {
            document.removeEventListener('keydown', handleEscape);
            document.body.style.overflow = 'unset';
        };
    }, [isOpen, onClose]);

    if (!isOpen) return null;

    const handleOverlayClick = (e) => {
        if (e.target === e.currentTarget) {
            onClose();
        }
    };

    return (
        <div
            onClick={handleOverlayClick}
            style={{
                position: 'fixed',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                backgroundColor: 'rgba(0, 0, 0, 0.5)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                zIndex: 1000
            }}
        >
            <div
                role="dialog"
                aria-labelledby="modal-title"
                style={{
                    backgroundColor: 'white',
                    borderRadius: '8px',
                    padding: '24px',
                    maxWidth: '600px',
                    width: '90%',
                    maxHeight: '80vh',
                    overflow: 'auto',
                    position: 'relative'
                }}
            >
                <button
                    onClick={onClose}
                    aria-label="Close modal"
                    style={{
                        position: 'absolute',
                        top: '16px',
                        right: '16px',
                        background: 'none',
                        border: 'none',
                        fontSize: '24px',
                        cursor: 'pointer',
                        padding: '4px 8px'
                    }}
                >
                    ×
                </button>

                <h2 id="modal-title" style={{ marginTop: 0, marginBottom: '20px' }}>
                    Dogs with {binRange} Stay
                </h2>

                {dogs && dogs.length > 0 ? (
                    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                        <thead>
                            <tr style={{ borderBottom: '2px solid #ddd' }}>
                                <th style={{ padding: '8px', textAlign: 'left' }}>Name</th>
                                <th style={{ padding: '8px', textAlign: 'left' }}>Breed</th>
                                <th style={{ padding: '8px', textAlign: 'left' }}>Age</th>
                                <th style={{ padding: '8px', textAlign: 'right' }}>Days</th>
                            </tr>
                        </thead>
                        <tbody>
                            {dogs.map((dog, index) => (
                                <tr key={dog.id || index} style={{ borderBottom: '1px solid #eee' }}>
                                    <td style={{ padding: '8px' }}>{dog.name}</td>
                                    <td style={{ padding: '8px' }}>{dog.breed || 'Unknown'}</td>
                                    <td style={{ padding: '8px' }}>{dog.age_group || 'Unknown'}</td>
                                    <td style={{ padding: '8px', textAlign: 'right' }}>{dog.length_of_stay_days}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                ) : (
                    <p>No dogs in this range</p>
                )}
            </div>
        </div>
    );
};

export default DogListModal;
