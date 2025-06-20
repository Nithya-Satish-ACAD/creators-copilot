import React from "react";

function LeftPanel({ onSelectBlock }) {
  return (
    <div style={{
      width: "250px",
      borderRight: "1px solid #ddd",
      padding: "1rem",
      backgroundColor: "#f8f9fa"
    }}>
      <h3 style={{ marginBottom: "1rem" }}>📦 Building Blocks</h3>
      <button
        onClick={() => onSelectBlock("generate_course")}
        style={{
          padding: "10px",
          marginBottom: "0.5rem",
          width: "100%",
          backgroundColor: "#fff",
          border: "1px solid #ccc",
          borderRadius: "8px",
          textAlign: "left",
          cursor: "pointer"
        }}
      >
        ⚙️ Generate Course Overview
      </button>
    </div>
  );
}

export default LeftPanel;
