import { describe, it, expect } from 'vitest'
import { computeMetrics, weeklyProgress } from './metrics.js'

// All fixture dates are mid-week (Tue/Wed) so the Monday-of-week bucketing in
// computeMetrics() groups them identically regardless of the timezone the test
// process runs in.
//
// Week A: Mon 2026-01-05 · Week B: Mon 2026-01-12 · Week C: Mon 2026-01-19
function baseTracker() {
  return {
    client: { name: 'Alex' },
    goals: { weekly_target: 2 },
    applications: [
      { id: '1', company: 'Acme', status: 'applied', fit: 75, sponsor: false, applied_date: '2026-01-06', updated_date: '2026-01-10' },
      { id: '2', company: 'Beta', status: 'screen', fit: 82, sponsor: false, applied_date: '2026-01-07', updated_date: '2026-01-12' },
      { id: '3', company: 'Gamma', status: 'onsite', fit: 91, sponsor: true, applied_date: '2026-01-14', updated_date: '2026-01-15' },
      { id: '4', company: 'Delta', status: 'offer', fit: 88, sponsor: false, applied_date: '2026-01-21', updated_date: '2026-01-22' },
      { id: '5', company: 'Acme', status: 'rejected', fit: 60, sponsor: false, applied_date: '2026-01-06', updated_date: '2026-01-08' },
      // curated only — must not count as applied anywhere
      { id: '6', company: 'Epsilon', status: 'curated', fit: 55, sponsor: false, applied_date: '2026-01-14', updated_date: '2026-01-05' },
      // messy row: empty company, non-numeric fit, truthy-but-not-true sponsor, empty date
      { id: '7', company: '', status: 'applied', fit: 'n/a', sponsor: 'yes', applied_date: '', updated_date: '' },
    ],
  }
}

describe('computeMetrics — cards', () => {
  const { cards } = computeMetrics(baseTracker())

  it('counts every application as a curated résumé', () => {
    expect(cards.resumesCurated).toBe(7)
  })

  it('counts applied/interviews/offers/rejected from cumulative status sets', () => {
    expect(cards.applications).toBe(6) // 5 real submissions + the messy applied row
    expect(cards.interviews).toBe(3) // screen + onsite + offer
    expect(cards.offers).toBe(1)
    expect(cards.rejected).toBe(1)
  })

  it('derives responseRate as interviews / applications, rounded', () => {
    expect(cards.responseRate).toBe(50) // 3 of 6
  })

  it('deduplicates companies and ignores empty company names', () => {
    expect(cards.totalCompanies).toBe(5) // Acme, Beta, Gamma, Delta, Epsilon
    expect(cards.companiesApplied).toBe(4) // Acme, Beta, Gamma, Delta — '' filtered out
  })

  it('counts sponsorNeeded only for sponsor === true, not merely truthy values', () => {
    expect(cards.sponsorNeeded).toBe(1) // id 3 only; id 7's 'yes' must not count
  })
})

describe('computeMetrics — funnel', () => {
  it('builds the cumulative curated → offer funnel', () => {
    const { funnel } = computeMetrics(baseTracker())
    expect(funnel.map((s) => s.key)).toEqual(['curated', 'applied', 'screen', 'onsite', 'offer'])
    expect(funnel.map((s) => s.value)).toEqual([7, 6, 3, 2, 1])
  })
})

describe('computeMetrics — overTime weekly bucketing', () => {
  it('groups applied applications by week, ascending', () => {
    const { overTime } = computeMetrics(baseTracker())
    expect(overTime).toHaveLength(3)
    expect(overTime.map((w) => w.count)).toEqual([3, 1, 1]) // A: ids 1,2,5 · B: id 3 · C: id 4
    const weeks = overTime.map((w) => w.week)
    expect([...weeks].sort()).toEqual(weeks) // ascending order
  })

  it('does not count curated-only applications even when they have a date', () => {
    const { overTime } = computeMetrics({ applications: [{ status: 'curated', applied_date: '2026-01-14' }] })
    expect(overTime).toEqual([])
  })

  it('skips applications with missing or invalid applied_date', () => {
    const { overTime } = computeMetrics({
      applications: [
        { status: 'applied', applied_date: 'not-a-date' },
        { status: 'applied' },
        { status: 'applied', applied_date: '2026-01-06' },
      ],
    })
    expect(overTime).toHaveLength(1)
    expect(overTime[0].count).toBe(1)
  })
})

describe('computeMetrics — fitBuckets', () => {
  it('distributes numeric fits into the five buckets', () => {
    const { fitBuckets } = computeMetrics(baseTracker())
    expect(fitBuckets.map((b) => b.count)).toEqual([1, 1, 1, 2, 1]) // 55 · 60 · 75 · 82+88 · 91
  })

  it('handles bucket boundaries and out-of-range/non-numeric fits', () => {
    const apps = [49, 50, 59, 60, 89, 90, 100, 101, '72', 'n/a'].map((fit) => ({ status: 'curated', fit }))
    const { fitBuckets } = computeMetrics({ applications: apps })
    // 49 and 101 fall outside every bucket; '72' coerces to a number; 'n/a' is skipped
    expect(fitBuckets.map((b) => b.count)).toEqual([2, 1, 1, 1, 2])
  })
})

describe('computeMetrics — applications list', () => {
  it('returns applications sorted by updated_date, newest first, without mutating input', () => {
    const tracker = baseTracker()
    const m = computeMetrics(tracker)
    expect(m.applications.map((a) => a.id)).toEqual(['4', '3', '2', '1', '5', '6', '7'])
    expect(tracker.applications[0].id).toBe('1') // input order untouched
  })
})

describe('computeMetrics — empty and malformed input', () => {
  it('returns zeroed metrics for undefined / empty / malformed trackers', () => {
    for (const tracker of [undefined, null, {}, { applications: 'nope' }]) {
      const m = computeMetrics(tracker)
      expect(m.cards.resumesCurated).toBe(0)
      expect(m.cards.applications).toBe(0)
      expect(m.cards.responseRate).toBe(0) // no divide-by-zero
      expect(m.funnel.map((s) => s.value)).toEqual([0, 0, 0, 0, 0])
      expect(m.overTime).toEqual([])
      expect(m.fitBuckets.map((b) => b.count)).toEqual([0, 0, 0, 0, 0])
      expect(m.applications).toEqual([])
    }
  })
})

describe('weeklyProgress', () => {
  it('reads the latest week against the weekly target', () => {
    const m = computeMetrics(baseTracker())
    expect(weeklyProgress(m)).toEqual({ thisWeek: 1, target: 2, pct: 50 })
  })

  it('caps pct at 100', () => {
    expect(weeklyProgress({ goals: { weekly_target: 1 }, overTime: [{ week: '2026-01-05', count: 3 }] })).toEqual({ thisWeek: 3, target: 1, pct: 100 })
  })

  it('reports zero progress with no target or data', () => {
    expect(weeklyProgress({})).toEqual({ thisWeek: 0, target: 0, pct: 0 })
    expect(weeklyProgress(undefined)).toEqual({ thisWeek: 0, target: 0, pct: 0 })
  })
})
