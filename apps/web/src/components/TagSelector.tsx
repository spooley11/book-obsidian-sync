import { useState } from "react";

const DEFAULT_TAGS = [
  { id: "source", label: "Source Content" },
  { id: "edge", label: "Edge Content" },
  { id: "conspiracy", label: "Conspiracy Watch" },
  { id: "devotional", label: "Devotional" },
  { id: "historical", label: "Historical Context" }
];

const TagSelector = () => {
  const [selectedTag, setSelectedTag] = useState<string>(DEFAULT_TAGS[0]!.id);

  return (
    <div className="rounded-xl bg-white p-4 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">Tag Guidance</h2>
      <p className="mt-1 text-sm text-slate-500">
        Choose a tone marker so the AI knows how to balance reverence, caution, or critical analysis.
      </p>
      <div className="mt-4 space-y-3">
        <label className="block text-sm font-medium text-slate-700" htmlFor="tag-category">
          Primary Category
        </label>
        <select
          id="tag-category"
          className="w-full rounded border border-slate-200 px-3 py-2 text-sm text-slate-700 focus:border-primary-500 focus:outline-none"
          value={selectedTag}
          onChange={(e) => setSelectedTag(e.target.value)}
        >
          {DEFAULT_TAGS.map((tag) => (
            <option key={tag.id} value={tag.id}>
              {tag.label}
            </option>
          ))}
        </select>
        <button className="w-full rounded border border-primary-200 px-3 py-2 text-sm font-medium text-primary-600 hover:border-primary-500">
          Optimise Tags (SQL sweep)
        </button>
        <p className="text-xs text-slate-500">
          The optimise routine will ask the backend to review project topics, merge duplicates, and surface recommended labels.
        </p>
      </div>
    </div>
  );
};

export default TagSelector;
