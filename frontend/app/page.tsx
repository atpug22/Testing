'use client';

import Link from "next/link";
import { useAuth } from "../components/AuthProvider";
import ProtectedRoute from "../components/ProtectedRoute";
import RepositoryPicker from "../components/RepositoryPicker";
import PublicRepoFetcher from "../components/PublicRepoFetcher";
import LoginForm from "../components/LoginForm";
import { useState } from "react";

export default function Home() {
  const { user, isAuthenticated, login } = useAuth();
  const [selectedRepo, setSelectedRepo] = useState<{owner: string, repo: string} | null>(null);
  const [showLoginForm, setShowLoginForm] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleRepositorySelect = (owner: string, repo: string) => {
    setSelectedRepo({ owner, repo });
  };

  const handleFetchData = (owner: string, repo: string) => {
    // Data has been fetched, could redirect to team member page or show success
    console.log(`Data fetched for ${owner}/${repo}`);
  };

  const handleEmailLogin = async (email: string, password: string) => {
    setLoading(true);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/v1'}/auth/email/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ email, password }),
      });
      
      if (response.ok) {
        // Login successful, refresh the page to update auth state
        window.location.reload();
      } else {
        const error = await response.json();
        alert(error.detail || 'Login failed');
      }
    } catch (error) {
      alert('Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleEmailRegister = async (email: string, password: string, username: string, name: string) => {
    setLoading(true);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/v1'}/auth/email/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ email, password, username, name }),
      });
      
      if (response.ok) {
        // Registration successful, refresh the page to update auth state
        window.location.reload();
      } else {
        const error = await response.json();
        alert(error.detail || 'Registration failed');
      }
    } catch (error) {
      alert('Registration failed');
    } finally {
      setLoading(false);
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="max-w-4xl mx-auto px-4 py-16">
          <div className="text-center mb-12">
            <h1 className="text-5xl font-bold text-gray-900 mb-4">
              LogPose
            </h1>
            <p className="text-xl text-gray-600 mb-8">
              Proactive Intelligence for Engineering Managers
            </p>
            <p className="text-lg text-gray-500 max-w-2xl mx-auto">
              Action over Alerts. Get real-time insights into your team's productivity, 
              identify bottlenecks, and make data-driven decisions.
            </p>
          </div>

          {showLoginForm ? (
            <LoginForm
              onLogin={handleEmailLogin}
              onRegister={handleEmailRegister}
              loading={loading}
            />
          ) : (
            <div className="space-y-6">
              <div className="bg-white rounded-2xl shadow-xl p-8 text-center">
                <h2 className="text-2xl font-semibold text-gray-900 mb-6">
                  Get Started
                </h2>
                <p className="text-gray-600 mb-8">
                  Choose how you'd like to sign in to LogPose
                </p>
                
                <div className="space-y-4">
                  <button
                    onClick={() => setShowLoginForm(true)}
                    className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207" />
                    </svg>
                    Sign in with Email
                  </button>

                  <button
                    onClick={login}
                    className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors"
                  >
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 0C4.477 0 0 4.484 0 10.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0110 4.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.203 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.942.359.31.678.921.678 1.856 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0020 10.017C20 4.484 15.522 0 10 0z" clipRule="evenodd" />
                    </svg>
                    Continue with GitHub
                  </button>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Or try the demo
                </h3>
                <div className="grid md:grid-cols-3 gap-4">
                  <Link
                    href="/member/5"
                    className="p-4 bg-gradient-to-br from-orange-50 to-red-50 rounded-lg border border-orange-200 hover:border-orange-300 hover:shadow-md transition-all"
                  >
                    <div className="text-center">
                      <div className="w-12 h-12 bg-gradient-to-br from-orange-500 to-red-600 rounded-full mx-auto mb-2 flex items-center justify-center text-white text-lg font-bold">
                        B
                      </div>
                      <h4 className="font-medium text-gray-900">Bob Engineer</h4>
                      <p className="text-sm text-orange-600">Overloaded 🟠</p>
                    </div>
                  </Link>
                  <Link
                    href="/member/6"
                    className="p-4 bg-gradient-to-br from-red-50 to-pink-50 rounded-lg border border-red-200 hover:border-red-300 hover:shadow-md transition-all"
                  >
                    <div className="text-center">
                      <div className="w-12 h-12 bg-gradient-to-br from-red-500 to-pink-600 rounded-full mx-auto mb-2 flex items-center justify-center text-white text-lg font-bold">
                        C
                      </div>
                      <h4 className="font-medium text-gray-900">Carol Engineer</h4>
                      <p className="text-sm text-red-600">Firefighting 🔥</p>
                    </div>
                  </Link>
                  <Link
                    href="/member/4"
                    className="p-4 bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg border border-green-200 hover:border-green-300 hover:shadow-md transition-all"
                  >
                    <div className="text-center">
                      <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-emerald-600 rounded-full mx-auto mb-2 flex items-center justify-center text-white text-lg font-bold">
                        A
                      </div>
                      <h4 className="font-medium text-gray-900">Alice Manager</h4>
                      <p className="text-sm text-green-600">Balanced 🟢</p>
                    </div>
                  </Link>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="max-w-6xl mx-auto px-4 py-8">
          <div className="mb-8">
            <h1 className="text-4xl font-bold text-gray-900 mb-2">
              Welcome back, {user?.login}!
            </h1>
            <p className="text-lg text-gray-600">
              Select a repository to analyze your team's productivity
            </p>
          </div>

          <div className="space-y-6">
            <RepositoryPicker
              onRepositorySelect={handleRepositorySelect}
              onFetchData={handleFetchData}
            />
            
            <PublicRepoFetcher
              onDataFetched={handleFetchData}
            />
          </div>

          <div className="mt-8 bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Team Members
            </h3>
            <div className="grid md:grid-cols-4 gap-4">
              <Link
                href="/member/20"
                className="p-4 bg-gradient-to-br from-white to-gray-50 rounded-lg border border-gray-200 hover:border-blue-300 hover:shadow-md transition-all"
              >
                <div className="text-center">
                  <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full mx-auto mb-2 flex items-center justify-center text-white text-lg font-bold">
                    S
                  </div>
                  <h4 className="font-medium text-gray-900">Sandy-1711</h4>
                  <p className="text-sm text-blue-600">Balanced 🟢</p>
                </div>
              </Link>
              <Link
                href="/member/21"
                className="p-4 bg-gradient-to-br from-white to-gray-50 rounded-lg border border-gray-200 hover:border-blue-300 hover:shadow-md transition-all"
              >
                <div className="text-center">
                  <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-600 rounded-full mx-auto mb-2 flex items-center justify-center text-white text-lg font-bold">
                    G
                  </div>
                  <h4 className="font-medium text-gray-900">guillaumejacquart</h4>
                  <p className="text-sm text-purple-600">Balanced 🟢</p>
                </div>
              </Link>
              <Link
                href="/member/22"
                className="p-4 bg-gradient-to-br from-white to-gray-50 rounded-lg border border-gray-200 hover:border-blue-300 hover:shadow-md transition-all"
              >
                <div className="text-center">
                  <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-emerald-600 rounded-full mx-auto mb-2 flex items-center justify-center text-white text-lg font-bold">
                    Y
                  </div>
                  <h4 className="font-medium text-gray-900">yehorkardash</h4>
                  <p className="text-sm text-green-600">Balanced 🟢</p>
                </div>
              </Link>
              <Link
                href="/member/13"
                className="p-4 bg-gradient-to-br from-white to-gray-50 rounded-lg border border-gray-200 hover:border-blue-300 hover:shadow-md transition-all"
              >
                <div className="text-center">
                  <div className="w-12 h-12 bg-gradient-to-br from-orange-500 to-red-600 rounded-full mx-auto mb-2 flex items-center justify-center text-white text-lg font-bold">
                    A
                  </div>
                  <h4 className="font-medium text-gray-900">Alice Manager</h4>
                  <p className="text-sm text-orange-600">Balanced 🟢</p>
                </div>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}
