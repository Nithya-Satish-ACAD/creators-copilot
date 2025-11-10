import React from "react";
import Modal from "./Modal";
import { FaCog, FaArrowRight } from "react-icons/fa";

export default function SettingsPromptModal({ open, onClose, onOpenSettings, contentType }) {
  return (
    <Modal open={open} onClose={onClose} modalStyle={{ minWidth: 0, maxWidth: 500, width: '100%', borderRadius: 18, boxShadow: '0 8px 32px rgba(37,99,235,0.10)', background: '#fff', padding: 0 }}>
      <div style={{ padding: '36px 48px 32px 48px', borderRadius: 18, textAlign: 'center' }}>
        <div style={{ 
          width: 64, 
          height: 64, 
          background: '#eff6ff', 
          borderRadius: '50%', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center', 
          margin: '0 auto 24px auto' 
        }}>
          <FaCog size={28} color="#3b82f6" />
        </div>
        
        <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 16, color: '#1f2937' }}>
          Recommended Settings
        </h2>
        
        <p style={{ 
          fontSize: 16, 
          color: '#6b7280', 
          marginBottom: 8, 
          lineHeight: 1.5 
        }}>
          For more accurate and personalized {contentType}, we recommend updating your course settings.
        </p>
        
        <p style={{ 
          fontSize: 14, 
          color: '#9ca3af', 
          marginBottom: 32, 
          lineHeight: 1.4 
        }}>
          This helps our AI understand your course requirements and generate more relevant content. You can skip this step and continue with default settings.
        </p>
        
        <div style={{ display: 'flex', justifyContent: 'center', gap: 12 }}>
          <button 
            onClick={onClose}
            style={{ 
              padding: '12px 24px', 
              fontSize: 15, 
              borderRadius: 8, 
              border: '1.5px solid #e5e7eb', 
              background: '#fff', 
              color: '#6b7280', 
              fontWeight: 500, 
              cursor: 'pointer',
              transition: 'all 0.2s ease'
            }}
            onMouseOver={e => e.target.style.border = '1.5px solid #d1d5db'}
            onMouseOut={e => e.target.style.border = '1.5px solid #e5e7eb'}
          >
            Continue Without Settings
          </button>
          
          <button 
            onClick={onOpenSettings}
            style={{ 
              padding: '12px 24px', 
              fontSize: 15, 
              borderRadius: 8, 
              border: 'none', 
              background: '#3b82f6', 
              color: '#fff', 
              fontWeight: 600, 
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              boxShadow: '0 2px 8px rgba(59, 130, 246, 0.3)',
              transition: 'all 0.2s ease'
            }}
            onMouseOver={e => e.target.style.background = '#2563eb'}
            onMouseOut={e => e.target.style.background = '#3b82f6'}
          >
            <FaCog size={14} />
            Update Settings
            <FaArrowRight size={12} />
          </button>
        </div>
      </div>
    </Modal>
  );
}
