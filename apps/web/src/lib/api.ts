import axios from "axios";

export const api = axios.create({
  baseURL: "/api",
});

export interface StageSnapshot {
  stage: string;
  status: "queued" | "running" | "succeeded" | "failed";
  detail?: string | null;
  started_at?: string | null;
  finished_at?: string | null;
}

export interface JobRecord {
  job_id: string;
  project_id: string;
  created_at: string;
  status: "queued" | "processing" | "completed" | "failed";
  metadata: Record<string, unknown>;
  stages: StageSnapshot[];
  errors: string[];
}

export interface JobsResponse {
  jobs: JobRecord[];
}

export interface SubmitResponse {
  status: string;
  job_id: string;
  project_id: string;
  project_slug: string;
  project_dir: string;
  files: Array<Record<string, unknown>>;
  references: Array<Record<string, unknown>>;
}

export const fetchJobs = async (): Promise<JobsResponse> => {
  const { data } = await api.get<JobsResponse>("/diagnostics/jobs");
  return data;
};

export const submitIngest = async ({
  files,
  urls,
  tagCategory,
  noteDetail,
  projectLabel,
}: {
  files: File[];
  urls: string;
  tagCategory: string;
  noteDetail: string;
  projectLabel: string;
}): Promise<SubmitResponse> => {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));
  if (urls.trim().length > 0) {
    formData.append("reference_urls", urls);
  }
  if (tagCategory) {
    formData.append("tag_category", tagCategory);
  }
  if (noteDetail) {
    formData.append("note_detail", noteDetail);
  }
  if (projectLabel.trim().length > 0) {
    formData.append("project_label", projectLabel.trim());
  }

  const { data } = await api.post<SubmitResponse>("/ingest/submit", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
};
