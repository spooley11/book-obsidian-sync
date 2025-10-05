import { useState } from "react";
import { BrowserRouter, Link, Route, Routes } from "react-router-dom";

import Dashboard from "./pages/Dashboard";
import Diagnostics from "./pages/Diagnostics";

function App() {
  const [activeProjectId, setActiveProjectId] = useState<string | null>(null);
  const [tagCategory, setTagCategory] = useState<string>("source");
  const [noteDetail, setNoteDetail] = useState<string>("standard");
  const [projectLabel, setProjectLabel] = useState<string>("");

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-100">
        <header className="border-b border-slate-200 bg-white">
          <div className="mx-auto flex max-w-6xl flex-col gap-3 px-6 py-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h1 className="text-xl font-semibold text-slate-900">Converter Control Deck</h1>
              <p className="text-sm text-slate-500">Track ingestion, transcription, and summarisation progress in real time.</p>
            </div>
            <nav className="flex items-center gap-4 text-sm">
              <Link to="/" className="text-slate-600 hover:text-primary-600">
                Dashboard
              </Link>
              <Link to="/diagnostics" className="text-slate-600 hover:text-primary-600">
                Diagnostics
              </Link>
              <span className="rounded border border-slate-200 px-3 py-1 text-xs uppercase text-slate-500">
                Active Project: <strong className="ml-1 text-slate-900">{activeProjectId ?? "None"}</strong>
              </span>
            </nav>
          </div>
        </header>

        <main className="mx-auto max-w-6xl px-6 py-6">
          <Routes>
            <Route
              path="/"
              element={
                <Dashboard
                  activeProjectId={activeProjectId}
                  setActiveProjectId={setActiveProjectId}
                  tagCategory={tagCategory}
                  setTagCategory={setTagCategory}
                  noteDetail={noteDetail}
                  setNoteDetail={setNoteDetail}
                  projectLabel={projectLabel}
                  setProjectLabel={setProjectLabel}
                />
              }
            />
            <Route path="/diagnostics" element={<Diagnostics />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
