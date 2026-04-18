import { FormEvent, useEffect, useState } from "react";

type ApiState = {
  status: "loading" | "online" | "offline";
  details?: string;
};

type TaskStatus = "todo" | "in_progress" | "done" | "failed";
type TaskType = "idea" | "feature" | "bugfix" | "research" | "review" | "ops";
type AgentRole =
  | "planner"
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
type AppView = "overview" | "work" | "projects" | "agents";
type WorkInspectorTab = "summary" | "activity" | "runs" | "review";
type ProjectPanelTab = "summary" | "plan" | "tasks";
type PlanStatus =
  | "draft"
  | "pending_approval"
  | "changes_requested"
  | "approved"
  | "completed";
type PlanTaskStatus = "proposed" | "queued" | "done" | "failed" | "cancelled";

type Project = {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
};

type ProjectPlanTask = {
  id: string;
  parent_plan_task_id: string | null;
  source_task_id: string | null;
  created_task_id: string | null;
  sequence: number;
  title: string;
  description: string;
  type: Exclude<TaskType, "idea"> | TaskType;
  status: PlanTaskStatus;
  spawn_budget: number;
  created_at: string;
  updated_at: string;
};

type ProjectPlan = {
  id: string;
  project_id: string;
  planning_task_id: string | null;
  idea_title: string;
  idea_description: string;
  planner_summary: string | null;
  status: PlanStatus;
  feedback: string | null;
  max_total_tasks: number;
  created_task_count: number;
  approved_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
  items: ProjectPlanTask[];
};

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
  template_id: string | null;
  instructions: string | null;
  skill_ids: string[];
  status: AgentStatus;
  current_task_id: string | null;
  created_at: string;
  updated_at: string;
};

type AgentTemplate = {
  id: string;
  role: AgentRole;
  name: string;
  summary: string;
  instructions: string;
  is_default: boolean;
};

type AgentSkill = {
  id: string;
  name: string;
  summary: string;
  instructions: string;
  path: string;
  source: string;
  recommended_roles: AgentRole[];
};

