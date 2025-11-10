import React, { useState } from "react";
import { FiX, FiDownload, FiCopy } from "react-icons/fi";
import Modal from "./Modal";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkBreaks from 'remark-breaks';
import { viewResource } from "../services/resources";
import { jsPDF } from "jspdf";

export default function ResourceViewModal({ open, onClose, resourceName, courseId }) {
  const [showCopyMessage, setShowCopyMessage] = useState(false);
  const [showDownloadMessage, setShowDownloadMessage] = useState(false);
  const [resourceData, setResourceData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  React.useEffect(() => {
    const fetchResourceContent = async () => {
      setLoading(true);
      setError(null);
      try {
        console.log('Fetching resource content for:', resourceName, 'in course:', courseId);
        const data = await viewResource(courseId, resourceName);
        console.log('Resource data received:', data);
        setResourceData(data);
      } catch (error) {
        console.error('Error fetching resource content:', error);
        setError(error.message || 'Failed to load resource content');
      } finally {
        setLoading(false);
      }
    };

    console.log('ResourceViewModal useEffect triggered:', { open, resourceName, courseId });
    if (open && resourceName && courseId) {
      console.log('Conditions met, calling fetchResourceContent');
      fetchResourceContent();
    } else {
      console.log('Conditions not met:', { 
        open: !!open, 
        resourceName: !!resourceName, 
        courseId: !!courseId 
      });
    }
  }, [open, resourceName, courseId]);

  const handleCopyContent = async () => {
    if (!resourceData?.content) return;
    
    try {
      await navigator.clipboard.writeText(resourceData.content);
      setShowCopyMessage(true);
      setTimeout(() => setShowCopyMessage(false), 2000);
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
    }
  };

  const handleDownload = async () => {
    if (!resourceData?.content) return;
    
    try {
      // Create PDF document
      const doc = new jsPDF();
      const pageWidth = doc.internal.pageSize.getWidth();
      const pageHeight = doc.internal.pageSize.getHeight();
      const margin = 15;
      const maxWidth = pageWidth - 2 * margin;
      let yPosition = margin;

      // Helper function to strip markdown formatting and convert to plain text
      const stripMarkdown = (text) => {
        // Remove markdown headers
        text = text.replace(/^#+\s+/gm, '');
        // Remove bold/italic markers
        text = text.replace(/\*\*([^*]+)\*\*/g, '$1');
        text = text.replace(/\*([^*]+)\*/g, '$1');
        // Remove links but keep text
        text = text.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1');
        // Remove code blocks
        text = text.replace(/```[\s\S]*?```/g, '');
        text = text.replace(/`([^`]+)`/g, '$1');
        // Remove list markers
        text = text.replace(/^[\s]*[-*+]\s+/gm, '');
        text = text.replace(/^[\s]*\d+\.\s+/gm, '');
        return text;
      };

      // Convert markdown content to plain text
      const plainText = stripMarkdown(resourceData.content);
      
      // Split text into lines
      const lines = plainText.split('\n');
      
      // Add title
      doc.setFontSize(18);
      doc.setFont('helvetica', 'bold');
      doc.setTextColor(30, 64, 175);
      const titleLines = doc.splitTextToSize(resourceName, maxWidth);
      doc.text(titleLines, margin, yPosition);
      yPosition += titleLines.length * 10 + 10;
      
      // Add a line separator
      doc.setDrawColor(200, 200, 200);
      doc.setLineWidth(0.5);
      doc.line(margin, yPosition, pageWidth - margin, yPosition);
      yPosition += 10;
      
      // Add content
      doc.setFontSize(10);
      doc.setFont('helvetica', 'normal');
      doc.setTextColor(51, 51, 51);
      
      lines.forEach((line) => {
        // Check if we need a new page
        if (yPosition > pageHeight - margin - 20) {
          doc.addPage();
          yPosition = margin;
        }
        
        if (line.trim() === '') {
          // Empty line - add spacing
          yPosition += 4;
        } else {
          // Split long lines to fit page width
          const textLines = doc.splitTextToSize(line.trim(), maxWidth);
          doc.text(textLines, margin, yPosition);
          yPosition += textLines.length * 5 + 3;
        }
      });
      
      // Save the PDF
      const filename = `${resourceName.replace(/\.(txt|pdf)$/i, '')}.pdf`;
      doc.save(filename);
      
      setShowDownloadMessage(true);
      setTimeout(() => setShowDownloadMessage(false), 2000);
    } catch (error) {
      console.error('Failed to download file:', error);
      alert('Failed to generate PDF. Please try again.');
    }
  };

  if (!open) return null;

  return (
    <Modal open={open} onClose={onClose}>
      <div style={{ 
        position: 'relative',
        maxHeight: '90vh',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column'
      }}>
        {/* Header */}
        <div style={{
          paddingBottom: '20px',
          borderBottom: '1px solid #e5e7eb',
          marginBottom: '20px',
          flexShrink: 0
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start'
          }}>
            <div>
              <h2 style={{ 
                margin: 0,
                fontSize: '24px',
                fontWeight: 700,
                color: '#1f2937'
              }}>
                {resourceName || 'Resource'}
              </h2>
            </div>
            
            {/* Action buttons */}
            <div style={{
              display: 'flex',
              gap: '8px',
              position: 'relative'
            }}>
              {/* Only show buttons if there's content and no error */}
              {!error && resourceData?.content && (
                <>
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
                    {showCopyMessage && (
                      <span style={{ 
                        fontSize: '12px', 
                        color: '#374151',
                        marginLeft: '4px'
                      }}>
                        ✓ Copied!
                      </span>
                    )}
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
                    title="Download content"
                  >
                    <FiDownload size={16} />
                    Download
                    {showDownloadMessage && (
                      <span style={{ 
                        fontSize: '12px', 
                        color: '#fff',
                        marginLeft: '4px'
                      }}>
                        ✓ Downloaded!
                      </span>
                    )}
                  </button>
                </>
              )}
              
              {/* Close Button - Always visible */}
              <button
                onClick={onClose}
                style={{
                  background: 'transparent',
                  border: 'none',
                  cursor: 'pointer',
                  padding: '8px',
                  borderRadius: '6px',
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
            </div>
          </div>
        </div>


        {/* Content */}
        <div style={{ 
          flex: 1, 
          overflow: 'auto',
          padding: '0 4px'
        }}>
          {loading && (
            <div style={{ 
              display: 'flex', 
              justifyContent: 'center', 
              alignItems: 'center',
              height: '200px',
              color: '#6b7280'
            }}>
              Loading resource content...
            </div>
          )}

          {error && (
            <div style={{ 
              display: 'flex', 
              justifyContent: 'center', 
              alignItems: 'center',
              height: '200px',
              color: '#dc2626',
              textAlign: 'center',
              padding: '20px'
            }}>
              <div>
                <div style={{ fontSize: '16px', fontWeight: '500', marginBottom: '8px' }}>
                  {/* {error} */}
                </div>
                <div style={{ fontSize: '14px', color: '#6b7280' }}>
                  Resources uploaded by you can't be viewed
                </div>
              </div>
            </div>
          )}

          {resourceData?.content && !loading && !error && (
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
                  h1: ({children, ...props}) => {
                    // Only render if there's content
                    if (!children || (Array.isArray(children) && children.every(child => !child))) {
                      return null;
                    }
                    return <h1 style={{fontSize: '20px', fontWeight: 'bold', margin: '16px 0 8px 0', color: '#1f2937'}} {...props}>{children}</h1>;
                  },
                  h2: ({children, ...props}) => {
                    // Only render if there's content
                    if (!children || (Array.isArray(children) && children.every(child => !child))) {
                      return null;
                    }
                    return <h2 style={{fontSize: '18px', fontWeight: 'bold', margin: '14px 0 6px 0', color: '#1f2937'}} {...props}>{children}</h2>;
                  },
                  h3: ({children, ...props}) => {
                    // Only render if there's content
                    if (!children || (Array.isArray(children) && children.every(child => !child))) {
                      return null;
                    }
                    return <h3 style={{fontSize: '16px', fontWeight: 'bold', margin: '12px 0 6px 0', color: '#1f2937'}} {...props}>{children}</h3>;
                  },
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
                {resourceData.content}
              </ReactMarkdown>
            </div>
          )}
        </div>
      </div>
    </Modal>
  );
}
