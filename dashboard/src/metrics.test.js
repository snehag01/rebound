import { describe, it, expect } from 'vitest'
import { computeMetrics, weeklyProgress } from './metrics.js'

// A small, deterministic fixture covering every status and an edge row
// (an application tracked from elsewhere with no curated résumé file).
const tracker = {
  client: { name: 'Test User', title: 'Software Engineer' },
  goals: { weekly_target: 5 },
  applications: [
    { id: '1', company: 'Acme', role: 'SWE', status: 'curated', fit: 82, resume_file: 'Acme.docx', applied_date: null, updated_date: '2026-07-01' },
    { id: '2', company: 'Beta', role: 'SWE', status: 'applied', fit: 71, resume_file: 'Beta.docx', applied_date: '2026-07-02', updated_date: '2026-07-02' },
    { id: '3', company: 'Cove', role: 'SWE', status: 'screen', fit: 90, resume_file: 'Cove.docx', applied_date: '2026-07-03', updated_date: '2026-07-03' },
    { id: '4', company: 'Beta', role: 'Senior SWE', status: 'offer', fit: 88, resume_file: 'Beta2.docx', applied_date: '2026-07-04', updated_date: '2026-07-05' },
    // Tracked from another source, applied without a Rebound-curated résumé:
    { id: '5', company: 'Delta', role: 'SWE', status: 'applied', fit: 55, resume_file: '', applied_date: '2026-07-06', updated_date: '2026-07-06' },
    { id: '6', company: 'Echo', role: 'SWE', status: 'rejected', fit: 60, resume_file: 'Echo.docx', applied_date: '2026-07-01', updated_date: '2026-07-07' },
  ],
}

describe('computeMetrics — honest counting', () => {
  const m = computeMetrics(tracker)

  it('counts "résumés curated" only for rows that actually have a resume_file', () => {
    // 6 applications, but row #5 has no resume_file → 5, not 6.
    expect(m.cards.resumesCurated).toBe(5)
  })

  it('counts applications as those actually submitted, not every tracked row', () => {
    // APPLIED = applied|screen|onsite|offer|accepted|rejected → all but the 'curated' row = 5
    expect(m.cards.applications).toBe(5)
  })

  it('counts interviews as screen-or-later', () => {
    expect(m.cards.interviews).toBe(2) // #3 screen + #4 offer
  })

  it('counts offers', () => {
    expect(m.cards.offers).toBe(1)
  })

  it('computes response rate as interviews / applied', () => {
    expect(m.cards.responseRate).toBe(40) // round(2/5 * 100)
  })

  it('dedupes companies applied to', () => {
    expect(m.cards.companiesApplied).toBe(4) // {Beta, Cove, Delta, Echo}
  })
})

describe('computeMetrics — funnel & buckets', () => {
  const m = computeMetrics(tracker)

  it('produces a monotonically non-increasing funnel', () => {
    const vals = m.funnel.map((f) => f.value)
    for (let i = 1; i < vals.length; i++) {
      expect(vals[i]).toBeLessThanOrEqual(vals[i - 1])
    }
  })

  it('buckets every application that has a numeric fit', () => {
    const total = m.fitBuckets.reduce((s, b) => s + b.count, 0)
    expect(total).toBe(6)
  })
})

describe('computeMetrics — empty / malformed input', () => {
  it('handles an empty tracker without throwing', () => {
    const m = computeMetrics({})
    expect(m.cards.resumesCurated).toBe(0)
    expect(m.cards.applications).toBe(0)
    expect(m.funnel[0].value).toBe(0)
  })

  it('tolerates a null tracker', () => {
    const m = computeMetrics(null)
    expect(m.cards.applications).toBe(0)
  })
})

describe('weeklyProgress', () => {
  it('computes a bounded percentage against the weekly target', () => {
    const m = computeMetrics(tracker)
    const w = weeklyProgress(m)
    expect(w.target).toBe(5)
    expect(w.pct).toBeGreaterThanOrEqual(0)
    expect(w.pct).toBeLessThanOrEqual(100)
  })

  it('returns 0% when no target is set', () => {
    const m = computeMetrics({ applications: [] })
    expect(weeklyProgress(m).pct).toBe(0)
  })
})
