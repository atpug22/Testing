'use client';

import { useState, useEffect } from 'react';

interface AnalyticsData {
  success: boolean;
  repository: string;
  total_prs: number;
  new_prs: number;
  existing_prs: number;
  open_prs: number;
  merged_prs: number;
  api_requests_made: number;
  message: string;
}

interface PRDetails {
  id: number;
  github_pr_id: number;
  title: string;
  description: string;
  status: string;
  labels: string[];
  additions: number;
  deletions: number;
  changed_files: number;
  created_at: string;
  merged_at?: string;
  closed_at?: string;
  pr_metadata: any;
  cicd_metadata: any;
  time_cycle_metadata: any;
  reviewers_metadata: any;
  file_changes_metadata: any;
  linked_issues_metadata: any;
  git_blame_metadata: any;
  repository_info: any;
}

interface AnalyticsTabProps {
  organizationId: number;
}

export default function AnalyticsTab({ organizationId }: AnalyticsTabProps) {
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData[]>([]);
  const [prDetails, setPrDetails] = useState<PRDetails[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [repoInput, setRepoInput] = useState('');
  const [days, setDays] = useState(30);
  const [selectedRepo, setSelectedRepo] = useState<string | null>(null);
  const [showDetails, setShowDetails] = useState(false);

  const fetchExistingData = async (owner: string, repo: string) => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/v1'}/github/public/prs?owner=${owner}&repo=${repo}&organization_id=${organizationId}`, {
        method: 'GET',
        credentials: 'include',
      });

      if (response.ok) {
        const data = await response.json();
        setPrDetails(data);
        return data.length;
      }
    } catch (err) {
      console.log('No existing data found or error fetching:', err);
    }
    return 0;
  };

  const fetchAnalytics = async (owner: string, repo: string, days: number) => {
    setLoading(true);
    setError(null);
    
    try {
      // First check if we have existing data
      const existingCount = await fetchExistingData(owner, repo);
      
      // Fetch new data from GitHub
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/v1'}/github/public/fetch-public`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          owner,
          repo,
          days,
          organization_id: organizationId,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        if (response.status === 404 && errorData.detail?.includes('GitHub integration not found')) {
          throw new Error('GitHub integration not found. Please set up a GitHub integration for this organization first.');
        } else if (response.status === 400 && errorData.detail?.includes('not active')) {
          throw new Error('GitHub integration is not active. Please activate the integration first.');
        }
        throw new Error(errorData.detail || 'Failed to fetch analytics data');
      }

      const data = await response.json();
      setAnalyticsData(prev => [...prev, data]);
      
      // Refresh PR details after fetching new data
      await fetchExistingData(owner, repo);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!repoInput.trim()) return;
    
    const [owner, repo] = repoInput.split('/');
    if (!owner || !repo) {
      setError('Please enter repository in format "owner/repo"');
      return;
    }
    
    fetchAnalytics(owner, repo, days);
    setRepoInput('');
  };

  const clearData = () => {
    setAnalyticsData([]);
    setPrDetails([]);
    setSelectedRepo(null);
    setShowDetails(false);
    setError(null);
  };

  const viewDetails = (repo: string) => {
    setSelectedRepo(repo);
    setShowDetails(true);
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Repository Analytics</h3>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="repo" className="block text-sm font-medium text-gray-700 mb-2">
              Repository (format: owner/repo)
            </label>
            <input
              type="text"
              id="repo"
              value={repoInput}
              onChange={(e) => setRepoInput(e.target.value)}
              placeholder="e.g., facebook/react"
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          
          <div>
            <label htmlFor="days" className="block text-sm font-medium text-gray-700 mb-2">
              Days to analyze
            </label>
            <select
              id="days"
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              <option value={7}>7 days</option>
              <option value={30}>30 days</option>
              <option value={60}>60 days</option>
              <option value={90}>90 days</option>
              <option value={180}>180 days</option>
            </select>
          </div>
          
          <div className="flex space-x-4">
            <button
              type="submit"
              disabled={loading || !repoInput.trim()}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {loading ? 'Analyzing...' : 'Analyze Repository'}
            </button>
            
            {analyticsData.length > 0 && (
              <button
                type="button"
                onClick={clearData}
                className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500"
              >
                Clear Data
              </button>
            )}
          </div>
        </form>
        
        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-600">{error}</p>
            {error.includes('GitHub integration not found') && (
              <div className="mt-2">
                <p className="text-sm text-gray-600">
                  To use this feature, you need to set up a GitHub integration first. 
                  Go to the Integrations page to connect your GitHub account.
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      {analyticsData.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900">Analytics Results</h3>
          
          {analyticsData.map((data, index) => (
            <div key={index} className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-lg font-medium text-gray-900">{data.repository}</h4>
                <div className="flex space-x-2">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    data.success ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                  }`}>
                    {data.success ? 'Success' : 'Failed'}
                  </span>
                  <button
                    onClick={() => viewDetails(data.repository)}
                    className="px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700"
                  >
                    View Details
                  </button>
                </div>
              </div>
              
              {data.success ? (
                <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <p className="text-sm font-medium text-blue-600">Total PRs</p>
                    <p className="text-2xl font-bold text-blue-900">{data.total_prs}</p>
                  </div>
                  
                  <div className="bg-green-50 p-4 rounded-lg">
                    <p className="text-sm font-medium text-green-600">New PRs</p>
                    <p className="text-2xl font-bold text-green-900">{data.new_prs}</p>
                  </div>
                  
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <p className="text-sm font-medium text-gray-600">Existing PRs</p>
                    <p className="text-2xl font-bold text-gray-900">{data.existing_prs}</p>
                  </div>
                  
                  <div className="bg-yellow-50 p-4 rounded-lg">
                    <p className="text-sm font-medium text-yellow-600">Open PRs</p>
                    <p className="text-2xl font-bold text-yellow-900">{data.open_prs}</p>
                  </div>
                  
                  <div className="bg-purple-50 p-4 rounded-lg">
                    <p className="text-sm font-medium text-purple-600">Merged PRs</p>
                    <p className="text-2xl font-bold text-purple-900">{data.merged_prs}</p>
                  </div>
                  
                  <div className="bg-indigo-50 p-4 rounded-lg">
                    <p className="text-sm font-medium text-indigo-600">API Requests</p>
                    <p className="text-2xl font-bold text-indigo-900">{data.api_requests_made}</p>
                  </div>
                </div>
              ) : (
                <div className="text-red-600">
                  <p>{data.message}</p>
                </div>
              )}
              
              <div className="mt-4 text-sm text-gray-600">
                <p>{data.message}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      {showDetails && selectedRepo && prDetails.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">PR Details - {selectedRepo}</h3>
            <button
              onClick={() => setShowDetails(false)}
              className="px-3 py-1 bg-gray-600 text-white text-sm rounded hover:bg-gray-700"
            >
              Close
            </button>
          </div>
          
          <div className="space-y-4">
            {prDetails.map((pr, index) => (
              <div key={pr.id} className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="text-lg font-medium text-gray-900">#{pr.github_pr_id} - {pr.title}</h4>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    pr.status === 'merged' ? 'bg-green-100 text-green-800' :
                    pr.status === 'open' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {pr.status}
                  </span>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                  <div className="bg-blue-50 p-3 rounded">
                    <p className="text-sm font-medium text-blue-600">Additions</p>
                    <p className="text-lg font-bold text-blue-900">+{pr.additions}</p>
                  </div>
                  <div className="bg-red-50 p-3 rounded">
                    <p className="text-sm font-medium text-red-600">Deletions</p>
                    <p className="text-lg font-bold text-red-900">-{pr.deletions}</p>
                  </div>
                  <div className="bg-gray-50 p-3 rounded">
                    <p className="text-sm font-medium text-gray-600">Files Changed</p>
                    <p className="text-lg font-bold text-gray-900">{pr.changed_files}</p>
                  </div>
                  <div className="bg-purple-50 p-3 rounded">
                    <p className="text-sm font-medium text-purple-600">Labels</p>
                    <p className="text-lg font-bold text-purple-900">{pr.labels?.length || 0}</p>
                  </div>
                </div>
                
                {pr.labels && pr.labels.length > 0 && (
                  <div className="mb-4">
                    <p className="text-sm font-medium text-gray-700 mb-2">Labels:</p>
                    <div className="flex flex-wrap gap-2">
                      {pr.labels.map((label, labelIndex) => (
                        <span key={labelIndex} className="px-2 py-1 bg-gray-100 text-gray-800 text-xs rounded">
                          {label}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                
                {pr.pr_metadata && Object.keys(pr.pr_metadata).length > 0 && (
                  <div className="mb-4">
                    <p className="text-sm font-medium text-gray-700 mb-2">Comments & Reviews:</p>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="bg-blue-50 p-3 rounded">
                        <p className="text-sm font-medium text-blue-600">Comments</p>
                        <p className="text-lg font-bold text-blue-900">{pr.pr_metadata.comments_count || 0}</p>
                      </div>
                      <div className="bg-green-50 p-3 rounded">
                        <p className="text-sm font-medium text-green-600">Review Comments</p>
                        <p className="text-lg font-bold text-green-900">{pr.pr_metadata.review_comments_count || 0}</p>
                      </div>
                      <div className="bg-purple-50 p-3 rounded">
                        <p className="text-sm font-medium text-purple-600">Total</p>
                        <p className="text-lg font-bold text-purple-900">{(pr.pr_metadata.comments_count || 0) + (pr.pr_metadata.review_comments_count || 0)}</p>
                      </div>
                    </div>
                  </div>
                )}
                
                {pr.cicd_metadata && Object.keys(pr.cicd_metadata).length > 0 && (
                  <div className="mb-4">
                    <p className="text-sm font-medium text-gray-700 mb-2">CI/CD Status:</p>
                    <div className="flex items-center space-x-4">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        pr.cicd_metadata.overall_status === 'success' ? 'bg-green-100 text-green-800' :
                        pr.cicd_metadata.overall_status === 'failure' ? 'bg-red-100 text-red-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                        {pr.cicd_metadata.overall_status || 'Unknown'}
                      </span>
                      {pr.cicd_metadata.consistently_failing && (
                        <span className="px-2 py-1 bg-red-100 text-red-800 text-xs rounded">
                          Consistently Failing
                        </span>
                      )}
                    </div>
                  </div>
                )}
                
                {pr.reviewers_metadata && Object.keys(pr.reviewers_metadata).length > 0 && (
                  <div className="mb-4">
                    <p className="text-sm font-medium text-gray-700 mb-2">Reviewers:</p>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="bg-green-50 p-3 rounded">
                        <p className="text-sm font-medium text-green-600">Approved</p>
                        <p className="text-lg font-bold text-green-900">{pr.reviewers_metadata.approved_reviews || 0}</p>
                      </div>
                      <div className="bg-yellow-50 p-3 rounded">
                        <p className="text-sm font-medium text-yellow-600">Changes Requested</p>
                        <p className="text-lg font-bold text-yellow-900">{pr.reviewers_metadata.changes_requested || 0}</p>
                      </div>
                      <div className="bg-blue-50 p-3 rounded">
                        <p className="text-sm font-medium text-blue-600">Total Reviews</p>
                        <p className="text-lg font-bold text-blue-900">{pr.reviewers_metadata.total_reviews || 0}</p>
                      </div>
                    </div>
                  </div>
                )}
                
                {pr.linked_issues_metadata && Object.keys(pr.linked_issues_metadata).length > 0 && (
                  <div className="mb-4">
                    <p className="text-sm font-medium text-gray-700 mb-2">Linked Issues:</p>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="bg-blue-50 p-3 rounded">
                        <p className="text-sm font-medium text-blue-600">GitHub Issues</p>
                        <p className="text-lg font-bold text-blue-900">{pr.linked_issues_metadata.github_issues?.length || 0}</p>
                      </div>
                      <div className="bg-orange-50 p-3 rounded">
                        <p className="text-sm font-medium text-orange-600">Jira Issues</p>
                        <p className="text-lg font-bold text-orange-900">{pr.linked_issues_metadata.jira_issues?.length || 0}</p>
                      </div>
                      <div className="bg-purple-50 p-3 rounded">
                        <p className="text-sm font-medium text-purple-600">Linear Issues</p>
                        <p className="text-lg font-bold text-purple-900">{pr.linked_issues_metadata.linear_issues?.length || 0}</p>
                      </div>
                    </div>
                  </div>
                )}
                
                <div className="text-xs text-gray-500">
                  <p>Created: {new Date(pr.created_at).toLocaleString()}</p>
                  {pr.merged_at && <p>Merged: {new Date(pr.merged_at).toLocaleString()}</p>}
                  {pr.closed_at && <p>Closed: {new Date(pr.closed_at).toLocaleString()}</p>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
