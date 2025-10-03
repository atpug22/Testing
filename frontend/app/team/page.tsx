'use client';

import { useState, useEffect } from 'react';
import DashboardLayout from '../../components/DashboardLayout';
import ProtectedRoute from '../../components/ProtectedRoute';

interface OrganizationMember {
  id: number;
  username: string;
  email: string;
  role: string;
}

export default function TeamPage() {
  const [organization, setOrganization] = useState<any>(null);
  const [members, setMembers] = useState<OrganizationMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('member');
  const [showInviteForm, setShowInviteForm] = useState(false);

  useEffect(() => {
    fetchOrganization();
  }, []);

  const fetchOrganization = async () => {
    setLoading(true);
    try {
      // Get organizations
      const orgsResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/v1'}/organizations/`, {
        credentials: 'include',
      });
      
      if (orgsResponse.ok) {
        const orgs = await orgsResponse.json();
        if (orgs.length > 0) {
          const orgId = orgs[0].id;
          
          // Get organization details with members
          const orgResponse = await fetch(
            `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/v1'}/organizations/${orgId}`,
            { credentials: 'include' }
          );
          
          if (orgResponse.ok) {
            const orgData = await orgResponse.json();
            setOrganization(orgData);
            setMembers(orgData.members || []);
          }
        }
      }
    } catch (error) {
      console.error('Failed to fetch organization:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleInvite = async () => {
    if (!inviteEmail.trim()) {
      alert('Please enter an email address');
      return;
    }

    if (!organization) {
      return;
    }

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/v1'}/organizations/${organization.id}/invite`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({
            email: inviteEmail,
            role: inviteRole,
          }),
        }
      );

      if (response.ok) {
        alert(`Invitation sent to ${inviteEmail}!`);
        setShowInviteForm(false);
        setInviteEmail('');
      } else {
        const error = await response.json();
        alert(error.detail || 'Failed to send invitation');
      }
    } catch (error) {
      alert('Failed to send invitation');
    }
  };

  if (loading) {
    return (
      <ProtectedRoute>
        <DashboardLayout>
          <div className="flex items-center justify-center h-screen">
            <div className="text-center">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
              <p className="mt-4 text-gray-600">Loading team...</p>
            </div>
          </div>
        </DashboardLayout>
      </ProtectedRoute>
    );
  }

  return (
    <ProtectedRoute>
      <DashboardLayout>
        <div className="p-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Team</h1>
            <p className="text-gray-600">
              Manage your organization members and roles
            </p>
          </div>

          {organization ? (
            <div className="space-y-6">
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900">{organization.name}</h2>
                    {organization.description && (
                      <p className="text-sm text-gray-500 mt-1">{organization.description}</p>
                    )}
                  </div>
                  <button
                    onClick={() => setShowInviteForm(!showInviteForm)}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    Invite Member
                  </button>
                </div>

                {showInviteForm && (
                  <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                    <h3 className="text-lg font-medium text-gray-900 mb-4">Invite New Member</h3>
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Email Address
                        </label>
                        <input
                          type="email"
                          value={inviteEmail}
                          onChange={(e) => setInviteEmail(e.target.value)}
                          placeholder="member@example.com"
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Role
                        </label>
                        <select
                          value={inviteRole}
                          onChange={(e) => setInviteRole(e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        >
                          <option value="member">Member</option>
                          <option value="admin">Admin</option>
                        </select>
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={handleInvite}
                          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                        >
                          Send Invite
                        </button>
                        <button
                          onClick={() => setShowInviteForm(false)}
                          className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">
                    Members ({members.length})
                  </h3>
                  <div className="space-y-2">
                    {members.map((member) => (
                      <div
                        key={member.id}
                        className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center text-white font-bold">
                            {member.username[0].toUpperCase()}
                          </div>
                          <div>
                            <p className="font-medium text-gray-900">{member.username}</p>
                            <p className="text-sm text-gray-500">{member.email}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                            member.role === 'admin'
                              ? 'bg-purple-100 text-purple-700'
                              : 'bg-gray-200 text-gray-700'
                          }`}>
                            {member.role.charAt(0).toUpperCase() + member.role.slice(1)}
                          </span>
                          {member.id === organization.owner_id && (
                            <span className="px-3 py-1 bg-yellow-100 text-yellow-700 rounded-full text-sm font-medium">
                              Owner
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
              <div className="flex items-start gap-3">
                <svg className="w-6 h-6 text-yellow-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <div>
                  <h3 className="text-lg font-medium text-yellow-900 mb-1">
                    No Organization Found
                  </h3>
                  <p className="text-yellow-700">
                    You need to create or join an organization first.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  );
}

