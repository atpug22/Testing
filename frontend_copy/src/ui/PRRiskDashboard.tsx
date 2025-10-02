/**
 * PR Risk Dashboard
 * Main dashboard for viewing PR risk metrics
 */

import React, { useState, useEffect } from 'react';
import { Card } from './components/Card';
import { Button } from './components/Button';
import { Loader } from './components/Loader';
import { Alert } from './components/Alert';
import { EmptyState } from './components/EmptyState';
import { PRRiskTable } from './components/PRRiskTable';
import { ExpandedPRView } from './components/ExpandedPRView';
import { RiskDistributionChart, RiskGauge } from './components/RiskMetricsChart';
import prRiskAPI from '../lib/pr-risk-api';
import type { 
  DashboardSummary, 
  PRListItem, 
  PRRiskAnalysisRequest,
  PRRiskAnalysis,
  RiskLevel 
} from '../types/pr-risk';

interface PRRiskDashboardProps {
  owner: string;
  repo: string;
}

export const PRRiskDashboard: React.FC<PRRiskDashboardProps> = ({ owner, repo }) => {
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [prs, setPrs] = useState<PRListItem[]>([]);
  const [selectedRiskLevel, setSelectedRiskLevel] = useState<'all' | RiskLevel>('all');
  const [error, setError] = useState<string | null>(null);
  const [selectedPR, setSelectedPR] = useState<PRRiskAnalysis | null>(null);
  const [loadingPRDetails, setLoadingPRDetails] = useState(false);

  const loadSummary = async () => {
    try {
      setError(null);
      setLoading(true);
      const summaryData = await prRiskAPI.getRepositorySummary(owner, repo);
      setSummary(summaryData);
    } catch (err) {
      console.error('Error loading summary:', err);
      setError(err instanceof Error ? err.message : 'Failed to load summary');
    } finally {
      setLoading(false);
    }
  };

  const loadPRs = async (riskLevel?: RiskLevel | 'all') => {
    try {
      setError(null);
      const prData = await prRiskAPI.getRepositoryPRs(
        owner, 
        repo, 
        riskLevel === 'all' ? undefined : riskLevel as RiskLevel,
        100
      );
      setPrs(prData);
    } catch (err) {
      console.error('Error loading PRs:', err);
      setError(err instanceof Error ? err.message : 'Failed to load PRs');
    }
  };

  const analyzeRepository = async (forceRefresh = false) => {
    try {
      setError(null);
      setAnalyzing(true);

      const request: PRRiskAnalysisRequest = {
        owner,
        repo,
        force_refresh: forceRefresh,
        include_closed_prs: false,
        max_prs: 50,
      };

      const response = await prRiskAPI.analyzeRepository(request);
      
      if (!response.success) {
        throw new Error(response.error_message || 'Analysis failed');
      }

      // Reload data after analysis
      await Promise.all([loadSummary(), loadPRs()]);
      
    } catch (err) {
      console.error('Error analyzing repository:', err);
      setError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setAnalyzing(false);
    }
  };

  const handlePRClick = async (pr: PRListItem) => {
    try {
      setLoadingPRDetails(true);
      console.log('Fetching PR details for:', pr.pr_number);
      const prDetails = await prRiskAPI.getPRDetails(owner, repo, pr.pr_number);
      console.log('Received PR details:', prDetails);
      setSelectedPR(prDetails);
    } catch (err) {
      console.error('Error loading PR details:', err);
      setError(err instanceof Error ? err.message : 'Failed to load PR details');
    } finally {
      setLoadingPRDetails(false);
    }
  };

  const closeExpandedView = () => {
    setSelectedPR(null);
  };

  useEffect(() => {
    loadSummary();
    loadPRs();
  }, [owner, repo]);

  useEffect(() => {
    if (selectedRiskLevel && selectedRiskLevel !== 'all') {
      loadPRs(selectedRiskLevel);
    } else if (selectedRiskLevel === 'all') {
      loadPRs();
    }
  }, [selectedRiskLevel]);

  const getRiskLevelCounts = () => {
    if (!summary) return { all: 0, low: 0, medium: 0, high: 0, critical: 0 };
    
    return {
      all: summary.total_prs,
      low: summary.risk_distribution.low,
      medium: summary.risk_distribution.medium,
      high: summary.risk_distribution.high,
      critical: summary.risk_distribution.critical,
    };
  };

  const riskCounts = getRiskLevelCounts();

  if (loading && !summary) {
    return (
      <div className="p-6">
        <Loader />
        <p className="mt-4 text-center text-gray-600">Loading PR risk data...</p>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">PR Risk Dashboard</h1>
          <p className="text-gray-600">{owner}/{repo}</p>
        </div>
        <div className="flex space-x-2">
                  <Button
          onClick={() => analyzeRepository(false)}
          disabled={analyzing}
          variant="secondary"
        >
          {analyzing ? 'Analyzing...' : 'Refresh Analysis'}
        </Button>
          <Button
            onClick={() => analyzeRepository(true)}
            disabled={analyzing}
          >
            {analyzing ? 'Analyzing...' : 'Force Refresh'}
          </Button>
        </div>
      </div>

      {error && (
        <Alert variant="error" message={error} />
      )}

      {!summary && !loading && (
        <EmptyState
          title="No analysis data found"
          message="Click 'Refresh Analysis' to analyze PR risks for this repository."
          cta={
            <Button onClick={() => analyzeRepository(false)}>
              Start Analysis
            </Button>
          }
        />
      )}

      {summary && (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <div className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Total PRs</p>
                    <p className="text-2xl font-bold text-gray-900">{summary.total_prs}</p>
                  </div>
                  <div className="text-3xl">📊</div>
                </div>
              </div>
            </Card>

            <Card>
              <div className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">High Risk</p>
                    <p className="text-2xl font-bold text-orange-600">{summary.high_risk_count}</p>
                  </div>
                  <div className="text-3xl">⚠️</div>
                </div>
              </div>
            </Card>

            <Card>
              <div className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Critical Risk</p>
                    <p className="text-2xl font-bold text-red-600">{summary.critical_risk_count}</p>
                  </div>
                  <div className="text-3xl">🚨</div>
                </div>
              </div>
            </Card>

            <Card>
              <div className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Avg Risk Score</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {summary.avg_risk_score.toFixed(1)}
                    </p>
                  </div>
                  <div className="text-3xl">📈</div>
                </div>
              </div>
            </Card>
          </div>

          {/* Risk Gauges */}
          <Card>
            <div className="p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Risk Metrics Overview</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <RiskGauge
                  score={summary.avg_risk_score}
                  title="Average Risk Score"
                  size="large"
                />
                <RiskGauge
                  score={summary.team_velocity_impact}
                  title="Team Velocity Impact"
                  size="large"
                />
                <div className="flex justify-center">
                  <RiskDistributionChart summary={summary} />
                </div>
              </div>
            </div>
          </Card>

          {/* Risk Level Filter */}
          <div className="flex space-x-2">
            {(['all', 'critical', 'high', 'medium', 'low'] as const).map((level) => (
              <Button
                key={level}
                variant={selectedRiskLevel === level ? 'primary' : 'secondary'}
                onClick={() => setSelectedRiskLevel(level)}
              >
                {level === 'all' ? 'All' : level.charAt(0).toUpperCase() + level.slice(1)} 
                ({riskCounts[level]})
              </Button>
            ))}
          </div>

          {/* Top Risk PRs */}
          {summary.top_risk_prs.length > 0 && (
            <Card>
              <div className="p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">
                  Top Risk PRs
                </h2>
                <PRRiskTable
                  prs={summary.top_risk_prs}
                  onPRClick={handlePRClick}
                />
              </div>
            </Card>
          )}

          {/* All PRs Table */}
          <Card>
            <div className="p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                All PRs {selectedRiskLevel !== 'all' && `(${selectedRiskLevel} risk)`}
              </h2>
              {prs.length === 0 ? (
                <EmptyState
                  title="No PRs found"
                  message={`No PRs found ${selectedRiskLevel !== 'all' ? `with ${selectedRiskLevel} risk level` : ''}.`}
                />
              ) : (
                <PRRiskTable
                  prs={prs}
                  onPRClick={handlePRClick}
                />
              )}
            </div>
          </Card>
        </>
      )}

      {/* Expanded PR View Modal */}
      {selectedPR && (
        <ExpandedPRView
          pr={selectedPR}
          onClose={closeExpandedView}
        />
      )}

      {/* Loading Overlay for PR Details */}
      {loadingPRDetails && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-8">
            <Loader />
            <p className="mt-4 text-center text-gray-600">Loading PR details...</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default PRRiskDashboard;