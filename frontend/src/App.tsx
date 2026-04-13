import { useEffect, useState } from "react";

type ApiState = {
  status: "loading" | "online" | "offline";
  details?: string;
};

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export default function App() {
  const [apiState, setApiState] = useState<ApiState>({ status: "loading" });

  useEffect(() => {
    let cancelled = false;

    async function checkApi() {
      try {
        const response = await fetch(`${apiBaseUrl}/api/v1/health`);
        if (!response.ok) {
          throw new Error(`Unexpected status: ${response.status}`);
        }

        const payload = (await response.json()) as { status: string };

        if (!cancelled) {
          setApiState({ status: "online", details: payload.status });
        }
      } catch (error) {
        if (!cancelled) {
          const message =
            error instanceof Error ? error.message : "Unable to reach backend";
          setApiState({ status: "offline", details: message });
        }
      }
    }

    void checkApi();

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <main className="app-shell">
      <section className="hero">
        <p className="eyebrow">Autonomous AI Software Corporation</p>
        <h1>Digital Company</h1>
        <p className="lede">
          Foundation scaffold for the autonomous software organization described
          in the Codex blueprint.
        </p>
      </section>

      <section className="status-panel">
        <div>
          <span className={`badge badge-${apiState.status}`}>
            {apiState.status}
          </span>
          <h2>System status</h2>
          <p>
            Backend endpoint: <code>{apiBaseUrl}/api/v1/health</code>
          </p>
        </div>
        <p className="status-copy">
          {apiState.status === "loading"
            ? "Checking backend reachability."
            : apiState.details}
        </p>
      </section>

      <section className="phase-grid">
        {[
          "Core backend and database",
          "Agent runtime",
          "Memory system",
          "Approval workflow",
          "Operator UI",
          "Self-improvement loop",
        ].map((phase) => (
          <article className="phase-card" key={phase}>
            <h3>{phase}</h3>
            <p>Planned for subsequent approved phases.</p>
          </article>
        ))}
      </section>
    </main>
  );
}

