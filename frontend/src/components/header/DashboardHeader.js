import React from "react";
import { FiGrid, FiList, FiSettings, FiUploadCloud, FiLogOut } from "react-icons/fi";

export default function DashboardHeader({
  isGridView,
  onGridView,
  onListView,
  onSettings,
  onExport,
  onLogout,
}) {
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
        {/* Grid/List View */}
        <button title="Grid View" onClick={onGridView} style={iconButtonStyle(isGridView)}>
          <FiGrid />
        </button>
        <button title="List View" onClick={onListView} style={iconButtonStyle(!isGridView)}>
          <FiList />
        </button>

        {/* Settings */}
        <button title="Settings" onClick={onSettings} style={iconButtonStyle()}>
          <FiSettings />
        </button>

        {/* Export */}
        <button
          title="Export to LMS"
          onClick={onExport}
          style={{
            background: "#2563eb",
            color: "#fff",
            borderRadius: 6,
            padding: "8px 14px",
            fontWeight: 500,
            fontSize: 14,
            border: "none",
            cursor: "pointer",
          }}
        >
          <FiUploadCloud style={{ marginRight: 6, marginTop: -2 }} />
          Export to LMS
        </button>

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

const iconButtonStyle = (active = false) => ({
  padding: 8,
  border: "1px solid #ccc",
  background: active ? "#2563eb" : "#fff",
  color: active ? "#fff" : "#222",
  borderRadius: 6,
  fontSize: 16,
  cursor: "pointer",
  display: "flex",
  alignItems: "center",
});
