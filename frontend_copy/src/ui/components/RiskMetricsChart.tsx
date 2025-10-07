/**
 * Risk Metrics Chart Component
 * Displays various risk metrics in chart format
 */

import React from 'react';
import { Pie, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from 'chart.js';
import type { DashboardSummary, CompositeRiskScore } from '../../types/pr-risk';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

interface RiskDistributionChartProps {
  summary: DashboardSummary;
}

export const RiskDistributionChart: React.FC<RiskDistributionChartProps> = ({ summary }) => {
  const data = {
    labels: ['Low Risk', 'Medium Risk', 'High Risk', 'Critical Risk'],
    datasets: [
      {
        data: [
          summary.risk_distribution.low,
          summary.risk_distribution.medium,
          summary.risk_distribution.high,
          summary.risk_distribution.critical,
        ],
        backgroundColor: [
          'rgb(34, 197, 94)',   // green
          'rgb(251, 191, 36)',  // yellow
          'rgb(249, 115, 22)',  // orange
          'rgb(239, 68, 68)',   // red
        ],
        borderColor: [
          'rgb(21, 128, 61)',
          'rgb(180, 83, 9)',
          'rgb(194, 65, 12)',
          'rgb(185, 28, 28)',
        ],
        borderWidth: 1,
      },
    ],
  };

  const options = {
    responsive: true,
    plugins: {
      legend: {
        position: 'bottom' as const,
      },
      title: {
        display: true,
        text: 'PR Risk Distribution',
      },
    },
  };

  return <Pie data={data} options={options} />;
};

interface CompositeScoresChartProps {
  scores: CompositeRiskScore[];
  labels: string[];
}

export const CompositeScoresChart: React.FC<CompositeScoresChartProps> = ({ scores, labels }) => {
  const data = {
    labels: labels,
    datasets: [
      {
        label: 'Stuckness',
        data: scores.map(s => s.stuckness_score),
        backgroundColor: 'rgba(239, 68, 68, 0.5)',
        borderColor: 'rgb(239, 68, 68)',
        borderWidth: 1,
      },
      {
        label: 'Blast Radius',
        data: scores.map(s => s.blast_radius_score),
        backgroundColor: 'rgba(249, 115, 22, 0.5)',
        borderColor: 'rgb(249, 115, 22)',
        borderWidth: 1,
      },
      {
        label: 'Dynamics',
        data: scores.map(s => s.dynamics_score),
        backgroundColor: 'rgba(251, 191, 36, 0.5)',
        borderColor: 'rgb(251, 191, 36)',
        borderWidth: 1,
      },
      {
        label: 'Business Impact',
        data: scores.map(s => s.business_impact_score),
        backgroundColor: 'rgba(59, 130, 246, 0.5)',
        borderColor: 'rgb(59, 130, 246)',
        borderWidth: 1,
      },
    ],
  };

  const options = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: 'Risk Score Breakdown by Category',
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 100,
        title: {
          display: true,
          text: 'Risk Score (0-100)',
        },
      },
    },
  };

  return <Bar data={data} options={options} />;
};

interface RiskGaugeProps {
  score: number;
  title: string;
  size?: 'small' | 'medium' | 'large';
}

export const RiskGauge: React.FC<RiskGaugeProps> = ({ score, title, size = 'medium' }) => {
  const getColorClass = (score: number): string => {
    if (score >= 80) return 'text-red-600';
    if (score >= 60) return 'text-orange-600';
    if (score >= 40) return 'text-yellow-600';
    return 'text-green-600';
  };

  const getBackgroundColor = (score: number): string => {
    if (score >= 80) return 'stroke-red-500';
    if (score >= 60) return 'stroke-orange-500';
    if (score >= 40) return 'stroke-yellow-500';
    return 'stroke-green-500';
  };

  const radius = size === 'small' ? 35 : size === 'large' ? 55 : 45;
  const strokeWidth = size === 'small' ? 6 : size === 'large' ? 10 : 8;
  const circumference = 2 * Math.PI * radius;
  const strokeDasharray = circumference;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  return (
    <div className="flex flex-col items-center">
      <div className="relative">
        <svg
          className={`transform -rotate-90 ${
            size === 'small' ? 'w-20 h-20' : size === 'large' ? 'w-32 h-32' : 'w-24 h-24'
          }`}
          viewBox="0 0 120 120"
        >
          {/* Background circle */}
          <circle
            cx="60"
            cy="60"
            r={radius}
            stroke="currentColor"
            strokeWidth={strokeWidth}
            fill="transparent"
            className="text-gray-200"
          />
          {/* Progress circle */}
          <circle
            cx="60"
            cy="60"
            r={radius}
            stroke="currentColor"
            strokeWidth={strokeWidth}
            fill="transparent"
            strokeLinecap="round"
            strokeDasharray={strokeDasharray}
            strokeDashoffset={strokeDashoffset}
            className={getBackgroundColor(score)}
            style={{
              transition: 'stroke-dashoffset 0.5s ease-in-out',
            }}
          />
        </svg>
        {/* Score text overlay */}
        <div className="absolute inset-0 flex items-center justify-center">
          <span className={`${
            size === 'small' ? 'text-sm' : size === 'large' ? 'text-xl' : 'text-lg'
          } font-bold ${getColorClass(score)}`}>
            {Math.round(score)}
          </span>
        </div>
      </div>
      <div className={`mt-2 text-center ${
        size === 'small' ? 'text-xs' : 'text-sm'
      } text-gray-600 font-medium`}>
        {title}
      </div>
    </div>
  );
};

export default RiskDistributionChart;
