import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowRight, Download, ChevronDown, ChevronUp, FileText } from 'lucide-react'
import { Card, Badge, Button } from '@/app/components/ui'
import { submissionsAPI } from '@/services/api'
import type { DocumentResult } from '@/types'

// ── Per-submission row (expandable) ──────────────────────────────────────────
function SubmissionRow({ h, onOpen }: { h: any; onOpen: () => void }) {
  const [expanded, setExpanded] = useState(false)
  const docResults: DocumentResult[] = h.document_results ?? []
  const worstScore = docResults.length
    ? Math.max(...docResults.map((r: DocumentResult) => r.plagiarism_score))
    : null
  const date = h.date ?? h.created_at?.split('T')[0] ?? '—'

  const scoreColor = (s: number) =>
    s >= 30 ? 'text-red-400' : s >= 15 ? 'text-orange-400' : 'text-emerald-400'

  return (
    <div className="border-b border-border last:border-0">
      {/* Main row */}
      <div className="px-5 py-4 grid grid-cols-12 gap-3 items-center hover:bg-accent/40 transition-colors">
        <div className="col-span-4">
          <button onClick={onOpen} className="text-left group">
            <p className="text-sm font-medium group-hover:text-primary transition-colors">
              {h.workspace_name}
            </p>
            <p className="text-xs text-muted-foreground flex items-center gap-1">
              Open workspace <ArrowRight size={10}/>
            </p>
          </button>
        </div>
        <span className="col-span-2 text-xs font-mono text-muted-foreground">{date}</span>
        <div className="col-span-2">
          {worstScore !== null
            ? <span className={`text-sm font-bold font-mono ${scoreColor(worstScore)}`}>
                {worstScore}%
              </span>
            : <span className="text-xs text-muted-foreground">—</span>
          }
        </div>
        <div className="col-span-2">
          <Badge variant={
            h.status === 'completed' ? 'success' :
            h.status === 'processing' ? 'warning' :
            h.status === 'pending' ? 'warning' :
            'default'
          }>
            {h.status === 'processing' ? '⏳ Processing…' : h.status}
          </Badge>
        </div>
        <div className="col-span-2 flex justify-end">
          {docResults.length > 0 && (
            <Button size="sm" variant="outline" onClick={() => setExpanded(p => !p)}>
              {expanded ? <ChevronUp size={13}/> : <ChevronDown size={13}/>}
              {expanded ? 'Hide' : 'View'}
            </Button>
          )}
        </div>
      </div>

      {/* Expanded per-document results */}
      {expanded && docResults.length > 0 && (
        <div className="px-5 pb-4 space-y-3 bg-secondary/20">
          {docResults.map((r: DocumentResult) => (
            <div key={r.document_id} className="rounded-xl border border-border bg-card p-4">
              {/* Doc header */}
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <FileText size={14} className="text-muted-foreground"/>
                  <span className="text-sm font-medium">{r.document_name}</span>
                </div>
                <Badge variant={
                  r.plagiarism_score >= 30 ? 'danger' :
                  r.plagiarism_score >= 15 ? 'warning' : 'success'
                }>
                  {r.plagiarism_score}% plagiarism
                </Badge>
              </div>

              {/* Matched sources */}
              {r.matched_sources.length === 0 ? (
                <p className="text-xs text-muted-foreground">No significant matches found.</p>
              ) : (
                <div className="space-y-2">
                  <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                    Matched Sources
                  </p>
                  {r.matched_sources.map((ms, i) => (
                    <div key={i}>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-muted-foreground truncate pr-3">{ms.source}</span>
                        <span className="font-bold font-mono flex-shrink-0" style={{ color: ms.color }}>
                          {ms.match}%
                        </span>
                      </div>
                      <div className="h-1.5 rounded-full bg-secondary">
                        <div className="h-full rounded-full transition-all duration-700"
                          style={{ width: `${Math.min(ms.match * 3, 100)}%`, backgroundColor: ms.color }}/>
                      </div>
                    </div>
                  ))}
                </div>
              )}
              {/* Highlighted plagiarised paragraphs */}
              {r.highlighted_segments?.filter((s:any) => s.highlight).length > 0 && (
                <div className="mt-3 space-y-2">
                  <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                    Plagiarised Paragraphs
                  </p>
                  {r.highlighted_segments.filter((s:any) => s.highlight).map((seg:any, i:number) => (
                    <div key={i} className="rounded-lg border-l-4 border-amber-400 bg-amber-400/10 p-2.5">
                      <div className="flex justify-between mb-1">
                        <span className="text-xs font-semibold text-amber-500 truncate pr-2">{seg.source}</span>
                        {seg.match_percentage && (
                          <span className="text-xs font-mono text-amber-500">{seg.match_percentage}%</span>
                        )}
                      </div>
                      <p className="text-xs leading-5 text-foreground/80">{seg.text}</p>
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

// ── Main page ──────────────────────────────────────────────────────────────────
export default function HistoryPage() {
  const navigate = useNavigate()
  const [history, setHistory] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadHistory = () => {
      setLoading(true)
      submissionsAPI.history()
        .then(res => setHistory(res.data.results ?? res.data))
        .catch(() => setHistory([]))
        .finally(() => setLoading(false))
    }
    
    loadHistory()
  }, [])

  // Refresh history when returning to page
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        submissionsAPI.history()
          .then(res => setHistory(res.data.results ?? res.data))
          .catch(() => {})
      }
    }
    
    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange)
  }, [])

  if (loading) return (
    <div className="flex items-center justify-center py-20">
      <div className="w-8 h-8 rounded-full border-4 border-primary/20 border-t-primary animate-spin"/>
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

      {history.length === 0 ? (
        <Card className="p-12 text-center">
          <p className="font-semibold">No submissions yet</p>
          <p className="text-sm text-muted-foreground mt-1 mb-4">
            Submit documents in a workspace to see results here
          </p>
          <Button variant="outline" onClick={() => navigate('/workspaces')}>
            Go to Workspaces
          </Button>
        </Card>
      ) : (
        <Card>
          {/* Table header */}
          <div className="px-5 py-3 border-b border-border grid grid-cols-12 gap-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            <span className="col-span-4">Workspace</span>
            <span className="col-span-2">Date</span>
            <span className="col-span-2">Worst Score</span>
            <span className="col-span-2">Status</span>
            <span className="col-span-2 text-right">Results</span>
          </div>
          {history.map(h => (
            <SubmissionRow
              key={h.id}
              h={h}
              onOpen={() => navigate(`/workspaces/${h.workspace_id}`)}
            />
          ))}
        </Card>
      )}
    </div>
  )
}
