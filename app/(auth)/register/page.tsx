'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { FormEvent, useState } from 'react';

import { ApiError } from '@/lib/api-client';
import { useLogin, useRegister } from '@/hooks/useAuth';

export default function RegisterPage(): JSX.Element {
  const router = useRouter();
  const registerMutation = useRegister();
  const loginMutation = useLogin();

  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);

    try {
      const normalizedUsername = username.trim();
      const normalizedEmail = email.trim().toLowerCase();

      await registerMutation.mutateAsync({ username: normalizedUsername, email: normalizedEmail, password });
      await loginMutation.mutateAsync({ identifier: normalizedUsername, password });
      router.push('/dashboard');
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Registration failed');
      }
    }
  };

  const isSubmitting = registerMutation.isPending || loginMutation.isPending;

  return (
    <div className="app-shell">
      <form className="centered-card" onSubmit={handleSubmit}>
        <h1 className="card-title">Create your account</h1>
        <p className="card-description">Register as an admin or staff member to manage events.</p>

        {error ? <div className="error-banner">{error}</div> : null}

        <div className="form-grid">
          <label>
            Username
            <input
              type="text"
              name="username"
              autoComplete="username"
              required
              minLength={3}
              maxLength={50}
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              placeholder="angrom-admin"
            />
          </label>
          <label>
            Email address
            <input
              type="email"
              name="email"
              autoComplete="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="admin@example.com"
            />
          </label>
          <label>
            Password
            <input
              type="password"
              name="password"
              autoComplete="new-password"
              required
              minLength={12}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Minimum 12 characters"
            />
          </label>
          <button type="submit" className="primary-button" disabled={isSubmitting}>
            {isSubmitting ? 'Creating account…' : 'Create account'}
          </button>
        </div>

        <div className="form-footer">
          <span>Already have access?</span>
          <Link href="/login">Sign in</Link>
        </div>
      </form>
    </div>
  );
}
