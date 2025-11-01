'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { FormEvent, useState } from 'react';

import { ApiError } from '@/lib/api-client';
import { useChangePassword, useLogout, useSession } from '@/hooks/useAuth';

export default function DashboardPage(): JSX.Element {
  const router = useRouter();
  const { user, isAuthenticated, isInitializing } = useSession();
  const logoutMutation = useLogout();
  const changePasswordMutation = useChangePassword();

  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [passwordMessage, setPasswordMessage] = useState<string | null>(null);
  const [passwordError, setPasswordError] = useState<string | null>(null);

  const handleLogout = async () => {
    await logoutMutation.mutateAsync();
    router.push('/');
  };

  const handlePasswordChange = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setPasswordError(null);
    setPasswordMessage(null);

    try {
      await changePasswordMutation.mutateAsync({ current_password: currentPassword, new_password: newPassword });
      setPasswordMessage('Password updated successfully.');
      setCurrentPassword('');
      setNewPassword('');
    } catch (err) {
      if (err instanceof ApiError) {
        setPasswordError(err.message);
      } else if (err instanceof Error) {
        setPasswordError(err.message);
      } else {
        setPasswordError('Unable to update password');
      }
    }
  };

  if (isInitializing) {
    return (
      <div className="app-shell">
        <div className="centered-card">
          <div className="card-description">Loading your session…</div>
        </div>
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return (
      <div className="app-shell">
        <div className="centered-card">
          <h1 className="card-title">You&apos;re signed out</h1>
          <p className="card-description">Sign in to manage tournaments and view dashboards.</p>
          <div className="form-grid">
            <Link href="/login" className="primary-button">
              Sign in
            </Link>
            <Link href="/register" className="primary-button">
              Create account
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <div className="centered-card">
        <h1 className="card-title">Welcome, {user.username}</h1>
        <p className="card-description">
          You&apos;re signed in with {user.email}. Use the admin tools below to continue planning events.
        </p>

        <button type="button" className="primary-button" onClick={handleLogout} disabled={logoutMutation.isPending}>
          {logoutMutation.isPending ? 'Signing out…' : 'Sign out'}
        </button>

        <h2 style={{ marginTop: '32px', marginBottom: '12px', fontSize: '1.25rem' }}>Update password</h2>
        {passwordError ? <div className="error-banner">{passwordError}</div> : null}
        {passwordMessage ? <div className="success-banner">{passwordMessage}</div> : null}

        <form className="form-grid" onSubmit={handlePasswordChange} style={{ marginTop: '12px' }}>
          <label>
            Current password
            <input
              type="password"
              name="currentPassword"
              required
              value={currentPassword}
              onChange={(event) => setCurrentPassword(event.target.value)}
            />
          </label>
          <label>
            New password
            <input
              type="password"
              name="newPassword"
              minLength={12}
              required
              value={newPassword}
              onChange={(event) => setNewPassword(event.target.value)}
            />
          </label>
          <button type="submit" className="primary-button" disabled={changePasswordMutation.isPending}>
            {changePasswordMutation.isPending ? 'Updating…' : 'Update password'}
          </button>
        </form>
      </div>
    </div>
  );
}
