import './LivePopulationTab.css';

import React, { useEffect, useState } from 'react';
import { fetchDogs, fetchDogById, updateDog, fetchLatestIndex } from './api';


function LivePopulationTab() {
  const [availables, setAvailables] = useState([]); // Initialize as empty array

  // New state for inline editing
  const [editDogId, setEditDogId] = useState(null);
  const [form, setForm] = useState({ origin: '', latitude: '', longitude: '' });

  useEffect(() => {
    fetch("/api/live_population")
      .then((res) => res.json())
      .then((data) => setAvailables(Array.isArray(data) ? data : []))
      .catch((error) => {
        console.error("Error fetching available dogs:", error);
        setAvailables([]);
      });
  }, []);

  // Open popup to edit dog info
  async function openEdit(dogId) {
    console.log('Editing dog id:', dogId);
    const dogData = await fetchDogById(dogId);
    console.log('dogData after fetchDogById: ', dogData);
    setEditDogId(dogId);
    setForm({
      index: dogData._index || "",
      age_group: dogData.age_group ?? "",
      birthdate: dogData.birthdate || "",
      bite_quarantine: dogData.bite_quarantine ?? "",
      breed: dogData.breed || "",
      color: dogData.color || "",
      id: dogData.id ?? "",
      intake_date: dogData.intake_date || "",
      length_of_stay_days: dogData.length_of_stay_days ?? "",
      returned: dogData.returned ?? "",
      secondary_breed: dogData.secondary_breed || "",
      timestamp: dogData.timestamp || "",
      url: dogData.url || "",
      weight_group: dogData.weight_group || "",
      name: dogData.name || "",
      location: dogData.location || "",
      origin: dogData.origin || "",
      latitude: dogData.latitude ?? "",
      longitude: dogData.longitude ?? "",
      status: dogData.status || "",
    });
  }

  // Handle form input changes
  function onChange(e) {
    const { name, value } = e.target;
    setForm((prevForm) => ({ ...prevForm, [name]: value }));
  }

  // Save updated info and reload dogs list
  async function onSave() {
    console.log("Data being sent to updateDog:", form);
    try {
      await updateDog(editDogId, form);
      alert("Dog updated!");
      setEditDogId(null);
      // Refresh dogs list here if needed
    } catch (err) {
      alert("Error updating dog: " + err.message);
    }
  }

  if (!Array.isArray(availables) || availables.length === 0) {
    return <p>Loading...</p>;
  }

  return (
    <>
      {/* Render existing availables list */}
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Location</th>
            <th style={{ textAlign: "center" }}>URL</th>
            <th style={{ textAlign: "center" }}>Edit</th>
          </tr>
        </thead>
        <tbody>
          {[...availables]
            .sort((a, b) => a.location.localeCompare(b.location))
            .map((dog) => {
              const url = new URL(dog.url);
              const dogIdFromUrl = url.pathname.split('/').filter(Boolean).pop();
              return (
                <tr key={dog.dog_id}>
                  <td style={{ paddingRight: "20px" }}>{dog.name.trim()}</td>
                  <td style={{ paddingRight: "20px" }}>{dog.location}</td>
                  <td style={{ textAlign: "center" }}>
                    <a href={dog.url} target="_blank" rel="noopener noreferrer">
                      Link
                    </a>
                  </td>
                  <td style={{ textAlign: "center" }}>
                    <button
                      onClick={() => openEdit(dogIdFromUrl)}
                      style={{ marginLeft: 8, cursor: "pointer", border: "none", background: "none" }}
                      aria-label={`Edit ${dog.name}`}
                      title={`Edit ${dog.name}`}
                    >
                      ✏️
                    </button>
                  </td>
                </tr>
              );
            })}
        </tbody>
      </table>

      {/* Render EditDogDialog conditionally, passing props */}
      {editDogId && (
        <EditDogDialog
          dogId={editDogId}
          form={form}
          setForm={setForm}
          onChange={onChange}
          onSave={onSave}
          setEditDogId={setEditDogId}
        />
      )}
    </>
  );
}

