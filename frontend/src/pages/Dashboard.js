import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Header from "../components/header/Header";
import SectionCard from "../components/SectionCard";
import KnowledgeBase from "../components/KnowledgBase";
import SettingsModal from "../components/SettingsModal";
import KnowledgeBaseSelectModal from "../components/KnowledgeBaseSelectModal";
import SelectionModal from "../components/SelectionModal";
import { getAllResources, uploadCourseResources, deleteResource as deleteResourceApi } from "../services/resources";
import { assetService } from "../services/asset";
import curriculumOptions from "../config/curriculumOptions";
import assessmentOptions from "../config/assessmentsOptions";
import AddResourceModal from '../components/AddReferencesModal';

export default function Dashboard() {
  const [showKBModal, setShowKBModal] = useState(false);
  const [selectedComponent, setSelectedComponent] = useState(null);
  const [showCurriculumModal, setShowCurriculumModal] = useState(false);
  const [showAssessmentModal, setShowAssessmentModal] = useState(false);
  const [selectedOption, setSelectedOption] = useState(0);
  const [selectedAssessmentOption, setSelectedAssessmentOption] = useState(0);
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [isGridView, setIsGridView] = useState(true);
  const [resources, setResources] = useState([]);
  const [loadingResources, setLoadingResources] = useState(true);
  const [assets, setAssets] = useState({ curriculum: [], assessments: [], evaluation: [] });
  const [, setLoadingAssets] = useState(true);
  const [showAddResourceModal, setShowAddResourceModal] = useState(false);
  const navigate = useNavigate();

  // Fetch resources on component mount
  useEffect(() => {
    const fetchResources = async () => {
      try {
        setLoadingResources(true);
        const courseId = localStorage.getItem('currentCourseId');
        if (!courseId) {
          console.error('No current course ID found');
          setResources([]);
          return;
        }
        
        const data = await getAllResources(courseId);
        // Transform the resources to match the expected format
        const transformedResources = (data.resources || []).map(resource => ({
          id: resource.resourceName,
          fileName: resource.resourceName,
          title: resource.resourceName,
          url: `#${resource.resourceName}` // Placeholder URL
        }));
        setResources(transformedResources);
      } catch (error) {
        console.error('Error fetching resources:', error);
        setResources([]);
      } finally {
        setLoadingResources(false);
      }
    };

    fetchResources();
  }, []);

  // Fetch assets on component mount
  useEffect(() => {
    const fetchAssets = async () => {
      try {
        setLoadingAssets(true);
        const courseId = localStorage.getItem('currentCourseId');
        if (!courseId) {
          console.error('No current course ID found');
          return;
        }
        
        const data = await assetService.getAssets(courseId);
        const assetsList = data.assets || [];
        
        // Group assets by category
        const groupedAssets = {
          curriculum: [],
          assessments: [],
          evaluation: []
        };
        
        assetsList.forEach(asset => {
          const category = asset.asset_category;
          if (groupedAssets.hasOwnProperty(category)) {
            groupedAssets[category].push({
              name: asset.asset_name,
              type: asset.asset_type,
              timestamp: asset.asset_last_updated_at,
              updatedBy: asset.asset_last_updated_by
            });
          }
        });
        
        setAssets(groupedAssets);
      } catch (error) {
        console.error('Error fetching assets:', error);
        setAssets({ curriculum: [], assessments: [], evaluation: [] });
      } finally {
        setLoadingAssets(false);
      }
    };

    fetchAssets();
  }, []);

  const handleCurriculumCreate = () => {
    setSelectedOption(0);
    setShowCurriculumModal(true);
  };

  const handleAssessmentCreate = () => {
    setSelectedAssessmentOption(0);
    setShowAssessmentModal(true);
  };

  const handleCurriculumSubmit = (selected) => {
    setShowCurriculumModal(false);
    setSelectedComponent(selected.url);
    setShowKBModal(true);
  };

  const handleAssessmentSubmit = (selected) => {
    setShowAssessmentModal(false);
    setSelectedComponent(selected.url);
    setShowKBModal(true);
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    navigate("/login");
  };

  // Add this handler to refresh resources after adding
  const handleAddResources = async (files) => {
    setShowAddResourceModal(false);
    const courseId = localStorage.getItem('currentCourseId');
    if (!courseId || !files.length) return;
    await uploadCourseResources(courseId, files); // upload to backend
    // Refresh resources
    const data = await getAllResources(courseId);
    const transformedResources = (data.resources || []).map(resource => ({
      id: resource.resourceName,
      fileName: resource.resourceName,
      title: resource.resourceName,
      url: `#${resource.resourceName}`
    }));
    setResources(transformedResources);
  };

  const handleDeleteResource = async (resourceId) => {
    const courseId = localStorage.getItem('currentCourseId');
    if (!courseId) return;
    try {
      await deleteResourceApi(courseId, resourceId);
      // Refresh resources
      const data = await getAllResources(courseId);
      const transformedResources = (data.resources || []).map(resource => ({
        id: resource.resourceName,
        fileName: resource.resourceName,
        title: resource.resourceName,
        url: `#${resource.resourceName}`
      }));
      setResources(transformedResources);
    } catch (err) {
      alert('Failed to delete resource.');
    }
  };

  return (
    <>
      <style>{`
        .dashboard-scroll-area::-webkit-scrollbar {
          width: 8px;
          background: transparent;
        }
        .dashboard-scroll-area::-webkit-scrollbar-thumb {
          background: #e0e7ef;
          border-radius: 6px;
        }
        .dashboard-scroll-area::-webkit-scrollbar-thumb:hover {
          background: #cbd5e1;
        }
        .dashboard-scroll-area {
          scrollbar-width: thin;
          scrollbar-color: #e0e7ef transparent;
        }
      `}</style>
      <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {/* Header and breadcrumbs (static) */}
        <Header
          title="Course Copilot"
          onLogout={handleLogout}
          onSettings={() => setShowSettingsModal(true)}
          onExport={() => alert("Export to LMS coming soon!")}
          onGridView={() => setIsGridView(true)}
          onListView={() => setIsGridView(false)}
          isGridView={isGridView}
        />

        {/* Breadcrumb */}
        <div style={{ maxWidth: 1200, margin: "1rem auto 0.5rem auto", width: "100%", display: 'flex', alignItems: 'center', gap: 10, fontSize: 18, fontWeight: 500 }}>
          <span style={{ color: '#2563eb', cursor: 'pointer', fontWeight: 600 }} onClick={() => navigate('/courses')}>Courses</span>
          <span style={{ color: '#888' }}>{'>'}</span>
          <span style={{ fontWeight: 700 }}>{localStorage.getItem("currentCourseTitle") || "Course Title"}</span>
        </div>

        <div style={{ flex: 1, display: 'flex', gap: 24, padding: '0 5vw', overflow: 'hidden' }}>
          {/* Main content area: scrollable */}
          <div className="dashboard-scroll-area" style={{ flex: 2, maxWidth: 900, width: '100%', margin: '0 auto', overflowY: 'auto', padding: '24px 0', display: 'flex', flexDirection: 'column', gap: 28 }}>
            <SectionCard 
              title="Curriculum" 
              buttonLabel="Create" 
              onButtonClick={handleCurriculumCreate}
              assets={assets.curriculum}
              courseId={localStorage.getItem('currentCourseId')}
            />
            <SectionCard 
              title="Assessments" 
              buttonLabel="Create" 
              onButtonClick={handleAssessmentCreate}
              assets={assets.assessments}
              courseId={localStorage.getItem('currentCourseId')}
            />
            <SectionCard 
              title="Evaluation" 
              buttonLabel="Start Evaluation"
              assets={assets.evaluation}
              courseId={localStorage.getItem('currentCourseId')}
            />
            {/* <div style={{ background: "#fff", borderRadius: 18, padding: 28, boxShadow: "0 4px 24px #0002" }}>
              <h2 style={{ margin: 0 }}>Sprint Plan <span style={{ fontSize: 13, fontWeight: 400, color: '#444' }}>(Based on the Academic term...)</span></h2>
              <button
                onClick={() => navigate("/studio/sprint-plan")}
                style={{ marginTop: 12, padding: "8px 22px", borderRadius: 6, border: "1px solid #bbb", background: "#fff", cursor: "pointer" }}
              >
                Create Documentation
              </button>
            </div> */}
          </div>
          {/* Right panel: Knowledge Base */}
          <div style={{ flex: 1, marginTop: 24, minWidth: 340, maxWidth: 420 }}>
            <KnowledgeBase
              resources={loadingResources ? [] : resources}
              fileInputRef={{ current: null }}
              onFileChange={() => {}}
              showCheckboxes={false}
              selected={[]}
              onSelect={() => {}}
              onAddResource={() => setShowAddResourceModal(true)}
              onDelete={handleDeleteResource}
            />
          </div>
        </div>

        {/* Selection Modals */}
        <SelectionModal
          open={showCurriculumModal}
          title="Curriculum"
          options={curriculumOptions}
          selectedOption={selectedOption}
          onSelect={setSelectedOption}
          onClose={() => setShowCurriculumModal(false)}
          onCreate={handleCurriculumSubmit}
        />

        <SelectionModal
          open={showAssessmentModal}
          title="Assessments"
          options={assessmentOptions}
          selectedOption={selectedAssessmentOption}
          onSelect={setSelectedAssessmentOption}
          onClose={() => setShowAssessmentModal(false)}
          onCreate={handleAssessmentSubmit}
        />

        {/* KB Selection Modal → AI Studio */}
        <KnowledgeBaseSelectModal
          open={showKBModal}
          onClose={() => setShowKBModal(false)}
          onGenerate={(selectedFiles) => {
            setShowKBModal(false);
            navigate(`/studio/${selectedComponent}`, {
              state: { selectedFiles }
            });
          }}
          files={loadingResources ? [] : resources}
        />

        <SettingsModal open={showSettingsModal} onClose={() => setShowSettingsModal(false)} />
        <AddResourceModal
          open={showAddResourceModal}
          onClose={() => setShowAddResourceModal(false)}
          onAdd={handleAddResources}
        />
      </div>
    </>
  );
}
