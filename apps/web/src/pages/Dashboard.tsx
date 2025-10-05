import IngestPanel from "../components/IngestPanel";
import PipelineStatus from "../components/PipelineStatus";
import TagGuidance from "../components/TagGuidance";

interface Props {
  activeProjectId: string | null;
  setActiveProjectId: (id: string | null) => void;
  tagCategory: string;
  setTagCategory: (tag: string) => void;
  noteDetail: string;
  setNoteDetail: (detail: string) => void;
  projectLabel: string;
  setProjectLabel: (label: string) => void;
}

const Dashboard = ({
  activeProjectId,
  setActiveProjectId,
  tagCategory,
  setTagCategory,
  noteDetail,
  setNoteDetail,
  projectLabel,
  setProjectLabel,
}: Props) => {
  return (
    <div className="space-y-6">
      <TagGuidance
        tagCategory={tagCategory}
        setTagCategory={setTagCategory}
        noteDetail={noteDetail}
        setNoteDetail={setNoteDetail}
        projectLabel={projectLabel}
        setProjectLabel={setProjectLabel}
      />
      <IngestPanel
        tagCategory={tagCategory}
        noteDetail={noteDetail}
        projectLabel={projectLabel}
        setActiveProjectId={setActiveProjectId}
      />
      <PipelineStatus projectId={activeProjectId} />
    </div>
  );
};

export default Dashboard;
