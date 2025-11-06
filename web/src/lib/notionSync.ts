import { api } from "./api";

const FEATURE_NOTION_SYNC =
  typeof window !== "undefined"
    ? process.env.NEXT_PUBLIC_FEATURE_NOTION_SYNC === "true"
    : false;

export interface WeeklyDigestData {
  weekStart: string; // ISO date string
  triaged: number;
  completed: number;
  utilizationPct: number;
}

export interface TaskData {
  id: string;
  title: string;
  status: string;
  priority: string;
  due: string | null;
  project: string | null;
  effortMin: number;
  completedAt: string | null;
  externalId: string | null;
}

export interface ProjectData {
  id: string;
  title: string;
  stage: string;
  targetDate: string | null;
  estimatedEffortMin: number;
  burnup: number;
  externalId: string | null;
}

/**
 * Push weekly workload digest to Notion Tasks database.
 * 
 * This will create/update a weekly summary entry in Notion based on
 * the workload data provided.
 * 
 * Command reference: .cursor/commands/notiontodo.md
 */
export async function pushWorkloadWeeklyDigest(
  data: WeeklyDigestData
): Promise<void> {
  if (!FEATURE_NOTION_SYNC) {
    console.warn("Notion sync is disabled. Set FEATURE_NOTION_SYNC=true to enable.");
    return;
  }

  // TODO: Implement Notion API call
  // This should call the cursor command defined in .cursor/commands/notiontodo.md
  // For now, log the operation
  console.log("Notion sync: pushWorkloadWeeklyDigest", data);
  
  // Call /api/notion/sync endpoint
  // The endpoint reads .cursor/commands/notiontodo.md and executes commands
  await api.notionSync({ weeklyDigest: data });
}

/**
 * Sync tasks and projects to Notion databases.
 * 
 * Maps local task/project data to Notion database entries:
 * - Tasks -> Notion "Tasks" database
 * - Projects -> Notion "Projects" database
 * 
 * Command reference: .cursor/commands/notiontodo.md
 */
export async function syncTasksAndProjects(data: {
  tasks: TaskData[];
  projects: ProjectData[];
}): Promise<void> {
  if (!FEATURE_NOTION_SYNC) {
    console.warn("Notion sync is disabled. Set FEATURE_NOTION_SYNC=true to enable.");
    return;
  }

  // TODO: Implement Notion API call
  // This should call the cursor command defined in .cursor/commands/notiontodo.md
  console.log("Notion sync: syncTasksAndProjects", data);
  
  // Call /api/notion/sync endpoint
  // The endpoint reads .cursor/commands/notiontodo.md and executes commands
  await api.notionSync({ tasksAndProjects: data });
}

/**
 * Check if Notion sync is enabled.
 */
export function isNotionSyncEnabled(): boolean {
  return FEATURE_NOTION_SYNC;
}

