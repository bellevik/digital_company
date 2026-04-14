import { FormEvent, useEffect, useState } from "react";

type ApiState = {
  status: "loading" | "online" | "offline";
  details?: string;
};

type TaskStatus = "todo" | "in_progress" | "done" | "failed";
type TaskType = "feature" | "bugfix" | "research" | "review" | "ops";
type AgentRole =
  | "designer"
  | "architect"
  | "developer"
  | "tester"
  | "reviewer"
  | "review_agent";
type AgentStatus = "idle" | "busy" | "offline";
type ApprovalStatus =
  | "not_required"
  | "pending_approval"
  | "approved"
  | "changes_requested";
type ReviewDecisionType = "approved" | "changes_requested";
type MemoryType = "conversation" | "decision" | "task_result" | "note";
type TaskRunStatus = "running" | "succeeded" | "failed";
type SearchStrategy = "keyword" | "vector" | "hybrid";

type Task = {
  id: string;
  title: string;
  description: string;
  type: TaskType;
  status: TaskStatus;
  assigned_agent_id: string | null;
  project_id: string | null;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
};

type Agent = {
  id: string;
  name: string;
  role: AgentRole;
  status: AgentStatus;
  current_task_id: string | null;
  created_at: string;
  updated_at: string;
};

type Memory = {
  id: string;
  type: MemoryType;
  summary: string;
  content: string;
  source_task_id: string | null;
  created_at: string;
  updated_at: string;
};

type MemorySearchResult = {
  memory_id: string;
  type: MemoryType;
  summary: string;
  content: string;
  source_task_id: string | null;
  created_at: string;
  keyword_score: number;
  vector_score: number;
  combined_score: number;
};

type TaskRun = {
  id: string;
  task_id: string;
  agent_id: string;
  status: TaskRunStatus;
  prompt: string;
  stdout: string;
  stderr: string;
  exit_code: number | null;
  result_payload: Record<string, unknown>;
  created_follow_up_tasks: number;
  started_at: string;
  finished_at: string | null;
  created_at: string;
  updated_at: string;
};

type ReviewDecision = {
  id: string;
  task_id: string;
  task_workflow_id: string;
  task_run_id: string | null;
  reviewer_name: string;
  decision: ReviewDecisionType;
  summary: string;
  created_at: string;
  updated_at: string;
};

type Workflow = {
  id: string;
  task_id: string;
  latest_task_run_id: string | null;
  approval_status: ApprovalStatus;
  branch_name: string | null;
  submission_notes: string | null;
  submitted_for_review_at: string | null;
  reviewed_at: string | null;
  created_at: string;
  updated_at: string;
  latest_task_run: TaskRun | null;
  review_decisions: ReviewDecision[];
};

type TaskEvent = {
  id: string;
  task_id: string | null;
  agent_id: string | null;
  event_type: string;
  payload: Record<string, unknown>;
  created_at: string;
};

type WorkerCycleResponse = {
  agent_id: string;
  outcome: string;
  task_id: string | null;
  task_run: TaskRun | null;
  memory_id: string | null;
  follow_up_task_ids: string[];
};

type SystemSummary = {
  tasks_total: number;
  tasks_todo: number;
  tasks_in_progress: number;
  tasks_done: number;
  tasks_failed: number;
  agents_total: number;
  agents_idle: number;
  agents_busy: number;
  agents_offline: number;
  workflows_pending: number;
  memories_total: number;
  task_runs_total: number;
  self_improvement_runs_total: number;
  scheduler_enabled: boolean;
  scheduler_running: boolean;
};

type SelfImprovementRun = {
  id: string;
  status: "running" | "succeeded" | "failed";
  trigger_mode: "manual" | "scheduled" | "seeded";
  summary: string;
  proposed_branch_name: string;
  proposed_pr_title: string;
  created_task_count: number;
  payload: Record<string, unknown>;
  started_at: string;
  finished_at: string | null;
  created_at: string;
  updated_at: string;
};

type SeedDemoResponse = {
  created_agents: number;
  created_tasks: number;
  created_memories: number;
  message: string;
};