type AgentCatalog = {
  templates: AgentTemplate[];
  skills: AgentSkill[];
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

type WorkerBatchResponse = {
  total_agents: number;
  completed: number;
  failed: number;
  idle: number;
  results: WorkerCycleResponse[];
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

type SeedStartupTeamResponse = {
  created_agents: number;
  existing_agents: number;
  created_names: string[];
  message: string;
};

type Toast = {
  tone: "info" | "success" | "error";
  message: string;
};

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
const refreshIntervalMs = 2500;

const defaultTaskDraft = {
  title: "",
  description: "",
  type: "feature" as TaskType,
  projectId: "",
};

const defaultIdeaPitchDraft = {
  title: "",
  description: "",
  feedback: "",
};

const defaultProjectDraft = {
  id: "",
  name: "",
  description: "",
};

const defaultAgentDraft = {
  name: "",
  role: "developer" as AgentRole,
  templateId: "",
  instructions: "",
  skillIds: [] as string[],
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
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectPlans, setProjectPlans] = useState<ProjectPlan[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [agentCatalog, setAgentCatalog] = useState<AgentCatalog>({
    templates: [],
    skills: [],
  });
  const [taskRuns, setTaskRuns] = useState<TaskRun[]>([]);
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [memories, setMemories] = useState<Memory[]>([]);
  const [systemSummary, setSystemSummary] = useState<SystemSummary | null>(null);
  const [selfImprovementRuns, setSelfImprovementRuns] = useState<
    SelfImprovementRun[]
  >([]);
  const [activeView, setActiveView] = useState<AppView>("work");
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [selectedTaskEvents, setSelectedTaskEvents] = useState<TaskEvent[]>([]);
  const [workInspectorTab, setWorkInspectorTab] =
    useState<WorkInspectorTab>("summary");
  const [projectPanelTab, setProjectPanelTab] =
    useState<ProjectPanelTab>("summary");
  const [taskDraft, setTaskDraft] = useState(defaultTaskDraft);
  const [projectDraft, setProjectDraft] = useState(defaultProjectDraft);
  const [ideaPitchDraft, setIdeaPitchDraft] = useState(defaultIdeaPitchDraft);
  const [agentDraft, setAgentDraft] = useState(defaultAgentDraft);
  const [reviewDraft, setReviewDraft] = useState(defaultReviewDraft);
  const [memoryQuery, setMemoryQuery] = useState("task locking");
  const [memoryStrategy, setMemoryStrategy] = useState<SearchStrategy>("hybrid");
  const [memoryResults, setMemoryResults] = useState<MemorySearchResult[]>([]);
  const [isSubmittingProject, setIsSubmittingProject] = useState(false);
  const [isSubmittingTask, setIsSubmittingTask] = useState(false);
  const [isSubmittingAgent, setIsSubmittingAgent] = useState(false);
  const [isSeedingStartupTeam, setIsSeedingStartupTeam] = useState(false);
  const [isRunningAllAgents, setIsRunningAllAgents] = useState(false);
  const [isRunningAgentId, setIsRunningAgentId] = useState<string | null>(null);
  const [isDeletingAgentId, setIsDeletingAgentId] = useState<string | null>(null);
  const [isDeletingProjectId, setIsDeletingProjectId] = useState<string | null>(null);
  const [isPitchingIdea, setIsPitchingIdea] = useState(false);
  const [isSubmittingPlanDecision, setIsSubmittingPlanDecision] = useState(false);
  const [isSubmittingWorkflow, setIsSubmittingWorkflow] = useState(false);
  const [isRunningSelfImprovement, setIsRunningSelfImprovement] = useState(false);
  const [isSeedingDemo, setIsSeedingDemo] = useState(false);
  const [taskActionInFlight, setTaskActionInFlight] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setIsRefreshing(true);
      try {
        const [
          catalogResponse,
          tasksResponse,
          projectsResponse,
          projectPlansResponse,
          agentsResponse,
          taskRunsResponse,
          workflowsResponse,
          memoriesResponse,
          summaryResponse,
          selfImprovementRunsResponse,
        ] = await Promise.all([
          apiGet<AgentCatalog>("/api/v1/agents/catalog"),
          apiGet<Task[]>("/api/v1/tasks"),
          apiGet<Project[]>("/api/v1/projects"),
          apiGet<ProjectPlan[]>("/api/v1/project-plans"),
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

        setAgentCatalog(catalogResponse);
        setTasks(tasksResponse);
        setProjects(projectsResponse);
        setProjectPlans(projectPlansResponse);
        setAgents(agentsResponse);
        setTaskRuns(taskRunsResponse);
        setWorkflows(workflowsResponse);
        setMemories(memoriesResponse);
        setSystemSummary(summaryResponse);
        setSelfImprovementRuns(selfImprovementRunsResponse);
        setApiState({ status: "online", details: "operator backend reachable" });
        setSelectedProjectId((current) =>
          current && projectsResponse.some((project) => project.id === current)
            ? current
            : projectsResponse[0]?.id ?? null,
        );
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
    const intervalId = window.setInterval(() => {
      void loadTaskEvents();
    }, refreshIntervalMs);

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, [selectedTaskId]);

  const selectedTask =
    tasks.find((task) => task.id === selectedTaskId) ?? tasks[0] ?? null;
  const selectedProject =
    projects.find((project) => project.id === selectedProjectId) ?? projects[0] ?? null;
  const selectedProjectPlans = selectedProject
    ? projectPlans.filter((plan) => plan.project_id === selectedProject.id)
    : [];
  const selectedProjectPlan = selectedProjectPlans[0] ?? null;
  const roleTemplates = agentCatalog.templates.filter(
    (template) => template.role === agentDraft.role,
  );
  const selectedAgentTemplate =
    roleTemplates.find((template) => template.id === agentDraft.templateId) ??
    roleTemplates.find((template) => template.is_default) ??
    roleTemplates[0] ??
    null;
  const sortedSkills = sortSkillsForRole(agentCatalog.skills, agentDraft.role);
  const selectedWorkflow =
    workflows.find((workflow) => workflow.task_id === selectedTask?.id) ?? null;
  const selectedTaskRuns = selectedTask
    ? taskRuns.filter((taskRun) => taskRun.task_id === selectedTask.id)
    : [];
  const selectedAgent = selectedTask?.assigned_agent_id
    ? agents.find((agent) => agent.id === selectedTask.assigned_agent_id) ?? null
    : null;
  const selectedProjectTasks = selectedProject
    ? tasks.filter((task) => task.project_id === selectedProject.id)
    : [];
  const recentTaskRuns = [...taskRuns]
    .sort((left, right) => right.started_at.localeCompare(left.started_at))
    .slice(0, 6);
  const viewTitles: Record<AppView, { title: string; subtitle: string }> = {
    overview: {
      title: "Overview",
      subtitle: "Health, throughput, and company-level controls.",
    },
    work: {
      title: "Work",
      subtitle: "Queue, inspect, and approve execution without losing context.",
    },
    projects: {
      title: "Projects",
      subtitle: "Create projects, pitch ideas, and manage bounded plans.",
    },
    agents: {
      title: "Agents",
      subtitle: "Manage the team, templates, skills, and execution cycles.",
    },
  };

  async function refreshDashboard() {
    const payload = await Promise.all([
      apiGet<AgentCatalog>("/api/v1/agents/catalog"),
      apiGet<Task[]>("/api/v1/tasks"),
      apiGet<Project[]>("/api/v1/projects"),
      apiGet<ProjectPlan[]>("/api/v1/project-plans"),
      apiGet<Agent[]>("/api/v1/agents"),
      apiGet<TaskRun[]>("/api/v1/task-runs"),
      apiGet<Workflow[]>("/api/v1/workflows"),
      apiGet<Memory[]>("/api/v1/memory"),
      apiGet<SystemSummary>("/api/v1/operations/summary"),
      apiGet<SelfImprovementRun[]>("/api/v1/operations/self-improvement/runs"),
    ]);
    setAgentCatalog(payload[0]);
    setTasks(payload[1]);
    setProjects(payload[2]);
    setProjectPlans(payload[3]);
    setAgents(payload[4]);
    setTaskRuns(payload[5]);
    setWorkflows(payload[6]);
    setMemories(payload[7]);
    setSystemSummary(payload[8]);
    setSelfImprovementRuns(payload[9]);
    setSelectedProjectId((current) =>
      current && payload[2].some((project) => project.id === current)
        ? current
        : payload[2][0]?.id ?? null,
    );
    setSelectedTaskId((current) =>
      current && payload[1].some((task) => task.id === current)
        ? current
        : payload[1][0]?.id ?? null,
    );
  }

  useEffect(() => {
    const matchingTemplates = agentCatalog.templates.filter(
      (template) => template.role === agentDraft.role,
    );
    if (matchingTemplates.length === 0) {
      return;
    }
    if (matchingTemplates.some((template) => template.id === agentDraft.templateId)) {
      return;
    }
    const nextTemplateId =
      matchingTemplates.find((template) => template.is_default)?.id ??
      matchingTemplates[0].id;
    setAgentDraft((current) => ({ ...current, templateId: nextTemplateId }));
  }, [agentCatalog.templates, agentDraft.role, agentDraft.templateId]);

  async function handleCreateProject(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmittingProject(true);
    try {
      const created = await apiPost<Project>("/api/v1/projects", {
        id: projectDraft.id.trim(),
        name: projectDraft.name.trim(),
        description: projectDraft.description.trim() || null,
      });
      setProjectDraft(defaultProjectDraft);
      setSelectedProjectId(created.id);
      setTaskDraft((current) => ({ ...current, projectId: created.id }));
      await refreshDashboard();
      pushToast(setToast, "success", `Project ${created.name} created.`);
    } catch (error) {
      pushToast(
        setToast,
        "error",
        error instanceof Error ? error.message : "Unable to create project.",
      );
    } finally {
      setIsSubmittingProject(false);
    }
  }

  async function handleCreateTask(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmittingTask(true);
    try {
      await apiPost<Task>("/api/v1/tasks", {
        title: taskDraft.title,
        description: taskDraft.description,
        type: taskDraft.type,
        project_id: taskDraft.projectId,
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

  async function handlePitchIdea(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedProject) {
      return;
    }

    setIsPitchingIdea(true);
    try {
      await apiPost<ProjectPlan>(
        `/api/v1/project-plans/projects/${selectedProject.id}/pitch`,
        {
          idea_title: ideaPitchDraft.title.trim(),
          idea_description: ideaPitchDraft.description.trim(),
        },
      );
      setIdeaPitchDraft(defaultIdeaPitchDraft);
      await refreshDashboard();
      pushToast(setToast, "success", "Idea pitched. Run a planner agent to generate the plan.");
    } catch (error) {
      pushToast(
        setToast,
        "error",
        error instanceof Error ? error.message : "Unable to pitch idea.",
      );
    } finally {
      setIsPitchingIdea(false);
    }
  }

  async function handleApprovePlan(planId: string) {
    setIsSubmittingPlanDecision(true);
    try {
      await apiPost<ProjectPlan>(`/api/v1/project-plans/${planId}/approve`, {});
      await refreshDashboard();
      pushToast(setToast, "success", "Plan approved and queued onto the board.");
    } catch (error) {
      pushToast(
        setToast,
        "error",
        error instanceof Error ? error.message : "Unable to approve plan.",
      );
    } finally {
      setIsSubmittingPlanDecision(false);
    }
  }

  async function handleRequestPlanChanges(planId: string) {
    setIsSubmittingPlanDecision(true);
    try {
      await apiPost<ProjectPlan>(`/api/v1/project-plans/${planId}/request-changes`, {
        feedback: ideaPitchDraft.feedback.trim(),
      });
      await refreshDashboard();
      pushToast(setToast, "success", "Plan sent back for changes.");
    } catch (error) {
      pushToast(
        setToast,
        "error",
        error instanceof Error ? error.message : "Unable to request plan changes.",
      );
    } finally {
      setIsSubmittingPlanDecision(false);
    }
  }

  async function handleDeleteProject(project: Project) {
    const shouldDelete = window.confirm(
      `Delete project "${project.name}"? This only works when the project has no tasks and no real files in its workspace.`,
    );
    if (!shouldDelete) {
      return;
    }

    setIsDeletingProjectId(project.id);
    try {
      await apiDelete(`/api/v1/projects/${project.id}`);
      if (selectedProjectId === project.id) {
        setSelectedProjectId(null);
      }
      if (taskDraft.projectId === project.id) {
        setTaskDraft((current) => ({ ...current, projectId: "" }));
      }
      await refreshDashboard();
      pushToast(setToast, "success", "Project deleted.");
    } catch (error) {
      pushToast(
        setToast,
        "error",
        error instanceof Error ? error.message : "Unable to delete project.",
      );
    } finally {
      setIsDeletingProjectId(null);
    }
  }

  async function handleCreateAgent(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmittingAgent(true);
    try {
      await apiPost<Agent>("/api/v1/agents", {
        name: agentDraft.name.trim(),
        role: agentDraft.role,
        template_id: selectedAgentTemplate?.id ?? null,
        instructions: agentDraft.instructions.trim() || null,
        skill_ids: agentDraft.skillIds,
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

  async function handleDeleteAgent(agent: Agent) {
    const shouldDelete = window.confirm(
      `Delete agent "${agent.name}"? Agents with execution history cannot be deleted.`,
    );
    if (!shouldDelete) {
      return;
    }

    setIsDeletingAgentId(agent.id);
    try {
      await apiDelete(`/api/v1/agents/${agent.id}`);
      await refreshDashboard();
      pushToast(setToast, "success", "Agent deleted.");
    } catch (error) {
      pushToast(
        setToast,
        "error",
        error instanceof Error ? error.message : "Unable to delete agent.",
      );
    } finally {
      setIsDeletingAgentId(null);
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

  async function handleRunAllAgents() {
    setIsRunningAllAgents(true);
    try {
      const payload = await apiPost<WorkerBatchResponse>("/api/v1/agents/run-all", {});
      await refreshDashboard();
      pushToast(
        setToast,
        payload.failed > 0 ? "error" : "success",
        `Ran ${payload.total_agents} agent(s): ${payload.completed} completed, ${payload.failed} failed, ${payload.idle} idle.`,
      );
    } catch (error) {
      pushToast(
        setToast,
        "error",
        error instanceof Error ? error.message : "Unable to run all agents.",
      );
    } finally {
      setIsRunningAllAgents(false);
    }
  }

  async function handleSeedStartupTeam() {
    setIsSeedingStartupTeam(true);
    try {
      const payload = await apiPost<SeedStartupTeamResponse>("/api/v1/operations/seed-startup-team", {});
      await refreshDashboard();
      pushToast(
        setToast,
        "success",
        `${payload.message} ${payload.created_agents} created, ${payload.existing_agents} already present.`,
      );
    } catch (error) {
      pushToast(
        setToast,
        "error",
        error instanceof Error ? error.message : "Unable to seed startup team.",
      );
    } finally {
      setIsSeedingStartupTeam(false);
    }
  }

  async function handleRetryTask() {
    if (!selectedTask) {
      return;
    }

    setTaskActionInFlight("retry");
    try {
      await apiPost<Task>(`/api/v1/tasks/${selectedTask.id}/retry`, {});
      await refreshDashboard();
      pushToast(setToast, "success", "Task returned to the queue.");
    } catch (error) {
      pushToast(
        setToast,
        "error",
        error instanceof Error ? error.message : "Unable to retry task.",
      );
    } finally {
      setTaskActionInFlight(null);
    }
  }

  async function handleDeleteTask(taskOverride?: Task) {
    const taskToDelete = taskOverride ?? selectedTask;
    if (!taskToDelete) {
      return;
    }

    const shouldDelete = window.confirm(
      `Delete "${taskToDelete.title}"? This removes task runs, workflow records, and activity for this task. Project files are not deleted.`,
    );
    if (!shouldDelete) {
      return;
    }

    setTaskActionInFlight(`delete:${taskToDelete.id}`);
    try {
      await apiDelete(`/api/v1/tasks/${taskToDelete.id}`);
      if (selectedTask?.id === taskToDelete.id) {
        setSelectedTaskId(null);
        setSelectedTaskEvents([]);
      }
      await refreshDashboard();
      pushToast(setToast, "success", "Task deleted.");
    } catch (error) {
      pushToast(
        setToast,
        "error",
        error instanceof Error ? error.message : "Unable to delete task.",
      );
    } finally {
      setTaskActionInFlight(null);
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
      <div className="app-frame">
        <aside className="app-sidebar">
          <div className="sidebar-brand">
            <p className="eyebrow">Operator Console</p>
            <h1>Digital Company</h1>
            <p className="sidebar-copy">
              A clearer control surface for running projects, plans, and agents.
            </p>
          </div>

          <nav className="sidebar-nav" aria-label="Primary">
            {(["overview", "work", "projects", "agents"] as AppView[]).map((view) => (
              <button
                className={`nav-link ${activeView === view ? "nav-link-active" : ""}`}
                key={view}
                onClick={() => setActiveView(view)}
                type="button"
              >
                <span className="nav-label">{viewTitles[view].title}</span>
                <span className="nav-detail">{viewTitles[view].subtitle}</span>
              </button>
            ))}
          </nav>

          <div className="sidebar-section">
            <p className="section-kicker">Live State</p>
            <div className="sidebar-stat-list">
              <div className="sidebar-stat">
                <span>Todo</span>
                <strong>{systemSummary?.tasks_todo ?? tasks.filter((task) => task.status === "todo").length}</strong>
              </div>
              <div className="sidebar-stat">
                <span>Busy agents</span>
                <strong>{systemSummary?.agents_busy ?? agents.filter((agent) => agent.status === "busy").length}</strong>
              </div>
              <div className="sidebar-stat">
                <span>Projects</span>
                <strong>{projects.length}</strong>
              </div>
              <div className="sidebar-stat">
                <span>Pending review</span>
                <strong>{systemSummary?.workflows_pending ?? 0}</strong>
              </div>
            </div>
          </div>

          <div className="sidebar-section sidebar-status">
            <span className={`badge badge-${apiState.status}`}>{apiState.status}</span>
            <p>{apiState.status === "loading" ? "Connecting to backend." : apiState.details}</p>
            <p className="muted">
              {isRefreshing ? "Refreshing dashboard." : "Polling every 2.5 seconds."}
            </p>
          </div>
        </aside>

        <div className="app-main">
          <header className="topbar">
            <div>
              <p className="eyebrow">Current View</p>
              <h2>{viewTitles[activeView].title}</h2>
              <p className="topbar-copy">{viewTitles[activeView].subtitle}</p>
            </div>
            <div className="topbar-actions">
              <button
                className="secondary-button"
                disabled={isSeedingStartupTeam || isRunningAllAgents || isRunningAgentId !== null}
                onClick={() => void handleSeedStartupTeam()}
                type="button"
              >
                {isSeedingStartupTeam ? "Seeding Team..." : "Seed Startup Team"}
              </button>
              <button
                className="primary-button"
                disabled={isRunningAllAgents || isRunningAgentId !== null || agents.length === 0}
                onClick={() => void handleRunAllAgents()}
                type="button"
              >
                {isRunningAllAgents ? "Running All..." : "Run All Agents"}
              </button>
            </div>
          </header>

          {toast ? (
            <section className={`toast toast-${toast.tone}`}>
              <p>{toast.message}</p>
            </section>
          ) : null}

          {activeView === "overview" ? (
            <div className="content-stack">
              <section className="overview-grid">
                <MetricCard
                  label="Tasks"
                  value={String(systemSummary?.tasks_total ?? tasks.length)}
                  detail="total tracked work"
                />
                <MetricCard
                  label="In Progress"
                  value={String(
                    systemSummary?.tasks_in_progress ??
                      tasks.filter((task) => task.status === "in_progress").length,
                  )}
                  detail="currently being executed"
                />
                <MetricCard
                  label="Agents"
                  value={String(systemSummary?.agents_total ?? agents.length)}
                  detail="available roster"
                />
                <MetricCard
                  label="Memories"
                  value={String(systemSummary?.memories_total ?? memories.length)}
                  detail="retrieval corpus"
                />
              </section>

              <section className="dashboard-grid">
                <Panel
                  title="Mission Control"
                  subtitle="High-value controls without digging through the app"
                >
                  <div className="action-grid">
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
                      {isRunningSelfImprovement ? "Running..." : "Run Self-Improvement"}
                    </button>
                    <button
                      className="secondary-button"
                      onClick={() => setActiveView("projects")}
                      type="button"
                    >
                      Open Projects
                    </button>
                    <button
                      className="secondary-button"
                      onClick={() => setActiveView("agents")}
                      type="button"
                    >
                      Open Agents
                    </button>
                  </div>
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
                </Panel>

                <Panel title="Recent Agent Runs" subtitle="Latest execution attempts across the company">
                  <div className="entity-list">
                    {recentTaskRuns.length > 0 ? (
                      recentTaskRuns.map((taskRun) => (
                        <article className="entity-card" key={taskRun.id}>
                          <div className="entity-meta">
                            <div>
                              <h4>{tasks.find((task) => task.id === taskRun.task_id)?.title ?? "Unknown task"}</h4>
                              <p>{findAgentName(taskRun.agent_id, agents)}</p>
                            </div>
                            <span className={`status-pill status-${mapRunStatus(taskRun.status)}`}>
                              {taskRun.status}
                            </span>
                          </div>
                          <p>{summarizeRunProgress(taskRun)}</p>
                          <p className="muted">{formatDateTime(taskRun.started_at)}</p>
                        </article>
                      ))
                    ) : (
                      <p className="muted">No task runs yet.</p>
                    )}
                  </div>
                </Panel>

                <Panel title="Projects At A Glance" subtitle="Open the projects view to manage plans and task creation">
                  <div className="entity-list">
                    {projects.slice(0, 5).map((project) => (
                      <article className="entity-card" key={project.id}>
                        <div className="entity-meta">
                          <div>
                            <h4>{project.name}</h4>
                            <p>{project.id}</p>
                          </div>
                          <span className="score-pill">
                            {tasks.filter((task) => task.project_id === project.id).length} task(s)
                          </span>
                        </div>
                        <p>{project.description ?? "No project description yet."}</p>
                        <button
                          className="secondary-button"
                          onClick={() => {
                            setSelectedProjectId(project.id);
                            setProjectPanelTab("summary");
                            setActiveView("projects");
                          }}
                          type="button"
                        >
                          Open Project
                        </button>
                      </article>
                    ))}
                  </div>
                </Panel>

                <Panel title="Self-Improvement History" subtitle="Most recent improvement cycles">
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
                </Panel>
              </section>
            </div>
          ) : null}

          {activeView === "work" ? (
            <div className="content-stack">
              <section className="overview-grid overview-grid-compact">
                <MetricCard
                  label="Todo"
                  value={String(systemSummary?.tasks_todo ?? tasks.filter((task) => task.status === "todo").length)}
                  detail="ready to claim"
                />
                <MetricCard
                  label="Done"
                  value={String(systemSummary?.tasks_done ?? tasks.filter((task) => task.status === "done").length)}
                  detail="completed output"
                />
                <MetricCard
                  label="Failed"
                  value={String(systemSummary?.tasks_failed ?? tasks.filter((task) => task.status === "failed").length)}
                  detail="needs intervention"
                />
                <MetricCard
                  label="Pending Review"
                  value={String(systemSummary?.workflows_pending ?? 0)}
                  detail="waiting for approval"
                />
              </section>

              <section className="work-layout">
                <Panel
                  title="Task Board"
                  subtitle="The execution queue, now isolated from everything else"
                  actions={
                    <span className="panel-note">
                      {selectedTask ? `Selected: ${selectedTask.title}` : "Select a task"}
                    </span>
                  }
                >
                  <div className="task-board">
                    {(["todo", "in_progress", "done", "failed"] as TaskStatus[]).map((status) => (
                      <div className="kanban-column" key={status}>
                        <header className="kanban-header">
                          <h3>{labelize(status)}</h3>
                          <span>{tasks.filter((task) => task.status === status).length}</span>
                        </header>
                        <div className="kanban-stack">
                          {tasks
                            .filter((task) => task.status === status)
                            .map((task) => {
                              const workflow = workflows.find((entry) => entry.task_id === task.id);
                              return (
                                <article
                                  className={`task-card ${
                                    selectedTask?.id === task.id ? "task-card-active" : ""
                                  }`}
                                  key={task.id}
                                  onClick={() => setSelectedTaskId(task.id)}
                                  onKeyDown={(event) => {
                                    if (event.key === "Enter" || event.key === " ") {
                                      event.preventDefault();
                                      setSelectedTaskId(task.id);
                                    }
                                  }}
                                  role="button"
                                  tabIndex={0}
                                >
                                  <div className="task-card-topline">
                                    <div className="task-card-topline-left">
                                      <span className={`tag tag-${task.type}`}>{task.type}</span>
                                      <span className="task-project">
                                        {formatTaskProject(task.project_id, projects)}
                                      </span>
                                    </div>
                                    <button
                                      aria-label={`Delete ${task.title}`}
                                      className="task-card-delete"
                                      disabled={taskActionInFlight !== null}
                                      onClick={(event) => {
                                        event.stopPropagation();
                                        void handleDeleteTask(task);
                                      }}
                                      type="button"
                                    >
                                      ×
                                    </button>
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
                                </article>
                              );
                            })}
                        </div>
                      </div>
                    ))}
                  </div>
                </Panel>

                <div className="work-inspector-column">
                  <Panel
                    title="Task Inspector"
                    subtitle="One selected task, with the important context grouped together"
                    actions={
                      selectedTask ? (
                        <span className="panel-note">
                          {selectedAgent ? `Assigned to ${selectedAgent.name}` : "No assigned agent"}
                        </span>
                      ) : null
                    }
                  >
                    {selectedTask ? (
                      <div className="detail-block">
                        <div className="detail-headline detail-headline-stack">
                          <div>
                            <h3>{selectedTask.title}</h3>
                            <p className="muted">
                              {selectedTask.type} • {formatTaskProject(selectedTask.project_id, projects)}
                            </p>
                          </div>
                          <span className={`status-pill status-${selectedTask.status}`}>
                            {selectedTask.status}
                          </span>
                        </div>

                        <div className="task-actions">
                          <button
                            className="secondary-button"
                            disabled={
                              taskActionInFlight !== null ||
                              selectedTask.status === "todo" ||
                              selectedTask.status === "in_progress"
                            }
                            onClick={() => void handleRetryTask()}
                            type="button"
                          >
                            {taskActionInFlight === "retry" ? "Retrying..." : "Retry Task"}
                          </button>
                          <button
                            className="danger-button"
                            disabled={taskActionInFlight !== null}
                            onClick={() => void handleDeleteTask()}
                            type="button"
                          >
                            {taskActionInFlight === `delete:${selectedTask.id}` ? "Deleting..." : "Delete Task"}
                          </button>
                        </div>

                        <div className="segmented-control">
                          {(["summary", "activity", "runs", "review"] as WorkInspectorTab[]).map((tab) => (
                            <button
                              className={`segment ${workInspectorTab === tab ? "segment-active" : ""}`}
                              key={tab}
                              onClick={() => setWorkInspectorTab(tab)}
                              type="button"
                            >
                              {labelize(tab)}
                            </button>
                          ))}
                        </div>

                        {workInspectorTab === "summary" ? (
                          <div className="detail-section">
                            <p className="detail-copy">{selectedTask.description}</p>
                            <div className="workflow-summary">
                              <p>
                                <strong>Workflow status:</strong>{" "}
                                {selectedWorkflow?.approval_status ?? "not_required"}
                              </p>
                              <p>
                                <strong>Branch:</strong>{" "}
                                {selectedWorkflow?.branch_name ?? "not submitted"}
                              </p>
                              <p>
                                <strong>Submission notes:</strong>{" "}
                                {selectedWorkflow?.submission_notes ?? "none"}
                              </p>
                              <p>
                                <strong>Completed at:</strong>{" "}
                                {selectedTask.completed_at
                                  ? formatDateTime(selectedTask.completed_at)
                                  : "not completed"}
                              </p>
                            </div>
                          </div>
                        ) : null}

                        {workInspectorTab === "activity" ? (
                          <div className="detail-section">
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
                        ) : null}

                        {workInspectorTab === "runs" ? (
                          <div className="detail-section">
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
                                  {taskRun.status === "running" ? (
                                    <div className="live-run-summary">
                                      <strong>Live update:</strong> {summarizeRunProgress(taskRun)}
                                      <span className="muted"> • updated {formatDateTime(taskRun.updated_at)}</span>
                                    </div>
                                  ) : null}
                                  <details open={taskRun.status === "running"}>
                                    <summary>stdout</summary>
                                    <pre>
                                      {taskRun.stdout ||
                                        (taskRun.status === "running"
                                          ? "Waiting for stdout..."
                                          : "No stdout captured.")}
                                    </pre>
                                  </details>
                                  <details open={taskRun.status === "running"}>
                                    <summary>stderr</summary>
                                    <pre>
                                      {taskRun.stderr ||
                                        (taskRun.status === "running"
                                          ? "Waiting for stderr..."
                                          : "No stderr captured.")}
                                    </pre>
                                  </details>
                                  <details>
                                    <summary>prompt</summary>
                                    <pre>{taskRun.prompt}</pre>
                                  </details>
                                </article>
                              ))}
                            </div>
                          </div>
                        ) : null}

                        {workInspectorTab === "review" ? (
                          <div className="detail-section">
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
                          </div>
                        ) : null}
                      </div>
                    ) : (
                      <p className="muted">Select a task from the board to inspect it.</p>
                    )}
                  </Panel>

                  <Panel title="Memory Search" subtitle="Project-aware retrieval stays available, but out of the main way">
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
                    <div className="entity-list compact-scroll">
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
            </div>
          ) : null}

          {activeView === "projects" ? (
            <div className="content-stack">
              <section className="split-layout">
                <Panel
                  title="Project Directory"
                  subtitle="Create projects on the left, then operate one project at a time"
                >
                  <form className="form-stack" onSubmit={handleCreateProject}>
                    <label>
                      Project ID
                      <input
                        required
                        placeholder="futurecalc"
                        value={projectDraft.id}
                        onChange={(event) =>
                          setProjectDraft((current) => ({
                            ...current,
                            id: event.target.value,
                          }))
                        }
                      />
                    </label>
                    <label>
                      Project name
                      <input
                        required
                        placeholder="FutureCalc"
                        value={projectDraft.name}
                        onChange={(event) =>
                          setProjectDraft((current) => ({
                            ...current,
                            name: event.target.value,
                          }))
                        }
                      />
                    </label>
                    <label>
                      Description
                      <textarea
                        rows={3}
                        value={projectDraft.description}
                        onChange={(event) =>
                          setProjectDraft((current) => ({
                            ...current,
                            description: event.target.value,
                          }))
                        }
                      />
                    </label>
                    <button className="primary-button" disabled={isSubmittingProject} type="submit">
                      {isSubmittingProject ? "Creating..." : "Create Project"}
                    </button>
                  </form>

                  <div className="entity-list project-list">
                    {projects.map((project) => (
                      <article
                        className={`entity-card ${selectedProject?.id === project.id ? "entity-card-active" : ""}`}
                        key={project.id}
                        onClick={() => {
                          setSelectedProjectId(project.id);
                          setTaskDraft((current) => ({ ...current, projectId: project.id }));
                        }}
                      >
                        <div className="entity-meta">
                          <div>
                            <h4>{project.name}</h4>
                            <p>{project.id}</p>
                          </div>
                          <div className="card-meta-actions">
                            <span className="score-pill">
                              {tasks.filter((task) => task.project_id === project.id).length} task(s)
                            </span>
                            <button
                              aria-label={`Delete ${project.name}`}
                              className="task-card-delete"
                              disabled={isDeletingProjectId !== null}
                              onClick={(event) => {
                                event.stopPropagation();
                                void handleDeleteProject(project);
                              }}
                              type="button"
                            >
                              ×
                            </button>
                          </div>
                        </div>
                        <p>{project.description ?? "No project description yet."}</p>
                        <p className="muted">workspace: projects/{project.id}</p>
                      </article>
                    ))}
                  </div>
                </Panel>

                <Panel
                  title={selectedProject ? selectedProject.name : "Project Workspace"}
                  subtitle={
                    selectedProject
                      ? `Operate ${selectedProject.id} without mixing it into the rest of the company UI`
                      : "Create or select a project first"
                  }
                >
                  {selectedProject ? (
                    <div className="detail-block">
                      <div className="project-hero">
                        <div>
                          <h3>{selectedProject.name}</h3>
                          <p className="muted">{selectedProject.id}</p>
                          <p className="detail-copy">
                            {selectedProject.description ?? "No project description yet."}
                          </p>
                        </div>
                        <div className="project-summary-grid">
                          <div className="mini-stat">
                            <span>Tasks</span>
                            <strong>{selectedProjectTasks.length}</strong>
                          </div>
                          <div className="mini-stat">
                            <span>Plan</span>
                            <strong>{selectedProjectPlan?.status ?? "none"}</strong>
                          </div>
                          <div className="mini-stat">
                            <span>Workspace</span>
                            <strong>projects/{selectedProject.id}</strong>
                          </div>
                        </div>
                      </div>

                      <div className="segmented-control">
                        {(["summary", "plan", "tasks"] as ProjectPanelTab[]).map((tab) => (
                          <button
                            className={`segment ${projectPanelTab === tab ? "segment-active" : ""}`}
                            key={tab}
                            onClick={() => setProjectPanelTab(tab)}
                            type="button"
                          >
                            {labelize(tab)}
                          </button>
                        ))}
                      </div>

                      {projectPanelTab === "summary" ? (
                        <div className="detail-section">
                          <div className="workflow-summary">
                            <p>
                              <strong>Open tasks:</strong>{" "}
                              {
                                selectedProjectTasks.filter(
                                  (task) => task.status === "todo" || task.status === "in_progress",
                                ).length
                              }
                            </p>
                            <p>
                              <strong>Done tasks:</strong>{" "}
                              {selectedProjectTasks.filter((task) => task.status === "done").length}
                            </p>
                            <p>
                              <strong>Failed tasks:</strong>{" "}
                              {selectedProjectTasks.filter((task) => task.status === "failed").length}
                            </p>
                          </div>
                          <div className="entity-list compact-scroll">
                            {selectedProjectTasks.map((task) => (
                              <article className="entity-card" key={task.id}>
                                <div className="entity-meta">
                                  <div>
                                    <h4>{task.title}</h4>
                                    <p>{task.type}</p>
                                  </div>
                                  <span className={`status-pill status-${task.status}`}>{task.status}</span>
                                </div>
                                <p>{task.description}</p>
                                <button
                                  className="secondary-button"
                                  onClick={() => {
                                    setSelectedTaskId(task.id);
                                    setWorkInspectorTab("summary");
                                    setActiveView("work");
                                  }}
                                  type="button"
                                >
                                  Open In Work View
                                </button>
                              </article>
                            ))}
                          </div>
                        </div>
                      ) : null}

                      {projectPanelTab === "plan" ? (
                        <div className="detail-section">
                          <form className="form-stack" onSubmit={handlePitchIdea}>
                            <label>
                              Idea title
                              <input
                                required
                                placeholder="Launch a futuristic calculator product"
                                value={ideaPitchDraft.title}
                                onChange={(event) =>
                                  setIdeaPitchDraft((current) => ({
                                    ...current,
                                    title: event.target.value,
                                  }))
                                }
                              />
                            </label>
                            <label>
                              Idea description
                              <textarea
                                required
                                rows={4}
                                placeholder="Describe the idea, goal, and why it matters before execution starts."
                                value={ideaPitchDraft.description}
                                onChange={(event) =>
                                  setIdeaPitchDraft((current) => ({
                                    ...current,
                                    description: event.target.value,
                                  }))
                                }
                              />
                            </label>
                            <button className="primary-button" disabled={isPitchingIdea} type="submit">
                              {isPitchingIdea ? "Pitching..." : "Pitch Idea"}
                            </button>
                          </form>

                          {selectedProjectPlan ? (
                            <article className="entity-card">
                              <div className="entity-meta">
                                <div>
                                  <h4>{selectedProjectPlan.idea_title}</h4>
                                  <p>{selectedProjectPlan.status}</p>
                                </div>
                                <span className={`status-pill status-${mapPlanStatus(selectedProjectPlan.status)}`}>
                                  {selectedProjectPlan.created_task_count}/{selectedProjectPlan.max_total_tasks}
                                </span>
                              </div>
                              <p>{selectedProjectPlan.idea_description}</p>
                              <p className="muted">
                                {selectedProjectPlan.planner_summary ??
                                  "No planner summary yet. Run a planner agent on the idea task."}
                              </p>
                              {selectedProjectPlan.feedback ? (
                                <p className="muted">latest feedback: {selectedProjectPlan.feedback}</p>
                              ) : null}
                              <div className="entity-list compact-scroll">
                                {selectedProjectPlan.items.map((item) => (
                                  <article className="activity-item" key={item.id}>
                                    <div className="entity-meta">
                                      <div>
                                        <h4>{item.title}</h4>
                                        <p>
                                          {item.type} • spawn budget {item.spawn_budget}
                                        </p>
                                      </div>
                                      <span className={`status-pill status-${mapPlanTaskStatus(item.status)}`}>
                                        {item.status}
                                      </span>
                                    </div>
                                    <p>{item.description}</p>
                                  </article>
                                ))}
                              </div>
                              <label>
                                Feedback for changes
                                <textarea
                                  rows={3}
                                  placeholder="Optional: Tell the planner what to change before approving."
                                  value={ideaPitchDraft.feedback}
                                  onChange={(event) =>
                                    setIdeaPitchDraft((current) => ({
                                      ...current,
                                      feedback: event.target.value,
                                    }))
                                  }
                                />
                              </label>
                              <div className="task-actions">
                                <button
                                  className="primary-button"
                                  disabled={
                                    isSubmittingPlanDecision ||
                                    !["pending_approval", "changes_requested"].includes(selectedProjectPlan.status)
                                  }
                                  onClick={() => void handleApprovePlan(selectedProjectPlan.id)}
                                  type="button"
                                >
                                  Approve Plan
                                </button>
                                <button
                                  className="secondary-button"
                                  disabled={
                                    isSubmittingPlanDecision ||
                                    !selectedProjectPlan.items.length ||
                                    !ideaPitchDraft.feedback.trim()
                                  }
                                  onClick={() => void handleRequestPlanChanges(selectedProjectPlan.id)}
                                  type="button"
                                >
                                  Request Changes
                                </button>
                              </div>
                            </article>
                          ) : (
                            <p className="muted">Pitch an idea for the selected project to start a bounded plan.</p>
                          )}
                        </div>
                      ) : null}

                      {projectPanelTab === "tasks" ? (
                        <div className="detail-section">
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
                              Project
                              <select
                                required
                                value={taskDraft.projectId}
                                onChange={(event) =>
                                  setTaskDraft((current) => ({
                                    ...current,
                                    projectId: event.target.value,
                                  }))
                                }
                              >
                                <option value="">Select project</option>
                                {projects.map((project) => (
                                  <option key={project.id} value={project.id}>
                                    {project.name} ({project.id})
                                  </option>
                                ))}
                              </select>
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
                            <button
                              className="primary-button"
                              disabled={isSubmittingTask || projects.length === 0}
                              type="submit"
                            >
                              {isSubmittingTask ? "Creating..." : "Create Task"}
                            </button>
                          </form>
                        </div>
                      ) : null}
                    </div>
                  ) : (
                    <p className="muted">Create or select a project first.</p>
                  )}
                </Panel>
              </section>
            </div>
          ) : null}

          {activeView === "agents" ? (
            <div className="content-stack">
              <section className="split-layout split-layout-wide">
                <Panel
                  title="Team Roster"
                  subtitle="The live company roster, with run controls kept visible"
                >
                  <div className="entity-list compact-scroll roster-scroll">
                    {agents.map((agent) => (
                      <article className="entity-card" key={agent.id}>
                        <div className="entity-meta">
                          <div>
                            <h4>{agent.name}</h4>
                            <p>
                              {agent.role} • {findTemplateName(agent.template_id, agentCatalog.templates)}
                            </p>
                          </div>
                          <span className={`status-pill status-${mapAgentStatus(agent.status)}`}>
                            {agent.status}
                          </span>
                        </div>
                        <p>{summarizeAgentInstructions(agent.instructions)}</p>
                        <p className="muted">
                          skills:{" "}
                          {agent.skill_ids.length > 0
                            ? agent.skill_ids
                                .map((skillId) => findSkillName(skillId, agentCatalog.skills))
                                .join(", ")
                            : "none"}
                        </p>
                        <p className="muted">
                          current task:{" "}
                          {agent.current_task_id
                            ? tasks.find((task) => task.id === agent.current_task_id)?.title ??
                              agent.current_task_id
                            : "none"}
                        </p>
                        <div className="task-actions">
                          <button
                            className="secondary-button"
                            disabled={
                              isRunningAllAgents ||
                              isRunningAgentId === agent.id ||
                              isDeletingAgentId === agent.id
                            }
                            onClick={() => void handleRunAgent(agent.id)}
                            type="button"
                          >
                            {isRunningAgentId === agent.id ? "Running..." : "Run Once"}
                          </button>
                          <button
                            className="danger-button"
                            disabled={
                              isRunningAllAgents ||
                              isRunningAgentId === agent.id ||
                              isDeletingAgentId === agent.id
                            }
                            onClick={() => void handleDeleteAgent(agent)}
                            type="button"
                          >
                            {isDeletingAgentId === agent.id ? "Deleting..." : "Delete Agent"}
                          </button>
                        </div>
                      </article>
                    ))}
                  </div>
                </Panel>

                <Panel
                  title="Agent Studio"
                  subtitle="Create agents with clearer templates and real SKILL.md attachments"
                >
                  <form className="form-stack" onSubmit={handleCreateAgent}>
                    <label>
                      Agent name
                      <input
                        required
                        placeholder="DesignyBoi"
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
                          "planner",
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
                    <div className="skill-section">
                      <div className="section-heading">
                        <h3>Template</h3>
                        <p>Choose the default operating posture for this role.</p>
                      </div>
                      <div className="template-picker studio-scroll-section studio-scroll-cards">
                        {roleTemplates.map((template) => (
                          <button
                            className={`template-card ${
                              selectedAgentTemplate?.id === template.id ? "template-card-active" : ""
                            }`}
                            key={template.id}
                            onClick={() =>
                              setAgentDraft((current) => ({
                                ...current,
                                templateId: template.id,
                              }))
                            }
                            type="button"
                          >
                            <div className="entity-meta">
                              <div>
                                <h4>{template.name}</h4>
                                <p>{template.summary}</p>
                              </div>
                              {template.is_default ? <span className="score-pill">default</span> : null}
                            </div>
                            <p className="muted template-preview">{template.instructions}</p>
                          </button>
                        ))}
                      </div>
                    </div>
                    <label>
                      Custom instructions
                      <textarea
                        rows={4}
                        placeholder="Optional: Give this agent your own operating style or constraints."
                        value={agentDraft.instructions}
                        onChange={(event) =>
                          setAgentDraft((current) => ({
                            ...current,
                            instructions: event.target.value,
                          }))
                        }
                      />
                    </label>
                    <div className="skill-section">
                      <div className="section-heading">
                        <h3>Skills</h3>
                        <p>Select extra behaviors to layer onto this agent.</p>
                      </div>
                      <div className="skill-grid studio-scroll-section studio-scroll-cards">
                        {sortedSkills.map((skill) => {
                          const isSelected = agentDraft.skillIds.includes(skill.id);
                          const isRecommended = skill.recommended_roles.includes(agentDraft.role);
                          return (
                            <label
                              className={`skill-card ${isSelected ? "skill-card-active" : ""}`}
                              key={skill.id}
                            >
                              <input
                                checked={isSelected}
                                onChange={() =>
                                  setAgentDraft((current) => ({
                                    ...current,
                                    skillIds: toggleSelection(current.skillIds, skill.id),
                                  }))
                                }
                                type="checkbox"
                              />
                              <div className="skill-card-copy">
                                <div className="entity-meta">
                                  <div>
                                    <h4>{skill.name}</h4>
                                    <p>{skill.summary}</p>
                                  </div>
                                  {isRecommended ? <span className="score-pill">recommended</span> : null}
                                </div>
                                <p className="muted">
                                  {skill.source} • {skill.path}
                                </p>
                                <pre className="template-preview markdown-preview">{skill.instructions}</pre>
                              </div>
                            </label>
                          );
                        })}
                      </div>
                    </div>
                    <button
                      className="primary-button"
                      disabled={isSubmittingAgent || roleTemplates.length === 0}
                      type="submit"
                    >
                      Create Agent
                    </button>
                    {roleTemplates.length === 0 ? (
                      <p className="muted">No templates are available for this role yet.</p>
                    ) : null}
                  </form>
                </Panel>
              </section>
            </div>
          ) : null}
        </div>
      </div>
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

async function apiDelete(path: string): Promise<void> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    throw new Error(await formatError(response));
  }
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

function findTemplateName(templateId: string | null, templates: AgentTemplate[]) {
  if (!templateId) {
    return "custom";
  }
  return templates.find((template) => template.id === templateId)?.name ?? templateId;
}

function findSkillName(skillId: string, skills: AgentSkill[]) {
  return skills.find((skill) => skill.id === skillId)?.name ?? skillId;
}

function formatTaskProject(projectId: string | null, projects: Project[]) {
  if (!projectId) {
    return "unscoped";
  }
  const project = projects.find((entry) => entry.id === projectId);
  return project ? `${project.name}` : projectId;
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

function mapPlanStatus(status: PlanStatus) {
  if (status === "approved") {
    return "in_progress";
  }
  if (status === "completed") {
    return "done";
  }
  if (status === "changes_requested") {
    return "failed";
  }
  return "todo";
}

function mapPlanTaskStatus(status: PlanTaskStatus) {
  if (status === "done") {
    return "done";
  }
  if (status === "failed" || status === "cancelled") {
    return "failed";
  }
  return "todo";
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

function summarizeRunProgress(taskRun: TaskRun) {
  const latestStderrLine = lastNonEmptyLine(taskRun.stderr);
  if (latestStderrLine) {
    return latestStderrLine;
  }
  const latestStdoutLine = lastNonEmptyLine(taskRun.stdout);
  if (latestStdoutLine) {
    return latestStdoutLine;
  }
  return "Agent started, waiting for terminal output.";
}

function lastNonEmptyLine(value: string) {
  const lines = value
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
  return lines[lines.length - 1] ?? "";
}

function sortSkillsForRole(skills: AgentSkill[], role: AgentRole) {
  return [...skills].sort((left, right) => {
    const leftRecommended = left.recommended_roles.includes(role) ? 0 : 1;
    const rightRecommended = right.recommended_roles.includes(role) ? 0 : 1;
    if (leftRecommended !== rightRecommended) {
      return leftRecommended - rightRecommended;
    }
    return left.name.localeCompare(right.name);
  });
}

function toggleSelection(values: string[], nextValue: string) {
  return values.includes(nextValue)
    ? values.filter((value) => value !== nextValue)
    : [...values, nextValue];
}

function summarizeAgentInstructions(instructions: string | null) {
  if (!instructions) {
    return "No extra custom instructions.";
  }
  return instructions;
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
