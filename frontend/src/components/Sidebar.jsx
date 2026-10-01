import React from "react";

const tools = [
  {
    name: "Weather",
    icon: "🌦️",
    description: "Current weather information",
  },
  {
    name: "Currency",
    icon: "💱",
    description: "Convert currencies",
  },
  {
    name: "Wikipedia",
    icon: "📚",
    description: "Search Wikipedia",
  },
  {
    name: "Calculator",
    icon: "🧮",
    description: "Calculate expressions",
  },
  {
    name: "News",
    icon: "📰",
    description: "Get recent news",
  },
  {
    name: "Location",
    icon: "📍",
    description: "Find coordinates",
  },
];

function Sidebar({ onToolClick }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="logo">🤖</div>

        <div>
          <h1>AI Assistant</h1>
          <p>Tool-powered chatbot</p>
        </div>
      </div>

      <div className="tools-title">
        <span>TOOLS</span>
      </div>

      <div className="tools-list">
        {tools.map((tool) => (
          <button
            className="tool-button"
            key={tool.name}
            onClick={() => onToolClick(tool.name)}
          >
            <span className="tool-icon">{tool.icon}</span>

            <span className="tool-info">
              <strong>{tool.name}</strong>
              <small>{tool.description}</small>
            </span>
          </button>
        ))}
      </div>

      <div className="sidebar-footer">
        <div className="status-dot"></div>

        <span>Groq-powered assistant</span>
      </div>
    </aside>
  );
}

export default Sidebar;