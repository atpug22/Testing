/**
 * AI Impact Dashboard Component
 * Main dashboard for AI Impact Analysis with tabs and metrics
 */

import React, { useState, useEffect } from 'react';
import { AIImpactAPI } from '../lib/ai-impact-api';
import { AIImpactAnalysis, AIImpactResponse } from '../types/ai-impact';
import { AIImpactCard } from './components/AIImpactCard';

interface AIImpactDashboardProps {
  owner: string;
  repo: string;
}

export const AIImpactDashboard: React.FC<AIImpactDashboardProps> = ({ owner, repo }) => {
  const [analysis, setAnalysis] = useState<AIImpactAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const fetchAnalysis = async (forceRefresh = false) => {
    try {
      setLoading(true);
      setError(null);
      
      const response: AIImpactResponse = await AIImpactAPI.analyzeAIImpact({
        owner,
        repo,
        days: 90,
        force_refresh: forceRefresh,
        include_detailed_analysis: true
      });

      if (response.success && response.analysis) {
        setAnalysis(response.analysis);
      } else {
        setError(response.error_message || 'Analysis failed');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch AI impact analysis');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchAnalysis(true);
  };

  useEffect(() => {
    fetchAnalysis();
  }, [owner, repo]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-gray-600">Analyzing AI Impact...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-center">
          <span className="text-red-500 mr-2">❌</span>
          <h3 className="text-lg font-medium text-red-800">Analysis Failed</h3>
        </div>
        <p className="mt-2 text-red-700">{error}</p>
        <button
          onClick={() => fetchAnalysis()}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
        >
          Retry Analysis
        </button>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
        <p className="text-gray-600">No analysis data available</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">AI Impact Analysis</h2>
          <p className="text-gray-600">
            Analyzing AI adoption and impact for {owner}/{repo}
          </p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {refreshing ? 'Refreshing...' : 'Refresh Analysis'}
        </button>
      </div>

      {/* Main Analysis Card */}
      <AIImpactCard analysis={analysis} />

      {/* Detailed Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Adoption Metrics */}
        <div className="bg-white rounded-lg shadow-md border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Adoption Metrics</h3>
          <div className="space-y-4">
            <div className="flex justify-between">
              <span className="text-gray-600">Total PRs Analyzed</span>
              <span className="font-semibold">{analysis.metrics.total_prs_analyzed}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">AI-Authored PRs</span>
              <span className="font-semibold text-blue-600">{analysis.metrics.ai_authored_prs}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Human-Authored PRs</span>
              <span className="font-semibold text-gray-600">{analysis.metrics.human_authored_prs}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Adoption Rate</span>
              <span className="font-semibold text-green-600">
                {(analysis.metrics.ai_adoption_rate * 100).toFixed(1)}%
              </span>
            </div>
          </div>
        </div>

        {/* Performance Comparison */}
        <div className="bg-white rounded-lg shadow-md border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance Impact</h3>
          <div className="space-y-4">
            {analysis.metrics.ai_avg_merge_time_hours && analysis.metrics.human_avg_merge_time_hours ? (
              <>
                <div className="flex justify-between">
                  <span className="text-gray-600">AI Avg Merge Time</span>
                  <span className="font-semibold text-blue-600">
                    {(analysis.metrics.ai_avg_merge_time_hours / 24).toFixed(1)}d
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Human Avg Merge Time</span>
                  <span className="font-semibold text-gray-600">
                    {(analysis.metrics.human_avg_merge_time_hours / 24).toFixed(1)}d
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Performance Impact</span>
                  <span className={`font-semibold ${
                    analysis.metrics.ai_avg_merge_time_hours < analysis.metrics.human_avg_merge_time_hours
                      ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {analysis.metrics.ai_avg_merge_time_hours < analysis.metrics.human_avg_merge_time_hours
                      ? '🚀 Faster' : '🐌 Slower'}
                  </span>
                </div>
              </>
            ) : (
              <p className="text-gray-500 text-sm">Insufficient data for performance comparison</p>
            )}
          </div>
        </div>

        {/* Quality Assessment */}
        <div className="bg-white rounded-lg shadow-md border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Quality Assessment</h3>
          <div className="space-y-4">
            <div className="flex justify-between">
              <span className="text-gray-600">Quality Score</span>
              <span className={`font-semibold ${
                analysis.quality.quality_score >= 70 ? 'text-green-600' :
                analysis.quality.quality_score >= 40 ? 'text-yellow-600' : 'text-red-600'
              }`}>
                {analysis.quality.quality_score.toFixed(0)}/100
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">High-Risk PRs</span>
              <span className={`font-semibold ${
                analysis.quality.high_risk_ai_prs.length > 0 ? 'text-red-600' : 'text-green-600'
              }`}>
                {analysis.quality.high_risk_ai_prs.length}
              </span>
            </div>
            {analysis.quality.common_issues.length > 0 && (
              <div>
                <span className="text-gray-600 text-sm">Common Issues:</span>
                <ul className="mt-1 text-sm text-gray-500">
                  {analysis.quality.common_issues.slice(0, 2).map((issue, index) => (
                    <li key={index} className="truncate">• {issue}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Trends Chart Placeholder */}
      <div className="bg-white rounded-lg shadow-md border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">AI Adoption Trends</h3>
        <div className="flex items-center justify-center h-32 bg-gray-50 rounded-lg">
          <div className="text-center">
            <span className="text-2xl mb-2 block">
              {analysis.trends.trend_direction === 'increasing' ? '📈' :
               analysis.trends.trend_direction === 'decreasing' ? '📉' : '➡️'}
            </span>
            <p className="text-gray-600 capitalize">
              AI adoption is {analysis.trends.trend_direction}
            </p>
            <p className="text-sm text-gray-500 mt-1">
              {Object.keys(analysis.trends.weekly_ai_adoption).length} weeks of data
            </p>
          </div>
        </div>
      </div>

      {/* Recommendations */}
      {analysis.quality.recommendations.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-4">Recommendations</h3>
          <ul className="space-y-2">
            {analysis.quality.recommendations.map((recommendation, index) => (
              <li key={index} className="flex items-start">
                <span className="text-blue-500 mr-2 mt-0.5">💡</span>
                <span className="text-blue-800">{recommendation}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
