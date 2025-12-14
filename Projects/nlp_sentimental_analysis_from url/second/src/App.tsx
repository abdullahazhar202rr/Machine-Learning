import { useState } from 'react';
import { LogOut, Sparkles } from 'lucide-react';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { Auth } from './components/Auth';
import { UrlInput } from './components/UrlInput';
import { Dashboard } from './components/Dashboard';
import { AnalysisHistory } from './components/AnalysisHistory';

function AppContent() {
  const { user, signOut } = useAuth();
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);

  if (!user) {
    return <Auth />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50">
      <nav className="bg-white shadow-md border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-2 rounded-lg">
                <Sparkles className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-800">Sentiment Analyzer</h1>
                <p className="text-xs text-gray-500">AI-powered web content analysis</p>
              </div>
            </div>
            <button
              onClick={signOut}
              className="flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition"
            >
              <LogOut className="w-4 h-4" />
              Sign Out
            </button>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <UrlInput onAnalysisStart={setCurrentJobId} />

        {currentJobId && (
          <div className="mb-8">
            <Dashboard jobId={currentJobId} />
          </div>
        )}

        <AnalysisHistory
          onSelectJob={setCurrentJobId}
          currentJobId={currentJobId || undefined}
        />
      </div>

      <footer className="bg-white border-t border-gray-200 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-gray-600 text-sm">
            Powered by AI - Analyze sentiment from any web content
          </p>
        </div>
      </footer>
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
