import { useEffect, useMemo, useState } from "react";
import { Sidebar } from "./components/Sidebar.jsx";
import { Header } from "./components/Header.jsx";
import { MetricsGrid } from "./components/MetricsGrid.jsx";
import { WorkOrdersPanel } from "./components/WorkOrdersPanel.jsx";
import { CompletedWorkOrdersPanel } from "./components/CompletedWorkOrdersPanel.jsx";
import { DetailPanel } from "./components/DetailPanel.jsx";
import { AssistantPanel } from "./components/AssistantPanel.jsx";
  import {
    addTechnicianNote,
    fetchWorkorderDetail,
    fetchWorkorders,
    generateWorkorderUpdate,
    refreshWorkorders,
    updateWorkorderStep,
    completeWorkorder,
  } from "./api.js";
  import { formatWorkOrderToText } from "./formatters.js";
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
  const [view, setView] = useState("dashboard");

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

  const handleSelectOrder = (order) => {
    setSelectedKey(order.key);
  };

  const handleNavigate = (next) => {
    setView(next);
  };

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
              ? `${response.warning ? `[${response.warning}]\n` : ""}${formatWorkOrderToText(
                  response.work_order
                )}`
              : response.missing_fields?.length
                ? `Missing Jira info: ${response.missing_fields.join(", ")}. Please update the ticket and try again.`
                : "Unable to generate update.",
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
      .then((resp) => {
        setSelectedDetail((prev) => {
          if (!prev) return prev;
          const nextStep = resp?.step || resp; // support both {step: {...}} and bare step
          const steps = prev.steps?.map((item, idx) => (idx === index ? nextStep : item));
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

  const handleComplete = (resolutionComment) => {
    if (!selectedKey) return;
    const currentId = selectedDetail?.jira_id || selectedKey;
    completeWorkorder(currentId, "31", resolutionComment)
      .then((resp) => {
        // update completed flag and optionally add note
        setSelectedDetail((prev) => (prev ? { ...prev, completed: true } : prev));
        if (resolutionComment) {
          setSelectedDetail((prev) => {
            if (!prev) return prev;
            const notes = [
              ...(prev.notes || []),
              { author: "System", note: resolutionComment, timestamp: new Date().toISOString() },
            ];
            return { ...prev, notes };
          });
        }
        // Automatically refresh queues and detail to reflect completion
        return refreshWorkorders()
          .then(fetchWorkorders)
          .then((payload) => {
            const results = payload.results || [];
            setOrders(results);
            if (currentId) {
              setSelectedKey(currentId);
              return fetchWorkorderDetail(currentId)
                .then((record) => setSelectedDetail(record))
                .catch((err) => setError(err.message));
            }
          })
          .finally(() => {
            // Navigate back to the work order list view after completion
            setView("workorders");
          });
      })
      .catch((err) => setError(err.message));
  };

  const selectedOrder = useMemo(
    () => orders.find((order) => order.key === selectedKey) || null,
    [orders, selectedKey],
  );

  const openOrders = useMemo(() => orders.filter((o) => !o.completed), [orders]);
  const completedOrders = useMemo(() => orders.filter((o) => o.completed), [orders]);

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
      <Sidebar active={view} onNavigate={handleNavigate} />
      <main className="main-panel">
        <Header onRefresh={handleRefresh} loading={loading} error={error} />
        {view === "dashboard" && (
          <>
            <MetricsGrid metrics={metrics} />
            <section className="main-grid">
              <WorkOrdersPanel
                orders={openOrders}
                selectedKey={selectedKey}
                loading={loading}
                onRefresh={handleRefresh}
                onSelect={handleSelectOrder}
                onOpenSelected={() => setView("workorderDetail")}
              />
              <CompletedWorkOrdersPanel
                orders={completedOrders}
                selectedKey={selectedKey}
                onSelect={handleSelectOrder}
                onOpenSelected={() => setView("workorderDetail")}
              />
            </section>
          </>
        )}

        {/* Workorders tab removed; list is available on Dashboard only */}

        {view === "workorderDetail" && (
          <section className="main-grid">
            <div className="panel panel--wide" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <h3>Work Order</h3>
              <button className="button ghost" type="button" onClick={() => setView("dashboard")}>Back to List</button>
            </div>
            <DetailPanel
              order={selectedDetail}
              loading={detailLoading}
              onStepUpdate={handleStepUpdate}
              onAddNote={handleAddNote}
              onComplete={handleComplete}
            />
          </section>
        )}

        {view === "tools" && (
          <section className="main-grid">
            <div className="panel panel--wide">
              <h3>Technician Tools</h3>
              <p>Use the assistant on the right to request next steps, summaries, or SOP lookups.</p>
            </div>
          </section>
        )}

        {view === "settings" && (
          <section className="main-grid">
            <div className="panel panel--wide">
              <h3>Settings</h3>
              <p>No settings available in this demo build.</p>
            </div>
          </section>
        )}
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
