'use client';

import { FormEvent, useMemo, useState } from 'react';

import {
  useGenerateRound,
  useLockRound,
  useRegistrationsQuery,
  useRecomputeSeason,
  useSeasonEvents,
  useStandingsQuery,
} from '@/hooks/useTournamentAdmin';

const Section = ({ title, children }: { title: string; children: React.ReactNode }) => (
  <section style={{ marginTop: '24px' }}>
    <h2 style={{ fontSize: '1.4rem', marginBottom: '12px' }}>{title}</h2>
    {children}
  </section>
);

export default function AdminDashboard(): JSX.Element {
  const [eventId, setEventId] = useState('');
  const [stageId, setStageId] = useState('');
  const [roundId, setRoundId] = useState('');
  const [seasonId, setSeasonId] = useState('');

  const registrationsQuery = useRegistrationsQuery(eventId ? eventId : null);
  const standingsQuery = useStandingsQuery(stageId ? stageId : null);
  const seasonEventsQuery = useSeasonEvents(seasonId ? seasonId : null);

  const generateRound = useGenerateRound(stageId ? stageId : null);
  const lockRound = useLockRound(roundId ? roundId : null);
  const recomputeSeason = useRecomputeSeason(seasonId ? seasonId : null);

  const handleGenerateRound = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await generateRound.mutateAsync({});
    if (generateRound.data) {
      setRoundId(generateRound.data.id);
    }
  };

  const handleLockRound = async () => {
    await lockRound.mutateAsync();
    standingsQuery.refetch();
  };

  const handleRecomputeSeason = async () => {
    await recomputeSeason.mutateAsync();
    seasonEventsQuery.refetch();
  };

  const registrationRows = useMemo(() => {
    if (!registrationsQuery.data) return [];
    return registrationsQuery.data.map((registration) => (
      <tr key={registration.id}>
        <td>{registration.id.slice(0, 8)}</td>
        <td>{registration.subject_id.slice(0, 8)}</td>
        <td>{registration.status}</td>
        <td>{new Date(registration.registered_at).toLocaleString()}</td>
      </tr>
    ));
  }, [registrationsQuery.data]);

  const standingRows = useMemo(() => {
    if (!standingsQuery.data) return [];
    return standingsQuery.data.rows.map((row) => (
      <tr key={`${row.subject_id}-${row.rank}`}>
        <td>{row.rank}</td>
        <td>{row.subject_id.slice(0, 8)}</td>
        <td>{row.match_points}</td>
        <td>{row.wins}-{row.losses}-{row.draws}</td>
      </tr>
    ));
  }, [standingsQuery.data]);

  return (
    <div className="app-shell" style={{ padding: '32px', flexDirection: 'column', gap: '32px' }}>
      <div className="centered-card" style={{ width: 'min(960px, 95vw)' }}>
        <h1 className="card-title">Tournament Admin Console</h1>
        <p className="card-description">
          Use this lightweight dashboard to inspect registrations, generate pairings, lock rounds, and recompute
          season standings during early development.
        </p>

        <Section title="Identifiers">
          <div className="form-grid">
            <label>
              Event ID
              <input value={eventId} onChange={(event) => setEventId(event.target.value)} placeholder="UUID" />
            </label>
            <label>
              Stage ID
              <input value={stageId} onChange={(event) => setStageId(event.target.value)} placeholder="UUID" />
            </label>
            <label>
              Round ID
              <input value={roundId} onChange={(event) => setRoundId(event.target.value)} placeholder="UUID" />
            </label>
            <label>
              Season ID
              <input value={seasonId} onChange={(event) => setSeasonId(event.target.value)} placeholder="UUID" />
            </label>
          </div>
        </Section>

        <Section title="Registrations">
          <form className="form-grid" onSubmit={(event) => event.preventDefault()}>
            <button className="primary-button" onClick={() => registrationsQuery.refetch()} type="button" disabled={!eventId || registrationsQuery.isLoading}>
              {registrationsQuery.isLoading ? 'Loading…' : 'Refresh Registrations'}
            </button>
          </form>
          {registrationsQuery.error ? (
            <div className="error-banner">{(registrationsQuery.error as Error).message}</div>
          ) : null}
          {registrationRows.length ? (
            <table style={{ width: '100%', marginTop: '16px', borderSpacing: '0 6px' }}>
              <thead>
                <tr>
                  <th align="left">Registration</th>
                  <th align="left">Subject</th>
                  <th align="left">Status</th>
                  <th align="left">Registered At</th>
                </tr>
              </thead>
              <tbody>{registrationRows}</tbody>
            </table>
          ) : (
            <p className="card-description">No registrations loaded yet.</p>
          )}
        </Section>

        <Section title="Pairings & Rounds">
          <form className="form-grid" onSubmit={handleGenerateRound}>
            <button className="primary-button" type="submit" disabled={!stageId || generateRound.isPending}>
              {generateRound.isPending ? 'Generating…' : 'Generate Round'}
            </button>
            {generateRound.data ? (
              <div className="success-banner">
                Round #{generateRound.data.number} created (id {generateRound.data.id.slice(0, 8)}).
              </div>
            ) : null}
          </form>
          <button
            className="primary-button"
            style={{ marginTop: '12px' }}
            type="button"
            disabled={!roundId || lockRound.isPending}
            onClick={handleLockRound}
          >
            {lockRound.isPending ? 'Locking…' : 'Lock Round'}
          </button>
        </Section>

        <Section title="Standings">
          <button
            className="primary-button"
            type="button"
            disabled={!stageId || standingsQuery.isFetching}
            onClick={() => standingsQuery.refetch()}
          >
            {standingsQuery.isFetching ? 'Refreshing…' : 'Refresh Standings'}
          </button>
          {standingRows.length ? (
            <table style={{ width: '100%', marginTop: '16px', borderSpacing: '0 6px' }}>
              <thead>
                <tr>
                  <th align="left">Rank</th>
                  <th align="left">Subject</th>
                  <th align="left">Points</th>
                  <th align="left">Record</th>
                </tr>
              </thead>
              <tbody>{standingRows}</tbody>
            </table>
          ) : (
            <p className="card-description">Standings will appear after rounds are locked.</p>
          )}
        </Section>

        <Section title="Season Snapshot">
          <div className="form-grid">
            <button
              className="primary-button"
              type="button"
              disabled={!seasonId || recomputeSeason.isPending}
              onClick={handleRecomputeSeason}
            >
              {recomputeSeason.isPending ? 'Recomputing…' : 'Recompute Season Leaderboard'}
            </button>
          </div>
          {seasonEventsQuery.data ? (
            <ul style={{ marginTop: '12px', listStyle: 'disc', paddingLeft: '20px' }}>
              {seasonEventsQuery.data.map((eventItem) => (
                <li key={eventItem.id}>
                  {eventItem.name} — {eventItem.status} (starts {new Date(eventItem.starts_at).toLocaleDateString()})
                </li>
              ))}
            </ul>
          ) : (
            <p className="card-description">Season events will populate after providing a season id.</p>
          )}
        </Section>
      </div>
    </div>
  );
}
