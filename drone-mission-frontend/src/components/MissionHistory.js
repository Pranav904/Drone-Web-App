// MissionHistory.jsx
import React from "react";

const MissionHistory = ({ missionHistory }) => {
  return (
    <div className="mission-history">
      <h3>Mission History:</h3>
      <ul>
        {missionHistory.map((mission, index) => (
          <li key={index}>{mission}</li>
        ))}
      </ul>
    </div>
  );
};

export default MissionHistory;
