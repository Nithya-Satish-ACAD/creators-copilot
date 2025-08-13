import React, { useState, useRef, useEffect } from "react";
import { FiMoreVertical } from "react-icons/fi";
import { uploadCourseResources } from "../services/resources";
// import { getResourceViewUrl, viewResourceFile, downloadResourceFile } from '../services/resources';

export default function KnowledgeBase({
  resources = [],
  fileInputRef,
  onFileChange,
  showCheckboxes = false, // 🔁 Controls checkbox display
  selected = [],
  onSelect = () => {},
  onSelectAll = () => {},
  onDelete = () => {}, // Callback to refresh resources after deletion
  onAddResource, // <-- new prop
  courseId // <-- add courseId prop
}) {
  const [menuOpenId, setMenuOpenId] = useState(null);
  const menuRef = useRef(null);
  const [deletingId, setDeletingId] = useState(null);
  // const [loadingViewId, setLoadingViewId] = useState(null);
  // const [loadingDownloadId, setLoadingDownloadId] = useState(null);

  // Close menu on outside click
  useEffect(() => {
    if (menuOpenId === null) return;
    function handleClick(e) {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setMenuOpenId(null);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [menuOpenId]);

  const toggleMenu = (id) => {
    setMenuOpenId(menuOpenId === id ? null : id);
  };

  const handleCheckboxToggle = (id) => {
    if (!onSelect) return;
    onSelect(id);
  };

  const handleFileUpload = async (event) => {
    const files = Array.from(event.target.files);
    if (files.length === 0) return;

    try {
      const courseId = localStorage.getItem('currentCourseId');

      // Call the upload API
      await uploadCourseResources(courseId, files);
      
      // Clear the file input
      event.target.value = '';
      
      // Call the onFileChange callback to refresh the resources list
      if (onFileChange) {
        onFileChange(event);
      }
      
      console.log(`Successfully uploaded ${files.length} file(s)`);
    } catch (error) {
      console.error('Error uploading files:', error);
      alert(`Failed to upload files: ${error.message}`);
    }
  };

  return (
    <div style={{
      background: "#fff",
      borderRadius: 12,
      boxShadow: "0 1px 4px #0001",
      padding: 18,
      minHeight: '60vh',
      maxHeight: '65vh',
      overflowY: 'auto'
    }}>
      <div style={{ fontWeight: 600, fontSize: 16, marginBottom: 4 }}>Knowledge Base</div>
      <div style={{ color: "#888", fontSize: 13, marginBottom: 10 }}>
        Add resources from the web or course documents you’ve already created — this helps AI give relevant results.
      </div>

      <input
        type="file"
        ref={fileInputRef}
        style={{ display: "none" }}
        multiple
        onChange={handleFileUpload}
      />

      <button
        style={{
          width: "100%",
          marginBottom: 12,
          padding: "8px 0",
          borderRadius: 6,
          border: "1px solid #bbb",
          background: "#fff",
          fontWeight: 500,
          fontSize: 15,
          cursor: "pointer"
        }}
        onClick={onAddResource}
      >
        Add Resource
      </button>

      {showCheckboxes && (
        <div style={{ marginBottom: 8 }}>
          <label style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            fontWeight: 500,
            fontSize: 14
          }}>
            <input
              type="checkbox"
              checked={selected.length === resources.length && resources.length > 0}
              onChange={(e) => {
                const allIds = resources.map(
                  (res, i) => res.id || res.resourceName || res.fileName || i
                );
                if (e.target.checked) {
                  onSelectAll(allIds);
                } else {
                  onSelectAll([]);
                }
              }}
            />
            Select All References
          </label>
        </div>
      )}

      <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
        {resources.length === 0 ? (
          <li style={{ color: '#888' }}>No resources uploaded yet.</li>
        ) : (
          resources.map((res, i) => {
            const id = res.id || res.resourceName || res.fileName || i;
            return (
              <li key={id} style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "7px 0",
                borderBottom: i < resources.length - 1 ? "1px solid #f0f0f0" : "none",
                position: "relative"
              }}>
                <label style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                  fontSize: 15,
                  flex: 1
                }}>
                  {showCheckboxes && (
                    <input
                      type="checkbox"
                      checked={selected.includes(id)}
                      onChange={() => handleCheckboxToggle(id)}
                    />
                  )}
                  <span>📄</span>
                  <span style={{ flex: 1, wordBreak: 'break-all', whiteSpace: 'pre-wrap' }}>{res.resourceName || res.fileName || res.title}</span>
                </label>

                {/* Three-dot menu */}
                <div style={{ position: "relative" }} ref={menuOpenId === id ? menuRef : null}>
                  <FiMoreVertical
                    style={{ cursor: "pointer", fontSize: 18 }}
                    onClick={() => toggleMenu(id)}
                  />
                  {menuOpenId === id && (
                    <ul style={{
                      position: "absolute",
                      top: 24,
                      right: 0,
                      background: "#fff",
                      border: "1px solid #ddd",
                      boxShadow: "0 2px 6px rgba(0,0,0,0.1)",
                      borderRadius: 6,
                      padding: "6px 0",
                      width: 120,
                      zIndex: 10,
                      fontSize: 14,
                      listStyleType: "none"
                    }}>
                      <li
                        style={{ ...menuItemStyle, color: "#d32f2f", cursor: deletingId === id ? "wait" : "pointer", opacity: deletingId === id ? 0.6 : 1 }}
                        onClick={async (e) => {
                          e.stopPropagation();
                          if (deletingId === id) return;
                          setDeletingId(id);
                          try {
                            await onDelete(id);
                            setMenuOpenId(null);
                          } finally {
                            setDeletingId(null);
                          }
                        }}
                      >
                        Delete
                      </li>
                    </ul>
                  )}
                </div>
              </li>
            );
          })
        )}
      </ul>
    </div>
  );
}

const menuItemStyle = {
  padding: "6px 12px",
  whiteSpace: "nowrap",
  cursor: "pointer"
};

// const linkStyle = {
//   color: "#222",
//   textDecoration: "none"
// };
