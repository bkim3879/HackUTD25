export function formatWorkOrderToText(work) {
  if (!work || typeof work !== "object") {
    return typeof work === "string" ? work : "(No work order content)";
  }

  const title = work.title || "Work Order";
  const impact = work.impact || "";
  const steps = Array.isArray(work.steps) ? work.steps : [];
  const materials = Array.isArray(work.materials) ? work.materials : [];
  const validation = Array.isArray(work.validation) ? work.validation : [];
  const refs = Array.isArray(work.jira_refs) ? work.jira_refs : [];

  const lines = [];
  lines.push(`Title: ${title}`);
  if (impact) lines.push(`Impact: ${impact}`);
  if (steps.length) {
    lines.push("\nSteps:");
    steps.forEach((s, i) => lines.push(`${i + 1}. ${s}`));
  }
  if (materials.length) {
    lines.push("\nMaterials:");
    materials.forEach((m) => lines.push(`- ${m}`));
  }
  if (validation.length) {
    lines.push("\nValidation:");
    validation.forEach((v) => lines.push(`- ${v}`));
  }
  if (refs.length) {
    lines.push("\nJira References:");
    lines.push(refs.join(", "));
  }

  return lines.join("\n");
}

export function extractLocationFromDescription(description) {
  if (!description || typeof description !== "string") return null;
  const text = description.toLowerCase();
  // Simple heuristics: look for 'rack <id>' and 'server <id>' or 'node <id>'
  const rackMatch = text.match(/rack\s+([a-z]\d{1,3})/i);
  const serverMatch = text.match(/server\s+([a-z0-9\-]+)/i) || text.match(/node\s+(\d{1,3})/i);
  const parts = [];
  if (rackMatch) parts.push(`Rack ${rackMatch[1].toUpperCase()}`);
  if (serverMatch) parts.push(`Server ${serverMatch[1]}`);
  if (parts.length) return parts.join(", ");
  // Also look for explicit 'location:'
  const locMatch = text.match(/location\s*:\s*([^\n]+)/i);
  if (locMatch) return locMatch[1].trim();
  return null;
}

// Returns structured location details if present in free-text descriptions.
// Example inputs it understands:
// - "GPU 4 in server 1 rack A12"
// - "rack 2 server 3 gpu #7"
// - "location: Rack B03, GPU 2"
export function extractLocationDetails(description) {
  if (!description || typeof description !== "string") return {};
  const text = description.toLowerCase();

  // Rack patterns: "rack A12", "rack 12", "rack b03"
  const rackMatch = text.match(/rack\s+([a-z]?[0-9]{1,3})\b/i);

  // Server/Node patterns: "server 1", "node 12"
  const serverMatch = text.match(/server\s+([a-z0-9\-]+)/i);
  const nodeMatch = text.match(/\bnode\s+([0-9]{1,3})\b/i);

  // GPU patterns: "gpu 4", "gpu #4", "gpu slot 4"
  const gpuMatch =
    text.match(/gpu\s*#?\s*([0-9]{1,3})\b/i) ||
    text.match(/gpu\s+slot\s*([a-z0-9\-]+)/i) ||
    text.match(/board\s*([0-9]{1,3})\b/i);

  // Fallback: parse after explicit "location:" label
  const explicitLoc = text.match(/location\s*:\s*([^\n]+)/i);

  const details = {};
  if (rackMatch) details.rack = rackMatch[1].toUpperCase();
  if (serverMatch) details.server = serverMatch[1];
  if (nodeMatch) details.node = nodeMatch[1];
  if (gpuMatch) details.gpu = gpuMatch[1];
  if (explicitLoc && !details.rack && !details.server && !details.node && !details.gpu) {
    details.freeform = explicitLoc[1].trim();
  }
  return details;
}
