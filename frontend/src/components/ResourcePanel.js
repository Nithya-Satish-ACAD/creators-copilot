import React, { useState } from "react";

function ResourcePanel({ onFileSelect }) {
  const [files, setFiles] = useState([]);

  const handleFileUpload = async (e) => {
    const selectedFiles = Array.from(e.target.files);
    
    // Placeholder: show names immediately. We'll replace with real file_id later.
    const newFiles = selectedFiles.map(file => ({
      id: `${file.name}-${Date.now()}`, // temporary id
      name: file.name,
      selected: false,
      fileObject: file // save for upload later
    }));

    const updatedFiles = [...files, ...newFiles];
    setFiles(updatedFiles);

    // Optionally notify parent
    onFileSelect && onFileSelect(updatedFiles);
  };

  const toggleFileSelection = (id) => {
    const updated = files.map(f =>
      f.id === id ? { ...f, selected: !f.selected } : f
    );
    setFiles(updated);
    onFileSelect && onFileSelect(updated);
  };

  return (
    <div style={panelStyle}>
      <h3 style={{ fontWeight: 600, marginBottom: "1rem", display: "flex", alignItems: "center" }}>
        <span style={{ fontSize: "1.25rem", marginRight: "8px" }}>📚</span>
        Resources
        </h3>
      <input type="file" multiple onChange={handleFileUpload} style={{ marginBottom: "1rem" }} value="" />
      {files.length === 0 && <p style={{ color: "#888" }}>No files uploaded yet.</p>}

      <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
        {files.map(file => (
            <li key={file.id} style={{
            display: "flex",
            alignItems: "center",
            padding: "10px",
            marginBottom: "10px",
            background: "#fff",
            borderRadius: "8px",
            boxShadow: "0 2px 5px rgba(0,0,0,0.05)"
            }}>
            <input
                type="checkbox"
                checked={file.selected}
                onChange={() => toggleFileSelection(file.id)}
                style={{
                width: "18px",
                height: "18px",
                marginRight: "12px",
                accentColor: "#6C63FF"
                }}
            />
            <span style={{
                fontSize: "0.8rem",
                wordBreak: "break-word",
                whiteSpace: "normal",
                maxWidth: "200px",
                display: "inline-block"
                }}>
                📄 {file.name}
                </span>
            </li>
        ))}
        </ul>

    </div>
  );
}

const panelStyle = {
  width: "280px",
  padding: "1rem",
  borderLeft: "1px solid #eee",
  background: "#fafafa",
  height: "100vh",
  overflowY: "auto",
  position: "fixed",
  right: 0,
  top: 0
};

export default ResourcePanel;
