'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { FormEvent, useState } from 'react';

import { ApiError } from '@/lib/api-client';
import { useLogin } from '@/hooks/useAuth';

export default function LoginPage(): JSX.Element {
  const router = useRouter();
  const loginMutation = useLogin();

  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);

    try {
      const normalizedIdentifier = identifier.trim();
      await loginMutation.mutateAsync({ identifier: normalizedIdentifier, password });
      router.push('/dashboard');
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Login failed');
      }
    }
  };

  return (
    <div className="app-shell">
      <form className="centered-card" onSubmit={handleSubmit}>
        <h1 className="card-title">Welcome back</h1>
        <p className="card-description">Sign in with your username or email address.</p>

        {error ? <div className="error-banner">{error}</div> : null}

        <div className="form-grid">
          <label>
            Username or email
            <input
              type="text"
              name="identifier"
              autoComplete="username"
              required
              value={identifier}
              onChange={(event) => setIdentifier(event.target.value)}
              placeholder="username or email"
            />
          </label>
          <label>
            Password
            <input
              type="password"
              name="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </label>
          <button type="submit" className="primary-button" disabled={loginMutation.isPending}>
            {loginMutation.isPending ? 'Signing in…' : 'Sign in'}
          </button>
        </div>

        <div className="form-footer">
          <Link href="/magic-link">Use magic link</Link>
          <Link href="/register">Create account</Link>
        </div>
      </form>
    </div>
  );
}
