/**
 * PR Risk Table Component
 * Displays PRs in a linear table format with expandable rows
 */

import React, { useState } from 'react';
import type { PRListItem, RiskLevel } from '../../types/pr-risk';

interface PRRiskTableProps {
  prs: PRListItem[];
  onPRClick: (pr: PRListItem) => void;
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

export const PRRiskTable: React.FC<PRRiskTableProps> = ({ prs, onPRClick }) => {
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());

  const toggleRow = (prNumber: number) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(prNumber)) {
      newExpanded.delete(prNumber);
    } else {
      newExpanded.add(prNumber);
    }
    setExpandedRows(newExpanded);
  };

  const isExpanded = (prNumber: number) => expandedRows.has(prNumber);

  if (prs.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No PRs found to display.
      </div>
    );
  }

  return (
    <div className="w-full">
      <div className="overflow-x-auto border border-gray-200 rounded-lg">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                PR
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Title
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Author
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Risk Level
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Risk Score
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                State
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Updated
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {prs.map((pr) => (
              <React.Fragment key={pr.pr_number}>
                {/* Main Row */}
                <tr
                  className={`hover:bg-gray-50 transition-colors cursor-pointer ${
                    isExpanded(pr.pr_number) ? 'bg-blue-50' : ''
                  }`}
                  onClick={() => toggleRow(pr.pr_number)}
                >
                  <td className="px-4 py-3 whitespace-nowrap">
                    <div className="flex items-center space-x-2">
                      <button
                        className={`w-4 h-4 text-gray-400 hover:text-gray-600 transition-transform ${
                          isExpanded(pr.pr_number) ? 'rotate-90' : ''
                        }`}
                        onClick={(e) => {
                          e.stopPropagation();
                          toggleRow(pr.pr_number);
                        }}
                      >
                        ▶
                      </button>
                      <span className="text-blue-600 font-medium">#{pr.pr_number}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="max-w-xs">
                      <div className="text-sm font-medium text-gray-900 truncate" title={pr.title}>
                        {pr.title}
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <span className="text-sm text-gray-900">@{pr.author}</span>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${getRiskLevelColor(pr.risk_level)}`}>
                      {getRiskLevelIcon(pr.risk_level)} {pr.risk_level.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <div className="flex items-center space-x-2">
                      <span className="text-sm font-medium text-gray-900">
                        {pr.delivery_risk_score.toFixed(1)}
                      </span>
                      <div className="w-16 bg-gray-200 rounded-full h-2">
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
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                      pr.state === 'open' ? 'bg-green-100 text-green-800' :
                      pr.state === 'merged' ? 'bg-purple-100 text-purple-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {pr.state}
                    </span>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                    {formatTimeAgo(pr.updated_at)}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <div className="flex space-x-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onPRClick(pr);
                        }}
                        className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                      >
                        View Details
                      </button>
                      <a
                        href={pr.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="text-gray-600 hover:text-gray-800 text-sm"
                      >
                        GitHub →
                      </a>
                    </div>
                  </td>
                </tr>

                {/* Expanded Row */}
                {isExpanded(pr.pr_number) && (
                  <tr className="bg-blue-50">
                    <td colSpan={8} className="px-4 py-4">
                      <div className="space-y-4">
                        {/* AI Summary */}
                        {pr.ai_summary && (
                          <div className="bg-white rounded-lg p-4 border border-blue-200">
                            <h4 className="text-sm font-semibold text-blue-900 mb-2">🤖 AI Summary</h4>
                            <p className="text-sm text-blue-800">{pr.ai_summary}</p>
                          </div>
                        )}

                        {/* Quick Stats */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          <div className="bg-white rounded-lg p-3 border border-gray-200 text-center">
                            <div className="text-lg font-bold text-gray-900">{pr.delivery_risk_score.toFixed(1)}</div>
                            <div className="text-xs text-gray-600">Risk Score</div>
                          </div>
                          <div className="bg-white rounded-lg p-3 border border-gray-200 text-center">
                            <div className="text-lg font-bold text-gray-900">{formatTimeAgo(pr.created_at)}</div>
                            <div className="text-xs text-gray-600">Created</div>
                          </div>
                          <div className="bg-white rounded-lg p-3 border border-gray-200 text-center">
                            <div className="text-lg font-bold text-gray-900">{formatTimeAgo(pr.updated_at)}</div>
                            <div className="text-xs text-gray-600">Updated</div>
                          </div>
                          <div className="bg-white rounded-lg p-3 border border-gray-200 text-center">
                            <div className="text-lg font-bold text-gray-900">{pr.risk_level}</div>
                            <div className="text-xs text-gray-600">Risk Level</div>
                          </div>
                        </div>

                        {/* Additional Actions */}
                        <div className="flex space-x-2">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              onPRClick(pr);
                            }}
                            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition-colors text-sm"
                          >
                            View Full Analysis
                          </button>
                          <a
                            href={pr.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            className="bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700 transition-colors text-sm"
                          >
                            Open in GitHub
                          </a>
                        </div>
                      </div>
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default PRRiskTable;
