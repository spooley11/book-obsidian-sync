import { useCallback, useMemo, useState } from "react";
import { useDropzone } from "react-dropzone";

import { submitIngest } from "../lib/api";

interface Props {
  tagCategory: string;
  noteDetail: string;
  projectLabel: string;
  setActiveProjectId: (id: string | null) => void;
}

interface SelectedFile {
  id: string;
  file: File;
}

const randomId = () =>
  typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
    ? crypto.randomUUID()
    : Math.random().toString(36).slice(2);

const IngestPanel = ({ tagCategory, noteDetail, projectLabel, setActiveProjectId }: Props) => {
  const [selectedFiles, setSelectedFiles] = useState<SelectedFile[]>([]);
  const [urlsText, setUrlsText] = useState("");
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setSubmitting] = useState(false);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    setSelectedFiles((prev) => [
      ...prev,
      ...acceptedFiles.map((file) => ({
        id: `${file.name}-${file.lastModified}-${randomId()}`,
        file,
      })),
    ]);
    setStatus(null);
    setError(null);
  }, []);

  const removeFile = (id: string) => {
    setSelectedFiles((prev) => prev.filter((item) => item.id !== id));
    setStatus(null);
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop, multiple: true, noClick: false });

  const filesReady = useMemo(() => selectedFiles.map((item) => item.file), [selectedFiles]);

  const handleSubmit = async () => {
    if (filesReady.length === 0 && urlsText.trim().length === 0) {
      setError("Add at least one file or URL before submitting.");
      return;
    }
    setSubmitting(true);
    setError(null);
    setStatus(null);
    try {
      const response = await submitIngest({
        files: filesReady,
        urls: urlsText,
        tagCategory,
        noteDetail,
        projectLabel,
      });
      setStatus(`Queued job ${response.job_id} for project ${response.project_slug}.`);
      setActiveProjectId(response.project_id);
      setSelectedFiles([]);
      setUrlsText("");
    } catch (err) {
      console.error(err);
      setError("Failed to queue ingestion. Check diagnostics for more info.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="rounded-xl bg-white p-6 shadow-sm">
      <div
        {...getRootProps()}
        className={`rounded-lg border-2 border-dashed p-8 transition ${
          isDragActive ? "border-primary-600 bg-primary-50" : "border-slate-300 bg-slate-50"
        }`}
      >
        <input {...getInputProps()} />
        <p className="text-lg font-medium text-slate-800">Drag & Drop files</p>
        <p className="text-sm text-slate-500">PDF, Markdown, audio/video supported. Everything stays in your local vault.</p>
        <span className="mt-3 inline-block rounded-full bg-primary-600 px-4 py-1 text-sm text-white">Add Files</span>
      </div>

      {selectedFiles.length > 0 && (
        <div className="mt-4 space-y-2">
          <p className="text-sm font-semibold text-slate-700">Selected files</p>
          <ul className="space-y-2">
            {selectedFiles.map(({ id, file }) => (
              <li
                key={id}
                className="flex items-center justify-between rounded border border-slate-200 px-3 py-2 text-sm text-slate-600"
              >
                <span>{file.name}</span>
                <button type="button" className="text-xs text-red-600 hover:text-red-700" onClick={() => removeFile(id)}>
                  Remove
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-6">
        <label htmlFor="ingest-urls" className="block text-sm font-medium text-slate-700">
          Reference URLs (one per line)
        </label>
        <textarea
          id="ingest-urls"
          className="mt-1 h-28 w-full rounded border border-slate-200 px-3 py-2 text-sm text-slate-700 focus:border-primary-500 focus:outline-none"
          placeholder="https://www.churchofjesuschrist.org/..."
          value={urlsText}
          onChange={(event) => setUrlsText(event.target.value)}
        />
      </div>

      <div className="mt-6 flex flex-wrap gap-3 text-sm">
        <button
          type="button"
          onClick={handleSubmit}
          className="rounded bg-primary-600 px-4 py-2 font-medium text-white hover:bg-primary-700 disabled:opacity-60"
          disabled={isSubmitting}
        >
          {isSubmitting ? "Submitting..." : "Submit & Queue"}
        </button>
        <button
          type="button"
          onClick={() => {
            setSelectedFiles([]);
            setUrlsText("");
            setStatus(null);
            setError(null);
          }}
          className="rounded border border-slate-200 px-4 py-2 font-medium text-slate-500 hover:border-slate-300"
        >
          Reset
        </button>
      </div>

      <div className="mt-4 space-y-1 text-sm">
        {status && <p className="text-green-600">{status}</p>}
        {error && <p className="text-red-600">{error}</p>}
      </div>
    </section>
  );
};

export default IngestPanel;
