import React, { useState, useEffect, useMemo } from "react";
import Modal from "./Modal";
import { assetService } from "../services/asset";

// Define asset type categories outside component to prevent recreation on every render
const ASSESSMENT_TYPES = ['project', 'activity', 'quiz', 'question-paper', 'mark-scheme', 'mock-interview'];
const CURRICULUM_TYPES = ['brainstorm', 'course-outcomes', 'modules', 'lecture', 'concept-map', 'course-notes'];
const SUPPORTED_EXPORT_TYPES = ['quiz', 'activity', 'lecture']; // Only these can be exported to LMS

export default function ActivitiesSelectionModal({
  open,
  onClose,
  selectedCourse,
  selectedModule,
  onActivitiesSelected
}) {
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState("");
  const [assets, setAssets] = useState([]);
  const [selected, setSelected] = useState({});
  const [search, setSearch] = useState("");

  useEffect(() => {
    if (!open) return;
    setError("");
    setSelected({});
    
    const load = async () => {
      try {
        setLoading(true);
        const courseId = localStorage.getItem("currentCourseId");
        if (!courseId) {
          setAssets([]);
          return;
        }
        const data = await assetService.getAssets(courseId);
        const list = (data?.assets || []).map((a, idx) => ({
          id: `${a.asset_category || ""}|${a.asset_type || ""}|${a.asset_name || ""}|${a.asset_last_updated_at || idx}`,
          name: a.asset_name,
          type: a.asset_type,
          category: a.asset_category,
          updatedAt: a.asset_last_updated_at,
          updatedBy: a.asset_last_updated_by,
          isExportable: SUPPORTED_EXPORT_TYPES.includes(a.asset_type)
        })).filter(asset => 
          ASSESSMENT_TYPES.includes(asset.type) || CURRICULUM_TYPES.includes(asset.type)
        );
        
        setAssets(list);
      } catch (e) {
        setError(e?.message || "Failed to load activities");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [open]);

  const filteredAssets = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return assets;
    return assets.filter(a =>
      a.name.toLowerCase().includes(q) ||
      (a.type || "").toLowerCase().includes(q) ||
      (a.category || "").toLowerCase().includes(q)
    );
  }, [assets, search]);

  const grouped = useMemo(() => {
    const assessments = [];
    const curriculum = [];
    
    filteredAssets.forEach(a => {
      if (ASSESSMENT_TYPES.includes(a.type)) {
        assessments.push(a);
      } else if (CURRICULUM_TYPES.includes(a.type)) {
        curriculum.push(a);
      }
    });
    
    const groups = {};
    if (assessments.length > 0) groups['Assessments'] = assessments;
    if (curriculum.length > 0) groups['Curriculum'] = curriculum;
    
    return groups;
  }, [filteredAssets]);

  const totalCount = filteredAssets.length;
  const exportableCount = filteredAssets.filter(a => a.isExportable).length;
  const selectedIds = Object.keys(selected).filter(k => selected[k]);
  const selectedCount = selectedIds.length;
  const allChecked = exportableCount > 0 && selectedCount === exportableCount;
  const someChecked = selectedCount > 0 && selectedCount < exportableCount;

  const toggleAll = () => {
    if (allChecked) {
      setSelected({});
    } else {
      const next = {};
      // Only select exportable assets
      filteredAssets.forEach(a => { 
        if (a.isExportable) {
          next[a.id] = true; 
        }
      });
      setSelected(next);
    }
  };

  const toggleOne = (id) => {
    setSelected(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const handleExport = async () => {
    try {
      setExporting(true);
      setError("");
      const chosen = assets.filter(a => selected[a.id]);
      
      if (chosen.length === 0) {
        setError("Please select at least one activity to export");
        return;
      }
      
      // Call the export API
      const courseId = localStorage.getItem("currentCourseId");
      if (courseId) {
        const assetNames = chosen.map(a => a.name);
        const assetTypes = chosen.map(a => a.type); // Array matching asset_names order
        const token = localStorage.getItem("token");
        
        console.log('Export request:', {
          courseId,
          assetNames,
          assetTypes,
          lms_course_id: selectedCourse?.id,
          lms_module_id: selectedModule?.id,
          lms_cookies: localStorage.getItem("lms_cookies") ? 'present' : 'missing'
        });

        const response = await fetch(`${process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000'}/api/courses/${courseId}/export-to-lms-module`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ 
            asset_names: assetNames,
            asset_type: assetTypes,
            lms_course_id: String(selectedCourse?.id || ''),
            lms_module_id: String(selectedModule?.id || ''),
            lms_cookies: String(localStorage.getItem("lms_cookies") || '')
          })
        });
        
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          console.error('Export error response:', errorData);
          
          // Handle validation errors properly
          let errorMessage = 'Export failed';
          if (errorData.detail) {
            if (Array.isArray(errorData.detail)) {
              // FastAPI validation errors
              errorMessage = errorData.detail.map(e => {
                if (e.msg && e.loc) {
                  return `${e.loc.join('.')}: ${e.msg}`;
                }
                return e.msg || JSON.stringify(e);
              }).join('; ');
            } else if (typeof errorData.detail === 'string') {
              errorMessage = errorData.detail;
            } else {
              errorMessage = JSON.stringify(errorData.detail);
            }
          }
          
          throw new Error(errorMessage);
        }
        
        const data = await response.json();
        console.log('Export data:', data);
        
        // Parse the results
        const summary = data.data?.summary || {};
        const exportedAssets = data.data?.exported_assets || [];
        const unsupportedAssets = data.data?.unsupported_assets || [];
        
        // Build success message
        let message = `Export to "${selectedModule?.name}" completed!\n\n`;
        
        if (summary.success > 0) {
          message += `✅ ${summary.success} asset(s) exported successfully\n`;
        }
        
        if (summary.failed > 0) {
          message += `❌ ${summary.failed} asset(s) failed to export\n`;
          const failed = exportedAssets.filter(a => a.status === 'failed');
          if (failed.length > 0) {
            message += `Failed assets: ${failed.map(a => a.asset_name).join(', ')}\n`;
          }
        }
        
        if (summary.unsupported > 0) {
          message += `⚠️ ${summary.unsupported} asset(s) not supported for export\n`;
          if (unsupportedAssets.length > 0) {
            message += `Unsupported: ${unsupportedAssets.map(a => `${a.asset_name} (${a.asset_type})`).join(', ')}\n`;
            message += `\nSupported types: quiz, activity`;
          }
        }
        
        // Show detailed alert
        alert(message);
        
        // Only close if all succeeded or user acknowledges
        if (summary.failed === 0 && summary.unsupported === 0) {
          if (onActivitiesSelected) onActivitiesSelected(chosen);
          onClose?.();
        } else {
          // Keep modal open to show error state
          setError(message);
        }
      }
      
    } catch (error) {
      console.error('Export error:', error);
      setError(error.message || 'Export failed');
    } finally {
      setExporting(false);
    }
  };

  if (!open) return null;

  return (
    <Modal open={open} onClose={onClose}>
      <div style={{ display: "flex", flexDirection: "column", gap: 16, position: "relative" }}>
        
        {/* Selected Course and Module Info */}
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
              Exporting to: {selectedCourse?.name} → {selectedModule?.name}
            </div>
            <div style={{ fontSize: 13, color: '#6b7280' }}>
              Select activities and quizzes to add to this module
            </div>
          </div>
        </div>
        
        {/* Loading Overlay */}
        {exporting && (
          <div style={{
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "rgba(255, 255, 255, 0.95)",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            gap: 16,
            zIndex: 1000,
            borderRadius: 12
          }}>
            <div style={{
              width: 48,
              height: 48,
              border: "4px solid #e5e7eb",
              borderTop: "4px solid #2563eb",
              borderRadius: "50%",
              animation: "spin 1s linear infinite"
            }}></div>
            <div style={{
              fontSize: 16,
              fontWeight: 600,
              color: "#2563eb"
            }}>
              Adding asset(s) to module, please wait...
            </div>
            <style>{`
              @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
              }
            `}</style>
          </div>
        )}
        
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <div style={{ fontWeight: 700, fontSize: 22 }}>Select Activities & Quizzes</div>
            <div style={{ color: "#6b7280", fontSize: 14 }}>
              {selectedCount} selected / {exportableCount} exportable
            </div>
          </div>
          <div style={{
            padding: '10px 12px',
            background: '#eff6ff',
            borderRadius: 8,
            border: '1px solid #bfdbfe',
            fontSize: 13,
            color: '#1e40af'
          }}>
            <strong>ℹ️ Note:</strong> Only <strong>Quiz</strong> and <strong>Activity</strong> assets can be exported to LMS modules. Other asset types will be shown but cannot be selected.
          </div>
        </div>

        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search by name, type, or category"
            style={{ flex: 1, padding: "10px 12px", border: "1px solid #d1d5db", borderRadius: 8 }}
          />
          <label style={{ display: "flex", alignItems: "center", gap: 8, userSelect: "none", cursor: "pointer" }}>
            <input
              type="checkbox"
              checked={allChecked}
              ref={el => { if (el) el.indeterminate = someChecked; }}
              onChange={toggleAll}
            />
            <span style={{ fontWeight: 600 }}>Select all</span>
          </label>
        </div>

        {error && (
          <div style={{ color: "#b91c1c", background: "#fee2e2", padding: 10, borderRadius: 8 }}>{error}</div>
        )}

        <div style={{
          maxHeight: "50vh",
          overflowY: "auto",
          border: "1px solid #e5e7eb",
          borderRadius: 10,
          background: "#fafbfc",
          padding: 8
        }}>
          {loading ? (
            <div style={{ padding: 16 }}>Loading activities…</div>
          ) : (
            Object.keys(grouped).sort().map(group => (
              <div key={group} style={{ marginBottom: 10 }}>
                <div style={{
                  position: "sticky",
                  top: 0,
                  background: "#f5f8ff",
                  padding: "8px 10px",
                  borderRadius: 8,
                  fontWeight: 700,
                  color: "#2563eb",
                  border: "1px solid #e5e7eb"
                }}>{group.charAt(0).toUpperCase() + group.slice(1)}</div>
                <div style={{ display: "flex", flexDirection: "column", marginTop: 6 }}>
                  {grouped[group].map(item => (
                    <label key={item.id} style={{
                      display: "grid",
                      gridTemplateColumns: "24px 1fr auto auto",
                      alignItems: "center",
                      gap: 10,
                      padding: "8px 10px",
                      borderBottom: "1px solid #eef2f7",
                      background: selected[item.id] ? "#eef6ff" : "transparent",
                      cursor: item.isExportable ? "pointer" : "not-allowed",
                      borderRadius: 6,
                      opacity: item.isExportable ? 1 : 0.6
                    }}>
                      <input 
                        type="checkbox" 
                        checked={!!selected[item.id]} 
                        onChange={() => item.isExportable && toggleOne(item.id)}
                        disabled={!item.isExportable}
                        style={{ cursor: item.isExportable ? 'pointer' : 'not-allowed' }}
                      />
                      <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                          <span style={{ fontWeight: 600 }}>{item.name}</span>
                          {!item.isExportable && (
                            <span style={{
                              padding: '2px 6px',
                              borderRadius: 4,
                              fontSize: 10,
                              fontWeight: 600,
                              background: '#fee2e2',
                              color: '#b91c1c',
                              textTransform: 'uppercase'
                            }}>
                              Not Exportable
                            </span>
                          )}
                          {item.isExportable && (
                            <span style={{
                              padding: '2px 6px',
                              borderRadius: 4,
                              fontSize: 10,
                              fontWeight: 600,
                              background: '#dcfce7',
                              color: '#16a34a',
                              textTransform: 'uppercase'
                            }}>
                              ✓ Exportable
                            </span>
                          )}
                        </div>
                        <span style={{ fontSize: 12, color: "#6b7280" }}>
                          {item.type.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </span>
                      </div>
                      <div style={{ fontSize: 11, color: "#9ca3af", whiteSpace: 'nowrap' }}>
                        {item.updatedAt ? new Date(item.updatedAt).toLocaleDateString() : ""}
                      </div>
                    </label>
                  ))}
                </div>
              </div>
            ))
          )}
          {!loading && totalCount === 0 && (
            <div style={{ padding: 16, color: "#6b7280" }}>No activities or quizzes found.</div>
          )}
        </div>

        <div style={{ display: "flex", justifyContent: "flex-end", gap: 12 }}>
          <button 
            onClick={onClose} 
            disabled={exporting}
            style={{ 
              padding: "10px 16px", 
              borderRadius: 8, 
              border: "1px solid #d1d5db", 
              background: "#fff",
              cursor: exporting ? "not-allowed" : "pointer",
              opacity: exporting ? 0.5 : 1
            }}
          >
            Cancel
          </button>
          <button
            onClick={handleExport}
            disabled={selectedCount === 0 || exporting}
            style={{
              padding: "10px 16px",
              borderRadius: 8,
              border: "none",
              background: (selectedCount === 0 || exporting) ? "#94a3b8" : "#2563eb",
              color: "#fff",
              fontWeight: 600,
              cursor: (selectedCount === 0 || exporting) ? "not-allowed" : "pointer"
            }}
          >
            {exporting ? "Adding to Module..." : `Add ${selectedCount > 0 ? `(${selectedCount})` : ""} to Module`}
          </button>
        </div>
      </div>
    </Modal>
  );
}
