import React, { useEffect, useMemo, useState } from "react";
import Modal from "./Modal";
import { assetService } from "../services/asset";

export default function ExportAssetsModal({
  open,
  onClose,
  assets: assetsProp,
  selectedLMSCourse,
  onExportSelected
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
        if (Array.isArray(assetsProp) && assetsProp.length) {
          // Ensure each asset has a stable unique id for selection
          const list = assetsProp.map((a, idx) => ({
            ...a,
            id: a.id || `${a.category || ""}|${a.type || ""}|${a.name || ""}|${a.updatedAt || idx}`
          }));
          setAssets(list);
          return;
        }
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
          updatedBy: a.asset_last_updated_by
        }));
        setAssets(list);
      } catch (e) {
        setError(e?.message || "Failed to load assets");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [open, assetsProp]);

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
    const groups = {};
    filteredAssets.forEach(a => {
      const key = (a.category || "Other");
      if (!groups[key]) groups[key] = [];
      groups[key].push(a);
    });
    return groups;
  }, [filteredAssets]);

  const totalCount = filteredAssets.length;
  const selectedIds = Object.keys(selected).filter(k => selected[k]);
  const selectedCount = selectedIds.length;
  const allChecked = totalCount > 0 && selectedCount === totalCount;
  const someChecked = selectedCount > 0 && selectedCount < totalCount;

  const toggleAll = () => {
    if (allChecked) {
      setSelected({});
    } else {
      const next = {};
      filteredAssets.forEach(a => { next[a.id] = true; });
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
      
      // Call the export API
      const courseId = localStorage.getItem("currentCourseId");
      if (courseId && chosen.length > 0) {
        const assetNames = chosen.map(a => a.name);
        const assetTypes = [...new Set(chosen.map(a => a.type))]; // Get unique asset types
        const token = localStorage.getItem("token");
        
        // Get LMS token from localStorage (set during login) - for future use with push-to-lms endpoint
        // const lmsToken = localStorage.getItem("lms_token");
        
        // ========================================
        // BACKEND INTEGRATION REQUIRED
        // ========================================
        // 
        // NEW ENDPOINT NEEDED: POST /api/courses/{course_id}/push-to-lms
        // 
        // REQUEST HEADERS:
        // - Authorization: Bearer <user_auth_token>
        // - X-LMS-Token: <lms_token_from_login>
        // - Content-Type: application/json
        // 
        // REQUEST BODY:
        // {
        //   "asset_names": ["asset1", "asset2", ...],
        //   "asset_type": ["quiz", "question-paper", ...],
        //   "lms_course_id": "optional_existing_course_id",
        //   "publish": true/false,
        //   "export_format": "lms_specific_format"
        // }
        // 
        // EXPECTED SUCCESS RESPONSE (200):
        // {
        //   "success": true,
        //   "message": "Successfully exported to LMS",
        //   "data": {
        //     "lms_course_id": "created_course_id",
        //     "lms_content_ids": ["content1", "content2", ...],
        //     "exported_assets": [
        //       {
        //         "asset_name": "quiz1",
        //         "lms_content_id": "lms_quiz_id",
        //         "status": "success"
        //       }
        //     ]
        //   }
        // }
        // 
        // EXPECTED ERROR RESPONSES:
        // - 400: { "detail": "LMS token expired or invalid" }
        // - 401: { "detail": "Unauthorized - invalid LMS credentials" }
        // - 404: { "detail": "Course not found" }
        // - 422: { "detail": "Invalid asset data" }
        // - 500: { "detail": "LMS export failed" }
        // 
        // BACKEND IMPLEMENTATION STEPS:
        // 1. Validate LMS token from X-LMS-Token header
        // 2. Get course data and selected assets
        // 3. Format assets according to LMS API requirements
        // 4. Call LMS platform API to create/update content
        // 5. Handle LMS-specific response format
        // 6. Return success with LMS IDs for tracking
        // 7. Implement retry logic for failed exports
        // 8. Add logging for audit trail
        // 
        // LMS API INTEGRATION EXAMPLE:
        // POST {LMS_BASE_URL}/api/v1/courses
        // Headers: Authorization: Bearer {lms_token}
        // Body: { course_data, assets: formatted_assets }
        // 
        // CURRENT: Downloads JSON file (temporary)
        // FUTURE: Push directly to LMS platform
        
        // ========================================
        // CURRENT: Using existing export-lms endpoint (temporary)
        // FUTURE: Switch to push-to-lms endpoint when implemented
        // ========================================
        const response = await fetch(`${process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000'}/api/courses/${courseId}/export-lms`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
            // TODO: Add LMS token header when push-to-lms endpoint is ready:
            // 'X-LMS-Token': lmsToken
          },
          body: JSON.stringify({ 
            asset_names: assetNames,
            asset_type: assetTypes,
            // Include selected LMS course information
            lms_course_id: selectedLMSCourse?.id || null, // null means create new course
            lms_course_name: selectedLMSCourse?.name || null,
            lms_course_code: selectedLMSCourse?.code || null
            // TODO: Add LMS-specific parameters when push-to-lms endpoint is ready:
            // publish: true/false,
            // export_format: "lms_specific_format"
          })
        });
        
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || 'Export failed');
        }
        
        const data = await response.json();
        console.log('Export data:', data);
        
        // Download the exported data as JSON
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `course-export-${new Date().getTime()}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }
      
      if (onExportSelected) onExportSelected(chosen);
      onClose?.();
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
        {/* Selected LMS Course Info */}
        {selectedLMSCourse && (
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
                Exporting to LMS Course:
              </div>
              <div style={{ fontSize: 15, fontWeight: 600, color: '#1e40af' }}>
                {selectedLMSCourse.name}
                {selectedLMSCourse.code && <span style={{ color: '#6b7280', marginLeft: 8 }}>({selectedLMSCourse.code})</span>}
              </div>
            </div>
          </div>
        )}
        
        {selectedLMSCourse === null && (
          <div style={{
            padding: '12px 16px',
            background: '#fef3c7',
            borderRadius: 8,
            border: '1px solid #f59e0b',
            display: 'flex',
            alignItems: 'center',
            gap: 12
          }}>
            <div style={{
              width: 40,
              height: 40,
              borderRadius: '50%',
              background: '#f59e0b',
              color: '#fff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 18,
              fontWeight: 'bold',
              flexShrink: 0
            }}>
              ➕
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#92400e', marginBottom: 2 }}>
                Creating New LMS Course
              </div>
              <div style={{ fontSize: 13, color: '#78350f' }}>
                A new course will be created in your LMS with the exported content
              </div>
            </div>
          </div>
        )}
        
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
              Formatting the content, please wait...
            </div>
            <style>{`
              @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
              }
            `}</style>
          </div>
        )}
        
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ fontWeight: 700, fontSize: 22 }}>Export Assets</div>
          <div style={{ color: "#6b7280", fontSize: 14 }}>
            {selectedCount} selected{totalCount ? ` / ${totalCount}` : ""}
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
            <div style={{ padding: 16 }}>Loading assets…</div>
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
                      gridTemplateColumns: "24px 1fr auto",
                      alignItems: "center",
                      gap: 10,
                      padding: "8px 10px",
                      borderBottom: "1px solid #eef2f7",
                      background: selected[item.id] ? "#eef6ff" : "transparent",
                      cursor: "pointer",
                      borderRadius: 6
                    }}>
                      <input type="checkbox" checked={!!selected[item.id]} onChange={() => toggleOne(item.id)} />
                      <div style={{ display: "flex", flexDirection: "column" }}>
                        <span style={{ fontWeight: 600 }}>{item.name}</span>
                        <span style={{ fontSize: 12, color: "#6b7280" }}>{item.type}</span>
                      </div>
                      <div style={{ fontSize: 12, color: "#6b7280" }}>
                        {item.updatedAt ? new Date(item.updatedAt).toLocaleString() : ""}
                      </div>
                    </label>
                  ))}
                </div>
              </div>
            ))
          )}
          {!loading && totalCount === 0 && (
            <div style={{ padding: 16, color: "#6b7280" }}>No assets found.</div>
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
            {exporting ? "Exporting..." : `Export ${selectedCount > 0 ? `(${selectedCount})` : ""}`}
          </button>
        </div>
      </div>
    </Modal>
  );
}


