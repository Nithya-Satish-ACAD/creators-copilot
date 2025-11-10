import React, { useState, useEffect, useCallback } from "react";
import Modal from "./Modal";
import { getLMSModules, createLMSModule } from "../services/lms";

export default function LMSModulesModal({
  open,
  onClose,
  selectedCourse,
  onModuleSelected
}) {
  const [modules, setModules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [isGridView, setIsGridView] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedModuleId, setSelectedModuleId] = useState(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newModuleName, setNewModuleName] = useState("");
  const [creating, setCreating] = useState(false);

  const fetchLMSModules = useCallback(async () => {
    try {
      setLoading(true);
      setError("");
      
      console.log('fetchLMSModules - selectedCourse:', selectedCourse);
      
      if (!selectedCourse) {
        throw new Error("No course selected");
      }
      
      if (!selectedCourse.id) {
        throw new Error(`Course ID is missing. Available keys: ${Object.keys(selectedCourse).join(', ')}`);
      }

      console.log('fetchLMSModules - calling getLMSModules with courseId:', selectedCourse.id);
      
      // Call the getLMSModules service function
      const result = await getLMSModules(selectedCourse.id);
      
      console.log('LMS Modules fetched:', result.modules);
      setModules(result.modules || []);
      
    } catch (err) {
      console.error('Error fetching LMS modules:', err);
      
      // Properly extract error message from various error formats
      let errorMessage = 'Failed to load modules from LMS';
      
      console.log('Error details for debugging:', err);
      
      if (typeof err === 'string') {
        errorMessage = err;
      } else if (err?.detail) {
        // FastAPI validation errors or custom error detail
        if (Array.isArray(err.detail)) {
          // Validation errors array - show detailed validation info
          errorMessage = err.detail.map(e => {
            if (e.msg && e.loc) {
              return `${e.loc.join('.')}: ${e.msg}`;
            }
            return e.msg || JSON.stringify(e);
          }).join('; ');
        } else if (typeof err.detail === 'string') {
          errorMessage = err.detail;
        } else {
          errorMessage = JSON.stringify(err.detail);
        }
      } else if (err?.message) {
        errorMessage = err.message;
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [selectedCourse]);

  useEffect(() => {
    if (open && selectedCourse) {
      fetchLMSModules();
      setSelectedModuleId(null);
      setShowCreateForm(false);
      setNewModuleName("");
    }
  }, [open, selectedCourse, fetchLMSModules]);

  const handleModuleSelect = (moduleId) => {
    console.log('Module selected:', moduleId);
    setSelectedModuleId(moduleId);
  };

  const handleProceedWithActivities = () => {
    if (!selectedModuleId) return;
    
    const selectedModule = modules.find(m => m.id === selectedModuleId);
    onModuleSelected(selectedModule);
  };

  const handleCreateModule = async () => {
    if (!newModuleName.trim()) {
      setError("Please enter a module name");
      return;
    }

    try {
      setCreating(true);
      setError("");
      
      // Create the module
      const result = await createLMSModule(
        selectedCourse.id,
        newModuleName.trim(),
        modules.length + 1 // Set order as next position
      );

      console.log('Module created:', result);

      // Refresh the modules list
      await fetchLMSModules();

      // Close the create form
      setShowCreateForm(false);
      setNewModuleName("");

      // Auto-select the newly created module if we have its ID
      if (result.module && result.module.id) {
        setSelectedModuleId(result.module.id);
      }
    } catch (err) {
      console.error('Error creating module:', err);
      
      // Properly extract error message from various error formats
      let errorMessage = 'Failed to create module';
      
      console.log('Error details for debugging:', err);
      
      if (typeof err === 'string') {
        errorMessage = err;
      } else if (err?.detail) {
        // FastAPI validation errors or custom error detail
        if (Array.isArray(err.detail)) {
          // Validation errors array - show detailed validation info
          errorMessage = err.detail.map(e => {
            if (e.msg && e.loc) {
              return `${e.loc.join('.')}: ${e.msg}`;
            }
            return e.msg || JSON.stringify(e);
          }).join('; ');
        } else if (typeof err.detail === 'string') {
          errorMessage = err.detail;
        } else {
          errorMessage = JSON.stringify(err.detail);
        }
      } else if (err?.message) {
        errorMessage = err.message;
      }
      
      setError(errorMessage);
    } finally {
      setCreating(false);
    }
  };

  // Filter modules based on search query
  const filteredModules = modules.filter(module => 
    module.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (module.description || "").toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (!open) return null;

  return (
    <Modal open={open} onClose={onClose}>
      <div style={{ display: "flex", flexDirection: "column", gap: 16, position: "relative", minHeight: 400 }}>
        
        {/* Header */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ fontWeight: 700, fontSize: 22 }}>Select Module</div>
          {!loading && !error && (
            <div style={{ display: "flex", gap: 8 }}>
              <button
                onClick={() => setIsGridView(true)}
                style={{
                  padding: "6px 12px",
                  borderRadius: 6,
                  border: "1px solid #d1d5db",
                  background: isGridView ? "#2563eb" : "#fff",
                  color: isGridView ? "#fff" : "#222",
                  cursor: "pointer",
                  fontSize: 16
                }}
              >
                ▦
              </button>
              <button
                onClick={() => setIsGridView(false)}
                style={{
                  padding: "6px 12px",
                  borderRadius: 6,
                  border: "1px solid #d1d5db",
                  background: !isGridView ? "#2563eb" : "#fff",
                  color: !isGridView ? "#fff" : "#222",
                  cursor: "pointer",
                  fontSize: 16
                }}
              >
                ≡
              </button>
            </div>
          )}
        </div>

        {/* Course Info */}
        {selectedCourse && (
          <div style={{
            padding: '12px 16px',
            background: '#eff6ff',
            borderRadius: 8,
            border: '1px solid #2563eb',
            display: 'flex',
            alignItems: 'center',
            gap: 12
          }}>
            <div style={{
              width: 40,
              height: 40,
              borderRadius: '50%',
              background: '#2563eb',
              color: '#fff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 18,
              fontWeight: 'bold',
              flexShrink: 0
            }}>
              📚
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#2563eb', marginBottom: 2 }}>
                Course: {selectedCourse.name}
              </div>
              <div style={{ fontSize: 13, color: '#6b7280' }}>
                {selectedCourse.code && `Code: ${selectedCourse.code}`}
              </div>
            </div>
          </div>
        )}

        <p style={{ margin: 0, color: "#6b7280", fontSize: 14 }}>
          Choose a module to add activities and quizzes to, or create a new one
        </p>

        {/* Create New Module Button */}
        {!loading && !error && !showCreateForm && (
          <button
            onClick={() => setShowCreateForm(true)}
            style={{
              width: '100%',
              padding: '12px 16px',
              borderRadius: 8,
              border: '2px dashed #2563eb',
              background: '#eff6ff',
              color: '#2563eb',
              fontWeight: 600,
              fontSize: 14,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 8,
              transition: 'all 0.2s'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = '#dbeafe';
              e.currentTarget.style.borderColor = '#1d4ed8';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = '#eff6ff';
              e.currentTarget.style.borderColor = '#2563eb';
            }}
          >
            <span style={{ fontSize: 18 }}>➕</span>
            Create New Module
          </button>
        )}

        {/* Create Module Form */}
        {showCreateForm && (
          <div style={{
            padding: 16,
            background: '#f0fdf4',
            border: '2px solid #22c55e',
            borderRadius: 10,
            display: 'flex',
            flexDirection: 'column',
            gap: 12
          }}>
            <div style={{ fontWeight: 700, fontSize: 16, color: '#15803d', display: 'flex', alignItems: 'center', gap: 8 }}>
              <span>📝</span> Create New Module
            </div>
            <input
              type="text"
              value={newModuleName}
              onChange={(e) => setNewModuleName(e.target.value)}
              placeholder="Enter module name..."
              disabled={creating}
              style={{
                padding: '10px 12px',
                borderRadius: 8,
                border: '1px solid #86efac',
                fontSize: 14,
                boxSizing: 'border-box',
                opacity: creating ? 0.6 : 1
              }}
              onKeyPress={(e) => {
                if (e.key === 'Enter' && !creating) {
                  handleCreateModule();
                }
              }}
            />
            <div style={{ display: 'flex', gap: 8 }}>
              <button
                onClick={() => {
                  setShowCreateForm(false);
                  setNewModuleName("");
                  setError("");
                }}
                disabled={creating}
                style={{
                  flex: 1,
                  padding: '8px 12px',
                  borderRadius: 6,
                  border: '1px solid #d1d5db',
                  background: '#fff',
                  color: '#374151',
                  fontWeight: 600,
                  fontSize: 14,
                  cursor: creating ? 'not-allowed' : 'pointer',
                  opacity: creating ? 0.6 : 1
                }}
              >
                Cancel
              </button>
              <button
                onClick={handleCreateModule}
                disabled={creating || !newModuleName.trim()}
                style={{
                  flex: 1,
                  padding: '8px 12px',
                  borderRadius: 6,
                  border: 'none',
                  background: (creating || !newModuleName.trim()) ? '#94a3b8' : '#22c55e',
                  color: '#fff',
                  fontWeight: 600,
                  fontSize: 14,
                  cursor: (creating || !newModuleName.trim()) ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 6
                }}
              >
                {creating ? (
                  <>
                    <div style={{
                      width: 14,
                      height: 14,
                      border: "2px solid #fff",
                      borderTop: "2px solid transparent",
                      borderRadius: "50%",
                      animation: "spin 0.8s linear infinite"
                    }}></div>
                    Creating...
                  </>
                ) : (
                  '✓ Create Module'
                )}
              </button>
            </div>
          </div>
        )}

        {/* Search Bar */}
        {!loading && !error && modules.length > 0 && (
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by module name..."
            style={{
              width: '100%',
              padding: '10px 12px',
              borderRadius: 8,
              border: '1px solid #d1d5db',
              fontSize: 14,
              boxSizing: 'border-box'
            }}
          />
        )}

        {/* Loading State */}
        {loading && (
          <div style={{ 
            textAlign: 'center',
            padding: '60px 20px'
          }}>
            <div style={{
              width: 48,
              height: 48,
              border: "4px solid #e5e7eb",
              borderTop: "4px solid #2563eb",
              borderRadius: "50%",
              animation: "spin 1s linear infinite",
              margin: '0 auto 16px auto'
            }}></div>
            <div style={{
              fontSize: 15,
              fontWeight: 600,
              color: "#2563eb"
            }}>
              Loading modules from LMS...
            </div>
            <style>{`
              @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
              }
            `}</style>
          </div>
        )}

        {/* Error State */}
        {error && !loading && (
          <div style={{ 
            padding: '16px',
            background: '#fee2e2',
            borderRadius: 8,
            border: '1px solid #fecaca',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: 16, fontWeight: 600, color: '#b91c1c', marginBottom: 8 }}>
              ❌ Error Loading Modules
            </div>
            <div style={{ fontSize: 14, color: '#991b1b', marginBottom: 12 }}>
              {String(error)}
            </div>
            <button
              onClick={fetchLMSModules}
              style={{
                padding: "8px 16px",
                borderRadius: 6,
                border: "none",
                background: "#b91c1c",
                color: "#fff",
                fontWeight: 600,
                fontSize: 14,
                cursor: "pointer"
              }}
            >
              Try Again
            </button>
          </div>
        )}

        {/* Modules List */}
        {!loading && !error && (
          <div style={{
            maxHeight: '400px',
            overflowY: 'auto',
            border: '1px solid #e5e7eb',
            borderRadius: 10,
            background: '#fafbfc',
            padding: 8
          }}>
            {filteredModules.length === 0 ? (
              <div style={{ 
                padding: '40px 20px',
                textAlign: 'center',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 12
              }}>
                <div style={{ fontSize: 48 }}>📚</div>
                <div style={{ fontSize: 16, fontWeight: 600, color: '#374151' }}>
                  {searchQuery ? `No modules found matching "${searchQuery}"` : "No modules found"}
                </div>
                <div style={{ fontSize: 13, color: '#6b7280' }}>
                  {searchQuery 
                    ? "Try a different search term or create a new module" 
                    : "Create a new module to get started"}
                </div>
                {!searchQuery && !showCreateForm && (
                  <button
                    onClick={() => setShowCreateForm(true)}
                    style={{
                      marginTop: 8,
                      padding: '10px 20px',
                      borderRadius: 8,
                      border: 'none',
                      background: '#2563eb',
                      color: '#fff',
                      fontWeight: 600,
                      fontSize: 14,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8
                    }}
                  >
                    <span>➕</span>
                    Create Your First Module
                  </button>
                )}
              </div>
            ) : isGridView ? (
              /* Grid View */
              <div style={{ display: 'grid', gap: 12 }}>
                {filteredModules.map(module => (
                  <div
                    key={module.id}
                    onClick={() => handleModuleSelect(module.id)}
                    style={{
                      background: '#fff',
                      borderRadius: 10,
                      padding: 16,
                      border: selectedModuleId === module.id ? '3px solid #2563eb' : '1px solid #e5e7eb',
                      cursor: 'pointer',
                      position: 'relative',
                      transition: 'all 0.2s'
                    }}
                    onMouseEnter={(e) => {
                      if (selectedModuleId !== module.id) {
                        e.currentTarget.style.borderColor = '#cbd5e1';
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (selectedModuleId !== module.id) {
                        e.currentTarget.style.borderColor = '#e5e7eb';
                      }
                    }}
                  >
                    {/* Selection indicator */}
                    {selectedModuleId === module.id && (
                      <div style={{
                        position: 'absolute',
                        top: 12,
                        right: 12,
                        width: 28,
                        height: 28,
                        borderRadius: '50%',
                        background: '#2563eb',
                        color: '#fff',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: 16,
                        fontWeight: 'bold'
                      }}>
                        ✓
                      </div>
                    )}

                    {/* Module Header */}
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10, marginBottom: 4 }}>
                      <div style={{ flex: 1 }}>
                        <h3 style={{ 
                          fontSize: 16, 
                          fontWeight: 700, 
                          color: '#2563eb',
                          margin: '0 0 4px 0'
                        }}>
                          {module.name || 'Unnamed Module'}
                        </h3>
                        <div style={{ fontSize: 12, color: '#6b7280', fontWeight: 600 }}>
                          Module ID: {module.id}
                        </div>
                      </div>
                      {module.visible !== undefined && (
                        <span style={{
                          padding: '4px 10px',
                          borderRadius: 10,
                          fontSize: 11,
                          fontWeight: 600,
                          textTransform: 'uppercase',
                          background: module.visible ? '#dcfce7' : '#f3f4f6',
                          color: module.visible ? '#16a34a' : '#6b7280'
                        }}>
                          {module.visible ? 'visible' : 'hidden'}
                        </span>
                      )}
                    </div>

                    {/* Module Description */}
                    {module.description && (
                      <div style={{ fontSize: 13, color: '#374151', lineHeight: 1.4, marginTop: 8 }}>
                        {module.description}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              /* List View */
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ background: '#f5f8ff', borderBottom: '1px solid #e5e7eb' }}>
                    <th style={{ padding: '10px 12px', textAlign: 'center', fontSize: 13, fontWeight: 700, color: '#2563eb', width: 50 }}>
                      Select
                    </th>
                    <th style={{ padding: '10px 12px', textAlign: 'left', fontSize: 13, fontWeight: 700, color: '#2563eb' }}>
                      Module
                    </th>
                    <th style={{ padding: '10px 12px', textAlign: 'center', fontSize: 13, fontWeight: 700, color: '#2563eb' }}>
                      Position
                    </th>
                    <th style={{ padding: '10px 12px', textAlign: 'center', fontSize: 13, fontWeight: 700, color: '#2563eb' }}>
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {filteredModules.map((module, index) => (
                    <tr 
                      key={module.id}
                      onClick={() => handleModuleSelect(module.id)}
                      style={{ 
                        borderBottom: index < filteredModules.length - 1 ? '1px solid #f3f4f6' : 'none',
                        cursor: 'pointer',
                        background: selectedModuleId === module.id ? '#eff6ff' : 'transparent'
                      }}
                    >
                      <td style={{ padding: '12px', textAlign: 'center' }}>
                        <input
                          type="radio"
                          checked={selectedModuleId === module.id}
                          onChange={() => handleModuleSelect(module.id)}
                          style={{ width: 18, height: 18, cursor: 'pointer' }}
                        />
                      </td>
                      <td style={{ padding: '12px' }}>
                        <div style={{ fontSize: 14, fontWeight: 600, color: '#2563eb' }}>
                          {module.name || 'Unnamed Module'}
                        </div>
                        <div style={{ fontSize: 11, color: '#9ca3af', marginTop: 2 }}>
                          ID: {module.id}
                        </div>
                      </td>
                      <td style={{ padding: '12px', fontSize: 13, color: '#6b7280', textAlign: 'center' }}>
                        {module.position || '-'}
                      </td>
                      <td style={{ padding: '12px', textAlign: 'center' }}>
                        {module.visible !== undefined ? (
                          <span style={{
                            padding: '4px 10px',
                            borderRadius: 10,
                            fontSize: 11,
                            fontWeight: 600,
                            textTransform: 'uppercase',
                            background: module.visible ? '#dcfce7' : '#f3f4f6',
                            color: module.visible ? '#16a34a' : '#6b7280'
                          }}>
                            {module.visible ? 'visible' : 'hidden'}
                          </span>
                        ) : (
                          <span style={{ fontSize: 13, color: '#9ca3af' }}>-</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {/* Action Buttons */}
        {!loading && !error && (
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12, marginTop: 8 }}>
            <button
              onClick={onClose}
              style={{
                padding: "10px 20px",
                borderRadius: 8,
                border: "1px solid #d1d5db",
                background: "#fff",
                color: "#374151",
                fontWeight: 600,
                fontSize: 15,
                cursor: "pointer"
              }}
            >
              Cancel
            </button>
            <button
              onClick={handleProceedWithActivities}
              disabled={!selectedModuleId}
              style={{
                padding: "10px 24px",
                borderRadius: 8,
                border: "none",
                background: selectedModuleId ? "#2563eb" : "#94a3b8",
                color: "#fff",
                fontWeight: 600,
                fontSize: 15,
                cursor: selectedModuleId ? "pointer" : "not-allowed",
                display: 'flex',
                alignItems: 'center',
                gap: 8
              }}
            >
              Select Activities
              <span style={{ fontSize: 16 }}>→</span>
            </button>
          </div>
        )}
      </div>
    </Modal>
  );
}
