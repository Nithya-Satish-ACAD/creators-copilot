import React from "react";
import Modal from "./Modal";
import { FaRegStar, FaStar } from "react-icons/fa";
import { generateCourseDescription } from "../services/course";
import './CourseModal.css';

export default function CourseModal({
  open, onClose,
  courseName, setCourseName,
  courseDesc, setCourseDesc,
  onSubmit, loading, error
}) {
  const [clicked, setClicked] = React.useState(false);
  const [isGenerating, setIsGenerating] = React.useState(false);
  const [starClicked, setStarClicked] = React.useState(false);

  React.useEffect(() => {
    if (!open) {
      setClicked(false);
      setIsGenerating(false);
      setStarClicked(false);
      // Reset form fields when modal closes
      setCourseName("");
      setCourseDesc("");
    }
  }, [open, setCourseName, setCourseDesc]);

  React.useEffect(() => {
    if (!loading) setClicked(false);
  }, [loading]);

  const handleStarClick = async () => {
    if (!courseName.trim() || isGenerating) return;
    
    setIsGenerating(true);
    setStarClicked(true);
    
    try {
      const generatedDescription = await generateCourseDescription(courseDesc, courseName);
      setCourseDesc(generatedDescription);
    } catch (error) {
      alert(`Failed to generate description: ${error.response?.data?.detail || error.message}`);
    } finally {
      setIsGenerating(false);
    }
  };

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
              onClick={handleStarClick}
              disabled={!courseName.trim() || isGenerating}
              style={{ 
                background: "none", 
                border: "none", 
                cursor: (!courseName.trim() || isGenerating) ? "not-allowed" : "pointer", 
                color: starClicked ? "#3b82f6" : "#2563eb", 
                fontSize: 20, 
                padding: 0, 
                marginLeft: 8,
                opacity: (!courseName.trim() || isGenerating) ? 0.5 : 1,
                transition: "color 0.3s ease"
              }}
              title={isGenerating ? "Generating..." : "AI Sparkle"}
            >
              {isGenerating ? (
                <div style={{
                  width: 20,
                  height: 20,
                  border: "2px solid #3b82f6",
                  borderTop: "2px solid transparent",
                  borderRadius: "50%",
                  animation: "spin 1s linear infinite"
                }} />
              ) : starClicked ? (
                <FaStar />
              ) : (
                <FaRegStar />
              )}
            </button>
          </div>
          <div style={{ position: 'relative', marginBottom: 32 }}>
            <textarea
              placeholder={isGenerating ? "Generating course description..." : "Describe your course audience, topics, projects etc."}
              value={courseDesc}
              onChange={e => setCourseDesc(e.target.value)}
              disabled={isGenerating}
              style={{
                width: "100%",
                minHeight: 90,
                padding: "12px 14px",
                fontSize: 15,
                borderRadius: 10,
                border: isGenerating ? "1.5px solid #3b82f6" : "1.5px solid #e5e7eb",
                resize: "vertical",
                outline: 'none',
                background: isGenerating ? '#eff6ff' : '#fafbfc',
                transition: 'border 0.18s, background 0.18s',
                opacity: isGenerating ? 0.8 : 1
              }}
              onFocus={e => !isGenerating && (e.target.style.border = '1.5px solid #2563eb')}
              onBlur={e => !isGenerating && (e.target.style.border = '1.5px solid #e5e7eb')}
              required
            />
            {isGenerating && (
              <div style={{
                position: 'absolute',
                top: '50%',
                left: '50%',
                transform: 'translate(-50%, -50%)',
                color: '#3b82f6',
                fontSize: 14,
                fontWeight: 500,
                pointerEvents: 'none',
                background: 'rgba(255, 255, 255, 0.9)',
                padding: '4px 8px',
                borderRadius: '4px'
              }}>
                ✨ Generating description...
              </div>
            )}
          </div>
          {error && <div style={{ color: "#e11d48", marginBottom: 10, textAlign: 'center', fontWeight: 500 }}>{error}</div>}
          <div style={{ display: "flex", justifyContent: "flex-end", gap: 12, marginTop: 8 }}>
            <button onClick={onClose} style={{ padding: "9px 22px", borderRadius: 8, border: "1.5px solid #e5e7eb", background: "#fff", fontSize: 15, color: '#222', fontWeight: 500, transition: 'border 0.18s, background 0.18s', cursor: 'pointer' }}>Close</button>
            <button onClick={() => { if (!loading && !clicked) { setClicked(true); onSubmit(); } }} disabled={!courseName.trim() || !courseDesc.trim() || loading || clicked}
              style={{
                padding: "9px 22px",
                borderRadius: 8,
                border: "none",
                background: (!courseName || !courseDesc || loading || clicked) ? "#b6cdfa" : "#2563eb",
                color: "#fff",
                fontSize: 15,
                fontWeight: 600,
                cursor: (!courseName || !courseDesc || loading || clicked) ? 'not-allowed' : 'pointer',
                boxShadow: (!courseName || !courseDesc || loading || clicked) ? 'none' : '0 2px 8px #2563eb22',
                transition: 'background 0.18s, box-shadow 0.18s',
                display: 'inline-flex',
                alignItems: 'center',
                gap: 8
              }}>
              {(loading || clicked) && (
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
              <span>{(loading || clicked) ? 'Creating...' : 'Get Started'}</span>
              <style>{`
                @keyframes spin { 
                  0% { transform: rotate(0deg); } 
                  100% { transform: rotate(360deg); } 
                }
                @keyframes pulse {
                  0%, 100% { opacity: 1; }
                  50% { opacity: 0.5; }
                }
              `}</style>
            </button>
          </div>
        </div>
      </Modal>
    </>
  );
}
