import { useEffect, useMemo, useState } from 'react'
import { computeMetrics, weeklyProgress } from './metrics.js'

const STATUS_META = {
  curated: { label: 'Curated', cls: 'st-curated' },
  applied: { label: 'Applied', cls: 'st-applied' },
  screen: { label: 'Screen', cls: 'st-screen' },
  onsite: { label: 'Onsite', cls: 'st-onsite' },
  offer: { label: 'Offer', cls: 'st-offer' },
  accepted: { label: 'Accepted', cls: 'st-accepted' },
  rejected: { label: 'Rejected', cls: 'st-rejected' },
}

function useTracker() {
  const [state, setState] = useState({ data: null, source: null, error: null, loading: true })
  async function load() {
    setState((s) => ({ ...s, loading: true }))
    try {
      // Live datastore via the dev middleware; fall back to the bundled sample.
      let res = await fetch('/api/tracker', { cache: 'no-store' })
      let source = res.headers.get('X-Rebound-Source') || 'datastore'
      if (!res.ok) throw new Error('api')
      const data = await res.json()
      setState({ data, source, error: null, loading: false })
    } catch {
      try {
        const res = await fetch('/data/tracker.sample.json', { cache: 'no-store' })
        setState({ data: await res.json(), source: 'sample', error: null, loading: false })
      } catch (e) {
        setState({ data: null, source: null, error: String(e), loading: false })
      }
    }
  }
  useEffect(() => { load() }, [])
  return { ...state, reload: load }
}

function StatCard({ label, value, sub, accent }) {
  return (
    <div className={'card stat' + (accent ? ' stat--accent' : '')}>
      <div className="stat__value">{value}</div>
      <div className="stat__label">{label}</div>
      {sub != null && <div className="stat__sub">{sub}</div>}
    </div>
  )
}

function ProgressBar({ pct, label, right }) {
  return (
    <div className="progress">
      <div className="progress__head">
        <span>{label}</span>
        <span className="progress__right">{right}</span>
      </div>
      <div className="progress__track">
        <div className="progress__fill" style={{ width: Math.max(2, pct) + '%' }} />
      </div>
    </div>
  )
}

function Funnel({ funnel }) {
  const max = Math.max(1, ...funnel.map((f) => f.value))
  return (
    <div className="funnel">
      {funnel.map((f, i) => {
        const prev = i > 0 ? funnel[i - 1].value : f.value
        const conv = prev > 0 ? Math.round((f.value / prev) * 100) : 100
        return (
          <div className="funnel__row" key={f.key}>
            <div className="funnel__label">{f.label}</div>
            <div className="funnel__barwrap">
              <div className={'funnel__bar fn-' + f.key} style={{ width: (f.value / max) * 100 + '%' }}>
                <span className="funnel__val">{f.value}</span>
              </div>
            </div>
            <div className="funnel__conv">{i === 0 ? '—' : conv + '%'}</div>
          </div>
        )
      })}
    </div>
  )
}

function BarChart({ data, valueKey = 'count', labelKey = 'label', accent = 'amber' }) {
  const max = Math.max(1, ...data.map((d) => d[valueKey]))
  if (!data.length) return <div className="empty">No data yet — apply to a role to see momentum.</div>
  return (
    <div className={'barchart bc-' + accent}>
      {data.map((d, i) => (
        <div className="barchart__col" key={i}>
          <div className="barchart__barwrap">
            <div className="barchart__val">{d[valueKey]}</div>
            <div className="barchart__bar" style={{ height: (d[valueKey] / max) * 100 + '%' }} />
          </div>
          <div className="barchart__label">{d[labelKey]}</div>
        </div>
      ))}
    </div>
  )
}

function StatusPill({ status }) {
  const m = STATUS_META[status] || { label: status, cls: '' }
  return <span className={'pill ' + m.cls}>{m.label}</span>
}

