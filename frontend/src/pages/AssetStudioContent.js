import React, { useEffect, useRef, useState } from "react";
import { useLocation, useParams } from "react-router-dom";
import AssetStudioLayout from "../layouts/AssetStudioLayout";
import KnowledgeBase from "../components/KnowledgBase";
import { FaDownload, FaFolderPlus, FaSave } from "react-icons/fa";
import { getAllResources, uploadCourseResources, deleteResource as deleteResourceApi } from "../services/resources";
import { assetService } from "../services/asset";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkBreaks from "remark-breaks";
import AddResourceModal from '../components/AddReferencesModal';

const optionTitles = {
  "course-outcomes": "Course Outcomes",
  "modules-and-topics": "Modules & Topics",
  "lesson-plans": "Lesson Plans",
  "concept-map": "Concept Map",
  "course-notes": "Course Notes",
  "brainstorm": "Brainstorm",
  "quiz": "Quiz",
  "assignment": "Assignment",
  "viva": "Viva",
  "sprint-plan": "Sprint Plan"
};


export default function AssetStudioContent() {
  const params = useParams();
  const option = params.feature;
  const location = useLocation();
  const bottomRef = useRef(null);
  const title = optionTitles[option] || option;

  // ✅ Pre-select only those passed from Dashboard
  const selectedFiles = location.state?.selectedFiles || [];
  const initialSelectedIds = selectedFiles.map(file => file.id);
  const [selectedIds, setSelectedIds] = useState(initialSelectedIds);

  const [chatMessages, setChatMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [resources, setResources] = useState([]);
  const [resourcesLoading, setResourcesLoading] = useState(true);
  const [threadId, setThreadId] = useState(null);
  const [showSaveModal, setShowSaveModal] = useState(false);
  const [saveModalMessage, setSaveModalMessage] = useState("");
  const [assetName, setAssetName] = useState("");
  const [showAddResourceModal, setShowAddResourceModal] = useState(false);
  const [isSavingAsset, setIsSavingAsset] = useState(false);
  const [isSavingResource, setIsSavingResource] = useState(false);
  const [showSaveResourceModal, setShowSaveResourceModal] = useState(false);
  const [resourceFileName, setResourceFileName] = useState("");
  const [resourceSaveMessage, setResourceSaveMessage] = useState("");
  const hasInitializedRef = useRef(false);
  const isSendingRef = useRef(false);

  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [chatMessages]);

  useEffect(() => {
    const fetchResources = async () => {
      try {
        setResourcesLoading(true);
        const courseId = localStorage.getItem('currentCourseId');
        if (!courseId) {
          console.error('No current course ID found');
          setResources([]);
          return;
        }
        
        const resourcesData = await getAllResources(courseId);
        setResources(resourcesData.resources);
      } catch (error) {
        console.error("Error fetching resources:", error);
        setResources([]);
      } finally {
        setResourcesLoading(false);
      }
    };

    fetchResources();
  }, []);

  // Create initial AI message only after resources have finished loading
  useEffect(() => {
    const createInitialMessage = async () => {
      try {
        setIsLoading(true);
        const courseId = localStorage.getItem('currentCourseId');
        if (!courseId) {
          console.error('No course ID found');
          return;
        }

        // If concept-map, first generate image using the image endpoint
        if (option === 'concept-map') {
          try {
            const img = await assetService.generateImageAsset(courseId, 'concept-map');
            if (img && img.image_url) {
              setChatMessages([{ type: 'bot-image', url: img.image_url }]);
            }
          } catch (e) {
            console.error('Image generation failed, continuing with text prompt', e);
          }
        }

        // Create asset chat with all available files (or empty array if no files) for follow-up text
        const fileNames = resources.map(file => file.resourceName || file.fileName || file.id);
        const response = await assetService.createAssetChat(courseId, option, fileNames);
        if (response && response.response) {
          setChatMessages(prev => [...prev, { type: "bot", text: response.response }]);
          setThreadId(response.thread_id);
        }
      } catch (error) {
        console.error("Error creating initial message:", error);
        // Don't show any error message to user - just log it
      } finally {
        setIsLoading(false);
      }
    };

    // Guard against double-invocation and ensure resources have been fetched first
    if (!hasInitializedRef.current && !resourcesLoading && chatMessages.length === 0) {
      hasInitializedRef.current = true;
      createInitialMessage();
    }
  }, [resourcesLoading, resources, option, chatMessages.length]);

  const toggleSelect = (id) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((f) => f !== id) : [...prev, id]
    );
  };

  const handleSend = async () => {
    if (!inputMessage.trim()) return;
    if (isSendingRef.current || isLoading) return;
    isSendingRef.current = true;
    const newMsg = { type: "user", text: inputMessage };
    setChatMessages((prev) => [...prev, newMsg]);
    setInputMessage("");
    setIsLoading(true);

    try {
      if (!threadId) {
        throw new Error("No active chat thread");
      }

      const courseId = localStorage.getItem('currentCourseId');
      if (!courseId) {
        throw new Error("No course ID found");
      }

      console.log("Sending chat message:", {
        courseId,
        assetName: option,
        threadId,
        userPrompt: inputMessage
      });

      // Continue the conversation with the backend
      const response = await assetService.continueAssetChat(courseId, option, threadId, inputMessage);
      
      console.log("Backend response:", response);
      
      if (response && response.response) {
        const botResponse = {
          type: "bot",
          text: response.response
        };
        setChatMessages((prev) => [...prev, botResponse]);
      }
    } catch (err) {
      console.error("Chat error:", err);
      console.error("Error details:", err.message);
      const errorResponse = {
        type: "bot",
        text: "Sorry, I encountered an error. Please try again."
      };
      setChatMessages((prev) => [...prev, errorResponse]);
    } finally {
      setIsLoading(false);
      isSendingRef.current = false;
    }
  };

  const handleDownload = async (message) => {
    try {
      const safeTitle = (title || 'asset').toString().replace(/[^a-zA-Z0-9-_]/g, '_');
      await assetService.downloadContentAsPdf(safeTitle, message || '', {
        asset_type: option,
        asset_category: undefined,
        updated_by: undefined,
        updated_at: undefined,
      });
    } catch (e) {
      console.error('PDF download failed', e);
    }
  };

  const handleSaveToAsset = (message) => {
    setSaveModalMessage(message);
    setAssetName("");
    setShowSaveModal(true);
  };

  const handleSaveAssetConfirm = async () => {
    if (isSavingAsset) return;
    setIsSavingAsset(true);
    try {
      const courseId = localStorage.getItem('currentCourseId');
      if (!courseId) {
        console.error('No course ID found');
        return;
      }

      const assetType = option;

      await assetService.saveAsset(courseId, assetName, assetType, saveModalMessage);
      console.log(`✅ Asset "${assetName}" saved successfully!`);
      
      // Close modal and reset
      setShowSaveModal(false);
      setSaveModalMessage("");
      setAssetName("");
    } catch (error) {
      console.error("Error saving asset:", error);
      // Optionally surface to user
      // alert(error?.message || 'Failed to save asset');
    } finally {
      setIsSavingAsset(false);
    }
  };

  const handleSaveAssetCancel = () => {
    setShowSaveModal(false);
    setSaveModalMessage("");
    setAssetName("");
  };

  const handleSaveToResource = (message) => {
    setResourceSaveMessage(message || "");
    setResourceFileName("");
    setShowSaveResourceModal(true);
  };

  const handleSaveResourceConfirm = async () => {
    if (isSavingResource) return;
    setIsSavingResource(true);
    try {
      const courseId = localStorage.getItem('currentCourseId');
      if (!courseId) return;
      const baseName = (resourceFileName || '').trim() || 'document';
      const safeBase = baseName.replace(/[^a-zA-Z0-9-_ ]/g, '_');
      const finalFileName = safeBase.toLowerCase().endsWith('.pdf') ? safeBase : `${safeBase}.pdf`;
      const blob = await assetService.generateContentPdfBlob(safeBase, resourceSaveMessage || '', {
        asset_type: option
      });
      const file = new File([blob], finalFileName, { type: 'application/pdf' });
      await uploadCourseResources(courseId, [file]);
      const resourcesData = await getAllResources(courseId);
      setResources(resourcesData.resources);
      setShowSaveResourceModal(false);
      setResourceFileName("");
      setResourceSaveMessage("");
    } catch (e) {
      console.error('Failed to save to resources', e);
      alert('Failed to save to resources');
    } finally {
      setIsSavingResource(false);
    }
  };

  const handleSaveResourceCancel = () => {
    setShowSaveResourceModal(false);
    setResourceFileName("");
    setResourceSaveMessage("");
  };

  const handleFileUpload = () => {
    // For mock data, we'll just log the upload
    console.log("File upload triggered - in real implementation this would refresh from API");
  };

  // Add this handler to refresh resources after adding
  const handleAddResources = async (files) => {
    setShowAddResourceModal(false);
    const courseId = localStorage.getItem('currentCourseId');
    if (!courseId || !files.length) return;
    await uploadCourseResources(courseId, files); // upload to backend
    // Refresh resources
    const resourcesData = await getAllResources(courseId);
    setResources(resourcesData.resources);
  };

  const handleDeleteResource = async (resourceId) => {
    const courseId = localStorage.getItem('currentCourseId');
    if (!courseId) return;
    try {
      await deleteResourceApi(courseId, resourceId);
      // Refresh resources
      const resourcesData = await getAllResources(courseId);
      setResources(resourcesData.resources);
    } catch (err) {
      alert('Failed to delete resource.');
    }
  };

  return (
    <AssetStudioLayout
      title={title}
      rightPanel={
        <KnowledgeBase
          resources={resources}
          showCheckboxes
          selected={selectedIds}
          onSelect={toggleSelect}
          onSelectAll={(ids) => setSelectedIds(ids)}
          fileInputRef={{ current: null }}
          onFileChange={handleFileUpload}
          onAddResource={() => setShowAddResourceModal(true)}
          onDelete={handleDeleteResource}
        />
      }
    >
      <div
        style={{
          background: "#fff",
          borderRadius: 12,
          padding: 16,
          boxShadow: "0 2px 12px #0001",
          flex: 1,
          height: "400px",
          overflow: "hidden",
          display: "flex",
          flexDirection: "column"
        }}
      >
        <div
          style={{
            flex: 1,
            overflowY: "auto",
            paddingRight: 8
          }}
        >
          {chatMessages.map((msg, i) => (
            <div
              key={i}
              style={{
                display: "flex",
                justifyContent:
                  msg.type === "user" ? "flex-end" : "flex-start",
                marginBottom: 12
              }}
            >
              <div
                style={{
                  background: msg.type === "user" ? "#e0f2ff" : "transparent",
                  borderRadius: 10,
                  padding: msg.type === 'bot-image' ? '8px' : "10px 12px 26px 12px",
                  minWidth: msg.type === "user" ? "120px" : "0",
                  maxWidth: msg.type === "user" ? "60%" : "100%",
                  position: "relative",
                  color: "#222",
                  fontSize: 15,
                  textAlign: msg.type === "user" ? "right" : "left",
                  wordBreak: "break-word"
                }}
              >
                <div 
                  style={{ 
                    marginBottom: 6,
                    lineHeight: "1.5"
                  }}
                >
                  {msg.type === 'bot-image' ? (
                    <img src={msg.url} alt="Concept Map" style={{ maxWidth: '100%', borderRadius: 8 }} />
                  ) : msg.type === "bot" ? (
                    <div style={{ 
                      fontSize: "15px",
                      lineHeight: "1.6",
                      color: "#222"
                    }}>
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm, remarkBreaks]}
                        components={{
                          h1: ({children}) => <h1 style={{ fontSize: "20px", fontWeight: "bold", margin: "8px 0", color: "#222" }}>{children}</h1>,
                          h2: ({children}) => <h2 style={{ fontSize: "18px", fontWeight: "bold", margin: "8px 0", color: "#222" }}>{children}</h2>,
                          h3: ({children}) => <h3 style={{fontSize: "16px", fontWeight: "bold", margin: "8px 0", color: "#222"}}>{children}</h3>,
                          p: ({children}) => <p style={{ margin: "8px 0", color: "#222" }}>{children}</p>,
                          li: ({children}) => <li style={{ margin: "4px 0", color: "#222" }}>{children}</li>,
                          ul: ({children}) => <ul style={{margin: "8px 0", paddingLeft: "20px", color: "#222"}}>{children}</ul>,
                          ol: ({children}) => <ol style={{margin: "8px 0", paddingLeft: "20px", color: "#222"}}>{children}</ol>,
                          strong: ({children}) => <strong style={{fontWeight: "bold", color: "#222"}}>{children}</strong>,
                          em: ({children}) => <em style={{fontStyle: "italic", color: "#222"}}>{children}</em>,
                          code: ({children}) => <code style={{backgroundColor: "#f0f0f0", padding: "2px 4px", borderRadius: "3px", fontFamily: "monospace", fontSize: "14px", color: "#222"}}>{children}</code>,
                          pre: ({children}) => <pre style={{backgroundColor: "#f0f0f0", padding: "8px", borderRadius: "4px", overflow: "auto", margin: "8px 0", fontSize: "14px", color: "#222"}}>{children}</pre>,
                          blockquote: ({children}) => <blockquote style={{borderLeft: "4px solid #ddd", paddingLeft: "12px", margin: "8px 0", color: "#666"}}>{children}</blockquote>,
                          table: ({children}) => <table style={{borderCollapse: "collapse", width: "100%", margin: "8px 0", border: "1px solid #ddd", tableLayout: "fixed"}}>{children}</table>,
                          thead: ({children}) => <thead style={{backgroundColor: "#f5f5f5"}}>{children}</thead>,
                          tbody: ({children}) => <tbody>{children}</tbody>,
                          tr: ({children}) => <tr style={{borderBottom: "1px solid #ddd"}}>{children}</tr>,
                          th: ({children}) => <th style={{padding: "12px 8px", textAlign: "left", border: "1px solid #ddd", fontWeight: "bold", backgroundColor: "#f5f5f5", verticalAlign: "top", wordWrap: "break-word"}}>{children}</th>,
                          td: ({children}) => <td style={{padding: "12px 8px", textAlign: "left", border: "1px solid #ddd", verticalAlign: "top", wordWrap: "break-word", lineHeight: "1.4"}}>{children}</td>,
                          a: ({href, children}) => <a href={href} target="_blank" rel="noopener noreferrer" style={{ color: "#2563eb", textDecoration: "underline" }}>{children}</a>
                        }}
                      >
                        {msg.text}
                      </ReactMarkdown>
                    </div>
                  ) : (
                    <div style={{ color: "#222", whiteSpace: 'pre-wrap' }}>{msg.text}</div>
                  )}
                </div>
                {msg.type !== "user" && msg.type !== 'bot-image' && (
              <div
                style={{
                  position: "absolute",
                  bottom: 6,
                  left: 12,
                  display: "flex",
                  gap: 10,
                  fontSize: 15,
                  color: "#888"
                }}
              >
                <FaDownload
                  title="Download"
                  style={{ cursor: "pointer", opacity: 0.8 }}
                  onClick={() => handleDownload(msg.text)}
                />
                <FaFolderPlus
                  title="Save to Asset"
                  style={{ cursor: "pointer", opacity: 0.8 }}
                  onClick={() => handleSaveToAsset(msg.text)}
                />
                <FaSave
                  title="Save to Resource"
                  style={{ cursor: "pointer", opacity: 0.8 }}
                  onClick={() => handleSaveToResource(msg.text)}
                />
              </div>
            )}
              </div>
            </div>
          ))}

          {/* Typing indicator or first-response placeholder */}
          {isLoading && (
            chatMessages.length === 0 ? (
              <div
                style={{
                  display: "flex",
                  justifyContent: "flex-start",
                  marginBottom: 12
                }}
              >
                <div
                  style={{
                    background: "transparent",
                    borderRadius: 10,
                    padding: "10px 12px",
                    color: "#666",
                    fontSize: 14
                  }}
                >
                  Processing answer...
                </div>
              </div>
            ) : (
              <div style={{ display: "flex", justifyContent: "flex-start", padding: "4px 8px" }}>
                <style>{`
                  @keyframes blink { 0% { opacity: 0.2 } 20% { opacity: 1 } 100% { opacity: 0.2 } }
                `}</style>
                <div aria-label="Assistant is typing" style={{ display: "flex", alignItems: "center", gap: 6, color: "#888" }}>
                  <span style={{ display: "inline-block", width: 6, height: 6, background: "#bbb", borderRadius: "50%", animation: "blink 1.4s infinite" }}></span>
                  <span style={{ display: "inline-block", width: 6, height: 6, background: "#bbb", borderRadius: "50%", animation: "blink 1.4s infinite", animationDelay: "0.2s" }}></span>
                  <span style={{ display: "inline-block", width: 6, height: 6, background: "#bbb", borderRadius: "50%", animation: "blink 1.4s infinite", animationDelay: "0.4s" }}></span>
                </div>
              </div>
            )
          )}
          <div ref={bottomRef}></div>
        </div>
      </div>

      <div style={{ display: "flex", gap: 12, marginTop: 16 }}>
        <input
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              if (!isLoading) {
                handleSend();
              }
            }
          }}
          placeholder="Type your message..."
          style={{
            flex: 1,
            padding: "10px 12px",
            borderRadius: 8,
            border: "1px solid #ccc",
            fontSize: 15
          }}
        />
        <button
          onClick={handleSend}
          disabled={isLoading}
          style={{
            padding: "10px 18px",
            borderRadius: 8,
            background: "#2563eb",
            color: "#fff",
            border: "none",
            fontWeight: 500,
            cursor: isLoading ? "not-allowed" : "pointer"
          }}
        >
          {isLoading ? "..." : "Send"}
        </button>
      </div>

      {/* Save Asset Modal */}
      {showSaveModal && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "rgba(0, 0, 0, 0.5)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000
          }}
        >
          <div
            style={{
              background: "#fff",
              borderRadius: 12,
              padding: 24,
              width: "400px",
              maxWidth: "90vw",
              boxShadow: "0 4px 20px rgba(0, 0, 0, 0.15)"
            }}
          >
            <h3 style={{ margin: "0 0 16px 0", fontSize: 18, fontWeight: 600 }}>
              Save Asset
            </h3>
            
            <div style={{ marginBottom: 16 }}>
              <label style={{ display: "block", marginBottom: 8, fontWeight: 500 }}>
                Asset Name:
              </label>
              <input
                type="text"
                value={assetName}
                onChange={(e) => setAssetName(e.target.value)}
                style={{
                  width: "100%",
                  padding: "10px 12px",
                  borderRadius: 6,
                  border: "1px solid #ccc",
                  fontSize: 14,
                  boxSizing: "border-box"
                }}
                placeholder="Enter asset name..."
              />
            </div>

            <div style={{ display: "flex", gap: 12, justifyContent: "flex-end" }}>
              <button
                onClick={handleSaveAssetCancel}
                style={{
                  padding: "8px 16px",
                  borderRadius: 6,
                  border: "1px solid #ccc",
                  background: "#fff",
                  cursor: "pointer",
                  fontSize: 14
                }}
              >
                Cancel
              </button>
              <button
                onClick={handleSaveAssetConfirm}
                disabled={!assetName.trim() || isSavingAsset}
                style={{
                  padding: "8px 16px",
                  borderRadius: 6,
                  border: "none",
                  background: assetName.trim() && !isSavingAsset ? "#2563eb" : "#ccc",
                  color: "#fff",
                  cursor: assetName.trim() && !isSavingAsset ? "pointer" : "not-allowed",
                  fontSize: 14,
                  fontWeight: 500
                }}
              >
                {isSavingAsset ? "Saving..." : "Save Asset"}
              </button>
            </div>
          </div>
        </div>
      )}
      {showSaveResourceModal && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "rgba(0, 0, 0, 0.5)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000
          }}
        >
          <div
            style={{
              background: "#fff",
              borderRadius: 12,
              padding: 24,
              width: "400px",
              maxWidth: "90vw",
              boxShadow: "0 4px 20px rgba(0, 0, 0, 0.15)"
            }}
          >
            <h3 style={{ margin: "0 0 16px 0", fontSize: 18, fontWeight: 600 }}>
              Save to Resource
            </h3>

            <div style={{ marginBottom: 16 }}>
              <label style={{ display: "block", marginBottom: 8, fontWeight: 500 }}>
                File Name:
              </label>
              <input
                type="text"
                value={resourceFileName}
                onChange={(e) => setResourceFileName(e.target.value)}
                style={{
                  width: "100%",
                  padding: "10px 12px",
                  borderRadius: 6,
                  border: "1px solid #ccc",
                  fontSize: 14,
                  boxSizing: "border-box"
                }}
                placeholder="Enter file name (e.g., Outcome Draft)"
              />
            </div>

            <div style={{ display: "flex", gap: 12, justifyContent: "flex-end" }}>
              <button
                onClick={handleSaveResourceCancel}
                style={{
                  padding: "8px 16px",
                  borderRadius: 6,
                  border: "1px solid #ccc",
                  background: "#fff",
                  cursor: "pointer",
                  fontSize: 14
                }}
              >
                Cancel
              </button>
              <button
                onClick={handleSaveResourceConfirm}
                disabled={!resourceFileName.trim() || isSavingResource}
                style={{
                  padding: "8px 16px",
                  borderRadius: 6,
                  border: "none",
                  background: resourceFileName.trim() && !isSavingResource ? "#2563eb" : "#ccc",
                  color: "#fff",
                  cursor: resourceFileName.trim() && !isSavingResource ? "pointer" : "not-allowed",
                  fontSize: 14,
                  fontWeight: 500
                }}
              >
                {isSavingResource ? "Saving..." : "Save"}
              </button>
            </div>
          </div>
        </div>
      )}
      <AddResourceModal
        open={showAddResourceModal}
        onClose={() => setShowAddResourceModal(false)}
        onAdd={handleAddResources}
      />
    </AssetStudioLayout>
  );
}
