import React from 'react';
import '../styles/LevelSelector.css';

const LevelSelector = ({ level, setLevel }) => {
  return (
    <div className="level-selector">
      <label htmlFor="level-select">Choose a level:</label>
      <select
        id="level-select"
        value={level}
        onChange={(e) => setLevel(e.target.value)}
      >
        <option value="a1">A1</option>
        <option value="a2">A2</option>
        <option value="b1">B1</option>
      </select>
    </div>
  );
};

export default LevelSelector;