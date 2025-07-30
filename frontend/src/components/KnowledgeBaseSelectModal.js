import React, { useState } from 'react';
import Modal from './Modal'; // Keep your existing modal structure
import { FiCheckSquare, FiSquare } from "react-icons/fi";

export default function KnowledgeBaseSelectModal({ open, onClose, onGenerate, files }) {
  const [selected, setSelected] = useState([]);

  const handleToggle = (file) => {
    setSelected((prev) =>
      prev.includes(file) ? prev.filter(f => f !== file) : [...prev, file]
    );
  };

  const handleGenerate = () => {
    onGenerate(selected);
    setSelected([]); // reset
  };

  if (!open) return null;

  return (
    <Modal open={open} onClose={onClose}>
      <div style={{
        background: '#fff',
        padding: '28px',
        borderRadius: '16px',
        boxShadow: '0 12px 40px rgba(0,0,0,0.1)',
        maxWidth: 520,
        margin: 'auto',
        fontFamily: 'Inter, sans-serif'
      }}>
        <h2 style={{
          fontSize: '20px',
          fontWeight: 600,
          marginBottom: 12
        }}>
          Select Knowledge Base Files
        </h2>

        <p style={{
          color: '#555',
          fontSize: '14px',
          marginBottom: 16
        }}>
          These files will be used by the AI to generate course content.
        </p>

        <div style={{
          maxHeight: 220,
          overflowY: 'auto',
          border: '1px solid #eee',
          borderRadius: 8,
          padding: 10,
          marginBottom: 24
        }}>
          {files.length === 0 ? (
            <div style={{ color: "#888", fontSize: 14 }}>No resources found.</div>
          ) : (
            <ul style={{ padding: 0, margin: 0, listStyle: 'none' }}>
              {files.map(file => {
                const id = file.id || file.fileName || file.name;
                const isSelected = selected.includes(file);
                return (
                  <li
                    key={id}
                    onClick={() => handleToggle(file)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      padding: '10px 8px',
                      borderBottom: '1px solid #f0f0f0',
                      cursor: 'pointer',
                      background: isSelected ? '#f5faff' : 'transparent',
                      borderRadius: 6,
                      transition: 'background 0.2s ease'
                    }}
                  >
                    {isSelected ? <FiCheckSquare size={18} /> : <FiSquare size={18} />}
                    <span style={{ marginLeft: 12, fontSize: 15, flex: 1 }}>
                      {file.name || file.fileName || file.title}
                    </span>
                  </li>
                );
              })}
            </ul>
          )}
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
          <button
            onClick={onClose}
            style={{
              padding: '8px 16px',
              fontSize: 15,
              borderRadius: 6,
              border: '1px solid #ccc',
              background: '#fff',
              cursor: 'pointer'
            }}
          >
            Cancel
          </button>
          <button
            onClick={handleGenerate}
            disabled={selected.length === 0}
            style={{
              padding: '8px 16px',
              fontSize: 15,
              borderRadius: 6,
              background: selected.length === 0 ? '#ccc' : '#007bff',
              color: '#fff',
              border: 'none',
              cursor: selected.length === 0 ? 'not-allowed' : 'pointer'
            }}
          >
            Generate
          </button>
        </div>
      </div>
    </Modal>
  );
}
