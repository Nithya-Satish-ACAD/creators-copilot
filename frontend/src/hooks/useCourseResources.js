import { useEffect, useState } from "react";

// TODO: Import actual service method
// import { getCourseResources } from "../services/resources";

export function useCourseResources(courseId, trigger) {
  const [allFiles, setAllFiles] = useState([]);

  useEffect(() => {
    async function fetchFiles() {
      if (!courseId) return;
      try {
        // Replace with: const data = await getCourseResources(courseId);
        const data = { resources: [] }; // dummy
        setAllFiles(data.resources || []);
      } catch (e) {
        setAllFiles([]);
      }
    }

    if (trigger) fetchFiles();
  }, [trigger, courseId]);

  return allFiles;
}