function EditDogDialog({ dogId, form, setForm, onChange, onSave, setEditDogId }) {
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function getLatestIndex() {
    try {
      const data = await fetchLatestIndex(dogId);
      console.log('Fetched index from API:', data.index);
      setForm(prev => ({ ...prev, index: data.index || "" }));
      setLoading(false);
    } catch (err) {
      console.error('Failed to fetch latest index:', err);
      setLoading(false);
    }
  }
  if (dogId) { getLatestIndex();}
  }, [dogId, setForm]);
 
  useEffect(() => {
    console.log('form.index updated:', form.index);
  }, [form.index]);

  if (loading) return <p>Loading form data...</p>;

  return (
    <>
      <div className="modal-overlay" onClick={() => setEditDogId(null)}></div>
      <div className="modal">
        <h3>Edit Dog Info</h3>

        <label>
          Index:<br />
          <input name="index" value={form.index || ""} onChange={onChange} />
        </label> <br />
        <label>
          Name:<br />
          <input name="name" value={form.name || ""} onChange={onChange} />
        </label> <br />
        <label>
          Location:<br />
          <input name="location" value={form.location || ""} onChange={onChange} />
        </label><br />
        <label>
          Origin:<br />
          <input name="origin" value={form.origin || ""} onChange={onChange} placeholder="Enter origin" />
        </label> <br />
        <label>
          Latitude:<br />
          <input name="latitude" value={form.latitude || ""} onChange={onChange} placeholder="Enter latitude" />
        </label><br />
        <label>
          Longitude:<br />
          <input name="longitude" value={form.longitude || ""} onChange={onChange} placeholder="Enter longitude" />
        </label><br />
        <label>
          Age Group:<br />
          <input name="age_group" value={form.age_group || ""} onChange={onChange} placeholder="Enter age group" />
        </label><br />
        <label>
          Birthdate:<br />
          <input name="birthdate" value={form.birthdate || ""} onChange={onChange} placeholder="Enter birthdate" />
        </label><br />
        <label>
          Bite Quarantine:<br />
          <input name="bite_quarantine" value={form.bite_quarantine || ""} onChange={onChange} placeholder="Enter bite quarantine" />
        </label><br />
        <label>
          Breed:<br />
          <input name="breed" value={form.breed || ""} onChange={onChange} placeholder="Enter breed" />
        </label><br />
        <label>
          Secondary Breed:<br />
          <input name="secondary_breed" value={form.secondary_breed || ""} onChange={onChange} placeholder="Enter secondary breed" />
        </label><br />
        <label>
          Color:<br />
          <input name="color" value={form.color || ""} onChange={onChange} placeholder="Enter color" />
        </label><br />
        <label>
          Id:<br />
          <input name="id" value={form.id || ""} onChange={onChange} placeholder="Enter id" />
        </label><br />
        <label>
          Intake Date:<br />
          <input name="intake_date" value={form.intake_date || ""} onChange={onChange} placeholder="Enter intake date" />
        </label><br />
        <label>
          Length of Stay (days):<br />
          <input name="length_of_stay_days" value={form.length_of_stay_days || ""} onChange={onChange} placeholder="Enter length of stay in days" />
        </label><br />
        <label>
          Returned:<br />
          <input name="returned" value={form.returned || ""} onChange={onChange} placeholder="Enter returned" />
        </label><br />
        <label>
          Timestamp:<br />
          <input name="timestamp" value={form.timestamp || ""} onChange={onChange} placeholder="Enter timestamp" />
        </label><br />
        <label>
          URL:<br />
          <input name="url" value={form.url || ""} onChange={onChange} placeholder="Enter URL" />
        </label><br />
        <label>
          Weight Group:<br />
          <input name="weight_group" value={form.weight_group || ""} onChange={onChange} placeholder="Enter weight group" />
        </label><br />
        <label>
          Status:<br />
          <input name="status" value={form.status || ""} onChange={onChange} placeholder="Enter status" />
        </label><br />
        <button onClick={onSave}>Save</button>
        <button onClick={() => setEditDogId(null)}>Cancel</button>
      </div>
    </>
  );
}

export default LivePopulationTab;

