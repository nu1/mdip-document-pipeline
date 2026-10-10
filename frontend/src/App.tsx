import { useState } from "react";
import { ErrorBanner } from "./components/common/ErrorBanner";
import { Footer } from "./components/layout/Footer";
import { Header } from "./components/layout/Header";
import { Intro } from "./components/layout/Intro";
import { DocumentLibrary } from "./components/library/DocumentLibrary";
import { UploadCard } from "./components/upload/UploadCard";
import { Workspace } from "./components/workspace/Workspace";
import { useDocumentDetail } from "./hooks/useDocumentDetail";
import { useDocuments } from "./hooks/useDocuments";
import { useHealth } from "./hooks/useHealth";

export function App() {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [page, setPage] = useState<number>(0);
  const [uploadError, setUploadError] = useState<string>("");
  const [isUploading, setIsUploading] = useState<boolean>(false);

  const { maxUploadBytes } = useHealth();

  const {
    documents,
    error: listError,
    setError: setListError,
  } = useDocuments(page, 20, isUploading);

  const {
    document,
    isLoading: isDocumentLoading,
    error: documentError,
    setError: setDocumentError,
  } = useDocumentDetail(selectedId);

  const handleUploadSuccess = (id: string) => {
    setSelectedId(id);
    setPage(0);
    setUploadError("");
  };

  const handleDismissAllErrors = () => {
    setUploadError("");
    setListError("");
    setDocumentError("");
  };

  return (
    <div className="app">
      <Header />
      <Intro />

      <ErrorBanner
        errors={[uploadError, listError]}
        onDismiss={handleDismissAllErrors}
      />

      <main>
        <aside>
          <UploadCard
            maxBytes={maxUploadBytes}
            onUploadSuccess={handleUploadSuccess}
            onError={setUploadError}
            onUploadingChange={setIsUploading}
          />

          <DocumentLibrary
            documents={documents}
            selectedId={selectedId}
            onSelect={setSelectedId}
            page={page}
            onPageChange={setPage}
            pageSize={20}
          />
        </aside>

        <Workspace
          selectedId={selectedId}
          document={document}
          isLoading={isDocumentLoading}
          documentError={documentError}
          onDismissError={() => setDocumentError("")}
        />
      </main>

      <Footer />
    </div>
  );
}

export default App;