type Toast = {
  tone: "info" | "success" | "error";
  message: string;
};

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
const refreshIntervalMs = 6000;

const defaultTaskDraft = {
  title: "",
  description: "",
  type: "feature" as TaskType,
  projectId: "",
};

const defaultAgentDraft = {
  name: "",
  role: "developer" as AgentRole,
};

const defaultReviewDraft = {
  branchName: "codex/",
  submissionNotes: "",
  reviewerName: "CEO",
  decision: "approved" as ReviewDecisionType,
  summary: "",
};

export default function App() {
  const [apiState, setApiState] = useState<ApiState>({ status: "loading" });
  const [toast, setToast] = useState<Toast | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [taskRuns, setTaskRuns] = useState<TaskRun[]>([]);
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [memories, setMemories] = useState<Memory[]>([]);
  const [systemSummary, setSystemSummary] = useState<SystemSummary | null>(null);
  const [selfImprovementRuns, setSelfImprovementRuns] = useState<
    SelfImprovementRun[]
  >([]);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [selectedTaskEvents, setSelectedTaskEvents] = useState<TaskEvent[]>([]);
  const [taskDraft, setTaskDraft] = useState(defaultTaskDraft);
  const [agentDraft, setAgentDraft] = useState(defaultAgentDraft);
  const [reviewDraft, setReviewDraft] = useState(defaultReviewDraft);
  const [memoryQuery, setMemoryQuery] = useState("task locking");
  const [memoryStrategy, setMemoryStrategy] = useState<SearchStrategy>("hybrid");
  const [memoryResults, setMemoryResults] = useState<MemorySearchResult[]>([]);
  const [isSubmittingTask, setIsSubmittingTask] = useState(false);
  const [isSubmittingAgent, setIsSubmittingAgent] = useState(false);
  const [isRunningAgentId, setIsRunningAgentId] = useState<string | null>(null);
  const [isSubmittingWorkflow, setIsSubmittingWorkflow] = useState(false);
  const [isRunningSelfImprovement, setIsRunningSelfImprovement] = useState(false);
  const [isSeedingDemo, setIsSeedingDemo] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setIsRefreshing(true);
      try {
        const [
          tasksResponse,
          agentsResponse,
          taskRunsResponse,
          workflowsResponse,
          memoriesResponse,
          summaryResponse,
          selfImprovementRunsResponse,
        ] = await Promise.all([
          apiGet<Task[]>("/api/v1/tasks"),
          apiGet<Agent[]>("/api/v1/agents"),
          apiGet<TaskRun[]>("/api/v1/task-runs"),
          apiGet<Workflow[]>("/api/v1/workflows"),
          apiGet<Memory[]>("/api/v1/memory"),
          apiGet<SystemSummary>("/api/v1/operations/summary"),
          apiGet<SelfImprovementRun[]>("/api/v1/operations/self-improvement/runs"),
        ]);

        if (cancelled) {
          return;
        }

        setTasks(tasksResponse);
        setAgents(agentsResponse);
        setTaskRuns(taskRunsResponse);
        setWorkflows(workflowsResponse);
        setMemories(memoriesResponse);
        setSystemSummary(summaryResponse);
        setSelfImprovementRuns(selfImprovementRunsResponse);
        setApiState({ status: "online", details: "operator backend reachable" });
        setSelectedTaskId((current) =>
          current && tasksResponse.some((task) => task.id === current)
            ? current
            : tasksResponse[0]?.id ?? null,
        );
      } catch (error) {
        if (cancelled) {
          return;
        }
        setApiState({
          status: "offline",
          details:
            error instanceof Error ? error.message : "Unable to reach backend",
        });
      } finally {
        if (!cancelled) {
          setIsRefreshing(false);
        }
      }
    }

    void load();
    const intervalId = window.setInterval(() => {
      void load();
    }, refreshIntervalMs);

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function loadTaskEvents() {
      if (!selectedTaskId) {
        setSelectedTaskEvents([]);
        return;
      }

      try {
        const payload = await apiGet<TaskEvent[]>(
          `/api/v1/tasks/${selectedTaskId}/events`,
        );
        if (!cancelled) {
          setSelectedTaskEvents(payload);
        }
      } catch (error) {
        if (!cancelled) {
          setSelectedTaskEvents([]);
          pushToast(
            setToast,
            "error",
            error instanceof Error
              ? error.message
              : "Unable to load task activity.",
          );
        }
      }
    }

    void loadTaskEvents();

    return () => {
      cancelled = true;
    };
  }, [selectedTaskId]);

  const selectedTask =
    tasks.find((task) => task.id === selectedTaskId) ?? tasks[0] ?? null;
  const selectedWorkflow =
    workflows.find((workflow) => workflow.task_id === selectedTask?.id) ?? null;
  const selectedTaskRuns = selectedTask
    ? taskRuns.filter((taskRun) => taskRun.task_id === selectedTask.id)
    : [];
  const selectedAgent = selectedTask?.assigned_agent_id
    ? agents.find((agent) => agent.id === selectedTask.assigned_agent_id) ?? null
    : null;

  async function refreshDashboard() {
    const payload = await Promise.all([
      apiGet<Task[]>("/api/v1/tasks"),
      apiGet<Agent[]>("/api/v1/agents"),
      apiGet<TaskRun[]>("/api/v1/task-runs"),
      apiGet<Workflow[]>("/api/v1/workflows"),
      apiGet<Memory[]>("/api/v1/memory"),
      apiGet<SystemSummary>("/api/v1/operations/summary"),
      apiGet<SelfImprovementRun[]>("/api/v1/operations/self-improvement/runs"),
    ]);
    setTasks(payload[0]);
    setAgents(payload[1]);
    setTaskRuns(payload[2]);
    setWorkflows(payload[3]);
    setMemories(payload[4]);
    setSystemSummary(payload[5]);
    setSelfImprovementRuns(payload[6]);
  }

  async function handleCreateTask(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmittingTask(true);
    try {
      await apiPost<Task>("/api/v1/tasks", {
        title: taskDraft.title,
        description: taskDraft.description,
        type: taskDraft.type,
        project_id: taskDraft.projectId.trim() || null,
      });
      setTaskDraft(defaultTaskDraft);
      await refreshDashboard();
      pushToast(setToast, "success", "Task created.");
    } catch (error) {
      pushToast(
        setToast,
        "error",
        error instanceof Error ? error.message : "Unable to create task.",
      );
    } finally {
      setIsSubmittingTask(false);
    }
  }

  async function handleCreateAgent(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmittingAgent(true);
    try {
      await apiPost<Agent>("/api/v1/agents", {
        name: agentDraft.name,
        role: agentDraft.role,
      });
      setAgentDraft(defaultAgentDraft);
      await refreshDashboard();
      pushToast(setToast, "success", "Agent created.");
    } catch (error) {
      pushToast(
        setToast,
        "error",
        error instanceof Error ? error.message : "Unable to create agent.",
      );
    } finally {
      setIsSubmittingAgent(false);
    }
  }

  async function handleRunAgent(agentId: string) {
    setIsRunningAgentId(agentId);
    try {
      const payload = await apiPost<WorkerCycleResponse>(
        `/api/v1/agents/${agentId}/work`,
        {},
      );
      await refreshDashboard();
      pushToast(
        setToast,
        payload.outcome === "failed" ? "error" : "success",
        payload.outcome === "idle"
          ? "No compatible work was available."
          : `Agent cycle finished with outcome: ${payload.outcome}.`,
      );
    } catch (error) {
      pushToast(
        setToast,
        "error",
        error instanceof Error ? error.message : "Unable to run agent.",
      );
    } finally {
      setIsRunningAgentId(null);
    }
  }

  async function handleSubmitForReview() {
    if (!selectedTask) {
      return;
    }

    setIsSubmittingWorkflow(true);
    try {
      await apiPost<Workflow>(
        `/api/v1/tasks/${selectedTask.id}/submit-for-review`,
        {
          branch_name: reviewDraft.branchName,
          submission_notes: reviewDraft.submissionNotes.trim() || null,
        },
      );
      await refreshDashboard();
      pushToast(setToast, "success", "Task submitted for review.");
    } catch (error) {
      pushToast(
        setToast,
        "error",
        error instanceof Error ? error.message : "Unable to submit task.",
      );
    } finally {
      setIsSubmittingWorkflow(false);
    }
  }

  async function handleRecordDecision() {
    if (!selectedTask) {
      return;
    }

    setIsSubmittingWorkflow(true);
    try {
      await apiPost<Workflow>(
        `/api/v1/tasks/${selectedTask.id}/review-decisions`,
        {
          reviewer_name: reviewDraft.reviewerName,
          decision: reviewDraft.decision,
          summary: reviewDraft.summary,
        },
      );
      await refreshDashboard();
      setReviewDraft((current) => ({ ...current, summary: "" }));
      pushToast(setToast, "success", "Review decision recorded.");
    } catch (error) {
      pushToast(
        setToast,
        "error",
        error instanceof Error ? error.message : "Unable to record decision.",
      );
    } finally {
      setIsSubmittingWorkflow(false);
    }
  }

  async function handleSearchMemory(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      const params = new URLSearchParams({
        query: memoryQuery,
        strategy: memoryStrategy,
      });
      if (selectedTask?.project_id) {
        params.set("project_id", selectedTask.project_id);
      }
      const payload = await apiGet<MemorySearchResult[]>(
        `/api/v1/memory/search?${params.toString()}`,
      );
      setMemoryResults(payload);
      pushToast(setToast, "info", "Memory search refreshed.");
    } catch (error) {
      pushToast(
        setToast,
        "error",
        error instanceof Error ? error.message : "Unable to search memory.",
      );
    }
  }

  async function handleRunSelfImprovement() {
    setIsRunningSelfImprovement(true);
    try {
      const payload = await apiPost<SelfImprovementRun>(
        "/api/v1/operations/self-improvement/run",
        {},
      );
      await refreshDashboard();
      pushToast(setToast, "success", payload.summary);
    } catch (error) {
      pushToast(
        setToast,
        "error",
        error instanceof Error
          ? error.message
          : "Unable to trigger self-improvement.",
      );
    } finally {
      setIsRunningSelfImprovement(false);
    }
  }

  async function handleSeedDemo() {
    setIsSeedingDemo(true);
    try {
      const payload = await apiPost<SeedDemoResponse>("/api/v1/operations/seed-demo", {});
      await refreshDashboard();
      pushToast(
        setToast,
        "success",
        `${payload.message} ${payload.created_agents} agent(s), ${payload.created_tasks} task(s), ${payload.created_memories} memory record(s).`,
      );
    } catch (error) {
      pushToast(
        setToast,
        "error",
        error instanceof Error ? error.message : "Unable to seed demo data.",
      );
    } finally {
      setIsSeedingDemo(false);
    }
  }

  return (
    <main className="app-shell">
      <section className="hero">
        <div>
          <p className="eyebrow">Operator Console</p>
          <h1>Digital Company</h1>
          <p className="lede">
            Task board, agent runtime control, memory retrieval, and approval
            workflow in one UI.
          </p>
        </div>
        <div className="hero-meta">
          <span className={`badge badge-${apiState.status}`}>
            {apiState.status}
          </span>
          <p>
            {apiState.status === "loading"
              ? "Connecting to backend."
              : apiState.details}
          </p>
          <p className="muted">
            {isRefreshing ? "Refreshing dashboard." : "Polling every 6 seconds."}
          </p>
        </div>
      </section>

      {toast ? (
        <section className={`toast toast-${toast.tone}`}>
          <p>{toast.message}</p>
        </section>
      ) : null}

      <section className="overview-grid">
        <MetricCard
          label="Tasks"
          value={String(systemSummary?.tasks_total ?? tasks.length)}
          detail="live queue"
        />
        <MetricCard
          label="In Progress"
          value={String(
            systemSummary?.tasks_in_progress ??
              tasks.filter((task) => task.status === "in_progress").length,
          )}
          detail="actively claimed"
        />
        <MetricCard
          label="Pending Review"
          value={String(systemSummary?.workflows_pending ?? 0)}
          detail="awaiting human decision"
        />
        <MetricCard
          label="Memories"
          value={String(systemSummary?.memories_total ?? memories.length)}
          detail="retrieval corpus"
        />
      </section>

      <section className="workspace-grid">
        <div className="column column-wide">
          <Panel
            title="Task Board"
            subtitle="Queue, status, and workflow state"
            actions={
              <span className="panel-note">
                {selectedTask ? `Selected: ${selectedTask.title}` : "No task selected"}
              </span>
            }
          >
            <div className="task-board">
              {(["todo", "in_progress", "done", "failed"] as TaskStatus[]).map(
                (status) => (
                  <div className="kanban-column" key={status}>
                    <header className="kanban-header">
                      <h3>{labelize(status)}</h3>
                      <span>{tasks.filter((task) => task.status === status).length}</span>
                    </header>
                    <div className="kanban-stack">
                      {tasks
                        .filter((task) => task.status === status)
                        .map((task) => {
                          const workflow = workflows.find(
                            (entry) => entry.task_id === task.id,
                          );
                          return (
                            <button
                              className={`task-card ${
                                selectedTask?.id === task.id ? "task-card-active" : ""
                              }`}
                              key={task.id}
                              onClick={() => setSelectedTaskId(task.id)}
                              type="button"
                            >
                              <div className="task-card-topline">
                                <span className={`tag tag-${task.type}`}>
                                  {task.type}
                                </span>
                                <span className="task-project">
                                  {task.project_id ?? "unscoped"}
                                </span>
                              </div>
                              <h4>{task.title}</h4>
                              <p>{task.description}</p>
                              <div className="task-card-footer">
                                <span>
                                  {task.assigned_agent_id
                                    ? findAgentName(task.assigned_agent_id, agents)
                                    : "unassigned"}
                                </span>
                                <span className={`approval approval-${workflow?.approval_status ?? "not_required"}`}>
                                  {workflow?.approval_status ?? "not_required"}
                                </span>
                              </div>
                            </button>
                          );
                        })}
                    </div>
                  </div>
                ),
              )}
            </div>
          </Panel>

          <div className="detail-grid">
            <Panel
              title="Task Detail"
              subtitle="Activity, runs, and review state"
              actions={
                selectedTask ? (
                  <span className="panel-note">
                    {selectedAgent
                      ? `Assigned to ${selectedAgent.name}`
                      : "No assigned agent"}
                  </span>
                ) : null
              }
            >
              {selectedTask ? (
                <div className="detail-block">
                  <div className="detail-headline">
                    <div>
                      <h3>{selectedTask.title}</h3>
                      <p className="muted">
                        {selectedTask.type} • {selectedTask.project_id ?? "unscoped"}
                      </p>
                    </div>
                    <span className={`status-pill status-${selectedTask.status}`}>
                      {selectedTask.status}
                    </span>
                  </div>
                  <p className="detail-copy">{selectedTask.description}</p>
                  <div className="detail-section">
                    <h4>Workflow</h4>
                    {selectedWorkflow ? (
                      <div className="workflow-summary">
                        <p>
                          <strong>Status:</strong> {selectedWorkflow.approval_status}
                        </p>
                        <p>
                          <strong>Branch:</strong>{" "}
                          {selectedWorkflow.branch_name ?? "not submitted"}
                        </p>
                        <p>
                          <strong>Submission notes:</strong>{" "}
                          {selectedWorkflow.submission_notes ?? "none"}
                        </p>
                      </div>
                    ) : (
                      <p className="muted">No workflow record yet.</p>
                    )}
                  </div>
                  <div className="detail-section">
                    <h4>Activity Feed</h4>
                    <div className="activity-feed">
                      {selectedTaskEvents.map((entry) => (
                        <article className="activity-item" key={entry.id}>
                          <div className="activity-meta">
                            <span>{entry.event_type}</span>
                            <time>{formatDateTime(entry.created_at)}</time>
                          </div>
                          <pre>{JSON.stringify(entry.payload, null, 2)}</pre>
                        </article>
                      ))}
                    </div>
                  </div>
                  <div className="detail-section">
                    <h4>Task Runs</h4>
                    <div className="run-stack">
                      {selectedTaskRuns.map((taskRun) => (
                        <article className="run-card" key={taskRun.id}>
                          <div className="run-header">
                            <span className={`status-pill status-${mapRunStatus(taskRun.status)}`}>
                              {taskRun.status}
                            </span>
                            <span>{findAgentName(taskRun.agent_id, agents)}</span>
                            <time>{formatDateTime(taskRun.started_at)}</time>
                          </div>
                          <p className="run-summary">
                            follow-up tasks: {taskRun.created_follow_up_tasks} • exit code:{" "}
                            {taskRun.exit_code ?? "n/a"}
                          </p>
                          <details>
                            <summary>stdout</summary>
                            <pre>{taskRun.stdout || "No stdout captured."}</pre>
                          </details>
                          <details>
                            <summary>stderr</summary>
                            <pre>{taskRun.stderr || "No stderr captured."}</pre>
                          </details>
                        </article>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <p className="muted">Create a task to begin operating the system.</p>
              )}
            </Panel>

            <Panel title="Approval Controls" subtitle="Submit and review selected task">
              {selectedTask ? (
                <div className="form-stack">
                  <label>
                    Branch name
                    <input
                      value={reviewDraft.branchName}
                      onChange={(event) =>
                        setReviewDraft((current) => ({
                          ...current,
                          branchName: event.target.value,
                        }))
                      }
                    />
                  </label>
                  <label>
                    Submission notes
                    <textarea
                      rows={3}
                      value={reviewDraft.submissionNotes}
                      onChange={(event) =>
                        setReviewDraft((current) => ({
                          ...current,
                          submissionNotes: event.target.value,
                        }))
                      }
                    />
                  </label>
                  <button
                    className="primary-button"
                    disabled={isSubmittingWorkflow || selectedTask.status !== "done"}
                    onClick={() => void handleSubmitForReview()}
                    type="button"
                  >
                    Submit For Review
                  </button>
                  <label>
                    Reviewer
                    <input
                      value={reviewDraft.reviewerName}
                      onChange={(event) =>
                        setReviewDraft((current) => ({
                          ...current,
                          reviewerName: event.target.value,
                        }))
                      }
                    />
                  </label>
                  <label>
                    Decision
                    <select
                      value={reviewDraft.decision}
                      onChange={(event) =>
                        setReviewDraft((current) => ({
                          ...current,
                          decision: event.target.value as ReviewDecisionType,
                        }))
                      }
                    >
                      <option value="approved">approved</option>
                      <option value="changes_requested">changes_requested</option>
                    </select>
                  </label>
                  <label>
                    Review summary
                    <textarea
                      rows={4}
                      value={reviewDraft.summary}
                      onChange={(event) =>
                        setReviewDraft((current) => ({
                          ...current,
                          summary: event.target.value,
                        }))
                      }
                    />
                  </label>
                  <button
                    className="secondary-button"
                    disabled={isSubmittingWorkflow || !reviewDraft.summary.trim()}
                    onClick={() => void handleRecordDecision()}
                    type="button"
                  >
                    Record Decision
                  </button>
                </div>
              ) : (
                <p className="muted">Select a task to operate the approval flow.</p>
              )}
            </Panel>
          </div>
        </div>

        <div className="column">
          <Panel
            title="System Operations"
            subtitle="Seed demo data and run the daily improvement loop"
          >
            <div className="form-stack">
              <div className="workflow-summary">
                <p>
                  <strong>Scheduler enabled:</strong>{" "}
                  {systemSummary?.scheduler_enabled ? "yes" : "no"}
                </p>
                <p>
                  <strong>Scheduler running:</strong>{" "}
                  {systemSummary?.scheduler_running ? "yes" : "no"}
                </p>
                <p>
                  <strong>Improvement runs:</strong>{" "}
                  {systemSummary?.self_improvement_runs_total ?? 0}
                </p>
              </div>
              <button
                className="primary-button"
                disabled={isSeedingDemo}
                onClick={() => void handleSeedDemo()}
                type="button"
              >
                {isSeedingDemo ? "Seeding..." : "Seed Demo"}
              </button>
              <button
                className="secondary-button"
                disabled={isRunningSelfImprovement}
                onClick={() => void handleRunSelfImprovement()}
                type="button"
              >
                {isRunningSelfImprovement
                  ? "Running..."
                  : "Run Self-Improvement"}
              </button>
              <div className="entity-list">
                {selfImprovementRuns.slice(0, 4).map((run) => (
                  <article className="entity-card" key={run.id}>
                    <div className="entity-meta">
                      <div>
                        <h4>{run.trigger_mode}</h4>
                        <p>{formatDateTime(run.started_at)}</p>
                      </div>
                      <span className={`status-pill status-${mapSelfImprovementStatus(run.status)}`}>
                        {run.status}
                      </span>
                    </div>
                    <p>{run.summary}</p>
                    <p className="muted">
                      {run.proposed_branch_name} • {run.created_task_count} task(s)
                    </p>
                  </article>
                ))}
              </div>
            </div>
          </Panel>

          <Panel title="Agents" subtitle="Create agents and run cycles">
            <form className="form-stack" onSubmit={handleCreateAgent}>
              <label>
                Agent name
                <input
                  required
                  value={agentDraft.name}
                  onChange={(event) =>
                    setAgentDraft((current) => ({
                      ...current,
                      name: event.target.value,
                    }))
                  }
                />
              </label>
              <label>
                Role
                <select
                  value={agentDraft.role}
                  onChange={(event) =>
                    setAgentDraft((current) => ({
                      ...current,
                      role: event.target.value as AgentRole,
                    }))
                  }
                >
                  {[
                    "designer",
                    "architect",
                    "developer",
                    "tester",
                    "reviewer",
                    "review_agent",
                  ].map((role) => (
                    <option key={role} value={role}>
                      {role}
                    </option>
                  ))}
                </select>
              </label>
              <button className="primary-button" disabled={isSubmittingAgent} type="submit">
                Create Agent
              </button>
            </form>
            <div className="entity-list">
              {agents.map((agent) => (
                <article className="entity-card" key={agent.id}>
                  <div className="entity-meta">
                    <div>
                      <h4>{agent.name}</h4>
                      <p>{agent.role}</p>
                    </div>
                    <span className={`status-pill status-${mapAgentStatus(agent.status)}`}>
                      {agent.status}
                    </span>
                  </div>
                  <p className="muted">
                    current task:{" "}
                    {agent.current_task_id
                      ? tasks.find((task) => task.id === agent.current_task_id)?.title ??
                        agent.current_task_id
                      : "none"}
                  </p>
                  <button
                    className="secondary-button"
                    disabled={isRunningAgentId === agent.id}
                    onClick={() => void handleRunAgent(agent.id)}
                    type="button"
                  >
                    {isRunningAgentId === agent.id ? "Running..." : "Run Once"}
                  </button>
                </article>
              ))}
            </div>
          </Panel>

          <Panel title="Create Task" subtitle="Seed the queue from the UI">
            <form className="form-stack" onSubmit={handleCreateTask}>
              <label>
                Title
                <input
                  required
                  value={taskDraft.title}
                  onChange={(event) =>
                    setTaskDraft((current) => ({
                      ...current,
                      title: event.target.value,
                    }))
                  }
                />
              </label>
              <label>
                Type
                <select
                  value={taskDraft.type}
                  onChange={(event) =>
                    setTaskDraft((current) => ({
                      ...current,
                      type: event.target.value as TaskType,
                    }))
                  }
                >
                  {["feature", "bugfix", "research", "review", "ops"].map((type) => (
                    <option key={type} value={type}>
                      {type}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Project ID
                <input
                  value={taskDraft.projectId}
                  onChange={(event) =>
                    setTaskDraft((current) => ({
                      ...current,
                      projectId: event.target.value,
                    }))
                  }
                />
              </label>
              <label>
                Description
                <textarea
                  required
                  rows={4}
                  value={taskDraft.description}
                  onChange={(event) =>
                    setTaskDraft((current) => ({
                      ...current,
                      description: event.target.value,
                    }))
                  }
                />
              </label>
              <button className="primary-button" disabled={isSubmittingTask} type="submit">
                Create Task
              </button>
            </form>
          </Panel>

          <Panel title="Memory Search" subtitle="Inspect retrieval relevance">
            <form className="form-stack" onSubmit={handleSearchMemory}>
              <label>
                Query
                <input
                  value={memoryQuery}
                  onChange={(event) => setMemoryQuery(event.target.value)}
                />
              </label>
              <label>
                Strategy
                <select
                  value={memoryStrategy}
                  onChange={(event) =>
                    setMemoryStrategy(event.target.value as SearchStrategy)
                  }
                >
                  <option value="hybrid">hybrid</option>
                  <option value="keyword">keyword</option>
                  <option value="vector">vector</option>
                </select>
              </label>
              <button className="secondary-button" type="submit">
                Search Memory
              </button>
            </form>
            <div className="entity-list">
              {memoryResults.map((result) => (
                <article className="entity-card" key={result.memory_id}>
                  <div className="entity-meta">
                    <div>
                      <h4>{result.summary}</h4>
                      <p>{result.type}</p>
                    </div>
                    <span className="score-pill">
                      {result.combined_score.toFixed(3)}
                    </span>
                  </div>
                  <p>{result.content}</p>
                  <p className="muted">
                    keyword {result.keyword_score.toFixed(3)} • vector{" "}
                    {result.vector_score.toFixed(3)}
                  </p>
                </article>
              ))}
            </div>
          </Panel>
        </div>
      </section>
    </main>
  );
}

function MetricCard(props: { label: string; value: string; detail: string }) {
  return (
    <article className="metric-card">
      <p>{props.label}</p>
      <strong>{props.value}</strong>
      <span>{props.detail}</span>
    </article>
  );
}

function Panel(props: {
  title: string;
  subtitle: string;
  children: React.ReactNode;
  actions?: React.ReactNode;
}) {
  return (
    <section className="panel">
      <header className="panel-header">
        <div>
          <h2>{props.title}</h2>
          <p>{props.subtitle}</p>
        </div>
        {props.actions ? <div>{props.actions}</div> : null}
      </header>
      {props.children}
    </section>
  );
}

async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`);
  if (!response.ok) {
    throw new Error(await formatError(response));
  }
  return (await response.json()) as T;
}

async function apiPost<T>(path: string, payload: unknown): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(await formatError(response));
  }
  return (await response.json()) as T;
}

async function formatError(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: string };
    return payload.detail
      ? `${response.status} ${payload.detail}`
      : `${response.status} request failed`;
  } catch {
    return `${response.status} request failed`;
  }
}

function labelize(value: string) {
  return value.replace(/_/g, " ");
}

function formatDateTime(value: string) {
  return new Date(value).toLocaleString();
}

function findAgentName(agentId: string, agents: Agent[]) {
  return agents.find((agent) => agent.id === agentId)?.name ?? agentId;
}

function mapRunStatus(status: TaskRunStatus) {
  if (status === "running") {
    return "in_progress";
  }
  if (status === "succeeded") {
    return "done";
  }
  return "failed";
}

function mapAgentStatus(status: AgentStatus) {
  if (status === "busy") {
    return "in_progress";
  }
  if (status === "offline") {
    return "failed";
  }
  return "done";
}

function mapSelfImprovementStatus(status: SelfImprovementRun["status"]) {
  if (status === "running") {
    return "in_progress";
  }
  if (status === "failed") {
    return "failed";
  }
  return "done";
}

function pushToast(
  setToast: React.Dispatch<React.SetStateAction<Toast | null>>,
  tone: Toast["tone"],
  message: string,
) {
  setToast({ tone, message });
  window.setTimeout(() => {
    setToast((current) => (current?.message === message ? null : current));
  }, 2800);
}
