import { useEffect, useState } from 'react'
import { PieChart as PieIcon, TrendingUp, Clock } from 'lucide-react'
import { DecisionPieChart, CommitTimelineChart, TimeSavedBarChart } from '../components/Charts'
import { analyticsService } from '../services/api'

const MOCK_TIMELINE = [
  { date: 'Feb 28', commits: 5  },
  { date: 'Mar 01', commits: 8  },
  { date: 'Mar 02', commits: 4  },
  { date: 'Mar 03', commits: 12 },
  { date: 'Mar 04', commits: 7  },
  { date: 'Mar 05', commits: 10 },
  { date: 'Mar 06', commits: 9  },
  { date: 'Mar 07', commits: 14 },
]

const MOCK_TIME_SAVED = [
  { date: 'Feb 28', minutes_saved: 50  },
  { date: 'Mar 01', minutes_saved: 80  },
  { date: 'Mar 02', minutes_saved: 30  },
  { date: 'Mar 03', minutes_saved: 110 },
  { date: 'Mar 04', minutes_saved: 60  },
  { date: 'Mar 05', minutes_saved: 90  },
  { date: 'Mar 06', minutes_saved: 70  },
  { date: 'Mar 07', minutes_saved: 140 },
]

function ChartCard({ icon: Icon, accent, title, subtitle, children }) {
  return (
    <div className="panel">
      <div className="panel-header">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg" style={{ background: accent + '18' }}>
            <Icon size={14} style={{ color: accent }} />
          </div>
          <div>
            <h2 className="section-title">{title}</h2>
            {subtitle && <p className="text-xs mt-0.5" style={{ color: '#8B949E' }}>{subtitle}</p>}
          </div>
        </div>
      </div>
      <div className="p-6 min-h-[320px]">{children}</div>
    </div>
  )
}

export default function AnalyticsPage() {
  const [summary, setSummary] = useState(null)
  const [timeline, setTimeline] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      analyticsService.getSummary(),
      analyticsService.getTimeline(30),
    ])
      .then(([summaryRes, timelineRes]) => {
        setSummary(summaryRes.data)
        setTimeline(timelineRes.data?.timeline ?? [])
      })
      .catch(() => {
        // Fallback to mock data when backend is unavailable
        setSummary({ skipped: 37, executed: 21, partial: 0, time_saved: 370 })
        setTimeline(MOCK_TIMELINE)
      })
      .finally(() => setLoading(false))
  }, [])

  const skipped  = summary?.skipped  ?? 0
  const executed = (summary?.executed ?? 0) + (summary?.partial ?? 0)
  const skipRate = (skipped + executed) > 0 ? skipped / (skipped + executed) : 0.6

  const timeSaved = timeline.length > 0
    ? timeline.map(({ date, commits }) => ({
        date,
        minutes_saved: Math.round(commits * skipRate * 10),
      }))
    : MOCK_TIME_SAVED

  return (
    <div className="max-w-7xl mx-auto space-y-8 sm:space-y-10 fade-in">

      {/* Page header */}
      <div>
        <h1 className="page-title">CI Analytics</h1>
        <p className="page-sub">Skip rates, commit trends, and time saved across your repositories</p>
      </div>

      {/* Row 1: Pie + Timeline */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        <div className="lg:col-span-2">
          <ChartCard icon={PieIcon} accent="#a371f7" title="Decision split" subtitle="Skip vs run breakdown">
            <DecisionPieChart data={{ skipped, executed }} loading={loading} />
          </ChartCard>
        </div>
        <div className="lg:col-span-3">
          <ChartCard icon={TrendingUp} accent="#388bfd" title="Commit activity" subtitle="Commits analyzed per day (last 8 days)">
            <CommitTimelineChart data={loading ? [] : timeline} loading={loading} />
          </ChartCard>
        </div>
      </div>

      {/* Row 2: Time saved */}
      <ChartCard icon={Clock} accent="#3fb950" title="CI time saved" subtitle="Estimated minutes saved per day by skipping tests">
        <TimeSavedBarChart data={loading ? [] : timeSaved} loading={loading} />
      </ChartCard>
    </div>
  )
}
