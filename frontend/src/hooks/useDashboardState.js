import { useState, useRef } from "react";

export default function useDashboardState() {
  const [showKBModal, setShowKBModal] = useState(false);
  const [selectedComponent, setSelectedComponent] = useState(null);
  const [showCurriculumModal, setShowCurriculumModal] = useState(false);
  const [showAssessmentsModal, setShowAssessmentsModal] = useState(false);
  const [selectedOption, setSelectedOption] = useState(0);
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [isGridView, setIsGridView] = useState(true);
  const [resourceError, setResourceError] = useState("");
  const [showAddResourceModal, setShowAddResourceModal] = useState(false);
  const [resourceTab, setResourceTab] = useState(null);
  const [pendingFiles, setPendingFiles] = useState([]);
  const [uploadProgress, setUploadProgress] = useState([]);
  const [isUploading, setIsUploading] = useState(false);

  const sidebarRef = useRef();

  const handleCurriculumCreate = () => {
    setSelectedOption(0);
    setShowCurriculumModal(true);
  };

  const handleAssessmentsCreate = () => {
    setSelectedOption(0);
    setShowAssessmentsModal(true);
  };

  return {
    showKBModal, setShowKBModal,
    selectedComponent, setSelectedComponent,
    showCurriculumModal, setShowCurriculumModal,
    showAssessmentsModal, setShowAssessmentsModal,
    selectedOption, setSelectedOption,
    showSettingsModal, setShowSettingsModal,
    isGridView, setIsGridView,
    resourceError, setResourceError,
    showAddResourceModal, setShowAddResourceModal,
    resourceTab, setResourceTab,
    pendingFiles, setPendingFiles,
    uploadProgress, setUploadProgress,
    isUploading, setIsUploading,
    sidebarRef, 
    handleCurriculumCreate,
    handleAssessmentsCreate
  };
}
