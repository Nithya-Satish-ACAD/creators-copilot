import React from "react";
import Modal from "./Modal";
import { FaRegStar } from "react-icons/fa";
import './CourseModal.css';

export default function CourseModal({
  open, onClose,
  courseName, setCourseName,
  courseDesc, setCourseDesc,
  onSubmit, loading, error
}) {
  return (
    <>
      <Modal open={open} onClose={onClose} modalStyle={{ minWidth: 0, maxWidth: 800, width: '100%', borderRadius: 18, boxShadow: '0 8px 32px rgba(37,99,235,0.10)', background: '#fff', padding: 0 }}>
        <div style={{ padding: '36px 48px 32px 48px', borderRadius: 18 }}>
          <div style={{ fontWeight: 800, fontSize: 26, marginBottom: 28, letterSpacing: 0.2, textAlign: 'center', color: '#2563eb !important' }}>Create Course</div>
          <div style={{ fontWeight: 600, fontSize: 15, marginBottom: 10 }}>Course Name</div>
          <input
            type="text"
            placeholder="e.g. Introduction to Python"
            value={courseName}
            onChange={e => setCourseName(e.target.value)}
            style={{
              width: "100%",
              padding: "12px 14px",
              fontSize: 16,
              borderRadius: 10,
              border: "1.5px solid #e5e7eb",
              marginBottom: 24,
              outline: 'none',
              background: '#fafbfc',
              transition: 'border 0.18s',
            }}
            onFocus={e => e.target.style.border = '1.5px solid #2563eb'}
            onBlur={e => e.target.style.border = '1.5px solid #e5e7eb'}
            required
          />
          <div style={{ fontWeight: 600, fontSize: 15, marginBottom: 10, display: "flex", justifyContent: "space-between", alignItems: 'center' }}>
            <span>About the course</span>
            <button
              type="button"
              style={{ background: "none", border: "none", cursor: "pointer", color: "#2563eb", fontSize: 20, padding: 0, marginLeft: 8 }}
              title="AI Sparkle"
            >
              <FaRegStar />
            </button>
          </div>
          <textarea
            placeholder="Describe your course audience, topics, projects etc."
            value={courseDesc}
            onChange={e => setCourseDesc(e.target.value)}
            style={{
              width: "100%",
              minHeight: 90,
              padding: "12px 14px",
              fontSize: 15,
              borderRadius: 10,
              border: "1.5px solid #e5e7eb",
              resize: "vertical",
              marginBottom: 32,
              outline: 'none',
              background: '#fafbfc',
              transition: 'border 0.18s',
            }}
            onFocus={e => e.target.style.border = '1.5px solid #2563eb'}
            onBlur={e => e.target.style.border = '1.5px solid #e5e7eb'}
            required
          />
          {error && <div style={{ color: "#e11d48", marginBottom: 10, textAlign: 'center', fontWeight: 500 }}>{error}</div>}
          <div style={{ display: "flex", justifyContent: "flex-end", gap: 12, marginTop: 8 }}>
            <button onClick={onClose} style={{ padding: "9px 22px", borderRadius: 8, border: "1.5px solid #e5e7eb", background: "#fff", fontSize: 15, color: '#222', fontWeight: 500, transition: 'border 0.18s, background 0.18s', cursor: 'pointer' }}>Close</button>
            <button onClick={onSubmit} disabled={!courseName.trim() || !courseDesc.trim() || loading}
              style={{
                padding: "9px 22px",
                borderRadius: 8,
                border: "none",
                background: (!courseName || !courseDesc || loading) ? "#b6cdfa" : "#2563eb",
                color: "#fff",
                fontSize: 15,
                fontWeight: 600,
                cursor: (!courseName || !courseDesc || loading) ? 'not-allowed' : 'pointer',
                boxShadow: (!courseName || !courseDesc || loading) ? 'none' : '0 2px 8px #2563eb22',
                transition: 'background 0.18s, box-shadow 0.18s',
                display: 'inline-flex',
                alignItems: 'center',
                gap: 8
              }}>
              {loading && (
                <span
                  aria-hidden
                  style={{
                    width: 14,
                    height: 14,
                    border: '2px solid rgba(255,255,255,0.6)',
                    borderTop: '2px solid #fff',
                    borderRadius: '50%',
                    animation: 'spin 0.8s linear infinite'
                  }}
                />
              )}
              <span>{loading ? 'Creating...' : 'Get Started'}</span>
              <style>{`@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`}</style>
            </button>
          </div>
        </div>
      </Modal>
    </>
  );
}
