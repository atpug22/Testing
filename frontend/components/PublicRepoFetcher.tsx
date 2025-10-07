'use client';

import { useState } from 'react';

interface PublicRepoFetcherProps {
  onDataFetched: (owner: string, repo: string) => void;
}

export default function PublicRepoFetcher({ onDataFetched }: PublicRepoFetcherProps) {
  const [owner, setOwner] = useState('');
  const [repo, setRepo] = useState('');
  const [days, setDays] = useState(90);
  const [githubToken, setGithubToken] = useState('');
  const [fetching, setFetching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFetch = async () => {
    if (!owner || !repo) {
      setError('Please enter both owner and repository name');
      return;
    }

    if (!githubToken) {
      setError('Please enter your GitHub token to analyze public repositories');
      return;
    }

    setFetching(true);
    setError(null);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/v1'}/github/public/fetch-public`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          owner,
          repo,
          days,
          github_token: githubToken || undefined,
        }),
      });

      if (response.ok) {
        const result = await response.json();
        onDataFetched(owner, repo);
        alert(`Successfully fetched ${result.total_prs} PRs from ${owner}/${repo}`);

        // Redirect to the first team member page after successful data fetch
        // We'll redirect to a team member that was created from the GitHub data
        // For now, let's redirect to a hardcoded member ID, but ideally we'd get this from the API response
        setTimeout(() => {
          window.location.href = '/member/20'; // Sandy-1711 from n8n data
        }, 2000);
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

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        Fetch Public Repository Data
      </h3>

      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Repository Owner
            </label>
            <input
              type="text"
              value={owner}
              onChange={(e) => setOwner(e.target.value)}
              placeholder="e.g., microsoft"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Repository Name
            </label>
            <input
              type="text"
              value={repo}
              onChange={(e) => setRepo(e.target.value)}
              placeholder="e.g., vscode"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

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

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            GitHub Token (Required for Public Repos)
          </label>
          <input
            type="password"
            value={githubToken}
            onChange={(e) => setGithubToken(e.target.value)}
            placeholder="ghp_... (required for public repository analysis)"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
          <p className="text-xs text-gray-500 mt-1">
            Required: Your GitHub personal access token for analyzing public repositories
          </p>
          <p className="text-xs text-blue-600 mt-1">
            <a href="https://github.com/settings/tokens" target="_blank" rel="noopener noreferrer" className="underline">
              Get your token here
            </a> (select "repo" scope)
          </p>
        </div>

        {error && (
          <div className="text-red-600 bg-red-50 p-3 rounded">
            {error}
          </div>
        )}

        <button
          onClick={handleFetch}
          disabled={fetching || !owner || !repo || !githubToken}
          className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
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
      </div>
    </div>
  );
}
