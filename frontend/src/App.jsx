import React, { Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Navbar } from './components/Navbar';
import { Footer } from './components/Footer';
import { ErrorBoundary } from './components/ErrorBoundary';
import { LoadingState } from './components/LoadingState';
import Home from './pages/Home';

// Route-level code-splitting for secondary analytical views
const KnowledgeGraphPage = lazy(() => import('./pages/KnowledgeGraphPage'));
const SimilarityPage = lazy(() => import('./pages/SimilarityPage'));
const DiscoverPage = lazy(() => import('./pages/DiscoverPage'));
const EvidencePage = lazy(() => import('./pages/EvidencePage'));
const DiseasePage = lazy(() => import('./pages/DiseasePage'));
const GenePage = lazy(() => import('./pages/GenePage'));
const MedGenRecordPage = lazy(() => import('./pages/MedGenRecordPage'));
const ComparePage = lazy(() => import('./pages/ComparePage'));
const WorkspacePage = lazy(() => import('./pages/WorkspacePage'));
const ReportPage = lazy(() => import('./pages/ReportPage'));
const ReproducibilityPage = lazy(() => import('./pages/ReproducibilityPage'));
const AboutPage = lazy(() => import('./pages/AboutPage'));

export function App() {
  return (
    <Router>
      <div className="app-container">
        <Navbar />
        <main className="main-content">
          <ErrorBoundary>
            <Suspense fallback={<LoadingState message="Loading research module..." />}>
              <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/graph" element={<KnowledgeGraphPage />} />
                <Route path="/similarity" element={<SimilarityPage />} />
                <Route path="/discover" element={<DiscoverPage />} />
                <Route path="/evidence" element={<EvidencePage />} />
                <Route path="/disease/:diseaseName" element={<DiseasePage />} />
                <Route path="/gene/:geneSymbol" element={<GenePage />} />
                <Route path="/medgen/:medgenUid" element={<MedGenRecordPage />} />
                <Route path="/compare" element={<ComparePage />} />
                <Route path="/workspace" element={<WorkspacePage />} />
                <Route path="/report/:reportId" element={<ReportPage />} />
                <Route path="/reproducibility/:snapshotId" element={<ReproducibilityPage />} />
                <Route path="/about" element={<AboutPage />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </Suspense>
          </ErrorBoundary>
        </main>
        <Footer />
      </div>
    </Router>
  );
}

export default App;
