import React, { useEffect, useState } from 'react';
import { fetchAdoptions } from './api';

function Adoptions() {
  const [adoptions, setAdoptions] = useState([]);

  useEffect(() => {
    fetchAdoptions()
      .then(data => {
        setAdoptions(Array.isArray(data) ? data : []);
      })
      .catch(err => {
        console.error("Error fetching adoptions:", err);
        setAdoptions([]);
      });
  }, []);

  if (!Array.isArray(adoptions) || adoptions.length === 0) {
    return <p>No adoptions to display.</p>;
  }

  return (
    <table>
      <thead>
        <tr>
          <th>Name</th>
          <th>Date Adopted</th>
          <th>Days at Shelter</th>
          <th>URL</th>
        </tr>
      </thead>
      <tbody>
        {[...adoptions]
          .sort((a, b) => a.date.localeCompare(b.date)) 
          .map((dog) => (
            <tr key={dog.name + dog.date}>
              <td style={{ paddingRight: "30px" }}>{dog.name.trim()}</td>
              <td style={{ paddingRight: "30px" }}>{dog.date}</td>
              <td style={{ paddingRight: "100px" }}>{dog.los}</td>
              <td><a href={dog.url} target="_blank" rel="noopener noreferrer">Link</a></td>
            </tr>
          ))}
      </tbody>
    </table>
  );
}

export default Adoptions;

