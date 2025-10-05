interface Props {
  tagCategory: string;
  setTagCategory: (tag: string) => void;
  noteDetail: string;
  setNoteDetail: (detail: string) => void;
  projectLabel: string;
  setProjectLabel: (label: string) => void;
}

const TAG_OPTIONS = [
  { id: "source", label: "Source Content", helper: "Primary trusted material." },
  { id: "edge", label: "Edge Content", helper: "Handle with measured caution." },
  { id: "conspiracy", label: "Conspiracy Watch", helper: "Flag speculative claims." },
  { id: "devotional", label: "Devotional", helper: "Pastoral tone." },
  { id: "historical", label: "Historical Context", helper: "Prioritise factual framing." }
];

const DETAIL_OPTIONS = [
  { id: "concise", label: "Concise Bullets", helper: "High-level takeaways only." },
  { id: "standard", label: "Balanced Notes", helper: "Blend detail and brevity." },
  { id: "deep", label: "Deep Dive", helper: "Exhaustive chapter analyses." }
];

const TagGuidance = ({ tagCategory, setTagCategory, noteDetail, setNoteDetail, projectLabel, setProjectLabel }: Props) => {
  return (
    <section className="rounded-xl bg-white p-5 shadow-sm">
      <div className="grid gap-4 lg:grid-cols-3">
        <div>
          <label className="block text-sm font-medium text-slate-700" htmlFor="project-label">
            Project Label
          </label>
          <input
            id="project-label"
            className="mt-1 w-full rounded border border-slate-200 px-3 py-2 text-sm text-slate-700 focus:border-primary-500 focus:outline-none"
            placeholder="e.g. Sermon - Faith and Works"
            value={projectLabel}
            onChange={(event) => setProjectLabel(event.target.value)}
          />
          <p className="mt-2 text-xs text-slate-500">Controls folder naming inside your Obsidian vault.</p>
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700" htmlFor="tag-category">
            Tag Category
          </label>
          <select
            id="tag-category"
            className="mt-1 w-full rounded border border-slate-200 px-3 py-2 text-sm text-slate-700 focus:border-primary-500 focus:outline-none"
            value={tagCategory}
            onChange={(event) => setTagCategory(event.target.value)}
          >
            {TAG_OPTIONS.map((option) => (
              <option key={option.id} value={option.id}>
                {option.label}
              </option>
            ))}
          </select>
          <p className="mt-2 text-xs text-slate-500">
            {TAG_OPTIONS.find((option) => option.id === tagCategory)?.helper}
          </p>
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700" htmlFor="note-detail">
            Note Detail
          </label>
          <select
            id="note-detail"
            className="mt-1 w-full rounded border border-slate-200 px-3 py-2 text-sm text-slate-700 focus:border-primary-500 focus:outline-none"
            value={noteDetail}
            onChange={(event) => setNoteDetail(event.target.value)}
          >
            {DETAIL_OPTIONS.map((option) => (
              <option key={option.id} value={option.id}>
                {option.label}
              </option>
            ))}
          </select>
          <p className="mt-2 text-xs text-slate-500">
            {DETAIL_OPTIONS.find((option) => option.id === noteDetail)?.helper}
          </p>
        </div>
      </div>
    </section>
  );
};

export default TagGuidance;
