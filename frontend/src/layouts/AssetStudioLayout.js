import React from "react";
import SettingsModal from "../components/SettingsModal";
import StudioHeader from "../components/header/StudioHeader";
import { useNavigate } from "react-router-dom";
import { logout } from "../services/auth";

export default function AssetStudioLayout({ title = "AI Studio", children, rightPanel }) {
  const [showSettingsModal, setShowSettingsModal] = React.useState(false);
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div style={{ minHeight: "60vh", background: "#e6f0fc", display: "flex", flexDirection: "column" }}>
      {/* Header */}
      <StudioHeader
        title={title}
        onSettings={() => setShowSettingsModal(true)}
        onLogout={handleLogout}
      />

      {/* Content Area */}
      <div style={{
        display: "flex",
        justifyContent: "center",
        alignItems: "flex-start",
        gap: 20,
        padding: "24px 28px",
        flex: 1,
        overflow: "hidden"
      }}>
        {/* Left Main Panel */}
        <div style={{
          flex: 2,
          background: "#fff",
          borderRadius: 12,
          padding: 24,
          boxShadow: "0 2px 10px rgba(0,0,0,0.08)",
          minHeight: "75vh",
          overflowY: "auto"
        }}>
          {children}
        </div>

        {/* Right Knowledge Base */}
        <div style={{
          flex: 1,
          background: "#fefefe",
          borderRadius: 12,
          padding: 20,
          boxShadow: "0 1px 6px rgba(0,0,0,0.06)",
          minHeight: "75vh",
          overflowY: "auto"
        }}>
          {rightPanel}
        </div>
      </div>

      {/* Settings Modal */}
      <SettingsModal open={showSettingsModal} onClose={() => setShowSettingsModal(false)} />
    </div>
  );
}
