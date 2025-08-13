export function useUploadHandler(courseId, sidebarRef, setResourceError) {
    const handleFilesUpload = async (files) => {
      if (!courseId) {
        console.error("No courseId set for upload!");
        return;
      }
  
      setResourceError("");
  
      try {
        // TODO: uploadCourseResources(courseId, files)
        console.log("Uploading files:", files);
  
        if (sidebarRef.current?.refreshResources) {
          sidebarRef.current.refreshResources();
        }
      } catch (err) {
        setResourceError("Failed to upload files");
      }
    };
  
    return handleFilesUpload;
  }
  