function AppsTable({ apps }) {
  const [q, setQ] = useState('')
  const [status, setStatus] = useState('all')
  const filtered = apps.filter((a) => {
    const hay = (a.company + ' ' + a.role + ' ' + (a.id || '')).toLowerCase()
    return (status === 'all' || a.status === status) && hay.includes(q.toLowerCase())
  })
  const statuses = ['all', ...Object.keys(STATUS_META)]
  return (
    <div className="card">
      <div className="table__controls">
        <input className="input" placeholder="Search company, role, JobId…" value={q} onChange={(e) => setQ(e.target.value)} />
        <div className="chips">
          {statuses.map((s) => (
            <button key={s} className={'chip' + (status === s ? ' chip--on' : '')} onClick={() => setStatus(s)}>
              {s === 'all' ? 'All' : (STATUS_META[s]?.label || s)}
            </button>
          ))}
        </div>
      </div>
      <div className="table__scroll">
        <table className="table">
          <thead>
            <tr>
              <th>Company</th><th>Role</th><th>JobId</th><th>Status</th>
              <th>Fit</th><th>Sponsor</th><th>Résumé</th><th>Applied</th><th>Source</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((a, i) => (
              <tr key={i}>
                <td className="td-strong">{a.company}</td>
                <td>{a.role}</td>
                <td className="td-mono">{a.id || '—'}</td>
                <td><StatusPill status={a.status} /></td>
                <td>{a.fit != null ? <span className="fit"><b>{a.fit}</b>%</span> : '—'}</td>
                <td>{a.sponsor ? <span className="tag">sponsor</span> : '—'}</td>
                <td className="td-file">{a.resume_file || '—'}</td>
                <td className="td-mono">{a.applied_date || '—'}</td>
                <td className="td-dim">{a.source || '—'}</td>
              </tr>
            ))}
            {!filtered.length && <tr><td colSpan="9" className="empty">No matching applications.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default function App() {
  const { data, source, error, loading, reload } = useTracker()
  const metrics = useMemo(() => (data ? computeMetrics(data) : null), [data])
  const goal = useMemo(() => (metrics ? weeklyProgress(metrics) : null), [metrics])

  if (loading) return <div className="shell"><div className="empty big">Loading your comeback…</div></div>
  if (error || !metrics) return <div className="shell"><div className="empty big">Couldn’t load data. Run <code>/rebound:start</code> then <code>/rebound:track</code>.</div></div>

  const c = metrics.cards
  const client = metrics.client || {}

  return (
    <div className="shell">
      <header className="topbar">
        <div className="brand">
          <span className="glove">🥊</span>
          <div>
            <div className="brand__name">Rebound</div>
            <div className="brand__tag">Knocked down. Not out.</div>
          </div>
        </div>
        <div className="who">
          <div className="who__name">{client.name || 'Your'} </div>
          <div className="who__title">{client.title || 'job search'}</div>
        </div>
        <div className="topbar__actions">
          {source === 'sample' && <span className="badge badge--warn">sample data</span>}
          {source === 'datastore' && <span className="badge badge--ok">live</span>}
          <button className="btn" onClick={reload}>↻ Refresh</button>
        </div>
      </header>

      {goal?.target > 0 && (
        <div className="card goal">
          <ProgressBar pct={goal.pct} label={`This week’s applications`} right={`${goal.thisWeek} / ${goal.target}`} />
        </div>
      )}

      <section className="cards">
        <StatCard label="Résumés curated" value={c.resumesCurated} accent />
        <StatCard label="Companies applied" value={c.companiesApplied} sub={`${c.totalCompanies} tracked`} />
        <StatCard label="Applications" value={c.applications} />
        <StatCard label="Interviews" value={c.interviews} sub={`${c.responseRate}% response`} />
        <StatCard label="Offers" value={c.offers} accent />
        <StatCard label="Need sponsorship" value={c.sponsorNeeded} sub="roles flagged" />
      </section>

      <section className="grid2">
        <div className="card">
          <h3 className="h">Pipeline</h3>
          <Funnel funnel={metrics.funnel} />
        </div>
        <div className="card">
          <h3 className="h">Applications over time</h3>
          <BarChart data={metrics.overTime} accent="amber" />
        </div>
      </section>

      <section className="grid2">
        <div className="card">
          <h3 className="h">Fit-score of targeted roles</h3>
          <BarChart data={metrics.fitBuckets} accent="teal" />
        </div>
        <div className="card insight">
          <h3 className="h">Momentum</h3>
          <p>
            You’ve curated <b>{c.resumesCurated}</b> résumés and applied to <b>{c.companiesApplied}</b> companies.
            {c.interviews > 0 ? <> That’s <b>{c.responseRate}%</b> turning into conversations — keep going.</>
              : <> No screens yet — referrals convert best; prioritize your highest-fit roles.</>}
          </p>
          <p className="dim">All numbers computed locally on this machine. Your private situation is never shown here.</p>
        </div>
      </section>

      <section>
        <h3 className="h h--section">Applications</h3>
        <AppsTable apps={metrics.applications} />
      </section>

      <footer className="foot">
        Rebound · local dashboard · data at <code>~/.rebound/data/tracker.json</code>
      </footer>
    </div>
  )
}
