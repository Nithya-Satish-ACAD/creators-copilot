import React, { useState } from "react";
import { FiEye } from "react-icons/fi";
import { assetService } from "../services/asset";
import AssetViewModal from "./AssetViewModal";

export default function AssetSubCard({ 
  label, 
  name, 
  updatedBy = "", 
  timestamp,
  courseId,
  onView,
  onDownload
}) {
  const [isLoading, setIsLoading] = useState(false);
  const [showViewModal, setShowViewModal] = useState(false);
  const [assetData, setAssetData] = useState(null);

  const handleView = async () => {
    if (!courseId || !name) return;
    
    setIsLoading(true);
    try {
      const asset = await assetService.viewAsset(courseId, name);
      setAssetData(asset);
      setShowViewModal(true);
      if (onView) {
        onView(asset);
      }
    } catch (error) {
      console.error('Error viewing asset:', error);
      alert('Failed to view asset. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <div
        style={{
          minWidth: 220,
          background: "#fff",
          border: "1px solid #e5e7eb",
          borderRadius: 14,
          boxShadow: "0 2px 8px #0001",
          padding: "18px 20px",
          display: "flex",
          flexDirection: "column",
          alignItems: "flex-start",
          position: "relative",
          marginRight: 12,
        }}
      >
        {/* Action button - top right */}
        <div
          style={{
            position: "absolute",
            top: 12,
            right: 12,
            display: "flex",
            gap: 6,
          }}
        >
          <button
            onClick={handleView}
            disabled={isLoading}
            style={{
              background: "transparent",
              border: "none",
              color: "#666",
              cursor: isLoading ? "not-allowed" : "pointer",
              padding: "4px",
              borderRadius: "4px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              transition: "all 0.2s ease",
              opacity: isLoading ? 0.5 : 1,
            }}
            onMouseEnter={(e) => {
              if (!isLoading) {
                e.currentTarget.style.background = "#f3f4f6";
                e.currentTarget.style.color = "#2563eb";
              }
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "transparent";
              e.currentTarget.style.color = "#666";
            }}
            title="View asset"
          >
            <FiEye size={16} />
          </button>
        </div>

        {/* Pill label */}
        <div
          style={{
            background: "#f3f4f6",
            color: "#444",
            fontWeight: 600,
            fontSize: 13,
            borderRadius: 16,
            padding: "2px 12px",
            marginBottom: 10,
            display: "inline-block",
          }}
        >
          {label}
        </div>
        {/* Asset name */}
        <div
          style={{
            fontWeight: 700,
            fontSize: 18,
            marginBottom: 8,
            paddingRight: 40, // Reduced padding since we only have one button now
          }}
        >
          {name}
        </div>
        {/* Last updated info */}
        <div
          style={{
            fontSize: 13,
            color: "#888",
            width: "100%",
          }}
        >
          <div style={{ 
            textAlign: "right",
            fontWeight: 500,
            color: "#666",
            marginBottom: 2
          }}>
            Last updated by {updatedBy}
          </div>
          <div style={{ 
            textAlign: "right",
            fontSize: 12,
            color: "#999"
          }}>
            {timestamp
              ? new Date(timestamp).toLocaleString("en-US", {
                  month: "short",
                  day: "numeric",
                  hour: "numeric",
                  minute: "2-digit",
                })
              : ""}
          </div>
        </div>
      </div>

      {/* Asset View Modal */}
      <AssetViewModal
        open={showViewModal}
        onClose={() => setShowViewModal(false)}
        assetData={assetData}
        courseId={courseId}
      />
    </>
  );
}