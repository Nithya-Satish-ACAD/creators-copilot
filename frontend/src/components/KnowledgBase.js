import React, { useState, useRef, useEffect } from "react";
import ReactDOM from "react-dom";
import { FiMoreVertical, FiAlertCircle } from "react-icons/fi";
import { uploadCourseResources } from "../services/resources";
import ResourceViewModal from "./ResourceViewModal";
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
  courseId, // <-- add courseId prop
  isUploading = false // <-- new prop for upload loading state
}) {
  const [menuOpenId, setMenuOpenId] = useState(null);
  const menuRef = useRef(null);
  const buttonRefs = useRef({});
  const [deletingId, setDeletingId] = useState(null);
  const [showViewModal, setShowViewModal] = useState(false);
  const [selectedResource, setSelectedResource] = useState(null);
  const [buttonPosition, setButtonPosition] = useState({ top: 0, left: 0 });
  const [uploadErrors, setUploadErrors] = useState([]);
  // const [loadingViewId, setLoadingViewId] = useState(null);
  // const [loadingDownloadId, setLoadingDownloadId] = useState(null);

  // Supported file types for OpenAI Assistants API
  const SUPPORTED_FILE_TYPES = [
    // Documents
    '.pdf', '.txt', '.md', '.docx',
    // Spreadsheets
    '.xlsx', '.csv',
    // Presentations
    '.pptx',
    // Code files
    '.py', '.js', '.html', '.css', '.json',
    // Additional common formats
    '.rtf', '.odt'
  ];

  const SUPPORTED_MIME_TYPES = [
    'application/pdf',
    'text/plain',
    'text/markdown',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'text/csv',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'text/javascript',
    'text/html',
    'text/css',
    'application/json',
    'application/rtf',
    'application/vnd.oasis.opendocument.text',
    'text/x-python'
  ];

  // Validate file type
  const validateFile = (file) => {
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    const isValidExtension = SUPPORTED_FILE_TYPES.includes(fileExtension);
    const isValidMimeType = SUPPORTED_MIME_TYPES.includes(file.type);
    
    return {
      isValid: isValidExtension && isValidMimeType,
      error: !isValidExtension ? `File type ${fileExtension} is not supported` : 
             !isValidMimeType ? `File MIME type ${file.type} is not supported` : null
    };
  };

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

  const toggleMenu = (id, event) => {
    if (menuOpenId === id) {
      setMenuOpenId(null);
    } else {
      const button = buttonRefs.current[id];
      if (button) {
        const rect = button.getBoundingClientRect();
        setButtonPosition({
          top: rect.bottom + window.scrollY,
          left: rect.right - 120 + window.scrollX // 120 is dropdown width
        });
      }
      setMenuOpenId(id);
    }
  };

  const handleCheckboxToggle = (id) => {
    if (!onSelect) return;
    onSelect(id);
  };

  const handleViewResource = (resource) => {
    console.log('View resource clicked:', resource);
    console.log('CourseId available:', courseId);
    console.log('Setting showViewModal to true');
    setSelectedResource(resource);
    setShowViewModal(true);
    setMenuOpenId(null);
  };

  const handleFileUpload = async (event) => {
    const files = Array.from(event.target.files);
    if (files.length === 0) return;

    // Validate files before upload
    const validFiles = [];
    const errors = [];

    files.forEach(file => {
      const validation = validateFile(file);
      if (validation.isValid) {
        validFiles.push(file);
      } else {
        errors.push({
          fileName: file.name,
          error: validation.error
        });
      }
    });

    // Show errors if any
    if (errors.length > 0) {
      setUploadErrors(errors);
      // Clear errors after 5 seconds
      setTimeout(() => setUploadErrors([]), 5000);
    }

    // Only upload valid files
    if (validFiles.length === 0) {
      event.target.value = '';
      return;
    }

    try {
      const courseId = localStorage.getItem('currentCourseId');

      // Call the upload API with only valid files
      await uploadCourseResources(courseId, validFiles);
      
      // Clear the file input
      event.target.value = '';
      
      // Call the onFileChange callback to refresh the resources list
      if (onFileChange) {
        onFileChange(event);
      }
      
    } catch (error) {
      console.error('Error uploading files:', error);
      alert(`Failed to upload files: ${error.message}`);
    }
  };

  return (
    <>
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
      <div style={{
        background: "#fff",
        borderRadius: 12,
        boxShadow: "0 1px 4px #0001",
        padding: 18,
        minHeight: '60vh',
        maxHeight: '65vh',
        overflowY: 'auto',
        overflowX: 'visible',
        position: 'relative'
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
        accept={SUPPORTED_FILE_TYPES.join(',')}
      />

      <button
        style={{
          width: "100%",
          marginBottom: 12,
          padding: "8px 0",
          borderRadius: 6,
          border: "1px solid #bbb",
          background: isUploading ? "#f5f5f5" : "#fff",
          fontWeight: 500,
          fontSize: 15,
          cursor: isUploading ? "not-allowed" : "pointer",
          opacity: isUploading ? 0.6 : 1
        }}
        onClick={onAddResource}
        disabled={isUploading}
      >
        {isUploading ? "Uploading..." : "Add Resource"}
      </button>

      {/* Upload Progress Indicator */}
      {isUploading && (
        <div style={{
          marginBottom: 12,
          padding: "8px 12px",
          background: "#f0f9ff",
          border: "1px solid #0ea5e9",
          borderRadius: 6,
          fontSize: 14,
          color: "#0369a1",
          display: "flex",
          alignItems: "center",
          gap: 8
        }}>
          <div style={{
            width: 16,
            height: 16,
            border: "2px solid #0ea5e9",
            borderTop: "2px solid transparent",
            borderRadius: "50%",
            animation: "spin 1s linear infinite"
          }} />
          Uploading resources...
        </div>
      )}

      {/* Upload Errors */}
      {uploadErrors.length > 0 && (
        <div style={{ marginBottom: 12 }}>
          <div style={{
            padding: "8px 12px",
            background: "#ffebee",
            border: "1px solid #ffcdd2",
            borderRadius: 6,
            fontSize: 14,
            color: "#c62828",
            marginBottom: 8
          }}>
            <div style={{ fontWeight: 500, marginBottom: 4 }}>
              <FiAlertCircle style={{ marginRight: 6, verticalAlign: 'middle' }} />
              Unsupported files ({uploadErrors.length})
            </div>
            <div style={{ fontSize: 12 }}>
              These file types are not supported by OpenAI Assistants API
            </div>
          </div>
          {uploadErrors.map((error, idx) => (
            <div key={idx} style={{
              padding: "6px 12px",
              background: "#fff5f5",
              border: "1px solid #fecaca",
              borderRadius: 4,
              fontSize: 12,
              color: "#dc2626",
              marginBottom: 4
            }}>
              <strong>{error.fileName}:</strong> {error.error}
            </div>
          ))}
        </div>
      )}

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
                <div style={{ position: "relative" }}>
                  <FiMoreVertical
                    ref={el => buttonRefs.current[id] = el}
                    style={{ cursor: "pointer", fontSize: 18 }}
                    onClick={(e) => toggleMenu(id, e)}
                  />
                </div>
              </li>
            );
          })
        )}
      </ul>
      </div>

      {/* Portal-based dropdown */}
      {menuOpenId && ReactDOM.createPortal(
        <div
          ref={menuRef}
          style={{
            position: "fixed",
            top: buttonPosition.top,
            left: buttonPosition.left,
            background: "#fff",
            border: "1px solid #ddd",
            boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
            borderRadius: 6,
            padding: "6px 0",
            width: 120,
            zIndex: 99999,
            fontSize: 14,
            listStyleType: "none"
          }}
        >
          <div
            style={{ ...menuItemStyle, color: "#2563eb", cursor: "pointer" }}
            onClick={(e) => {
              e.stopPropagation();
              const selectedRes = resources.find(res => (res.id || res.resourceName || res.fileName) === menuOpenId);
              if (selectedRes) {
                handleViewResource(selectedRes.resourceName || selectedRes.fileName || selectedRes.name);
              }
              setMenuOpenId(null);
            }}
          >
            View
          </div>
          <div
            style={{ ...menuItemStyle, color: "#d32f2f", cursor: deletingId === menuOpenId ? "wait" : "pointer", opacity: deletingId === menuOpenId ? 0.6 : 1 }}
            onClick={async (e) => {
              e.stopPropagation();
              if (deletingId === menuOpenId) return;
              setDeletingId(menuOpenId);
              try {
                await onDelete(menuOpenId);
                setMenuOpenId(null);
              } finally {
                setDeletingId(null);
              }
            }}
          >
            Delete
          </div>
        </div>,
        document.body
      )}

      {/* Resource View Modal */}
      <ResourceViewModal
        open={showViewModal}
        onClose={() => {
          setShowViewModal(false);
          setSelectedResource(null);
        }}
        resourceName={selectedResource}
        courseId={courseId}
      />
    </>
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
