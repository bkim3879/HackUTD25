import { useState } from "react";
import { Sidebar } from "./components/Sidebar.jsx";
import { Header } from "./components/Header.jsx";
import { MetricsGrid } from "./components/MetricsGrid.jsx";
import { WorkOrdersPanel } from "./components/WorkOrdersPanel.jsx";
import { DetailPanel } from "./components/DetailPanel.jsx";
import { UptimePanel } from "./components/UptimePanel.jsx";
import { AssistantPanel } from "./components/AssistantPanel.jsx";
import { assistantMessages, checklist, metrics, workOrders } from "./mockData.js";

export default function App() {
  const [selectedOrder, setSelectedOrder] = useState(workOrders[0]);
  const [messages, setMessages] = useState(assistantMessages);

  const handleSelectOrder = (order) => setSelectedOrder(order);

  const handleAssistantSubmit = (text) => {
    setMessages((prev) => [
      ...prev,
      { author: "user", text },
      {
        author: "ai",
        text: "Acknowledged. Logging action and syncing with Jira automations.",
      },
    ]);
  };

  return (
    <div className="app-shell">
      <Sidebar />
      <main className="main-panel">
        <Header />
        <MetricsGrid metrics={metrics} />
        <section className="main-grid">
          <WorkOrdersPanel
            orders={workOrders}
            selectedKey={selectedOrder?.key}
            onSelect={handleSelectOrder}
          />
          <UptimePanel />
          <DetailPanel order={selectedOrder} checklist={checklist} />
        </section>
      </main>
      <AssistantPanel messages={messages} onSubmit={handleAssistantSubmit} />
    </div>
  );
}
