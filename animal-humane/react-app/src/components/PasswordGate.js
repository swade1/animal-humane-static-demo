import React, { useState, useEffect } from 'react';

const PasswordGate = ({ children }) => {
  const [authenticated, setAuthenticated] = useState(false);
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const correctPassword = 'ahnm2026'; // Change this to your preferred password

  useEffect(() => {
    // Check if already authenticated
    if (localStorage.getItem('ah-authenticated') === 'true') {
      setAuthenticated(true);
    }
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (password === correctPassword) {
      setAuthenticated(true);
      localStorage.setItem('ah-authenticated', 'true');
      setError('');
    } else {
      setError('Incorrect access code');
      setPassword('');
    }
  };

  if (!authenticated) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        backgroundColor: '#f5f5f5',
        fontFamily: 'Arial, sans-serif'
      }}>
        <div style={{
          backgroundColor: 'white',
          padding: '40px',
          borderRadius: '8px',
          boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
          width: '100%',
          maxWidth: '400px'
        }}>
          <h2 style={{ textAlign: 'center', marginBottom: '30px', color: '#333' }}>
            Animal Humane Dashboard
          </h2>
          <p style={{ textAlign: 'center', color: '#666', marginBottom: '20px' }}>
            This is a private demonstration. Please enter the access code.
          </p>
          <form onSubmit={handleSubmit}>
            <input
              type="password"
              placeholder="Enter access code"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={{
                width: '100%',
                padding: '12px',
                fontSize: '16px',
                border: '2px solid #ddd',
                borderRadius: '4px',
                marginBottom: '15px',
                boxSizing: 'border-box'
              }}
              autoFocus
            />
            {error && (
              <p style={{ color: 'red', fontSize: '14px', marginBottom: '15px' }}>
                {error}
              </p>
            )}
            <button
              type="submit"
              style={{
                width: '100%',
                padding: '12px',
                fontSize: '16px',
                backgroundColor: '#007bff',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              Access Dashboard
            </button>
          </form>
        </div>
      </div>
    );
  }

  return children;
};

export default PasswordGate;
