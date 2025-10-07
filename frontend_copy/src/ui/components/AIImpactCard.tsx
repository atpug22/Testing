/**
 * AI Impact Card Component
 * Displays AI-related metrics in a card format similar to PR Risk cards
 */

import React from 'react';
import { AIImpactAnalysis, AIConfidenceLevel } from '../../types/ai-impact';

interface AIImpactCardProps {
  analysis: AIImpactAnalysis;
  className?: string;
}

export const AIImpactCard: React.FC<AIImpactCardProps> = ({ analysis, className = '' }) => {
  const getConfidenceColor = (confidence: AIConfidenceLevel): string => {
    switch (confidence) {
      case 'high': return 'text-green-600 bg-green-50';
      case 'medium': return 'text-yellow-600 bg-yellow-50';
      case 'low': return 'text-orange-600 bg-orange-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getImpactScoreColor = (score: number): string => {
    if (score >= 70) return 'text-green-600';
    if (score >= 40) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getTrendIcon = (direction: string): string => {
    switch (direction) {
      case 'increasing': return '📈';
      case 'decreasing': return '📉';
      default: return '➡️';
    }
  };

  const formatPercentage = (value: number): string => {
    return `${(value * 100).toFixed(1)}%`;
  };

  const formatHours = (hours?: number): string => {
    if (!hours) return 'N/A';
    if (hours < 24) return `${hours.toFixed(1)}h`;
    return `${(hours / 24).toFixed(1)}d`;
  };

  return (
    <div className={`bg-white rounded-lg shadow-md border border-gray-200 p-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            {analysis.repository}
          </h3>
          <p className="text-sm text-gray-500">
            AI Impact Analysis • {analysis.days_analyzed} days
          </p>
        </div>
        <div className={`px-3 py-1 rounded-full text-sm font-medium ${getConfidenceColor(analysis.confidence_level)}`}>
          {analysis.confidence_level.toUpperCase()}
        </div>
      </div>

      {/* Impact Score */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">AI Impact Score</span>
          <span className={`text-2xl font-bold ${getImpactScoreColor(analysis.impact_score)}`}>
            {analysis.impact_score.toFixed(0)}/100
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full ${
              analysis.impact_score >= 70 ? 'bg-green-500' :
              analysis.impact_score >= 40 ? 'bg-yellow-500' : 'bg-red-500'
            }`}
            style={{ width: `${analysis.impact_score}%` }}
          />
        </div>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="text-center p-3 bg-blue-50 rounded-lg">
          <div className="text-2xl font-bold text-blue-600">
            {formatPercentage(analysis.metrics.ai_adoption_rate)}
          </div>
          <div className="text-sm text-gray-600">AI Adoption</div>
        </div>

        <div className="text-center p-3 bg-purple-50 rounded-lg">
          <div className="text-2xl font-bold text-purple-600">
            {analysis.metrics.ai_authored_prs}
          </div>
          <div className="text-sm text-gray-600">AI PRs</div>
        </div>

        <div className="text-center p-3 bg-green-50 rounded-lg">
          <div className="text-2xl font-bold text-green-600">
            {analysis.quality.quality_score.toFixed(0)}
          </div>
          <div className="text-sm text-gray-600">Quality Score</div>
        </div>

        <div className="text-center p-3 bg-orange-50 rounded-lg">
          <div className="text-xl">
            {getTrendIcon(analysis.trends.trend_direction)}
          </div>
          <div className="text-sm text-gray-600 capitalize">
            {analysis.trends.trend_direction}
          </div>
        </div>
      </div>

      {/* Performance Comparison */}
      {analysis.metrics.ai_avg_merge_time_hours && analysis.metrics.human_avg_merge_time_hours && (
        <div className="mb-6">
          <h4 className="text-sm font-medium text-gray-700 mb-3">Merge Time Comparison</h4>
          <div className="flex justify-between items-center">
            <div className="text-center">
              <div className="text-lg font-semibold text-blue-600">
                {formatHours(analysis.metrics.ai_avg_merge_time_hours)}
              </div>
              <div className="text-xs text-gray-500">AI PRs</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-semibold text-gray-600">
                {formatHours(analysis.metrics.human_avg_merge_time_hours)}
              </div>
              <div className="text-xs text-gray-500">Human PRs</div>
            </div>
          </div>
        </div>
      )}

      {/* Risk Indicators */}
      {analysis.quality.high_risk_ai_prs.length > 0 && (
        <div className="mb-4">
          <div className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
            <div className="flex items-center">
              <span className="text-red-500 mr-2">⚠️</span>
              <span className="text-sm font-medium text-red-700">
                {analysis.quality.high_risk_ai_prs.length} High-Risk AI PRs
              </span>
            </div>
            <button className="text-xs text-red-600 hover:text-red-800 font-medium">
              View Details
            </button>
          </div>
        </div>
      )}

      {/* Key Insights */}
      <div>
        <h4 className="text-sm font-medium text-gray-700 mb-2">Key Insights</h4>
        <div className="space-y-2">
          {analysis.summary_insights.slice(0, 3).map((insight, index) => (
            <div key={index} className="flex items-start">
              <span className="text-blue-500 mr-2 mt-0.5">•</span>
              <span className="text-sm text-gray-600">{insight}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className="mt-4 pt-4 border-t border-gray-100">
        <div className="flex justify-between items-center text-xs text-gray-500">
          <span>
            Analyzed {analysis.metrics.total_prs_analyzed} PRs
          </span>
          <span>
            {new Date(analysis.analysis_date).toLocaleDateString()}
          </span>
        </div>
      </div>
    </div>
  );
};
