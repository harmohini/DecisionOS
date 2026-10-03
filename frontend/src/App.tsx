import React, { useEffect, useState } from 'react';
import { Header } from './components/Header';
import { Footer } from './components/Footer';
import { Home } from './pages/Home';
import { checkHealth } from './services/api';
import { SystemHealth } from './types';

export const App: React.FC = () => {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await checkHealth();
      setHealth(data);
    } catch (err: any) {
      setError(err?.message || 'Could not connect to DecisionOS backend server.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHealth();
  }, []);

  return (
    <div className="min-h-screen flex flex-col bg-[#FBF9F5] text-stone-800">
      <Header />
      
      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 lg:px-8 pt-8">
        <Home 
          health={health} 
          loading={loading} 
          error={error} 
          onRefreshHealth={loadHealth} 
        />
      </main>

      <Footer />
    </div>
  );
};

export default App;
