import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowRight, ChevronDown, ChevronUp, FileText } from 'lucide-react'
import { Card, Badge, Button, Alert } from '@/app/components/ui'
import { submissionsAPI } from '@/services/api'
import type { DocumentResult } from '@/types'

type HistorySubmission = {
  id: number
  workspace_id?: number
  workspace_name?: string
  date?: string
  created_at?: string
  status: string
  document_results?: DocumentResult[]
}

const STALE_ANALYSIS_MS = 10 * 60 * 1000

const formatDate = (value?: string) => {
  if (!value) return '-'
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return value.split('T')[0] || value
  return parsed.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
}

const isStaleSubmission = (submission: HistorySubmission) => {
  if (!['pending', 'processing'].includes(submission.status)) return false
  const timestamp = submission.date ?? submission.created_at
  if (!timestamp) return false
  const submittedAt = new Date(timestamp).getTime()
  if (Number.isNaN(submittedAt)) return false
  return Date.now() - submittedAt > STALE_ANALYSIS_MS
}

const statusLabel = (status: string) => {
  if (status === 'processing') return 'Processing...'
  if (status === 'pending') return 'Pending'
  if (status === 'completed') return 'Completed'
  if (status === 'failed') return 'Failed'
  return status || 'Unknown'
}

function SubmissionRow({ h, onOpen }: { h: HistorySubmission; onOpen: () => void }) {
  const [expanded, setExpanded] = useState(false)
  const docResults = h.document_results ?? []
  const displayStatus = isStaleSubmission(h) ? 'failed' : h.status
  const worstScore = docResults.length
    ? Math.max(...docResults.map((r) => r.plagiarism_score))
    : null

  const scoreColor = (score: number) =>
    score >= 30 ? 'text-red-400' : score >= 15 ? 'text-orange-400' : 'text-emerald-400'

  return (
    <div className="border-b border-border last:border-0">
      <div className="px-5 py-4 grid grid-cols-1 sm:grid-cols-12 gap-3 items-start sm:items-center hover:bg-accent/40 transition-colors">
        <div className="sm:col-span-4">
          <button onClick={onOpen} className="text-left group" disabled={!h.workspace_id}>
            <p className="text-sm font-medium group-hover:text-primary transition-colors">
              {h.workspace_name || 'Workspace'}
            </p>
            <p className="text-xs text-muted-foreground flex items-center gap-1">
              Open workspace <ArrowRight size={10} />
            </p>
          </button>
        </div>

        <span className="sm:col-span-2 text-xs font-mono text-muted-foreground">
          {formatDate(h.date ?? h.created_at)}
        </span>

        <div className="sm:col-span-2">
          {worstScore !== null ? (
            <span className={`text-sm font-bold font-mono ${scoreColor(worstScore)}`}>
              {worstScore}%
            </span>
          ) : (
            <span className="text-xs text-muted-foreground">-</span>
          )}
        </div>

        <div className="sm:col-span-2">
          <Badge variant={
            displayStatus === 'completed' ? 'success' :
            displayStatus === 'processing' || displayStatus === 'pending' ? 'warning' :
            displayStatus === 'failed' ? 'danger' :
            'default'
          }>
            {statusLabel(displayStatus)}
          </Badge>
        </div>

        <div className="sm:col-span-2 flex sm:justify-end">
          {docResults.length > 0 && (
            <Button size="sm" variant="outline" onClick={() => setExpanded((prev) => !prev)}>
              {expanded ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
              {expanded ? 'Hide' : 'View'}
            </Button>
          )}
        </div>
      </div>

      {expanded && docResults.length > 0 && (
        <div className="px-5 pb-4 space-y-3 bg-secondary/20">
          {docResults.map((result) => (
            <div key={result.document_id} className="rounded-xl border border-border bg-card p-4">
              <div className="flex items-center justify-between gap-3 mb-3">
                <div className="flex items-center gap-2 min-w-0">
                  <FileText size={14} className="text-muted-foreground flex-shrink-0" />
                  <span className="text-sm font-medium truncate">{result.document_name}</span>
                </div>
                <Badge variant={
                  result.plagiarism_score >= 30 ? 'danger' :
                  result.plagiarism_score >= 15 ? 'warning' :
                  'success'
                }>
                  {result.plagiarism_score}% plagiarism
                </Badge>
              </div>

              {result.matched_sources.length === 0 ? (
                <p className="text-xs text-muted-foreground">No significant matches found.</p>
              ) : (
                <div className="space-y-2">
                  <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                    Matched Sources
                  </p>
                  {result.matched_sources.map((source, index) => (
                    <div key={`${source.source}-${index}`}>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-muted-foreground truncate pr-3">{source.source}</span>
                        <span className="font-bold font-mono flex-shrink-0" style={{ color: source.color }}>
                          {source.match}%
                        </span>
                      </div>
                      <div className="h-1.5 rounded-full bg-secondary">
                        <div
                          className="h-full rounded-full transition-all duration-700"
                          style={{ width: `${Math.min(Math.max(source.match, 0), 100)}%`, backgroundColor: source.color }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {result.highlighted_segments?.filter((segment: any) => segment.highlight).length > 0 && (
                <div className="mt-3 space-y-2">
                  <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                    Plagiarised Paragraphs
                  </p>
                  {result.highlighted_segments.filter((segment: any) => segment.highlight).map((segment: any, index: number) => (
                    <div key={index} className="rounded-lg border-l-4 border-amber-400 bg-amber-400/10 p-2.5">
                      <div className="flex justify-between mb-1">
                        <span className="text-xs font-semibold text-amber-500 truncate pr-2">
                          {segment.source ?? 'Unknown source'}
                        </span>
                        {segment.match_percentage && (
                          <span className="text-xs font-mono text-amber-500">{segment.match_percentage}%</span>
                        )}
                      </div>
                      <p className="text-xs leading-5 text-foreground/80">{segment.text}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default function HistoryPage() {
  const navigate = useNavigate()
  const [history, setHistory] = useState<HistorySubmission[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadHistory = (showSpinner = false) => {
    if (showSpinner) setLoading(true)

    return submissionsAPI.history()
      .then((res) => {
        const nextHistory = res.data.results ?? res.data
        setHistory(Array.isArray(nextHistory) ? nextHistory : [])
        setError('')
      })
      .catch(() => {
        setHistory([])
        setError('Failed to load submission history. Please try again.')
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    let cancelled = false
    let intervalId: ReturnType<typeof setInterval>

    const refresh = (showSpinner = false) => {
      if (cancelled) return
      loadHistory(showSpinner)
    }

    refresh(true)
    intervalId = setInterval(() => {
      if (!document.hidden) refresh(false)
    }, 10000)

    return () => {
      cancelled = true
      clearInterval(intervalId)
    }
  }, [])

  useEffect(() => {
    const handleVisibilityChange = () => {
      if (!document.hidden) loadHistory(false)
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange)
  }, [])

  if (loading) return (
    <div className="flex items-center justify-center py-20">
      <div className="w-8 h-8 rounded-full border-4 border-primary/20 border-t-primary animate-spin" />
    </div>
  )

  return (
    <div className="space-y-5 animate-fade-in">
      <div>
        <h2 className="text-xl font-bold">Submission History</h2>
        <p className="text-sm text-muted-foreground mt-0.5">
          {history.length} submission{history.length !== 1 ? 's' : ''}
        </p>
      </div>

      {error && <Alert variant="error">{error}</Alert>}

      {history.length === 0 && !error ? (
        <Card className="p-12 text-center">
          <p className="font-semibold">No submissions yet</p>
          <p className="text-sm text-muted-foreground mt-1 mb-4">
            Submit documents in a workspace to see results here
          </p>
          <Button variant="outline" onClick={() => navigate('/workspaces')}>
            Go to Workspaces
          </Button>
        </Card>
      ) : history.length > 0 ? (
        <Card className="overflow-hidden">
          <div className="hidden sm:grid px-5 py-3 border-b border-border grid-cols-12 gap-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            <span className="col-span-4">Workspace</span>
            <span className="col-span-2">Date</span>
            <span className="col-span-2">Worst Score</span>
            <span className="col-span-2">Status</span>
            <span className="col-span-2 text-right">Results</span>
          </div>
          {history.map((item) => (
            <SubmissionRow
              key={item.id}
              h={item}
              onOpen={() => item.workspace_id && navigate(`/workspaces/${item.workspace_id}`)}
            />
          ))}
        </Card>
      ) : null}
    </div>
  )
}
