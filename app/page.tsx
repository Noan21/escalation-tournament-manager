import Link from 'next/link';

export default function HomePage(): JSX.Element {
  return (
    <div className="app-shell">
      <div className="centered-card">
        <h1 className="card-title">Angrom Tournament Manager</h1>
        <p className="card-description">
          Manage registrations, pairings, and standings for your organization. Sign in to
          continue or create a new admin account.
        </p>
        <div className="form-grid">
          <Link href="/login" className="primary-button">
            Sign in
          </Link>
          <Link href="/register" className="primary-button">
            Create account
          </Link>
        </div>
        <div className="form-footer">
          <span>Need passwordless access?</span>
          <Link href="/magic-link">Request magic link</Link>
        </div>
      </div>
    </div>
  );
}
