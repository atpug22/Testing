/**
 * Expanded PR View Component
 * Shows detailed information for a selected PR
 */

import React from 'react';
import type { PRRiskAnalysis } from '../../types/pr-risk';

interface ExpandedPRViewProps {
  pr: PRRiskAnalysis;
  onClose: () => void;
}

const getRiskLevelColor = (level: string): string => {
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

const getRiskLevelIcon = (level: string): string => {
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

export const ExpandedPRView: React.FC<ExpandedPRViewProps> = ({ pr, onClose }) => {
  const riskColorClass = getRiskLevelColor(pr.risk_level);
  const riskIcon = getRiskLevelIcon(pr.risk_level);

  // Debug logging to see what data we're receiving
  console.log('ExpandedPRView received PR data:', pr);

  // Check if we have the required data
  if (!pr || !pr.pr_number) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
        <div className="bg-white rounded-lg p-8 max-w-md">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Error Loading PR Details</h2>
          <p className="text-gray-600 mb-4">Unable to load PR details. The data may be incomplete.</p>
          <button
            onClick={onClose}
            className="w-full bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <span className="text-2xl font-bold text-blue-600">#{pr.pr_number}</span>
              <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${riskColorClass}`}>
                {riskIcon} {pr.risk_level?.toUpperCase() || 'UNKNOWN'}
              </span>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-2xl font-bold"
            >
              ×
            </button>
          </div>
          <h1 className="text-xl font-semibold text-gray-900 mt-2">{pr.title || 'No Title'}</h1>
          <div className="flex items-center space-x-4 mt-2 text-sm text-gray-600">
            <span>by @{pr.author || 'Unknown'}</span>
            <span>•</span>
            <span className={`px-2 py-1 rounded text-xs ${
              pr.state === 'open' ? 'bg-green-100 text-green-700' :
              pr.state === 'merged' ? 'bg-purple-100 text-purple-700' :
              'bg-gray-100 text-gray-700'
            }`}>
              {pr.state || 'Unknown'}
            </span>
            <span>•</span>
            <span>Created {pr.created_at ? formatTimeAgo(pr.created_at) : 'Unknown'}</span>
            <span>•</span>
            <span>Updated {pr.updated_at ? formatTimeAgo(pr.updated_at) : 'Unknown'}</span>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* AI Summary */}
          {pr.ai_summary && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-blue-900 mb-2">🤖 AI Summary</h3>
              <p className="text-blue-800">{pr.ai_summary}</p>
            </div>
          )}

          {/* Risk Score Overview */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">📊 Overall Risk Score</h3>
              <div className="text-3xl font-bold text-gray-900 mb-2">
                {(pr.delivery_risk_score || 0).toFixed(1)}/100
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3 mb-2">
                <div 
                  className={`h-3 rounded-full ${
                    (pr.delivery_risk_score || 0) >= 80 ? 'bg-red-500' :
                    (pr.delivery_risk_score || 0) >= 60 ? 'bg-orange-500' :
                    (pr.delivery_risk_score || 0) >= 40 ? 'bg-yellow-500' :
                    'bg-green-500'
                  }`}
                  style={{ width: `${Math.min(pr.delivery_risk_score || 0, 100)}%` }}
                />
              </div>
              <p className="text-sm text-gray-600">
                {(pr.delivery_risk_score || 0) >= 80 ? 'Critical risk level' :
                 (pr.delivery_risk_score || 0) >= 60 ? 'High risk level' :
                 (pr.delivery_risk_score || 0) >= 40 ? 'Medium risk level' :
                 'Low risk level'}
              </p>
            </div>

            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">🔗 Quick Actions</h3>
              <div className="space-y-2">
                <a
                  href={pr.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block w-full bg-blue-600 text-white text-center py-2 px-4 rounded hover:bg-blue-700 transition-colors"
                >
                  View PR on GitHub
                </a>
                <button 
                  onClick={() => {
                    navigator.clipboard.writeText(pr.url || '');
                    // You could add a toast notification here
                  }}
                  className="w-full bg-gray-600 text-white py-2 px-4 rounded hover:bg-gray-700 transition-colors"
                >
                  Copy PR Link
                </button>
              </div>
            </div>
          </div>

          {/* Detailed Metrics - Only show if we have the data */}
          {pr.stuckness_metrics && pr.blast_radius_metrics && pr.dynamics_metrics && pr.business_impact_metrics ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Stuckness Metrics */}
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">⏰ Stuckness Metrics</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Time since last activity:</span>
                    <span className="font-medium">{pr.stuckness_metrics.time_since_last_activity_hours}h</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Unresolved review threads:</span>
                    <span className="font-medium">{pr.stuckness_metrics.unresolved_review_threads}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Failed CI checks:</span>
                    <span className="font-medium">{pr.stuckness_metrics.failed_ci_checks}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Time waiting for reviewer:</span>
                    <span className="font-medium">{pr.stuckness_metrics.time_waiting_for_reviewer_hours}h</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">PR age:</span>
                    <span className="font-medium">{pr.stuckness_metrics.pr_age_days}d</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Rebase/force push count:</span>
                    <span className="font-medium">{pr.stuckness_metrics.rebase_force_push_count}</span>
                  </div>
                </div>
              </div>

              {/* Blast Radius Metrics */}
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">💥 Blast Radius Metrics</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Lines added:</span>
                    <span className="font-medium text-green-600">+{pr.blast_radius_metrics.lines_added}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Lines removed:</span>
                    <span className="font-medium text-red-600">-{pr.blast_radius_metrics.lines_removed}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Files changed:</span>
                    <span className="font-medium">{pr.blast_radius_metrics.files_changed}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Downstream dependencies:</span>
                    <span className="font-medium">{pr.blast_radius_metrics.downstream_dependencies}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Critical path touched:</span>
                    <span className={`font-medium ${pr.blast_radius_metrics.critical_path_touched ? 'text-red-600' : 'text-green-600'}`}>
                      {pr.blast_radius_metrics.critical_path_touched ? 'Yes' : 'No'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Test coverage delta:</span>
                    <span className="font-medium">{pr.blast_radius_metrics.test_coverage_delta.toFixed(1)}%</span>
                  </div>
                </div>
              </div>

              {/* Dynamics Metrics */}
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">👥 Team Dynamics</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Author experience score:</span>
                    <span className="font-medium">{pr.dynamics_metrics.author_experience_score.toFixed(1)}/100</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Reviewer load:</span>
                    <span className="font-medium">{pr.dynamics_metrics.reviewer_load.toFixed(1)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Approval ratio:</span>
                    <span className="font-medium">{pr.dynamics_metrics.approval_ratio.toFixed(1)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Author merge history:</span>
                    <span className="font-medium">{pr.dynamics_metrics.author_merge_history}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Avg review time:</span>
                    <span className="font-medium">{pr.dynamics_metrics.avg_review_time_hours.toFixed(1)}h</span>
                  </div>
                </div>
              </div>

              {/* Business Impact Metrics */}
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">💼 Business Impact</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Linked to release:</span>
                    <span className={`font-medium ${pr.business_impact_metrics.linked_to_release ? 'text-blue-600' : 'text-gray-600'}`}>
                      {pr.business_impact_metrics.linked_to_release ? 'Yes' : 'No'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">External dependencies:</span>
                    <span className="font-medium">{pr.business_impact_metrics.external_dependencies}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Affects core functionality:</span>
                    <span className={`font-medium ${pr.business_impact_metrics.affects_core_functionality ? 'text-red-600' : 'text-green-600'}`}>
                      {pr.business_impact_metrics.affects_core_functionality ? 'Yes' : 'No'}
                    </span>
                  </div>
                  {pr.business_impact_metrics.priority_label && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Priority label:</span>
                      <span className="font-medium bg-yellow-100 text-yellow-800 px-2 py-1 rounded text-sm">
                        {pr.business_impact_metrics.priority_label}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-yellow-900 mb-2">⚠️ Limited Data Available</h3>
              <p className="text-yellow-800">
                Detailed metrics are not available for this PR. This may be because the PR hasn't been fully analyzed yet, or the analysis data is incomplete.
              </p>
            </div>
          )}

          {/* Composite Scores - Only show if we have the data */}
          {pr.composite_scores ? (
            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">📈 Composite Risk Scores</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">{pr.composite_scores.stuckness_score.toFixed(1)}</div>
                  <div className="text-sm text-gray-600">Stuckness</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-orange-600">{pr.composite_scores.blast_radius_score.toFixed(1)}</div>
                  <div className="text-sm text-gray-600">Blast Radius</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-600">{pr.composite_scores.dynamics_score.toFixed(1)}</div>
                  <div className="text-sm text-gray-600">Dynamics</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">{pr.composite_scores.business_impact_score.toFixed(1)}</div>
                  <div className="text-sm text-gray-600">Business Impact</div>
                </div>
              </div>
            </div>
          ) : null}

          {/* Detailed PR Information */}
          {pr.detailed_info && (
            <>
              {/* Description Section */}
              {pr.detailed_info.description && (
                <div className="bg-white border border-gray-200 rounded-lg p-4">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">📝 Description</h3>
                  <div className="prose prose-sm max-w-none text-gray-700 whitespace-pre-wrap">
                    {pr.detailed_info.description}
                  </div>
                </div>
              )}

              {/* Labels */}
              {pr.detailed_info.labels && pr.detailed_info.labels.length > 0 && (
                <div className="bg-white border border-gray-200 rounded-lg p-4">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">🏷️ Labels</h3>
                  <div className="flex flex-wrap gap-2">
                    {pr.detailed_info.labels.map((label, idx) => (
                      <span
                        key={idx}
                        className="px-3 py-1 rounded-full text-sm font-medium border"
                        style={{
                          backgroundColor: `#${label.color}20`,
                          borderColor: `#${label.color}`,
                          color: `#${label.color}`
                        }}
                      >
                        {label.name}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Timeline Metrics */}
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">⏱️ Timeline Metrics</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {pr.detailed_info.timeline_metrics.time_to_first_review_hours !== null && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Time to first review:</span>
                      <span className="font-medium">{pr.detailed_info.timeline_metrics.time_to_first_review_hours?.toFixed(1)}h</span>
                    </div>
                  )}
                  {pr.detailed_info.timeline_metrics.time_to_first_approval_hours !== null && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Time to first approval:</span>
                      <span className="font-medium">{pr.detailed_info.timeline_metrics.time_to_first_approval_hours?.toFixed(1)}h</span>
                    </div>
                  )}
                  {pr.detailed_info.timeline_metrics.time_to_merge_hours !== null && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Time to merge:</span>
                      <span className="font-medium">{pr.detailed_info.timeline_metrics.time_to_merge_hours?.toFixed(1)}h</span>
                    </div>
                  )}
                  {pr.detailed_info.timeline_metrics.first_commit_at && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">First commit:</span>
                      <span className="font-medium">{new Date(pr.detailed_info.timeline_metrics.first_commit_at).toLocaleString()}</span>
                    </div>
                  )}
                  {pr.detailed_info.timeline_metrics.last_commit_at && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Last commit:</span>
                      <span className="font-medium">{new Date(pr.detailed_info.timeline_metrics.last_commit_at).toLocaleString()}</span>
                    </div>
                  )}
                  {pr.detailed_info.timeline_metrics.time_from_first_to_last_commit_hours !== null && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Development time:</span>
                      <span className="font-medium">{pr.detailed_info.timeline_metrics.time_from_first_to_last_commit_hours?.toFixed(1)}h</span>
                    </div>
                  )}
                  <div className="flex justify-between">
                    <span className="text-gray-600">Review cycles:</span>
                    <span className="font-medium">{pr.detailed_info.timeline_metrics.number_of_review_cycles}</span>
                  </div>
                </div>
              </div>

              {/* File Changes Table */}
              {pr.detailed_info.files && pr.detailed_info.files.length > 0 && (
                <div className="bg-white border border-gray-200 rounded-lg p-4">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">📂 File Changes ({pr.detailed_info.files.length} files)</h3>
                  <div className="mb-3 flex gap-4 text-sm">
                    <span className="text-green-600 font-medium">+{pr.detailed_info.total_additions} additions</span>
                    <span className="text-red-600 font-medium">-{pr.detailed_info.total_deletions} deletions</span>
                    <span className="text-gray-600 font-medium">{pr.detailed_info.total_changes} total changes</span>
                  </div>
                  <div className="overflow-x-auto max-h-96 overflow-y-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50 sticky top-0">
                        <tr>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">File</th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                          <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">+/-</th>
                          <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Changes</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {pr.detailed_info.files.map((file, idx) => (
                          <tr key={idx} className="hover:bg-gray-50">
                            <td className="px-4 py-2 text-sm">
                              <a 
                                href={file.blob_url || '#'} 
                                target="_blank" 
                                rel="noopener noreferrer"
                                className="text-blue-600 hover:underline font-mono text-xs"
                              >
                                {file.filename}
                              </a>
                            </td>
                            <td className="px-4 py-2 text-sm">
                              <span className={`px-2 py-1 rounded text-xs ${
                                file.status === 'added' ? 'bg-green-100 text-green-800' :
                                file.status === 'removed' ? 'bg-red-100 text-red-800' :
                                file.status === 'modified' ? 'bg-blue-100 text-blue-800' :
                                'bg-gray-100 text-gray-800'
                              }`}>
                                {file.status}
                              </span>
                            </td>
                            <td className="px-4 py-2 text-sm text-right">
                              <span className="text-green-600">+{file.additions}</span>
                              {' / '}
                              <span className="text-red-600">-{file.deletions}</span>
                            </td>
                            <td className="px-4 py-2 text-sm text-right font-medium">{file.changes}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* CI/CD Checks */}
              {pr.detailed_info.ci_checks && pr.detailed_info.ci_checks.length > 0 && (
                <div className="bg-white border border-gray-200 rounded-lg p-4">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">
                    🔄 CI/CD Checks 
                    <span className={`ml-2 text-sm font-normal ${
                      pr.detailed_info.ci_status === 'success' ? 'text-green-600' :
                      pr.detailed_info.ci_status === 'failure' ? 'text-red-600' :
                      pr.detailed_info.ci_status === 'pending' ? 'text-yellow-600' :
                      'text-gray-600'
                    }`}>
                      ({pr.detailed_info.ci_status})
                    </span>
                  </h3>
                  <div className="space-y-2">
                    {pr.detailed_info.ci_checks.map((check, idx) => (
                      <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                        <div className="flex items-center space-x-3">
                          <span className="text-lg">
                            {check.conclusion === 'success' ? '✅' :
                             check.conclusion === 'failure' ? '❌' :
                             check.status === 'in_progress' ? '⏳' :
                             check.status === 'queued' ? '⏸️' :
                             '⚪'}
                          </span>
                          <div>
                            <div className="font-medium text-sm">{check.name}</div>
                            <div className="text-xs text-gray-500">
                              {check.conclusion || check.status}
                              {check.completed_at && ` • Completed ${formatTimeAgo(check.completed_at)}`}
                            </div>
                          </div>
                        </div>
                        {check.html_url && (
                          <a 
                            href={check.html_url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:underline text-sm"
                          >
                            Details →
                          </a>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Linked Issues */}
              {pr.detailed_info.linked_issues && pr.detailed_info.linked_issues.length > 0 && (
                <div className="bg-white border border-gray-200 rounded-lg p-4">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">🔗 Linked Issues</h3>
                  <div className="space-y-2">
                    {pr.detailed_info.linked_issues.map((issue, idx) => (
                      <div key={idx} className="flex items-start justify-between p-3 bg-gray-50 rounded">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2">
                            <span className="font-medium text-blue-600">#{issue.number}</span>
                            <span className={`px-2 py-1 rounded text-xs ${
                              issue.state === 'open' ? 'bg-green-100 text-green-800' :
                              'bg-purple-100 text-purple-800'
                            }`}>
                              {issue.state}
                            </span>
                          </div>
                          <div className="text-sm text-gray-700 mt-1">{issue.title}</div>
                          {issue.labels && issue.labels.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-2">
                              {issue.labels.map((label, labelIdx) => (
                                <span key={labelIdx} className="px-2 py-0.5 bg-gray-200 text-gray-700 rounded text-xs">
                                  {label}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                        <a 
                          href={issue.url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:underline text-sm ml-4"
                        >
                          View →
                        </a>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Comments and Discussions */}
              {pr.detailed_info.comments && pr.detailed_info.comments.length > 0 && (
                <div className="bg-white border border-gray-200 rounded-lg p-4">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">
                    💬 Comments & Discussions ({pr.detailed_info.total_comments})
                  </h3>
                  <div className="max-h-96 overflow-y-auto space-y-3">
                    {pr.detailed_info.comments.slice(0, 10).map((comment, idx) => (
                      <div key={idx} className="p-3 bg-gray-50 rounded">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center space-x-2">
                            <span className="font-medium text-sm text-gray-900">@{comment.author}</span>
                            <span className={`px-2 py-0.5 rounded text-xs ${
                              comment.comment_type === 'review' ? 'bg-purple-100 text-purple-800' :
                              comment.comment_type === 'review_comment' ? 'bg-blue-100 text-blue-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {comment.comment_type}
                            </span>
                          </div>
                          <span className="text-xs text-gray-500">{formatTimeAgo(comment.created_at)}</span>
                        </div>
                        {comment.path && (
                          <div className="text-xs text-gray-500 mb-1">
                            📁 {comment.path}{comment.line ? `:${comment.line}` : ''}
                          </div>
                        )}
                        <div className="text-sm text-gray-700 whitespace-pre-wrap line-clamp-3">{comment.body}</div>
                      </div>
                    ))}
                    {pr.detailed_info.comments.length > 10 && (
                      <div className="text-center text-sm text-gray-500 py-2">
                        ... and {pr.detailed_info.comments.length - 10} more comments
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Review Summary */}
              {pr.detailed_info.review_summary && (
                <div className="bg-white border border-gray-200 rounded-lg p-4">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">👥 Review Summary</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-gray-900">{pr.detailed_info.review_summary.total_reviews}</div>
                      <div className="text-xs text-gray-600">Total Reviews</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-600">{pr.detailed_info.review_summary.approved_count}</div>
                      <div className="text-xs text-gray-600">Approved</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-red-600">{pr.detailed_info.review_summary.changes_requested_count}</div>
                      <div className="text-xs text-gray-600">Changes Requested</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-600">{pr.detailed_info.review_summary.commented_count}</div>
                      <div className="text-xs text-gray-600">Commented</div>
                    </div>
                  </div>
                  {pr.detailed_info.review_summary.reviewers.length > 0 && (
                    <div>
                      <div className="text-sm font-medium text-gray-700 mb-2">Reviewers:</div>
                      <div className="flex flex-wrap gap-2">
                        {pr.detailed_info.review_summary.reviewers.map((reviewer, idx) => (
                          <span key={idx} className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
                            @{reviewer}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Commit Info */}
              {pr.detailed_info.commit_count > 0 && (
                <div className="bg-white border border-gray-200 rounded-lg p-4">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">💻 Commit Information</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Total commits:</span>
                      <span className="font-medium">{pr.detailed_info.commit_count}</span>
                    </div>
                    {pr.detailed_info.commits_authors.length > 0 && (
                      <div>
                        <div className="text-gray-600 mb-2">Contributors:</div>
                        <div className="flex flex-wrap gap-2">
                          {pr.detailed_info.commits_authors.map((author, idx) => (
                            <span key={idx} className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">
                              @{author}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Metadata */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">📋 Additional Metadata</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Draft PR:</span>
                    <span className={`font-medium ${pr.detailed_info.draft ? 'text-yellow-600' : 'text-green-600'}`}>
                      {pr.detailed_info.draft ? 'Yes' : 'No'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Mergeable:</span>
                    <span className={`font-medium ${
                      pr.detailed_info.mergeable === true ? 'text-green-600' :
                      pr.detailed_info.mergeable === false ? 'text-red-600' :
                      'text-gray-600'
                    }`}>
                      {pr.detailed_info.mergeable === true ? 'Yes' :
                       pr.detailed_info.mergeable === false ? 'No' :
                       'Unknown'}
                    </span>
                  </div>
                  {pr.detailed_info.mergeable_state && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Mergeable state:</span>
                      <span className="font-medium">{pr.detailed_info.mergeable_state}</span>
                    </div>
                  )}
                  {pr.detailed_info.requested_reviewers.length > 0 && (
                    <div>
                      <div className="text-gray-600 mb-2">Requested reviewers:</div>
                      <div className="flex flex-wrap gap-2">
                        {pr.detailed_info.requested_reviewers.map((reviewer, idx) => (
                          <span key={idx} className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded text-xs">
                            @{reviewer}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  {pr.detailed_info.assignees.length > 0 && (
                    <div>
                      <div className="text-gray-600 mb-2">Assignees:</div>
                      <div className="flex flex-wrap gap-2">
                        {pr.detailed_info.assignees.map((assignee, idx) => (
                          <span key={idx} className="px-2 py-1 bg-purple-100 text-purple-800 rounded text-xs">
                            @{assignee}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </>
          )}

          {/* Analysis Info */}
          <div className="text-center text-sm text-gray-500 border-t border-gray-200 pt-4">
            {pr.analyzed_at ? `Analyzed at ${new Date(pr.analyzed_at).toLocaleString()}` : 'Analysis date not available'}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ExpandedPRView; 