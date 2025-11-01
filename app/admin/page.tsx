'use client';

import { FormEvent, useMemo, useState } from 'react';

import {
  useDispatchNotification,
  useGenerateRound,
  useLockRound,
  useNotificationPreferences,
  useRegistrationsQuery,
  useRecomputeSeason,
  useRunMaintenanceArchive,
  useRunMaintenanceCleanup,
  useRunMaintenanceMigrations,
  useSeasonEvents,
  useStandingsQuery,
  useUpsertNotificationPreference,
} from '@/hooks/useTournamentAdmin';
import type { NotificationTrigger } from '@/types/tournament';

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
  const [organizationId, setOrganizationId] = useState('');
  const [notificationSubjectType, setNotificationSubjectType] = useState<'participant' | 'team' | 'admin'>('participant');
  const [notificationSubjectId, setNotificationSubjectId] = useState('');
  const [channelAddress, setChannelAddress] = useState('');
  const [selectedTriggers, setSelectedTriggers] = useState<NotificationTrigger[]>(['round_pairings']);
  const [dispatchTrigger, setDispatchTrigger] = useState<NotificationTrigger>('round_pairings');
  const [dispatchSubject, setDispatchSubject] = useState('');
  const [dispatchBody, setDispatchBody] = useState('');
  const [dispatchStageId, setDispatchStageId] = useState('');
  const [dispatchRoundId, setDispatchRoundId] = useState('');
  const [dispatchSeasonId, setDispatchSeasonId] = useState('');
  const [dispatchRecipientIds, setDispatchRecipientIds] = useState('');
  const [cleanupDryRun, setCleanupDryRun] = useState(true);
  const [selectedCleanupTargets, setSelectedCleanupTargets] = useState<string[]>(['stale_registrations', 'notifications']);
  const [archivePolicyIds, setArchivePolicyIds] = useState('');
  const [archiveDryRun, setArchiveDryRun] = useState(false);
  const [migrationPolicyIds, setMigrationPolicyIds] = useState('');
  const [migrationDryRun, setMigrationDryRun] = useState(false);

  const registrationsQuery = useRegistrationsQuery(eventId ? eventId : null);
  const standingsQuery = useStandingsQuery(stageId ? stageId : null);
  const seasonEventsQuery = useSeasonEvents(seasonId ? seasonId : null);
  const notificationPrefsQuery = useNotificationPreferences({ organizationId: organizationId || null });

  const generateRound = useGenerateRound(stageId ? stageId : null);
  const lockRound = useLockRound(roundId ? roundId : null);
  const recomputeSeason = useRecomputeSeason(seasonId ? seasonId : null);
  const upsertPreference = useUpsertNotificationPreference();
  const dispatchNotification = useDispatchNotification();
  const runCleanup = useRunMaintenanceCleanup();
  const runArchive = useRunMaintenanceArchive();
  const runMigrations = useRunMaintenanceMigrations();

  const triggerOptions: NotificationTrigger[] = [
    'registration_confirmed',
    'round_pairings',
    'round_locked',
    'standings_published',
    'season_leaderboard',
  ];

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

  const toggleTrigger = (trigger: NotificationTrigger) => {
    setSelectedTriggers((current) =>
      current.includes(trigger)
        ? current.filter((item) => item !== trigger)
        : [...current, trigger]
    );
  };

  const toggleCleanupTarget = (target: string) => {
    setSelectedCleanupTargets((current) =>
      current.includes(target)
        ? current.filter((item) => item !== target)
        : [...current, target]
    );
  };

  const handlePreferenceSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!organizationId || !notificationSubjectId || !channelAddress || selectedTriggers.length === 0) {
      return;
    }
    await upsertPreference.mutateAsync({
      organization_id: organizationId,
      subject_type: notificationSubjectType,
      subject_id: notificationSubjectId,
      triggers: selectedTriggers,
      channels: [
        {
          channel: 'email',
          address: channelAddress,
          enabled: true,
          rate_limit_per_hour: null,
        },
      ],
    });
    notificationPrefsQuery.refetch();
  };

  const handleDispatch = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await dispatchNotification.mutateAsync({
      trigger: dispatchTrigger,
      organization_id: organizationId || undefined,
      stage_id: dispatchStageId || undefined,
      round_id: dispatchRoundId || undefined,
      season_id: dispatchSeasonId || undefined,
      subject: dispatchSubject || undefined,
      body_text: dispatchBody || undefined,
      recipient_subject_ids: dispatchRecipientIds
        ? dispatchRecipientIds.split(',').map((value) => value.trim())
        : undefined,
      context: {},
    });
  };

  const handleCleanup = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await runCleanup.mutateAsync({
      targets: selectedCleanupTargets,
      dry_run: cleanupDryRun,
    });
  };

  const handleArchive = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const policyIds = archivePolicyIds
      .split(',')
      .map((value) => value.trim())
      .filter(Boolean);
    await runArchive.mutateAsync({
      policy_ids: policyIds.length ? policyIds : undefined,
      dry_run: archiveDryRun,
    });
  };

  const handleMigrations = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const policyIds = migrationPolicyIds
      .split(',')
      .map((value) => value.trim())
      .filter(Boolean);
    await runMigrations.mutateAsync({
      policy_ids: policyIds.length ? policyIds : undefined,
      dry_run: migrationDryRun,
    });
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

  const notificationRows = useMemo(() => {
    if (!notificationPrefsQuery.data) return [];
    return notificationPrefsQuery.data.map((preference) => (
      <tr key={preference.id}>
        <td>{preference.subject_type}</td>
        <td>{preference.subject_id.slice(0, 8)}</td>
        <td>{preference.triggers.join(', ')}</td>
        <td>{preference.channels.map((channel) => channel.address).join(', ')}</td>
      </tr>
    ));
  }, [notificationPrefsQuery.data]);

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

        <Section title="Notification Preferences">
          <form className="form-grid" onSubmit={handlePreferenceSubmit}>
            <label>
              Organization ID
              <input value={organizationId} onChange={(event) => setOrganizationId(event.target.value)} placeholder="UUID" />
            </label>
            <label>
              Subject Type
              <select value={notificationSubjectType} onChange={(event) => setNotificationSubjectType(event.target.value as typeof notificationSubjectType)}>
                <option value="participant">Participant</option>
                <option value="team">Team</option>
                <option value="admin">Admin</option>
              </select>
            </label>
            <label>
              Subject ID
              <input value={notificationSubjectId} onChange={(event) => setNotificationSubjectId(event.target.value)} placeholder="UUID" />
            </label>
            <label>
              Email Address
              <input value={channelAddress} onChange={(event) => setChannelAddress(event.target.value)} placeholder="user@example.com" />
            </label>
            <fieldset style={{ border: '1px solid var(--border)', padding: '12px', borderRadius: '8px' }}>
              <legend>Triggers</legend>
              <div className="form-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))' }}>
                {triggerOptions.map((trigger) => (
                  <label key={trigger} style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <input
                      type="checkbox"
                      checked={selectedTriggers.includes(trigger)}
                      onChange={() => toggleTrigger(trigger)}
                    />
                    <span>{trigger}</span>
                  </label>
                ))}
              </div>
            </fieldset>
            <button className="primary-button" type="submit" disabled={upsertPreference.isPending}>
              {upsertPreference.isPending ? 'Saving…' : 'Save Preference'}
            </button>
            <button
              className="secondary-button"
              type="button"
              disabled={!organizationId || notificationPrefsQuery.isFetching}
              onClick={() => notificationPrefsQuery.refetch()}
            >
              {notificationPrefsQuery.isFetching ? 'Refreshing…' : 'Refresh Preferences'}
            </button>
          </form>
          {upsertPreference.error ? <div className="error-banner">{upsertPreference.error.message}</div> : null}
          {upsertPreference.isSuccess ? <div className="success-banner">Preference saved.</div> : null}
          {notificationPrefsQuery.error ? (
            <div className="error-banner">{(notificationPrefsQuery.error as Error).message}</div>
          ) : null}
          {notificationRows.length ? (
            <table style={{ width: '100%', marginTop: '16px', borderSpacing: '0 6px' }}>
              <thead>
                <tr>
                  <th align="left">Subject Type</th>
                  <th align="left">Subject</th>
                  <th align="left">Triggers</th>
                  <th align="left">Channels</th>
                </tr>
              </thead>
              <tbody>{notificationRows}</tbody>
            </table>
          ) : (
            <p className="card-description">Load an organization to view preferences.</p>
          )}
        </Section>

        <Section title="Dispatch Notifications">
          <form className="form-grid" onSubmit={handleDispatch}>
            <label>
              Trigger
              <select value={dispatchTrigger} onChange={(event) => setDispatchTrigger(event.target.value as NotificationTrigger)}>
                {triggerOptions.map((trigger) => (
                  <option key={trigger} value={trigger}>
                    {trigger}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Stage ID (optional)
              <input value={dispatchStageId} onChange={(event) => setDispatchStageId(event.target.value)} placeholder="UUID" />
            </label>
            <label>
              Round ID (optional)
              <input value={dispatchRoundId} onChange={(event) => setDispatchRoundId(event.target.value)} placeholder="UUID" />
            </label>
            <label>
              Season ID (optional)
              <input value={dispatchSeasonId} onChange={(event) => setDispatchSeasonId(event.target.value)} placeholder="UUID" />
            </label>
            <label>
              Recipient IDs (comma separated)
              <input value={dispatchRecipientIds} onChange={(event) => setDispatchRecipientIds(event.target.value)} placeholder="uuid-1, uuid-2" />
            </label>
            <label>
              Subject (optional)
              <input value={dispatchSubject} onChange={(event) => setDispatchSubject(event.target.value)} placeholder="Email subject" />
            </label>
            <label>
              Body (optional)
              <textarea value={dispatchBody} onChange={(event) => setDispatchBody(event.target.value)} rows={3} />
            </label>
            <button className="primary-button" type="submit" disabled={dispatchNotification.isPending}>
              {dispatchNotification.isPending ? 'Sending…' : 'Dispatch Notification'}
            </button>
          </form>
          {dispatchNotification.error ? <div className="error-banner">{dispatchNotification.error.message}</div> : null}
          {dispatchNotification.isSuccess ? <div className="success-banner">Notification request accepted.</div> : null}
        </Section>

        <Section title="Maintenance Jobs">
          <form className="form-grid" onSubmit={handleCleanup}>
            <fieldset style={{ border: '1px solid var(--border)', padding: '12px', borderRadius: '8px' }}>
              <legend>Cleanup Targets</legend>
              {['stale_registrations', 'notifications', 'sessions', 'archived_events', 'logs'].map((target) => (
                <label key={target} style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <input
                    type="checkbox"
                    checked={selectedCleanupTargets.includes(target)}
                    onChange={() => toggleCleanupTarget(target)}
                  />
                  <span>{target}</span>
                </label>
              ))}
            </fieldset>
            <label style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <input type="checkbox" checked={cleanupDryRun} onChange={(event) => setCleanupDryRun(event.target.checked)} />
              <span>Dry run only</span>
            </label>
            <button className="primary-button" type="submit" disabled={runCleanup.isPending}>
              {runCleanup.isPending ? 'Running…' : 'Run Cleanup'}
            </button>
          </form>
          {runCleanup.data ? <div className="success-banner">{runCleanup.data.summary}</div> : null}
          {runCleanup.error ? <div className="error-banner">{runCleanup.error.message}</div> : null}

          <form className="form-grid" onSubmit={handleArchive} style={{ marginTop: '24px' }}>
            <label>
              Archive Policy IDs (comma separated)
              <input value={archivePolicyIds} onChange={(event) => setArchivePolicyIds(event.target.value)} placeholder="uuid-1, uuid-2" />
            </label>
            <label style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <input type="checkbox" checked={archiveDryRun} onChange={(event) => setArchiveDryRun(event.target.checked)} />
              <span>Dry run only</span>
            </label>
            <button className="primary-button" type="submit" disabled={runArchive.isPending}>
              {runArchive.isPending ? 'Running…' : 'Run Archive'}
            </button>
          </form>
          {runArchive.data ? <div className="success-banner">{runArchive.data.summary}</div> : null}
          {runArchive.error ? <div className="error-banner">{runArchive.error.message}</div> : null}

          <form className="form-grid" onSubmit={handleMigrations} style={{ marginTop: '24px' }}>
            <label>
              Migration Policy IDs (comma separated)
              <input value={migrationPolicyIds} onChange={(event) => setMigrationPolicyIds(event.target.value)} placeholder="uuid-1, uuid-2" />
            </label>
            <label style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <input type="checkbox" checked={migrationDryRun} onChange={(event) => setMigrationDryRun(event.target.checked)} />
              <span>Dry run only</span>
            </label>
            <button className="primary-button" type="submit" disabled={runMigrations.isPending}>
              {runMigrations.isPending ? 'Running…' : 'Run Migration Checks'}
            </button>
          </form>
          {runMigrations.data ? <div className="success-banner">{runMigrations.data.summary}</div> : null}
          {runMigrations.error ? <div className="error-banner">{runMigrations.error.message}</div> : null}
        </Section>
      </div>
    </div>
  );
}
