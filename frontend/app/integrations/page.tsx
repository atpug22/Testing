'use client';

import { useState, useEffect } from 'react';
import DashboardLayout from '../../components/DashboardLayout';
import ProtectedRoute from '../../components/ProtectedRoute';

export default function IntegrationsPage() {
  const [githubToken, setGithubToken] = useState('');
  const [githubOwner, setGithubOwner] = useState('');
  const [loading, setLoading] = useState(false);
  const [hasIntegration, setHasIntegration] = useState(false);
  const [integration, setIntegration] = useState<any>(null);
  const [currentOrgId, setCurrentOrgId] = useState<number | null>(null);
  const [showTokenInput, setShowTokenInput] = useState(false);

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
            const data = await integrationResponse.json();
            if (data) {
              setHasIntegration(true);
              setIntegration(data);
              setGithubOwner(data.github_owner || '');
            }
          }
        }
      }
    } catch (error) {
      console.error('Failed to check integration:', error);
    }
  };

  const handleSaveGitHub = async () => {
    if (!githubToken.trim()) {
      alert('Please enter a GitHub access token');
      return;
    }

    if (!currentOrgId) {
      alert('No organization found. Please create an organization first.');
      return;
    }

    setLoading(true);
    try {
      const url = hasIntegration
        ? `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/v1'}/integrations/github/${currentOrgId}`
        : `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/v1'}/integrations/github/${currentOrgId}`;
      
      const method = hasIntegration ? 'PATCH' : 'POST';
      
      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          access_token: githubToken,
          github_owner: githubOwner || null,
        }),
      });

      if (response.ok) {
        alert('GitHub integration configured successfully!');
        setShowTokenInput(false);
        checkIntegration();
      } else {
        const error = await response.json();
        alert(error.detail || 'Failed to configure GitHub integration');
      }
    } catch (error) {
      alert('Failed to configure GitHub integration');
    } finally {
      setLoading(false);
      setGithubToken('');
    }
  };

  const handleDeleteIntegration = async () => {
    if (!confirm('Are you sure you want to delete this integration?')) {
      return;
    }

    if (!currentOrgId) return;

    setLoading(true);
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/v1'}/integrations/github/${currentOrgId}`,
        {
          method: 'DELETE',
          credentials: 'include',
        }
      );

      if (response.ok) {
        alert('Integration deleted successfully');
        setHasIntegration(false);
        setIntegration(null);
      } else {
        alert('Failed to delete integration');
      }
    } catch (error) {
      alert('Failed to delete integration');
    } finally {
      setLoading(false);
    }
  };

  return (
    <ProtectedRoute>
      <DashboardLayout>
        <div className="p-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Integrations</h1>
            <p className="text-gray-600">
              Connect your tools to sync data and enhance your workflow
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* GitHub Integration */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-12 h-12 bg-gray-900 rounded-lg flex items-center justify-center">
                  <svg className="w-7 h-7 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 0C4.477 0 0 4.484 0 10.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0110 4.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.203 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.942.359.31.678.921.678 1.856 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0020 10.017C20 4.484 15.522 0 10 0z" clipRule="evenodd" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">GitHub</h3>
                  <p className="text-sm text-gray-500">
                    {hasIntegration ? 'Connected' : 'Not connected'}
                  </p>
                </div>
              </div>

              {hasIntegration && !showTokenInput ? (
                <div className="space-y-4">
                  <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                    <div className="flex items-center gap-2 text-green-700">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span className="text-sm font-medium">Active</span>
                    </div>
                    {integration?.github_owner && (
                      <p className="text-sm text-green-600 mt-1">
                        Owner: {integration.github_owner}
                      </p>
                    )}
                  </div>
                  
                  <div className="space-y-2">
                    <button
                      onClick={() => setShowTokenInput(true)}
                      className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                    >
                      Update Token
                    </button>
                    <button
                      onClick={handleDeleteIntegration}
                      disabled={loading}
                      className="w-full px-4 py-2 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 transition-colors"
                    >
                      Disconnect
                    </button>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      GitHub Access Token *
                    </label>
                    <input
                      type="password"
                      value={githubToken}
                      onChange={(e) => setGithubToken(e.target.value)}
                      placeholder="ghp_xxxxxxxxxxxx"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      <a 
                        href="https://github.com/settings/tokens/new?scopes=repo,read:org" 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:underline"
                      >
                        Generate a token
                      </a>
                    </p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      GitHub Username/Org (optional)
                    </label>
                    <input
                      type="text"
                      value={githubOwner}
                      onChange={(e) => setGithubOwner(e.target.value)}
                      placeholder="your-username"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>

                  <div className="space-y-2">
                    <button
                      onClick={handleSaveGitHub}
                      disabled={loading}
                      className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
                    >
                      {loading ? 'Saving...' : hasIntegration ? 'Update' : 'Connect'}
                    </button>
                    {showTokenInput && (
                      <button
                        onClick={() => setShowTokenInput(false)}
                        className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                      >
                        Cancel
                      </button>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Slack Integration (Placeholder) */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 opacity-60">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-12 h-12 bg-purple-600 rounded-lg flex items-center justify-center">
                  <svg className="w-7 h-7 text-white" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M5.042 15.165a2.528 2.528 0 01-2.52 2.523A2.528 2.528 0 010 15.165a2.527 2.527 0 012.522-2.52h2.52v2.52zM6.313 15.165a2.527 2.527 0 012.521-2.52 2.527 2.527 0 012.521 2.52v6.313A2.528 2.528 0 018.834 24a2.528 2.528 0 01-2.521-2.522v-6.313zM8.834 5.042a2.528 2.528 0 01-2.521-2.52A2.528 2.528 0 018.834 0a2.528 2.528 0 012.521 2.522v2.52H8.834zM8.834 6.313a2.528 2.528 0 012.521 2.521 2.528 2.528 0 01-2.521 2.521H2.522A2.528 2.528 0 010 8.834a2.528 2.528 0 012.522-2.521h6.312zM18.956 8.834a2.528 2.528 0 012.522-2.521A2.528 2.528 0 0124 8.834a2.528 2.528 0 01-2.522 2.521h-2.522V8.834zM17.688 8.834a2.528 2.528 0 01-2.523 2.521 2.527 2.527 0 01-2.52-2.521V2.522A2.527 2.527 0 0115.165 0a2.528 2.528 0 012.523 2.522v6.312zM15.165 18.956a2.528 2.528 0 012.523 2.522A2.528 2.528 0 0115.165 24a2.527 2.527 0 01-2.52-2.522v-2.522h2.52zM15.165 17.688a2.527 2.527 0 01-2.52-2.523 2.526 2.526 0 012.52-2.52h6.313A2.527 2.527 0 0124 15.165a2.528 2.528 0 01-2.522 2.523h-6.313z"/>
                  </svg>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">Slack</h3>
                  <p className="text-sm text-gray-500">Coming soon</p>
                </div>
              </div>
              <p className="text-sm text-gray-600 mb-4">
                Get notifications about your team's activity in Slack.
              </p>
              <button
                disabled
                className="w-full px-4 py-2 bg-gray-200 text-gray-500 rounded-lg cursor-not-allowed"
              >
                Coming Soon
              </button>
            </div>

            {/* Jira Integration (Placeholder) */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 opacity-60">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center">
                  <svg className="w-7 h-7 text-white" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M11.571 11.513H0a5.218 5.218 0 0 0 5.232 5.215h2.13v2.057A5.215 5.215 0 0 0 12.575 24V12.518a1.005 1.005 0 0 0-1.005-1.005zm5.723-5.756H5.736a5.215 5.215 0 0 0 5.215 5.214h2.129v2.058a5.218 5.218 0 0 0 5.215 5.214V6.758a1.001 1.001 0 0 0-1.001-1.001zM23.013 0H11.455a5.215 5.215 0 0 0 5.215 5.215h2.129v2.057A5.215 5.215 0 0 0 24 12.483V1.005A1.001 1.001 0 0 0 23.013 0Z"/>
                  </svg>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">Jira</h3>
                  <p className="text-sm text-gray-500">Coming soon</p>
                </div>
              </div>
              <p className="text-sm text-gray-600 mb-4">
                Sync issues and track progress across tools.
              </p>
              <button
                disabled
                className="w-full px-4 py-2 bg-gray-200 text-gray-500 rounded-lg cursor-not-allowed"
              >
                Coming Soon
              </button>
            </div>
          </div>
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  );
}

