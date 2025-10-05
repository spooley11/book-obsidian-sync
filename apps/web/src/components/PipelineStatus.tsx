import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";

import { JobRecord, JobsResponse, fetchJobs } from "../lib/api";

interface Props {
  projectId: string | null;
}

const DEFAULT_STAGES = [
  { stage: "ingest", status: "queued" as const },
  { stage: "transcribe", status: "queued" as const },
  { stage: "chunk", status: "queued" as const },
  { stage: "summarise", status: "queued" as const },
  { stage: "export", status: "queued" as const },
];

const PipelineStatus = ({ projectId }: Props) => {
  const { data, isFetching } = useQuery<JobsResponse>({
    queryKey: ["jobs"],
    queryFn: fetchJobs,
    refetchInterval: projectId ? 4000 : false,
  });

  const activeJob: JobRecord | null = useMemo(() => {
    if (!projectId || !data) {
      return null;
    }
    return data.jobs.find((job) => job.project_id === projectId) ?? null;
  }, [data, projectId]);

  const stages = activeJob?.stages ?? DEFAULT_STAGES;
  const errors = activeJob?.errors ?? [];

  return (
    <div className="rounded-xl bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-slate-900">Pipeline State</h2>
        <div className="flex gap-2 text-sm">
          <button className="rounded border border-slate-200 px-3 py-1 text-slate-600 hover:border-primary-500 hover:text-primary-600">
            Stop
          </button>
          <button className="rounded border border-slate-200 px-3 py-1 text-slate-600 hover:border-primary-500 hover:text-primary-600">
            Restart
          </button>
        </div>
      </div>
      <p className="mt-1 text-sm text-slate-500">
        {projectId ? `Tracking project ${projectId} (status: ${activeJob?.status ?? "n/a"})` : "Prepare and process intake to start."}
        {isFetching && projectId && <span className="ml-2 text-xs text-slate-400">Refreshing…</span>}
      </p>
      <div className="mt-4 space-y-3">
        {stages.map((stage) => (
          <div key={stage.stage} className="flex items-center justify-between rounded-lg border border-slate-200 px-4 py-3">
            <div>
              <p className="text-sm font-semibold uppercase text-slate-800">{stage.stage}</p>
              <p className="text-xs text-slate-500">Status: {stage.status}</p>\n              {stage.detail && <p className="text-xs text-slate-400">{stage.detail}</p>}
            </div>
          </div>
        ))}
      </div>
      {errors.length > 0 && (
        <div className="mt-4 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          <p className="font-semibold">Errors</p>
          <ul className="mt-1 list-disc pl-5">
            {errors.map((error, index) => (
              <li key={index}>{error}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default PipelineStatus;

