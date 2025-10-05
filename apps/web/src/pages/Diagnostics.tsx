import { useQuery } from "@tanstack/react-query";

import { JobRecord, JobsResponse, fetchJobs } from "../lib/api";

const Diagnostics = () => {
  const { data, isLoading, isError, refetch, isFetching } = useQuery<JobsResponse>({
    queryKey: ["jobs"],
    queryFn: fetchJobs,
    refetchInterval: 8000,
  });

  if (isLoading) {
    return <div className="rounded-xl bg-white p-4 shadow-sm">Loading diagnostics...</div>;
  }

  if (isError || !data) {
    return (
      <div className="rounded-xl bg-red-50 p-4 text-sm text-red-700">
        Failed to load diagnostics. Please verify the API is running.
      </div>
    );
  }

  const jobs = data.jobs;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-slate-900">In-flight Jobs</h2>
        <button
          className="rounded border border-slate-200 px-3 py-1 text-sm text-slate-600 hover:border-primary-500 hover:text-primary-600"
          onClick={() => refetch()}
        >
          Refresh {isFetching && "..."}
        </button>
      </div>
      {jobs.length === 0 ? (
        <p className="rounded-xl bg-white p-4 text-sm text-slate-500">No jobs registered yet.</p>
      ) : (
        <div className="space-y-4">
          {jobs.map((job: JobRecord) => (
            <div key={job.job_id} className="rounded-xl bg-white p-4 shadow-sm">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <h3 className="text-sm font-semibold text-slate-800">Project {job.project_id}</h3>
                  <p className="text-xs text-slate-500">
                    Job {job.job_id} - {new Date(job.created_at).toLocaleString()}
                  </p>
                </div>
                <span className="rounded-full border border-slate-200 px-3 py-1 text-xs uppercase text-slate-600">
                  {job.status}
                </span>
              </div>
              <pre className="mt-3 overflow-auto rounded bg-slate-900 p-3 text-xs text-slate-100">
{JSON.stringify(job, null, 2)}
              </pre>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Diagnostics;
