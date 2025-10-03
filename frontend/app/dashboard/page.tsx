'use client';

import { useState, useEffect } from 'react';
import DashboardLayout from '../../components/DashboardLayout';
import ProtectedRoute from '../../components/ProtectedRoute';
import Link from 'next/link';

interface Repository {
  name: string;
  full_name: string;
  description: string | null;
  private: boolean;
  html_url: string;
}

export default function DashboardPage() {
  const [selectedRepos, setSelectedRepos] = useState<string[]>([]);
  const [availableRepos, setAvailableRepos] = useState<Repository[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasIntegration, setHasIntegration] = useState(false);
  const [currentOrgId, setCurrentOrgId] = useState<number | null>(null);

  useEffect(() => {
    checkIntegration();
  }, []);

  const checkIntegration = async () => {
    try {
      // Get organizations
      const orgsResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/v1'}/organizations/`, {
        credentials: 'include',
      });
      
      if (orgsResponse.ok) {
        const orgs = await orgsResponse.json();
        if (orgs.length > 0) {
          const orgId = orgs[0].id;
          setCurrentOrgId(orgId);
          
          // Check if GitHub integration exists
          const integrationResponse = await fetch(
            `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/v1'}/integrations/github/${orgId}`,
            { credentials: 'include' }
          );
          
          if (integrationResponse.ok) {
            const integration = await integrationResponse.json();
            if (integration) {
              setHasIntegration(true);
              setSelectedRepos(integration.selected_repos || []);
              fetchRepositories(orgId);
            }
          }
        }
      }
    } catch (error) {
      console.error('Failed to check integration:', error);
    }
  };

  const fetchRepositories = async (orgId: number) => {
    setLoading(true);
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/v1'}/integrations/github/${orgId}/repositories`,
        { credentials: 'include' }
      );
      
      if (response.ok) {
        const repos = await response.json();
        setAvailableRepos(repos);
      }
    } catch (error) {
      console.error('Failed to fetch repositories:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRepoToggle = async (repoName: string) => {
    const newSelected = selectedRepos.includes(repoName)
      ? selectedRepos.filter(r => r !== repoName)
      : [...selectedRepos, repoName];
    
    setSelectedRepos(newSelected);

    // Update on backend
    if (currentOrgId) {
      try {
        await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/v1'}/integrations/github/${currentOrgId}`,
          {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ selected_repos: newSelected }),
          }
        );
      } catch (error) {
        console.error('Failed to update selected repos:', error);
      }
    }
  };

  return (
    <ProtectedRoute>
      <DashboardLayout>
        <div className="p-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Dashboard</h1>
            <p className="text-gray-600">
              Select repositories to track and analyze your team's productivity
            </p>
          </div>

          {!hasIntegration ? (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
              <div className="flex items-start gap-3">
                <svg className="w-6 h-6 text-yellow-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <div>
                  <h3 className="text-lg font-medium text-yellow-900 mb-1">
                    GitHub Integration Required
                  </h3>
                  <p className="text-yellow-700 mb-4">
                    You need to configure GitHub integration before you can select repositories.
                  </p>
                  <Link
                    href="/integrations"
                    className="inline-flex items-center px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors"
                  >
                    Go to Integrations
                  </Link>
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">
                  Repository Selector
                </h2>
                
                {loading ? (
                  <div className="text-center py-8">
                    <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                    <p className="mt-2 text-gray-600">Loading repositories...</p>
                  </div>
                ) : availableRepos.length === 0 ? (
                  <p className="text-gray-500">No repositories found.</p>
                ) : (
                  <div className="space-y-2 max-h-96 overflow-y-auto">
                    {availableRepos.map((repo) => (
                      <label
                        key={repo.full_name}
                        className="flex items-start gap-3 p-3 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
                      >
                        <input
                          type="checkbox"
                          checked={selectedRepos.includes(repo.name)}
                          onChange={() => handleRepoToggle(repo.name)}
                          className="mt-1 w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                        />
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <p className="font-medium text-gray-900">{repo.full_name}</p>
                            {repo.private && (
                              <span className="px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded">
                                Private
                              </span>
                            )}
                          </div>
                          {repo.description && (
                            <p className="text-sm text-gray-500 mt-1">{repo.description}</p>
                          )}
                        </div>
                      </label>
                    ))}
                  </div>
                )}
              </div>

              {selectedRepos.length > 0 && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                  <h3 className="text-lg font-medium text-blue-900 mb-2">
                    Selected Repositories ({selectedRepos.length})
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {selectedRepos.map((repo) => (
                      <span
                        key={repo}
                        className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium"
                      >
                        {repo}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  );
}

