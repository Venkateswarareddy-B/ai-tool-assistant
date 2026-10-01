import React from "react";

function ToolCard({ name, description, icon, onClick }) {
  return (
    <button className="tool-card" onClick={onClick}>
      <div className="tool-card-icon">{icon}</div>

      <div>
        <h3>{name}</h3>
        <p>{description}</p>
      </div>

      <span className="arrow">→</span>
    </button>
  );
}

export default ToolCard;