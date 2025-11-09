import { useEffect, useMemo, useState } from "react";
import { Sidebar } from "./components/Sidebar.jsx";
import { Header } from "./components/Header.jsx";
import { MetricsGrid } from "./components/MetricsGrid.jsx";
import { WorkOrdersPanel } from "./components/WorkOrdersPanel.jsx";
import { DetailPanel } from "./components/DetailPanel.jsx";
import { UptimePanel } from "./components/UptimePanel.jsx";
import { AssistantPanel } from "./components/AssistantPanel.jsx";
import {
  addTechnicianNote,
  fetchWorkorderDetail,
  fetchWorkorders,
  generateWorkorderUpdate,
  refreshWorkorders,
  updateWorkorderStep,
} from "./api.js";
import { assistantMessages as mockAssistantMessages, metrics as mockMetrics } from "./mockData.js";

export default function App() {
  const [orders, setOrders] = useState([]);
  const [selectedKey, setSelectedKey] = useState(null);
  const [selectedDetail, setSelectedDetail] = useState(null);
  const [messages, setMessages] = useState(mockAssistantMessages);
  const [loading, setLoading] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState(null);
  const [assistantBusy, setAssistantBusy] = useState(false);

  useEffect(() => {
    setLoading(true);
    fetchWorkorders()
      .then((payload) => {
        setOrders(payload.results || []);
        if ((payload.results || []).length) {
          setSelectedKey(payload.results[0].key);
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!selectedKey) return;
    setDetailLoading(true);
    fetchWorkorderDetail(selectedKey)
      .then((record) => setSelectedDetail(record))
      .catch((err) => setError(err.message))
      .finally(() => setDetailLoading(false));
  }, [selectedKey]);

  const handleRefresh = () => {
    setLoading(true);
    refreshWorkorders()
      .then(fetchWorkorders)
      .then((payload) => {
        setOrders(payload.results || []);
        if ((payload.results || []).length) {
          setSelectedKey(payload.results[0].key);
        } else {
          setSelectedDetail(null);
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  };

  const handleSelectOrder = (order) => setSelectedKey(order.key);

  const handleAssistantSubmit = (text) => {
    if (!selectedKey) return;
    setAssistantBusy(true);
    setMessages((prev) => [
      ...prev,
      { author: "user", text },
    ]);
    generateWorkorderUpdate(selectedDetail?.jira_id || selectedKey, text, selectedDetail?.key)
      .then((response) => {
        setMessages((prev) => [
          ...prev,
          {
            author: "ai",
            text: response.work_order
              ? `Proposed update:\n${JSON.stringify(response.work_order, null, 2)}`
              : "Unable to generate update. Please ensure Jira fields are complete.",
          },
        ]);
      })
      .catch((err) => {
        setMessages((prev) => [...prev, { author: "ai", text: `Error: ${err.message}` }]);
      })
      .finally(() => setAssistantBusy(false));
  };

  const handleStepUpdate = (index, status) => {
    if (!selectedKey) return;
    updateWorkorderStep(selectedKey, index, status)
      .then((step) => {
        setSelectedDetail((prev) => {
          if (!prev) return prev;
          const steps = prev.steps?.map((item, idx) => (idx === index ? step : item));
          return { ...prev, steps };
        });
      })
      .catch((err) => setError(err.message));
  };

  const handleAddNote = (author, note) => {
    if (!selectedKey) return;
    addTechnicianNote(selectedKey, author, note)
      .then((resp) => {
        setSelectedDetail((prev) => {
          if (!prev) return prev;
          const notes = [...(prev.notes || []), resp.entry];
          return { ...prev, notes };
        });
      })
      .catch((err) => setError(err.message));
  };

  const selectedOrder = useMemo(
    () => orders.find((order) => order.key === selectedKey) || null,
    [orders, selectedKey],
  );

  const metrics = useMemo(() => {
    if (!orders.length) return mockMetrics;
    const openCritical = orders.filter((order) => (order.priority || "").toLowerCase().includes("high")).length;
    return [
      {
        label: "GPU Uptime %",
        value: "99.7%",
        trend: `${orders.length} active tickets`,
        direction: "flat",
      },
      {
        label: "Active Work Orders",
        value: `${orders.length}`,
        trend: `${openCritical} high priority`,
        direction: openCritical > 0 ? "up" : "flat",
      },
      {
        label: "Avg. Resolution Time",
        value: "3.3 hrs",
        trend: "Rolling 24h",
        direction: "flat",
      },
    ];
  }, [orders]);

  return (
    <div className="app-shell">
      <Sidebar />
      <main className="main-panel">
        <Header onRefresh={handleRefresh} loading={loading} error={error} />
        <MetricsGrid metrics={metrics} />
        <section className="main-grid">
          <WorkOrdersPanel
            orders={orders}
            selectedKey={selectedKey}
            loading={loading}
            onRefresh={handleRefresh}
            onSelect={handleSelectOrder}
          />
          <UptimePanel />
          <DetailPanel
            order={selectedDetail}
            loading={detailLoading}
            onStepUpdate={handleStepUpdate}
            onAddNote={handleAddNote}
          />
        </section>
      </main>
      <AssistantPanel
        messages={messages}
        onSubmit={handleAssistantSubmit}
        disabled={!selectedKey}
        busy={assistantBusy}
        contextKey={selectedKey}
      />
    </div>
  );
}
