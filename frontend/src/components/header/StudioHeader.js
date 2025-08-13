import React from "react";
import { FiLogOut } from "react-icons/fi";
import { useNavigate } from "react-router-dom";


export default function StudioHeader({
  onSettings,
  onLogout,
  onBack
}) {
    const navigate = useNavigate();
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "16px 5vw 8px",
        background: "#fafbfc",
        borderBottom: "1px solid #e5e7eb",
      }}
    >
      {/* Left: Brand */}
      <div style={{ fontWeight: 700, fontSize: 20 }}>Course Copilot</div>

      {/* Right: Buttons */}
      <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
        <button onClick={() => navigate(-1)} style={btnStyle}>Close</button>

        {/* Logout */}
        <button
          title="Logout"
          onClick={onLogout}
          style={{
            border: "1px solid #ddd",
            background: "#fff",
            borderRadius: 6,
            padding: 8,
            display: "flex",
            alignItems: "center",
            cursor: "pointer",
            fontSize: 16,
          }}
        >
          <FiLogOut /> Logout
        </button>
      </div>
    </div>
  );
}

const btnStyle = {
  padding: "8px 14px",
  borderRadius: 5,
  border: "1px solid #bbb",
  background: "#fff",
  cursor: "pointer",
  fontSize: 14,
  fontWeight: 500,
};
