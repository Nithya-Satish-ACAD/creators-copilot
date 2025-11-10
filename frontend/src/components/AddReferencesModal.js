import React, { useState, useRef } from 'react';
import { FiUploadCloud, FiSearch, FiTrash2, FiAlertCircle } from 'react-icons/fi';
import Modal from './Modal';

export default function AddResourceModal({ open, onClose, onAdd }) {
  const [step, setStep] = useState(1); // 1: choose, 2: upload, 3: discover
  const [files, setFiles] = useState([]); // uploaded files
  const [discovered, setDiscovered] = useState([]); // discovered files (placeholder)
  const [errors, setErrors] = useState([]); // file validation errors
  const fileInputRef = useRef();

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

  // Handle file selection
  const handleFiles = (fileList) => {
    const newFiles = Array.from(fileList);
    const newErrors = [];
    const validFiles = [];

    newFiles.forEach(file => {
      const validation = validateFile(file);
      if (validation.isValid) {
        validFiles.push(file);
      } else {
        newErrors.push({
          fileName: file.name,
          error: validation.error
        });
      }
    });

    if (newErrors.length > 0) {
      setErrors(prev => [...prev, ...newErrors]);
    }

    if (validFiles.length > 0) {
      setFiles(prev => [...prev, ...validFiles]);
    }
  };

  // Handle drag and drop
  const handleDrop = (e) => {
    e.preventDefault();
    handleFiles(e.dataTransfer.files);
  };

  // Remove file
  const handleDelete = (idx) => {
    setFiles(prev => prev.filter((_, i) => i !== idx));
  };

  // Remove error
  const handleDeleteError = (idx) => {
    setErrors(prev => prev.filter((_, i) => i !== idx));
  };

  // Reset state on close
  const handleClose = () => {
    setStep(1);
    setFiles([]);
    setDiscovered([]);
    setErrors([]);
    onClose();
  };

  // Step 1: Choose Upload or Discover
  if (!open) return null;
  if (step === 1) {
    return (
      <Modal open={open} onClose={handleClose}>
        <h2 style={{ fontSize: 20, fontWeight: 600, marginBottom: 8 }}>Add Resources</h2>
        <p style={{ color: '#555', fontSize: 14, marginBottom: 24 }}>
          Add resources from the web or course documents you’ve already created — this helps AI give relevant results.
        </p>
        <div style={{ display: 'flex', gap: 24, marginBottom: 32 }}>
          <button
            style={{
              flex: 1,
              border: '1.5px solid #e5e7eb',
              borderRadius: 12,
              background: '#fafbfc',
              padding: '32px 0',
              display: 'flex', flexDirection: 'column', alignItems: 'center',
              cursor: 'pointer', fontSize: 17, fontWeight: 500,
              position: 'relative'
            }}
            onClick={() => setStep(2)}
          >
            <FiUploadCloud size={36} style={{ marginBottom: 12, color: '#2563eb' }} />
            Upload
            {files.length > 0 && (
              <div style={{ color: '#2563eb', fontSize: 14, fontWeight: 500, marginTop: 10 }}>
                {files.length} file{files.length > 1 ? 's' : ''} uploaded
              </div>
            )}
          </button>
          <button
            style={{
              flex: 1,
              border: '1.5px solid #e5e7eb',
              borderRadius: 12,
              background: '#fafbfc',
              padding: '32px 0',
              display: 'flex', flexDirection: 'column', alignItems: 'center',
              cursor: 'pointer', fontSize: 17, fontWeight: 500,
              position: 'relative'
            }}
            onClick={() => setStep(3)}
          >
            <FiSearch size={36} style={{ marginBottom: 12, color: '#2563eb' }} />
            Discover
            <span style={{
              position: 'absolute',
              top: 12, right: 18,
              background: '#2563eb', color: '#fff', borderRadius: '50%',
              fontSize: 13, fontWeight: 600, width: 22, height: 22, display: discovered.length > 0 ? 'flex' : 'none', alignItems: 'center', justifyContent: 'center'
            }}>{discovered.length}</span>
          </button>
        </div>
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
          <button onClick={handleClose} style={{ padding: '8px 16px', fontSize: 15, borderRadius: 6, border: '1px solid #ccc', background: '#fff', cursor: 'pointer' }}>Close</button>
        </div>
      </Modal>
    );
  }

  // Step 2: Upload
  if (step === 2) {
    return (
      <Modal open={open} onClose={handleClose}>
        <h3 style={{ fontSize: 18, fontWeight: 600, marginBottom: 8 }}>Upload</h3>
        <div
          onDrop={handleDrop}
          onDragOver={e => e.preventDefault()}
          style={{
            border: '2px dashed #cbd5e1',
            borderRadius: 12,
            padding: '32px 0',
            textAlign: 'center',
            marginBottom: 18,
            background: '#fafbfc',
            cursor: 'pointer'
          }}
          onClick={() => fileInputRef.current.click()}
        >
          <FiUploadCloud size={32} style={{ color: '#2563eb', marginBottom: 8 }} />
          <div style={{ fontSize: 15, marginBottom: 6 }}>Drag and drop or <span style={{ color: '#2563eb', textDecoration: 'underline' }}>browse</span> files to upload</div>
          <div style={{ color: '#888', fontSize: 13, marginBottom: 4 }}>Accepted formats: <span style={{ color: '#2563eb' }}>.pdf .docx .txt .md .xlsx .pptx .py .js .html .css .json</span></div>
          <input
            type="file"
            multiple
            ref={fileInputRef}
            style={{ display: 'none' }}
            onChange={e => handleFiles(e.target.files)}
            accept={SUPPORTED_FILE_TYPES.join(',')}
          />
        </div>
        <div style={{ marginBottom: 18 }}>
          {files.length > 0 && (
            <div style={{ marginBottom: 8, fontWeight: 500, fontSize: 15 }}>Valid files ({files.length})</div>
          )}
          {files.map((file, idx) => (
            <div key={idx} style={{ display: 'flex', alignItems: 'center', marginBottom: 8, background: '#f4f6f8', borderRadius: 6, padding: '6px 10px' }}>
              <span style={{ flex: 1, wordBreak: 'break-all', fontSize: 15 }}>{file.name}</span>
              <button onClick={() => handleDelete(idx)} style={{ background: 'none', border: 'none', color: '#d32f2f', cursor: 'pointer', marginLeft: 8 }}><FiTrash2 size={18} /></button>
            </div>
          ))}
          
          {errors.length > 0 && (
            <div style={{ marginTop: 16 }}>
              <div style={{ marginBottom: 8, fontWeight: 500, fontSize: 15, color: '#d32f2f' }}>Unsupported files ({errors.length})</div>
              {errors.map((error, idx) => (
                <div key={idx} style={{ display: 'flex', alignItems: 'center', marginBottom: 8, background: '#ffebee', borderRadius: 6, padding: '6px 10px', border: '1px solid #ffcdd2' }}>
                  <FiAlertCircle size={16} style={{ color: '#d32f2f', marginRight: 8 }} />
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 14, fontWeight: 500, color: '#d32f2f' }}>{error.fileName}</div>
                    <div style={{ fontSize: 12, color: '#c62828' }}>{error.error}</div>
                  </div>
                  <button onClick={() => handleDeleteError(idx)} style={{ background: 'none', border: 'none', color: '#d32f2f', cursor: 'pointer', marginLeft: 8 }}><FiTrash2 size={16} /></button>
                </div>
              ))}
            </div>
          )}
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10 }}>
          <button onClick={() => setStep(1)} style={{ padding: '8px 16px', fontSize: 15, borderRadius: 6, border: '1px solid #ccc', background: '#fff', cursor: 'pointer' }}>Back</button>
          <button onClick={() => { onAdd(files); handleClose(); }} style={{ padding: '8px 16px', fontSize: 15, borderRadius: 6, border: 'none', background: '#2563eb', color: '#fff', fontWeight: 600, cursor: 'pointer' }} disabled={files.length === 0}>Add Resource</button>
        </div>
      </Modal>
    );
  }

  // Step 3: Discover (placeholder)
  if (step === 3) {
    return (
      <Modal open={open} onClose={handleClose}>
        <h3 style={{ fontSize: 18, fontWeight: 600, marginBottom: 8 }}>Discover</h3>
        <div style={{ padding: '32px 0', textAlign: 'center', color: '#888', fontSize: 15 }}>
          Discover feature coming soon.
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10 }}>
          <button onClick={() => setStep(1)} style={{ padding: '8px 16px', fontSize: 15, borderRadius: 6, border: '1px solid #ccc', background: '#fff', cursor: 'pointer' }}>Back to Add Resources</button>
          <button onClick={handleClose} style={{ padding: '8px 16px', fontSize: 15, borderRadius: 6, border: 'none', background: '#e0e7ef', color: '#888', fontWeight: 600, cursor: 'pointer' }}>Cancel</button>
        </div>
      </Modal>
    );
  }
  return null;
} 