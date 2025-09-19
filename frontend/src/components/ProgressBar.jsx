import React from 'react';
import '../styles/ProgressBar.css';

const ProgressBar = ({ progress }) => {
  const { current, total } = progress;
  
  // Prevent division by zero and handle the initial state
  const percentage = total > 0 ? (current / total) * 100 : 0;
  
  // Ensure the percentage doesn't exceed 100, which can happen with edge cases
  const displayPercentage = Math.min(percentage, 100);

  // --- THIS IS THE FIX: Format the percentage for display ---
  const percentageLabel = `${Math.floor(displayPercentage)}%`;

  return (
    <div className="progress-bar-container">
      <div className="progress-bar-header">
        <span className="progress-bar-title">Daily Goal Progress</span>
        {/* --- THIS IS THE FIX: Show the percentage label --- */}
        <span className="progress-bar-label">{percentageLabel}</span>
      </div>
      <div className="progress-bar-background">
        <div 
          className="progress-bar-fill" 
          style={{ width: `${displayPercentage}%` }}
          aria-valuenow={current}
          aria-valuemin="0"
          aria-valuemax={total}
          role="progressbar"
        />
      </div>
    </div>
  );
};

export default ProgressBar;