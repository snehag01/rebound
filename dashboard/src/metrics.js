// Pure, local analytics over the tracker datastore. Nothing leaves the machine.

export const STAGES = ['curated', 'applied', 'screen', 'onsite', 'offer', 'accepted']
export const STAGE_RANK = Object.fromEntries(STAGES.map((s, i) => [s, i]))

// Statuses that mean "the person actually submitted an application"
const APPLIED_SET = new Set(['applied', 'screen', 'onsite', 'offer', 'accepted', 'rejected'])
const SCREENED_SET = new Set(['screen', 'onsite', 'offer', 'accepted'])
const ONSITE_SET = new Set(['onsite', 'offer', 'accepted'])
const OFFER_SET = new Set(['offer', 'accepted'])

const pct = (n, d) => (d > 0 ? Math.round((n / d) * 100) : 0)

function isoWeekKey(dateStr) {
  // Group by Monday-of-week; returns "YYYY-MM-DD" of that Monday.
  if (!dateStr) return null
  const d = new Date(dateStr + 'T00:00:00')
  if (isNaN(d)) return null
  const day = (d.getDay() + 6) % 7 // Mon=0
  d.setDate(d.getDate() - day)
  return d.toISOString().slice(0, 10)
}

export function computeMetrics(tracker) {
  const apps = Array.isArray(tracker?.applications) ? tracker.applications : []

  const resumesCurated = apps.length
  const applied = apps.filter((a) => APPLIED_SET.has(a.status))
  const screened = apps.filter((a) => SCREENED_SET.has(a.status))
  const onsite = apps.filter((a) => ONSITE_SET.has(a.status))
  const offers = apps.filter((a) => OFFER_SET.has(a.status))
  const rejected = apps.filter((a) => a.status === 'rejected')

  const companies = new Set(apps.map((a) => a.company).filter(Boolean))
  const companiesApplied = new Set(applied.map((a) => a.company).filter(Boolean))

  // Funnel (cumulative "reached at least this stage")
  const funnel = [
    { key: 'curated', label: 'Résumés curated', value: resumesCurated },
    { key: 'applied', label: 'Applied', value: applied.length },
    { key: 'screen', label: 'Phone screen', value: screened.length },
    { key: 'onsite', label: 'Onsite', value: onsite.length },
    { key: 'offer', label: 'Offer', value: offers.length },
  ]

  // Applications over time (by week of applied_date)
  const weekMap = new Map()
  for (const a of applied) {
    const wk = isoWeekKey(a.applied_date)
    if (!wk) continue
    weekMap.set(wk, (weekMap.get(wk) || 0) + 1)
  }
  const overTime = [...weekMap.entries()]
    .sort((a, b) => a[0].localeCompare(b[0]))
    .map(([week, count]) => ({
      week,
      count,
      label: new Date(week + 'T00:00:00').toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
    }))

  // Fit-score distribution
  const buckets = [
    { label: '50–59', min: 50, max: 59, count: 0 },
    { label: '60–69', min: 60, max: 69, count: 0 },
    { label: '70–79', min: 70, max: 79, count: 0 },
    { label: '80–89', min: 80, max: 89, count: 0 },
    { label: '90+', min: 90, max: 100, count: 0 },
  ]
  for (const a of apps) {
    const f = Number(a.fit)
    if (!Number.isFinite(f)) continue
    const b = buckets.find((x) => f >= x.min && f <= x.max)
    if (b) b.count++
  }

  const sponsorNeeded = apps.filter((a) => a.sponsor === true).length

  return {
    client: tracker?.client || {},
    goals: tracker?.goals || {},
    cards: {
      resumesCurated,
      companiesApplied: companiesApplied.size,
      applications: applied.length,
      interviews: screened.length,
      offers: offers.length,
      responseRate: pct(screened.length, applied.length),
      rejected: rejected.length,
      totalCompanies: companies.size,
      sponsorNeeded,
    },
    funnel,
    overTime,
    fitBuckets: buckets,
    applications: apps.slice().sort((a, b) => (b.updated_date || '').localeCompare(a.updated_date || '')),
  }
}

export function weeklyProgress(metrics) {
  const target = Number(metrics?.goals?.weekly_target) || 0
  const weeks = metrics?.overTime || []
  const thisWeek = weeks.length ? weeks[weeks.length - 1].count : 0
  return { thisWeek, target, pct: target ? Math.min(100, Math.round((thisWeek / target) * 100)) : 0 }
}
