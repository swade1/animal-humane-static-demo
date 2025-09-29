// src/App.js

import React, { useState } from 'react';
import { runDocumentUpdates } from './api';
import Tabs from './Tabs'; // import your new Tabs component
import './App.css'
import 'leaflet/dist/leaflet.css'

function App() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleUpdate = async () => {
    setLoading(true);
    try {
      const data = await runDocumentUpdates();
      setResult(data);
    } catch (err) {
      setResult({ error: err.message });
    }
    setLoading(false);
  };

  return (
    <div style={{padding:20}}>
      <h1>Animal Humane Pupdates</h1>
      <button 
         onClick={handleUpdate} 
         disabled={loading}
         style={{display:"none"}}>
        {loading ? "Updating..." : "Run Updates"}
      </button>
      {result && (
        <pre style={{whiteSpace: 'pre-wrap', marginTop:20}}>
          {typeof result === 'string' ? result : JSON.stringify(result, null, 2)}
        </pre>
      )}
      {/*Add 5-tab UI here */}
      <Tabs />
    </div>
  );
}

export default App;
