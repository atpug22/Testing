'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import ProtectedRoute from '../../components/ProtectedRoute';
import { useAuth } from '../../components/AuthProvider';

interface Invitation {
  id: number;
  uuid: string;
  email: string;
  organization_id: number;
  organization_name: string;
  role: string;
  status: string;
  expires_at: string;
  invited_by_username: string | null;
}

export default function OnboardingPage() {
  const router = useRouter();
  const { user } = useAuth();
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [loading, setLoading] = useState(true);
  const [organizations, setOrganizations] = useState<any[]>([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [orgName, setOrgName] = useState('');
  const [orgDescription, setOrgDescription] = useState('');
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    checkStatus();
  }, []);

  const checkStatus = async () => {
    setLoading(true);
    try {
      // Check if user already has organizations
      const orgsResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/v1'}/organizations/`, {
        credentials: 'include',
      });
      
      if (orgsResponse.ok) {
        const orgs = await orgsResponse.json();
        if (orgs.length > 0) {
          // User already has an organization, redirect to dashboard
          router.push('/dashboard');
          return;
        }
        setOrganizations(orgs);
      }

      // Check for pending invitations
      const invitationsResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/v1'}/invitations/me`, {
        credentials: 'include',
      });
      
      if (invitationsResponse.ok) {
        const invites = await invitationsResponse.json();
        setInvitations(invites);
      }
    } catch (error) {
      console.error('Failed to check status:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAcceptInvitation = async (invitationId: number) => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/v1'}/invitations/${invitationId}/accept`,
        {
          method: 'POST',
          credentials: 'include',
        }
      );

      if (response.ok) {
        alert('Invitation accepted! Redirecting to dashboard...');
        router.push('/dashboard');
      } else {
        const error = await response.json();
        alert(error.detail || 'Failed to accept invitation');
      }
    } catch (error) {
      alert('Failed to accept invitation');
    }
  };

  const handleDeclineInvitation = async (invitationId: number) => {
    if (!confirm('Are you sure you want to decline this invitation?')) {
      return;
    }

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/v1'}/invitations/${invitationId}/decline`,
        {
          method: 'POST',
          credentials: 'include',
        }
      );

      if (response.ok) {
        // Remove from list
        setInvitations(invitations.filter(inv => inv.id !== invitationId));
      } else {
        const error = await response.json();
        alert(error.detail || 'Failed to decline invitation');
      }
    } catch (error) {
      alert('Failed to decline invitation');
    }
  };

  const handleCreateOrganization = async () => {
    if (!orgName.trim()) {
      alert('Please enter an organization name');
      return;
    }

    setCreating(true);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/v1'}/organizations/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          name: orgName,
          description: orgDescription || null,
        }),
      });

      if (response.ok) {
        alert('Organization created successfully! Redirecting to dashboard...');
        router.push('/dashboard');
      } else {
        const error = await response.json();
        alert(error.detail || 'Failed to create organization');
      }
    } catch (error) {
      alert('Failed to create organization');
    } finally {
      setCreating(false);
    }
  };

  if (loading) {
    return (
      <ProtectedRoute>
        <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">Loading...</p>
          </div>
        </div>
      </ProtectedRoute>
    );
  }

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="max-w-4xl mx-auto px-4 py-16">
          <div className="text-center mb-12">
            <h1 className="text-4xl font-bold text-gray-900 mb-4">
              Welcome to LogPose! 🎉
            </h1>
            <p className="text-lg text-gray-600">
              Let's get you set up with an organization
            </p>
          </div>

          {invitations.length > 0 && (
            <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">
                You've Been Invited! 📨
              </h2>
              <p className="text-gray-600 mb-6">
                You have {invitations.length} pending invitation{invitations.length > 1 ? 's' : ''}
              </p>

              <div className="space-y-4">
                {invitations.map((invitation) => (
                  <div
                    key={invitation.id}
                    className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="text-lg font-medium text-gray-900">
                          {invitation.organization_name}
                        </h3>
                        <div className="mt-2 space-y-1">
                          <p className="text-sm text-gray-600">
                            Role: <span className="font-medium capitalize">{invitation.role}</span>
                          </p>
                          {invitation.invited_by_username && (
                            <p className="text-sm text-gray-600">
                              Invited by: <span className="font-medium">{invitation.invited_by_username}</span>
                            </p>
                          )}
                          <p className="text-sm text-gray-500">
                            Expires: {new Date(invitation.expires_at).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                      <div className="flex gap-2 ml-4">
                        <button
                          onClick={() => handleAcceptInvitation(invitation.id)}
                          className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                        >
                          Accept
                        </button>
                        <button
                          onClick={() => handleDeclineInvitation(invitation.id)}
                          className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
                        >
                          Decline
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-6 pt-6 border-t border-gray-200">
                <p className="text-center text-gray-600 mb-4">
                  Or create your own organization
                </p>
                <button
                  onClick={() => setShowCreateForm(true)}
                  className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Create New Organization
                </button>
              </div>
            </div>
          )}

          {invitations.length === 0 && !showCreateForm && (
            <div className="bg-white rounded-lg shadow-lg p-8 text-center">
              <div className="mb-6">
                <svg className="w-16 h-16 text-blue-600 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
              </div>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">
                No Invitations Yet
              </h2>
              <p className="text-gray-600 mb-8">
                You haven't been invited to any organizations yet. You can create your own organization to get started!
              </p>
              <button
                onClick={() => setShowCreateForm(true)}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-lg font-medium"
              >
                Create Your Organization
              </button>
            </div>
          )}

          {showCreateForm && (
            <div className="bg-white rounded-lg shadow-lg p-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-6">
                Create Your Organization
              </h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Organization Name *
                  </label>
                  <input
                    type="text"
                    value={orgName}
                    onChange={(e) => setOrgName(e.target.value)}
                    placeholder="e.g., Acme Inc."
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Description (optional)
                  </label>
                  <textarea
                    value={orgDescription}
                    onChange={(e) => setOrgDescription(e.target.value)}
                    placeholder="Brief description of your organization"
                    rows={3}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <div className="flex gap-3">
                  <button
                    onClick={handleCreateOrganization}
                    disabled={creating}
                    className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
                  >
                    {creating ? 'Creating...' : 'Create Organization'}
                  </button>
                  {invitations.length > 0 && (
                    <button
                      onClick={() => setShowCreateForm(false)}
                      className="px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
                    >
                      Cancel
                    </button>
                  )}
                </div>
              </div>
              <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-sm text-blue-800">
                  <strong>Note:</strong> As the creator, you'll become an admin and can invite team members to join your organization.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </ProtectedRoute>
  );
}

