import React, { useState } from "react";
import { FiX, FiDownload, FiCopy } from "react-icons/fi";
import Modal from "./Modal";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkBreaks from 'remark-breaks';
import { assetService } from "../services/asset";

export default function AssetViewModal({ open, onClose, assetData, courseId }) {
  const [showCopyMessage, setShowCopyMessage] = useState(false);
  const [showDownloadMessage, setShowDownloadMessage] = useState(false);

  if (!open || !assetData) return null;

  const handleCopyContent = async () => {
    try {
      await navigator.clipboard.writeText(assetData.asset_content);
      setShowCopyMessage(true);
      setTimeout(() => setShowCopyMessage(false), 2000); // Hide after 2 seconds
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
    }
  };

  const handleDownload = async () => {
    try {
      if (!courseId || !assetData?.asset_name) return;
      await assetService.downloadAsset(courseId, assetData.asset_name);
      setShowDownloadMessage(true);
      setTimeout(() => setShowDownloadMessage(false), 2000);
    } catch (error) {
      console.error('Failed to download file:', error);
    }
  };

  return (
    <Modal open={open} onClose={onClose}>
      <div style={{ width: '100%', maxWidth: '800px', maxHeight: '80vh' }}>
        {/* Header */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '24px',
          paddingBottom: '16px',
          borderBottom: '1px solid #e5e7eb'
        }}>
          <div>
            <h2 style={{
              margin: 0,
              fontSize: '24px',
              fontWeight: 700,
              color: '#1f2937'
            }}>
              {assetData.asset_name}
            </h2>
            <div style={{
              display: 'flex',
              gap: '16px',
              marginTop: '8px',
              fontSize: '14px',
              color: '#6b7280'
            }}>
              <span>Type: {assetData.asset_type}</span>
              <span>Category: {assetData.asset_category}</span>
              <span>Updated by: {assetData.asset_last_updated_by}</span>
            </div>
          </div>
          
          {/* Action buttons */}
          <div style={{
            display: 'flex',
            gap: '8px',
            position: 'relative'
          }}>
            <button
              onClick={handleCopyContent}
              style={{
                background: '#f3f4f6',
                border: '1px solid #d1d5db',
                borderRadius: '6px',
                padding: '8px 12px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                fontSize: '14px',
                color: '#374151',
                transition: 'all 0.2s ease'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = '#e5e7eb';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = '#f3f4f6';
              }}
              title="Copy content"
            >
              <FiCopy size={16} />
              Copy
            </button>
            <button
              onClick={handleDownload}
              style={{
                background: '#2563eb',
                border: 'none',
                borderRadius: '6px',
                padding: '8px 12px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                fontSize: '14px',
                color: 'white',
                transition: 'all 0.2s ease'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = '#1d4ed8';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = '#2563eb';
              }}
              title="Download as PDF"
            >
              <FiDownload size={16} />
              Download
            </button>
            <button
              onClick={onClose}
              style={{
                background: 'transparent',
                border: 'none',
                borderRadius: '6px',
                padding: '8px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#6b7280',
                transition: 'all 0.2s ease'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = '#f3f4f6';
                e.currentTarget.style.color = '#374151';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'transparent';
                e.currentTarget.style.color = '#6b7280';
              }}
              title="Close"
            >
              <FiX size={20} />
            </button>

            {/* Copy confirmation message */}
            {showCopyMessage && (
              <div style={{
                position: 'absolute',
                top: '-40px',
                left: '50%',
                transform: 'translateX(-50%)',
                background: '#10b981',
                color: 'white',
                padding: '6px 12px',
                borderRadius: '6px',
                fontSize: '12px',
                fontWeight: 500,
                whiteSpace: 'nowrap',
                zIndex: 1000,
                animation: 'fadeInOut 2s ease-in-out'
              }}>
                ✓ Copied to clipboard!
              </div>
            )}

            {/* Download confirmation message */}
            {showDownloadMessage && (
              <div style={{
                position: 'absolute',
                top: '-40px',
                left: '50%',
                transform: 'translateX(-50%)',
                background: '#2563eb',
                color: 'white',
                padding: '6px 12px',
                borderRadius: '6px',
                fontSize: '12px',
                fontWeight: 500,
                whiteSpace: 'nowrap',
                zIndex: 1000,
                animation: 'fadeInOut 2s ease-in-out'
              }}>
                ✓ Downloaded successfully!
              </div>
            )}
          </div>
        </div>

        {/* Content with Markdown Rendering */}
        <div style={{
          background: '#fafbfc',
          border: '1px solid #e5e7eb',
          borderRadius: '8px',
          padding: '20px',
          maxHeight: '60vh',
          overflowY: 'auto',
          fontSize: '14px',
          lineHeight: '1.6'
        }}>
          <ReactMarkdown 
            remarkPlugins={[remarkGfm, remarkBreaks]}
            components={{
              // Custom styling for markdown elements
              h1: (props) => <h1 style={{fontSize: '20px', fontWeight: 'bold', margin: '16px 0 8px 0', color: '#1f2937'}} {...props} />,
              h2: (props) => <h2 style={{fontSize: '18px', fontWeight: 'bold', margin: '14px 0 6px 0', color: '#1f2937'}} {...props} />,
              h3: (props) => <h3 style={{fontSize: '16px', fontWeight: 'bold', margin: '12px 0 6px 0', color: '#1f2937'}} {...props} />,
              p: (props) => <p style={{margin: '8px 0', color: '#374151'}} {...props} />,
              strong: (props) => <strong style={{fontWeight: 'bold', color: '#1f2937'}} {...props} />,
              em: (props) => <em style={{fontStyle: 'italic', color: '#374151'}} {...props} />,
              code: ({inline, ...props}) => 
                inline ? 
                  <code style={{background: '#f3f4f6', padding: '2px 4px', borderRadius: '3px', fontFamily: 'monospace', fontSize: '13px'}} {...props} /> :
                  <code style={{background: '#f3f4f6', padding: '8px', borderRadius: '6px', fontFamily: 'monospace', fontSize: '13px', display: 'block', margin: '8px 0'}} {...props} />,
              ul: (props) => <ul style={{margin: '8px 0', paddingLeft: '20px'}} {...props} />,
              ol: (props) => <ol style={{margin: '8px 0', paddingLeft: '20px'}} {...props} />,
              li: (props) => <li style={{margin: '4px 0', color: '#374151'}} {...props} />,
              blockquote: (props) => <blockquote style={{borderLeft: '4px solid #2563eb', paddingLeft: '12px', margin: '8px 0', color: '#6b7280', fontStyle: 'italic'}} {...props} />,
              a: ({href, children, ...props}) => <a href={href} target="_blank" rel="noopener noreferrer" style={{color: '#2563eb', textDecoration: 'underline'}} {...props}>{children}</a>,
              table: (props) => <table style={{borderCollapse: 'collapse', width: '100%', margin: '8px 0'}} {...props} />,
              th: (props) => <th style={{border: '1px solid #d1d5db', padding: '8px', background: '#f9fafb', fontWeight: 'bold'}} {...props} />,
              td: (props) => <td style={{border: '1px solid #d1d5db', padding: '8px'}} {...props} />
            }}
          >
            {assetData.asset_content}
          </ReactMarkdown>
        </div>

        {/* Footer */}
        <div style={{
          marginTop: '16px',
          paddingTop: '16px',
          borderTop: '1px solid #e5e7eb',
          fontSize: '12px',
          color: '#6b7280',
          textAlign: 'center'
        }}>
          Last updated: {new Date(assetData.asset_last_updated_at).toLocaleString()}
        </div>
      </div>

      {/* CSS for animation */}
      <style>{`
        @keyframes fadeInOut {
          0% { opacity: 0; transform: translateX(-50%) translateY(-10px); }
          20% { opacity: 1; transform: translateX(-50%) translateY(0); }
          80% { opacity: 1; transform: translateX(-50%) translateY(0); }
          100% { opacity: 0; transform: translateX(-50%) translateY(-10px); }
        }
      `}</style>
    </Modal>
  );
} 