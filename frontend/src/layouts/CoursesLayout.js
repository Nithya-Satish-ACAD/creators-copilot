import React from "react";
import { FaUserCircle } from "react-icons/fa";
import { useNavigate } from "react-router-dom";

export default function CoursesLayout({ onAddCourse, onLogout, children }) {
  const navigate = useNavigate();
  return (
    <>
      {/* Header Bar */}
      <div style={{
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
        <div 
          style={{ display: "flex", alignItems: "center", gap: 16, cursor: "pointer" }}
          onClick={() => navigate('/courses')}
        >
          <img 
            src="/favicon.svg" 
            alt="Course Copilot Logo" 
            style={{
              width: 40,
              height: 40,
              marginRight: 14,
            }}
          />
          <span style={{ fontWeight: 700, fontSize: 22, color: "#222", letterSpacing: 0.5 }}>Course Copilot</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
          <button
            onClick={onAddCourse}
            style={{
              background: '#2563eb',
              color: '#fff',
              border: 'none',
              borderRadius: 8,
              padding: '10px 26px',
              fontWeight: 600,
              fontSize: 16,
              boxShadow: '0 2px 8px #2563eb22',
              cursor: 'pointer'
            }}
          >
            Add Course
          </button>
          <button
            onClick={onLogout}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              background: "none",
              border: "none",
              color: "#222",
              fontWeight: 500,
              fontSize: 16,
              cursor: "pointer",
              padding: 0
            }}
          >
            <FaUserCircle style={{ fontSize: 26, color: "#2563eb" }} /> Logout
          </button>
        </div>
      </div>

      {/* Dynamic Page Content */}
      <div style={{ flex: 1, overflowY: 'auto', overflowX: 'hidden', minHeight: 0, width: '100%' }}>
        {children}
      </div>
    </>
  );
}
