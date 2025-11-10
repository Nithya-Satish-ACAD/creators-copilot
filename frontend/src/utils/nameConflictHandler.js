/**
 * Handles name conflicts by adding a number in parentheses
 * @param {string} name - The original name
 * @param {Array} existingNames - Array of existing names to check against
 * @returns {string} - The name with conflict resolution
 */
export function resolveNameConflict(name, existingNames) {
  if (!existingNames || existingNames.length === 0) {
    return name;
  }

  // Check if the name already exists
  const nameExists = existingNames.includes(name);
  
  if (!nameExists) {
    return name;
  }

  // Find the next available number
  let counter = 1;
  let newName = `${name} (${counter})`;
  
  while (existingNames.includes(newName)) {
    counter++;
    newName = `${name} (${counter})`;
  }
  
  return newName;
}

/**
 * Gets all existing asset names from the assets object
 * @param {Object} assets - Assets object with curriculum, assessments, evaluation arrays
 * @returns {Array} - Array of all asset names
 */
export function getAllAssetNames(assets) {
  const allNames = [];
  
  if (assets?.curriculum) {
    allNames.push(...assets.curriculum.map(asset => asset.name));
  }
  
  if (assets?.assessments) {
    allNames.push(...assets.assessments.map(asset => asset.name));
  }
  
  if (assets?.evaluation) {
    allNames.push(...assets.evaluation.map(asset => asset.name));
  }
  
  return allNames;
}

/**
 * Gets all existing resource names from the resources array
 * @param {Array} resources - Array of resource objects
 * @returns {Array} - Array of all resource names
 */
export function getAllResourceNames(resources) {
  if (!resources || !Array.isArray(resources)) {
    return [];
  }
  
  return resources.map(resource => 
    resource.resourceName || resource.fileName || resource.title || resource.name
  ).filter(Boolean); // Remove any undefined/null values
}
