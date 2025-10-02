'use client';

import { useEffect, useState } from 'react';

interface Repository {
  id: number;
  name: string;
  full_name: string;
  private: boolean;
  owner: {
    login: string;
    id: number;
    avatar_url?: string;
  };
  description?: string;
  language?: string;
  stars: number;
  forks: number;
  updated_at: string;
}

interface RepositoryPickerProps {
  onRepositorySelect: (owner: string, repo: string) => void;
  onFetchData: (owner: string, repo: string, days: number) => void;
}

export default function RepositoryPicker({ onRepositorySelect, onFetchData }: RepositoryPickerProps) {
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedRepo, setSelectedRepo] = useState<Repository | null>(null);
  const [days, setDays] = useState(90);
  const [fetching, setFetching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchRepositories();
  }, []);

  const fetchRepositories = async () => {
    try {
              const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/v1'}/auth/repos`, {
        credentials: 'include',
      });
      
      if (response.ok) {
        const repos = await response.json();
        setRepositories(repos);
      } else {
        setError('Failed to load repositories');
      }
    } catch (err) {
      setError('Failed to load repositories');
    } finally {
      setLoading(false);
    }
  };

  const handleRepositorySelect = (repo: Repository) => {
    setSelectedRepo(repo);
    onRepositorySelect(repo.owner.login, repo.name);
  };

  const handleFetchData = async () => {
    if (!selectedRepo) return;
    
    setFetching(true);
    setError(null);
    
    try {
              const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/v1'}/github/repos/fetch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          owner: selectedRepo.owner.login,
          repo: selectedRepo.name,
          days: days,
        }),
      });
      
      if (response.ok) {
        const result = await response.json();
        onFetchData(selectedRepo.owner.login, selectedRepo.name, days);
        alert(`Successfully fetched ${result.total_prs} PRs from ${selectedRepo.full_name}`);
      } else {
        const error = await response.json();
        setError(error.detail || 'Failed to fetch repository data');
      }
    } catch (err) {
      setError('Failed to fetch repository data');
    } finally {
      setFetching(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Select Repository</h3>
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-2 text-gray-600">Loading repositories...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Select Repository</h3>
        <div className="text-red-600 bg-red-50 p-4 rounded">
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Repository Selection */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Select Repository</h3>
        <div className="space-y-3 max-h-64 overflow-y-auto">
          {repositories.map((repo) => (
            <div
              key={repo.id}
              onClick={() => handleRepositorySelect(repo)}
              className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                selectedRepo?.id === repo.id
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h4 className="font-medium text-gray-900">{repo.full_name}</h4>
                    {repo.private && (
                      <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                        Private
                      </span>
                    )}
                  </div>
                  {repo.description && (
                    <p className="text-sm text-gray-600 mt-1 line-clamp-2">{repo.description}</p>
                  )}
                  <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                    {repo.language && <span>{repo.language}</span>}
                    <span>⭐ {repo.stars}</span>
                    <span>🍴 {repo.forks}</span>
                    <span>Updated {new Date(repo.updated_at).toLocaleDateString()}</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Selected Repository Actions */}
      {selectedRepo && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Fetch Data</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Analysis Period (days)
              </label>
              <select
                value={days}
                onChange={(e) => setDays(Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value={30}>30 days</option>
                <option value={60}>60 days</option>
                <option value={90}>90 days</option>
                <option value={180}>180 days</option>
                <option value={365}>1 year</option>
              </select>
            </div>
            
            <div className="flex items-center gap-4">
              <button
                onClick={handleFetchData}
                disabled={fetching}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {fetching ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    Fetching...
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                    </svg>
                    Fetch Repository Data
                  </>
                )}
              </button>
              
              <div className="text-sm text-gray-600">
                This will fetch PRs, commits, and compute team metrics
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
