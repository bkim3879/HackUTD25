export const metrics = [
  {
    label: "GPU Uptime %",
    value: "99.74%",
    trend: "+0.3% vs 24h",
    direction: "up",
  },
  {
    label: "Active Work Orders",
    value: "28",
    trend: "5 critical in queue",
    direction: "flat",
  },
  {
    label: "Avg. Resolution Time",
    value: "3.2 hrs",
    trend: "-12% vs last week",
    direction: "down",
  },
];

export const workOrders = [
  {
    key: "DWOS-118",
    summary: "GPU thermal excursion on rack A12",
    priority: "Critical",
    status: "In Progress",
    assignee: "R. Patel",
    updated: "3 min ago",
  },
  {
    key: "DWOS-117",
    summary: "Switch fabric packet loss",
    priority: "High",
    status: "Waiting Parts",
    assignee: "L. Chen",
    updated: "18 min ago",
  },
  {
    key: "DWOS-113",
    summary: "Firmware drift detected zone C",
    priority: "Medium",
    status: "Triaged",
    assignee: "AutoBot",
    updated: "42 min ago",
  },
  {
    key: "DWOS-110",
    summary: "Rack power audit for cluster 9",
    priority: "Low",
    status: "Done",
    assignee: "K. Jordan",
    updated: "1 hr ago",
  },
];

export const checklist = [
  { text: "Confirm rack temperature sensors", done: true },
  { text: "Throttle workload via scheduler", done: true },
  { text: "Dispatch field tech with liquid loop kit", done: false },
  { text: "Validate GPU stability post-fix", done: false },
];

export const assistantMessages = [
  {
    author: "ai",
    text: "Monitoring GPU connectivity, GPU rack 12 has high packet loss. Recommend focusing there first.",
  },
  {
    author: "user",
    text: "Recommended approach?",
  },
  {
    author: "ai",
    text: "Initial triage suggests a potential faulty switch. Advise checking switch logs and performing a physical inspection of rack 12's network connections.",
  },
];
