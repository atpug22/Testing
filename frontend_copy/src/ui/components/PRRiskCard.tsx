/**
 * PR Risk Card Component
 * Displays individual PR with risk metrics
 */

import React from 'react';
import type { PRListItem, RiskLevel } from '../../types/pr-risk';

interface PRRiskCardProps {
  pr: PRListItem;
  onClick?: () => void;
}

const getRiskLevelColor = (level: RiskLevel): string => {
  switch (level) {
    case 'critical':
      return 'bg-red-100 text-red-800 border-red-200';
    case 'high':
      return 'bg-orange-100 text-orange-800 border-orange-200';
    case 'medium':
      return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    case 'low':
      return 'bg-green-100 text-green-800 border-green-200';
    default:
      return 'bg-gray-100 text-gray-800 border-gray-200';
  }
};

const getRiskLevelIcon = (level: RiskLevel): string => {
  switch (level) {
    case 'critical':
      return '🚨';
    case 'high':
      return '⚠️';
    case 'medium':
      return '⚡';
    case 'low':
      return '✅';
    default:
      return '📊';
  }
};

const formatTimeAgo = (dateString: string): string => {
  const date = new Date(dateString);
  const now = new Date();
  const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));

  if (diffInHours < 1) return 'Just now';
  if (diffInHours < 24) return `${diffInHours}h ago`;

  const diffInDays = Math.floor(diffInHours / 24);
  if (diffInDays < 7) return `${diffInDays}d ago`;

  const diffInWeeks = Math.floor(diffInDays / 7);
  return `${diffInWeeks}w ago`;
};

export const PRRiskCard: React.FC<PRRiskCardProps> = ({ pr, onClick }) => {
  const riskColorClass = getRiskLevelColor(pr.risk_level);
  const riskIcon = getRiskLevelIcon(pr.risk_level);

  return (
    <div
      className={`
        bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow cursor-pointer
        ${onClick ? 'hover:bg-gray-50' : ''}
      `}
      onClick={onClick}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center space-x-2">
          <span className="text-blue-600 font-medium">#{pr.pr_number}</span>
          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${riskColorClass}`}>
            {riskIcon} {pr.risk_level.toUpperCase()}
          </span>
        </div>
        <div className="text-right text-sm text-gray-500">
          <div>Score: {pr.delivery_risk_score.toFixed(1)}</div>
          <div>{formatTimeAgo(pr.updated_at)}</div>
        </div>
      </div>

      {/* Title */}
      <h3 className="text-sm font-medium text-gray-900 mb-2 line-clamp-2">
        {pr.title}
      </h3>

      {/* Author and State */}
      <div className="flex items-center justify-between text-xs text-gray-500 mb-2">
        <div className="flex items-center space-x-2">
          <span>@{pr.author}</span>
          <span className={`px-2 py-1 rounded ${
            pr.state === 'open' ? 'bg-green-100 text-green-700' :
            pr.state === 'merged' ? 'bg-purple-100 text-purple-700' :
            'bg-gray-100 text-gray-700'
          }`}>
            {pr.state}
          </span>
        </div>
      </div>

      {/* AI Summary */}
      {pr.ai_summary && (
        <div className="text-xs text-gray-600 bg-gray-50 rounded p-2 mt-2">
          {pr.ai_summary}
        </div>
      )}

      {/* Risk Score Bar */}
      <div className="mt-3">
        <div className="flex justify-between text-xs text-gray-500 mb-1">
          <span>Delivery Risk</span>
          <span>{pr.delivery_risk_score.toFixed(1)}/100</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full ${
              pr.delivery_risk_score >= 80 ? 'bg-red-500' :
              pr.delivery_risk_score >= 60 ? 'bg-orange-500' :
              pr.delivery_risk_score >= 40 ? 'bg-yellow-500' :
              'bg-green-500'
            }`}
            style={{ width: `${Math.min(pr.delivery_risk_score, 100)}%` }}
          />
        </div>
      </div>
    </div>
  );
};

export default PRRiskCard;
