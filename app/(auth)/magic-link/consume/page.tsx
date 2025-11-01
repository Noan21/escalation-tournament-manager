'use client';

import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { useEffect, useState } from 'react';

import { ApiError } from '@/lib/api-client';
import { useConsumeMagicLink } from '@/hooks/useAuth';

export default function MagicLinkConsumePage(): JSX.Element {
  const router = useRouter();
  const searchParams = useSearchParams();
  const consumeMutation = useConsumeMagicLink();

  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState<string>('Validating magic link…');

  useEffect(() => {
    const token = searchParams.get('token');
    if (!token) {
      setStatus('error');
      setMessage('Magic link token missing. Request a new link.');
      return;
    }

    (async () => {
      try {
        await consumeMutation.mutateAsync({ token });
        setStatus('success');
        setMessage('You are signed in. Redirecting to dashboard…');
        setTimeout(() => router.push('/dashboard'), 1200);
      } catch (err) {
        if (err instanceof ApiError) {
          setMessage(err.message);
        } else if (err instanceof Error) {
          setMessage(err.message);
        } else {
          setMessage('Magic link could not be consumed');
        }
        setStatus('error');
      }
    })();
  }, [consumeMutation, router, searchParams]);

  const bannerClass = status === 'error' ? 'error-banner' : 'success-banner';

  return (
    <div className="app-shell">
      <div className="centered-card">
        <h1 className="card-title">Magic link</h1>
        <div className={status === 'loading' ? 'card-description' : bannerClass}>{message}</div>
        {status === 'error' ? (
          <div className="form-footer">
            <Link href="/magic-link">Request another link</Link>
            <Link href="/login">Back to login</Link>
          </div>
        ) : null}
      </div>
    </div>
  );
}
