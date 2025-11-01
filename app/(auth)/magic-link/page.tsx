'use client';

import Link from 'next/link';
import { FormEvent, useState } from 'react';

import { ApiError } from '@/lib/api-client';
import { useRequestMagicLink } from '@/hooks/useAuth';

export default function MagicLinkRequestPage(): JSX.Element {
  const requestMutation = useRequestMagicLink();
  const [email, setEmail] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setSuccess(null);

    try {
      await requestMutation.mutateAsync({ email });
      setSuccess('Magic link sent. Check your email within the next 15 minutes.');
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Unable to send magic link');
      }
    }
  };

  return (
    <div className="app-shell">
      <form className="centered-card" onSubmit={handleSubmit}>
        <h1 className="card-title">Email me a magic link</h1>
        <p className="card-description">We&apos;ll send a single-use link that signs you in instantly.</p>

        {error ? <div className="error-banner">{error}</div> : null}
        {success ? <div className="success-banner">{success}</div> : null}

        <div className="form-grid">
          <label>
            Email address
            <input
              type="email"
              name="email"
              autoComplete="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@example.com"
            />
          </label>
          <button type="submit" className="primary-button" disabled={requestMutation.isPending}>
            {requestMutation.isPending ? 'Sending…' : 'Send magic link'}
          </button>
        </div>

        <div className="form-footer">
          <Link href="/login">Back to sign in</Link>
          <Link href="/register">Need an account?</Link>
        </div>
      </form>
    </div>
  );
}
