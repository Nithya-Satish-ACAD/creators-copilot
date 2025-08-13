import React from "react";
import { FaUserCircle } from "react-icons/fa";

export default function Header({
  title = "Creators Copilot",
  onLogout,
  onSettings,
  onExport,
  onGridView,
  onListView,
  isGridView = true
}) {
  return (
    <header style={{
      height: 64,
      minHeight: 64,
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      borderBottom: "1px solid #e5eaf2",
      padding: "0 32px",
      position: 'sticky',
      top: 0,
      background: '#fff',
      zIndex: 10,
      boxShadow: '0 2px 12px #2563eb0a',
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
        <div style={{ background: "#2563eb", color: "#fff", borderRadius: 12, width: 40, height: 40, display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 700, fontSize: 22, marginRight: 14, boxShadow: '0 2px 8px #2563eb22' }}>
          C
        </div>
        <span style={{ fontWeight: 700, fontSize: 22, color: "#222", letterSpacing: 0.5 }}>{title}</span>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 18 }}>
        {/* Grid/List Toggle */}
        <div style={{ display: "flex", alignItems: "center", gap: 0, background: "#f5f8ff", borderRadius: 8, border: "1px solid #e0e7ef", overflow: "hidden", height: 38 }}>
          <button
            style={{
              background: isGridView ? "#2563eb" : "#fff",
              color: isGridView ? "#fff" : "#222",
              border: "none",
              padding: "0 14px",
              fontWeight: 600,
              fontSize: 18,
              height: 38,
              cursor: "pointer",
              outline: "none",
              display: "flex",
              alignItems: "center",
              borderRadius: 0
            }}
            onClick={onGridView}
          >
            <span style={{ fontSize: 18, verticalAlign: "middle" }}>▦</span>
          </button>
          <button
            style={{
              background: !isGridView ? "#2563eb" : "#fff",
              color: !isGridView ? "#fff" : "#222",
              border: "none",
              padding: "0 14px",
              fontWeight: 600,
              fontSize: 18,
              height: 38,
              cursor: "pointer",
              outline: "none",
              borderLeft: "1px solid #e0e7ef",
              display: "flex",
              alignItems: "center",
              borderRadius: 0
            }}
            onClick={onListView}
          >
            <span style={{ fontSize: 18, verticalAlign: "middle" }}>≡</span>
          </button>
        </div>
        {/* Settings Button */}
        <button
          style={{
            height: 38,
            padding: "0 22px",
            borderRadius: 8,
            border: "1px solid #ddd",
            background: "#fff",
            fontWeight: 500,
            fontSize: 16,
            color: "#222",
            cursor: "pointer"
          }}
          onClick={onSettings}
        >
          Settings
        </button>
        {/* Export to LMS Button */}
        <button
          style={{
            height: 38,
            padding: "0 22px",
            borderRadius: 8,
            border: "none",
            background: "#2563eb",
            fontWeight: 500,
            fontSize: 16,
            color: "#fff",
            cursor: "pointer"
          }}
          onClick={onExport}
        >
          Export to LMS
        </button>
        {/* Logout Button */}
        <button
          onClick={onLogout}
          style={{ display: "flex", alignItems: "center", gap: 8, background: "none", border: "none", color: "#222", fontWeight: 500, fontSize: 16, cursor: "pointer", padding: 0 }}
        >
          <FaUserCircle style={{ fontSize: 26, color: "#2563eb" }} /> Logout
        </button>
      </div>
    </header>
  );
} 