export interface IWebhook {
  created_at: string;
  cycle: boolean;
  id: string;
  is_active: boolean;
  issue: boolean;
  issue_comment: boolean;
  module: boolean;
  project: boolean;
  secret_key?: string;
  updated_at: string;
  url: string;
  project_type?: "all" | "individual";
  selected_projects?: string[];
}

export type TWebhookEventTypes = "all" | "individual";
export type TWebhookProjectType = "all" | "individual";
