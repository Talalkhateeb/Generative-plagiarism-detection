import { useState, useEffect } from 'react'
import { useParams, useNavigate, useLocation } from 'react-router-dom'
import {
  ChevronLeft, Send, AlertTriangle, CheckCircle,
  FileText, ChevronDown, ChevronUp, Download
} from 'lucide-react'
import { Card, Badge, Button, FileRow, DropZone, Alert, ScoreRing } from '@/app/components/ui'
import { useWorkspaces } from '@/app/context/WorkspaceContext'
import type { Source, Document, DocumentResult, Submission } from '@/types'
import { workspacesAPI } from '@/services/api'

const ALLOWED_EXTS = ['pdf', 'docx', 'doc', 'txt']
const STEPS = [
  'Validating files…',
  'Checking plan limits…',
  'Sending to AI Model…',
  'Analyzing documents…',
  'Calculating scores…',
]

function scoreColor(score: number) {
  if (score >= 30) return 'text-red-400'
  if (score >= 15) return 'text-orange-400'
  if (score >= 5)  return 'text-yellow-400'
  return 'text-emerald-400'
}

function scoreBadgeVariant(score: number): 'danger' | 'warning' | 'success' {
  if (score >= 30) return 'danger'
  if (score >= 15) return 'warning'
  return 'success'
}

// ── Per-document result card ───────────────────────────────────────────────────
function DocumentResultCard({ result }: { result: DocumentResult }) {
  const [expanded, setExpanded] = useState(false)
  return (
    <Card className="overflow-hidden">
      <button
        className="w-full flex items-center justify-between p-4 hover:bg-secondary/40 transition-colors text-left"
        onClick={() => setExpanded(p => !p)}
      >
        <div className="flex items-center gap-3 min-w-0">
          <FileText size={16} className="text-muted-foreground flex-shrink-0" />
          <span className="font-medium text-sm truncate">{result.document_name}</span>
        </div>
        <div className="flex items-center gap-3 flex-shrink-0 ml-3">
          <Badge variant={scoreBadgeVariant(result.plagiarism_score)}>
            {result.plagiarism_score}% plagiarism
          </Badge>
          <span className="text-xs text-muted-foreground">{result.original_percentage}% original</span>
          {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </div>
      </button>

      {expanded && (
        <div className="border-t border-border p-4 space-y-4">
          <div className="flex items-center gap-6">
            <ScoreRing score={result.plagiarism_score} />
            <div className="flex-1 space-y-2">
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                Most Suspicious Sources
              </p>
              {result.matched_sources.length === 0 ? (
                <p className="text-xs text-muted-foreground">No significant matches found.</p>
              ) : (
                result.matched_sources.map((ms, i) => (
                  <div key={i}>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-muted-foreground truncate pr-4">{ms.source}</span>
                      <span className="font-bold font-mono flex-shrink-0" style={{ color: ms.color }}>{ms.match}%</span>
                    </div>
                    <div className="h-1.5 rounded-full bg-secondary">
                      <div className="h-full rounded-full transition-all duration-700"
                        style={{ width: `${Math.min(ms.match * 3, 100)}%`, backgroundColor: ms.color }} />
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {result.highlighted_segments.filter((s:any) => s.highlight).length > 0 && (
            <div>
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">
                Plagiarised Paragraphs
              </p>
              <div className="space-y-3 max-h-72 overflow-y-auto">
                {result.highlighted_segments.filter((s:any) => s.highlight).map((seg:any, i:number) => (
                  <div key={i} className="rounded-lg border-l-4 border-amber-400 bg-amber-400/10 p-3">
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-xs font-semibold text-amber-500 truncate pr-2">
                        Matched: {seg.source ?? 'Unknown source'}
                      </span>
                      {seg.match_percentage && (
                        <span className="text-xs font-mono font-bold text-amber-500 flex-shrink-0">
                          {seg.match_percentage}%
                        </span>
                      )}
                    </div>
                    <p className="text-sm leading-6 text-foreground/80">{seg.text}</p>
                  </div>
                ))}
              </div>
              <p className="text-xs text-muted-foreground mt-2 flex items-center gap-1">
                <AlertTriangle size={11} /> Only plagiarised paragraphs are shown
              </p>
            </div>
          )}
        </div>
      )}
    </Card>
  )
}

// ── Main page ──────────────────────────────────────────────────────────────────
export default function WorkspaceDetailPage() {
  const { id }   = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  const { workspaces, setWorkspaces } = useWorkspaces()

  const [sources,     setSources]     = useState<Source[]>([])
  const [documents,   setDocuments]   = useState<Document[]>([])
  const [submissions, setSubmissions] = useState<Submission[]>([])
  const [step,        setStep]        = useState(-1)
  const [results,     setResults]     = useState<DocumentResult[] | null>(null)
  const [warning,     setWarning]     = useState('')
  const [downloading, setDownloading] = useState(false)
  const [wsName,      setWsName]      = useState(location.state?.workspace?.name ?? '')
  const [wsStatus,    setWsStatus]    = useState(location.state?.workspace?.status ?? 'draft')
  const [loading,     setLoading]     = useState(true)

  const wsId = Number(id)

  useEffect(() => {
    // Guard against NaN
    if (!id || id === 'undefined' || isNaN(wsId)) {
      setLoading(false)
      return
    }

    // If came from Create Workspace — data is in location.state, no need to fetch
    const navWs = location.state?.workspace
    if (navWs && Number(navWs.id) === wsId) {
      setWsName(navWs.name ?? '')
      setWsStatus(navWs.status ?? 'draft')
      setSources([])
      setDocuments([])
      setSubmissions([])
      setLoading(false)
      return
    }

    // Fetch from API
    setLoading(true)
    workspacesAPI.get(wsId)
      .then(res => {
        const data = res.data
        setWsName(data.name ?? '')
        setWsStatus(data.status ?? 'draft')
        setSources(data.sources ?? [])
        setDocuments(data.documents ?? [])
        setSubmissions(data.submissions ?? [])
      })
      .catch(() => {
        // Fallback to context data
        const ws = workspaces.find(w => w.id === wsId)
        if (ws) { setWsName(ws.name); setWsStatus(ws.status ?? 'draft') }
      })
      .finally(() => setLoading(false))
  }, [wsId])

  // Auto-load last completed result on page entry
  useEffect(() => {
    if (loading || wsId === 0 || results) return
    const lastCompleted = submissions.find((s: any) => s.status === 'completed' && s.document_results?.length > 0)
    if (lastCompleted) setResults(lastCompleted.document_results)
  }, [loading, submissions.length])

  // Redirect if no valid id
  if (!id || id === 'undefined' || isNaN(wsId)) return (
    <div className="text-center py-20">
      <p className="text-muted-foreground mb-4">Workspace not found.</p>
      <Button variant="outline" onClick={() => navigate('/workspaces')}>← Back to Workspaces</Button>
    </div>
  )

  if (loading) return (
    <div className="flex items-center justify-center py-20">
      <div className="w-8 h-8 rounded-full border-4 border-primary/20 border-t-primary animate-spin" />
    </div>
  )

  const validateExt = (files: File[]) =>
    files.every(f => ALLOWED_EXTS.includes(f.name.split('.').pop()?.toLowerCase() || ''))

  const addSources = async (files: File[]) => {
    if (!validateExt(files)) { setWarning('Unsupported type. Allowed: PDF, DOCX, DOC, TXT'); return }
    setWarning('')
    for (const file of files) {
      try { const res = await workspacesAPI.uploadSource(wsId, file); setSources(p => [...p, res.data]) }
      catch (err: any) { setWarning(err.response?.data?.error || 'Failed to upload source') }
    }
  }

  const addDocs = async (files: File[]) => {
    if (!validateExt(files)) { setWarning('Unsupported type. Allowed: PDF, DOCX, DOC, TXT'); return }
    setWarning('')
    for (const file of files) {
      try { const res = await workspacesAPI.uploadDocument(wsId, file); setDocuments(p => [...p, res.data]) }
      catch (err: any) { setWarning(err.response?.data?.error || 'Failed to upload document') }
    }
  }

  const deleteSource = async (srcId: string | number) => {
    try { await workspacesAPI.deleteSource(wsId, srcId); setSources(p => p.filter(s => s.id !== srcId)) }
    catch { setWarning('Failed to delete source') }
  }

  const deleteDocument = async (docId: string | number) => {
    try { await workspacesAPI.deleteDocument(wsId, docId); setDocuments(p => p.filter(d => d.id !== docId)) }
    catch { setWarning('Failed to delete document') }
  }

  const canSubmit = sources.length >= 2 && documents.length >= 1 && step < 0

  // Polling function for result retrieval
  const pollForResults = async () => {
    let attempts = 0
    const maxAttempts = 120
    const pollInterval = 2000

    const poll = async () => {
      try {
        const res = await workspacesAPI.results(wsId)
        if (res.status === 200 && res.data?.document_results) {
          setResults(res.data.document_results)
          setSubmissions(p => [res.data, ...p])
          setWsStatus('analyzed')
          setWorkspaces(prev => prev.map(w =>
            w.id === wsId
              ? { ...w, status: 'analyzed', sources_count: sources.length, documents_count: documents.length }
              : w
          ))
          return
        }
      } catch (err: any) {
        if (err.response?.status === 202) {
          attempts++
          if (attempts < maxAttempts) {
            setTimeout(poll, pollInterval)
            return
          } else {
            setWarning('Analysis is taking longer than expected. Check back later.')
            return
          }
        }
        setWarning('Failed to retrieve results. Please try again.')
      }
    }

    setWarning('')
    poll()
  }

  const handleSubmit = async () => {
    setWarning(''); setStep(0)
    try {
      setStep(0); await new Promise(r => setTimeout(r, 600))
      setStep(1); await new Promise(r => setTimeout(r, 600))
      setStep(2)
      const sourceIds   = sources.map(s => Number(s.id))
      const documentIds = documents.map(d => Number(d.id))
      const res         = await workspacesAPI.submit(wsId, sourceIds, documentIds)
      const submission: Submission = res.data
      setStep(3); await new Promise(r => setTimeout(r, 600))
      setStep(4); await new Promise(r => setTimeout(r, 600))
      
      if (submission.document_results?.length > 0) {
        setStep(-1)
        setResults(submission.document_results)
        setSubmissions(p => [submission, ...p])
        setWsStatus('analyzed')
        setWorkspaces(prev => prev.map(w =>
          w.id === wsId
            ? { ...w, status: 'analyzed', sources_count: sources.length, documents_count: documents.length }
            : w
        ))
      } else {
        setStep(-1)
        pollForResults()
      }
    } catch (err: any) {
      setStep(-1)
      setWarning(err.response?.data?.error || err.response?.data?.detail || 'Submission failed. Please try again.')
    }
  }

  // ── PDF Download using jsPDF ──────────────────────────────────────────────
  const handleDownload = async () => {
    if (!results) return
    setDownloading(true)
    try {
      const { jsPDF } = await import('jspdf')
      const doc   = new jsPDF()
      const pageW = doc.internal.pageSize.getWidth()
      let y = 20

      const addLine = (text: string, size = 11, bold = false, color = '#000000') => {
        if (y > 270) { doc.addPage(); y = 20 }
        doc.setFontSize(size)
        doc.setFont('helvetica', bold ? 'bold' : 'normal')
        doc.setTextColor(color)
        const lines = doc.splitTextToSize(text, pageW - 30)
        doc.text(lines, 15, y)
        y += (size * 0.6) * lines.length
      }
      const gap = (n = 5) => { y += n }

      // Header
      doc.setFillColor(15, 23, 42)
      doc.rect(0, 0, pageW, 30, 'F')
      doc.setFontSize(18); doc.setFont('helvetica', 'bold'); doc.setTextColor('#ffffff')
      doc.text('GPD.AI — Plagiarism Report', 15, 20)
      y = 38

      addLine(`Workspace: ${wsName}`, 11, true)
      addLine(`Generated: ${new Date().toLocaleString()}`, 10, false, '#666666')
      addLine(`Documents analysed: ${results.length}`, 10, false, '#666666')
      gap(8)

      doc.setDrawColor(200, 200, 200); doc.line(15, y, pageW - 15, y); gap(8)

      // One section per document
      results.forEach((r, idx) => {
        addLine(`Document ${idx + 1}: ${r.document_name}`, 13, true)
        gap(2)
        const riskLabel = r.plagiarism_score >= 30 ? 'HIGH RISK' : r.plagiarism_score >= 15 ? 'MEDIUM RISK' : 'LOW RISK'
        const riskColor = r.plagiarism_score >= 30 ? '#ef4444' : r.plagiarism_score >= 15 ? '#f97316' : '#22c55e'
        addLine(`Score: ${r.plagiarism_score}%  |  Original: ${r.original_percentage}%  |  ${riskLabel}`, 11, false, riskColor)
        gap(4)
        addLine('Matched Sources (sorted by similarity):', 10, true)
        gap(2)
        if (r.matched_sources.length === 0) {
          addLine('  No significant matches found.', 10, false, '#666666')
        } else {
          r.matched_sources.forEach((ms, i) => {
            const bar = '█'.repeat(Math.max(1, Math.round(ms.match / 5)))
            addLine(`  ${i + 1}. ${ms.source}  →  ${ms.match}%  ${bar}`, 10)
          })
        }
        gap(6)
        if (idx < results.length - 1) {
          doc.setDrawColor(220, 220, 220); doc.line(15, y, pageW - 15, y); gap(8)
        }
      })

      gap(10)
      doc.setFontSize(9); doc.setTextColor('#aaaaaa')
      doc.text('Generated by GPD.AI — Academic Integrity Platform', 15, y)
      doc.save(`GPD-report-${wsName}.pdf`)
    } catch (e) {
      setWarning('PDF generation failed. Run: npm install jspdf')
    }
    setDownloading(false)
  }

  const worstScore = results ? Math.max(...results.map(r => r.plagiarism_score)) : null

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Header */}
      <div className="flex items-center gap-3 flex-wrap">
        <button onClick={() => navigate('/workspaces')}
          className="text-xs flex items-center gap-1 text-muted-foreground hover:text-foreground">
          <ChevronLeft size={14} /> Workspaces
        </button>
        <div className="w-px h-4 bg-border" />
        <h2 className="text-lg font-bold">{wsName || 'Workspace'}</h2>
        <Badge variant={wsStatus === 'analyzed' ? 'success' : wsStatus === 'pending' ? 'warning' : 'default'}>
          {wsStatus}
        </Badge>
      </div>

      {/* Previous submissions */}
      {submissions.length > 0 && !results && step < 0 && (
        <Card className="p-4">
          <h3 className="font-semibold text-sm mb-3">Previous Submissions</h3>
          <div className="space-y-2">
            {submissions.map(sub => {
              const worst = sub.document_results?.length
                ? Math.max(...sub.document_results.map(r => r.plagiarism_score))
                : null
              return (
                <div key={sub.id} className="flex items-center justify-between p-3 rounded-lg bg-secondary/50">
                  <div>
                    <p className="text-xs font-medium">{sub.date?.split('T')[0]}</p>
                    <p className="text-xs text-muted-foreground">{sub.documents?.length ?? 0} doc(s) · {sub.status}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    {worst !== null && (
                      <span className={`text-sm font-bold font-mono ${scoreColor(worst)}`}>↑{worst}%</span>
                    )}
                    {sub.document_results?.length > 0 && (
                      <Button size="sm" variant="outline" onClick={() => setResults(sub.document_results)}>
                        View Results
                      </Button>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </Card>
      )}

      {/* Results view */}
      {results && (
        <div className="space-y-4">
          <Card className="p-4">
            <div className="flex items-center justify-between flex-wrap gap-3">
              <div className="flex items-center gap-3">
                <CheckCircle size={18} className="text-emerald-400" />
                <div>
                  <p className="font-semibold">Analysis Complete</p>
                  <p className="text-xs text-muted-foreground">
                    {results.length} document{results.length !== 1 ? 's' : ''} analysed ·{' '}
                    highest: <span className={`font-bold font-mono ${scoreColor(worstScore ?? 0)}`}>{worstScore}%</span>
                  </p>
                </div>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={handleDownload} disabled={downloading}>
                  <Download size={13} /> {downloading ? 'Generating PDF…' : 'Download PDF'}
                </Button>
                <Button variant="outline" size="sm" onClick={() => setResults(null)}>← Back to Files</Button>
              </div>
            </div>
          </Card>
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide px-1">
            Results — click a document to expand
          </p>
          {results.map(r => <DocumentResultCard key={r.document_id} result={r} />)}
        </div>
      )}

      {/* Loading */}
      {step >= 0 && (
        <Card className="p-10">
          <div className="flex flex-col items-center gap-5 text-center">
            <div className="w-14 h-14 rounded-full border-4 border-primary/20 border-t-primary animate-spin" />
            <div>
              <p className="font-semibold">{STEPS[step]}</p>
              <p className="text-xs text-muted-foreground mt-1">Step {step + 1} of {STEPS.length}</p>
            </div>
            <div className="flex gap-2">
              {STEPS.map((_, i) => (
                <div key={i} className={`h-1.5 rounded-full transition-all duration-500 ${i <= step ? 'bg-primary w-10' : 'bg-secondary w-5'}`} />
              ))}
            </div>
          </div>
        </Card>
      )}

      {/* Analyzing (Polling) */}
      {step < 0 && warning === '' && !results && submissions.length > 0 && (
        <Card className="p-10">
          <div className="flex flex-col items-center gap-5 text-center">
            <div className="w-14 h-14 rounded-full border-4 border-primary/20 border-t-primary animate-spin" />
            <div>
              <p className="font-semibold">Analyzing Documents…</p>
              <p className="text-xs text-muted-foreground mt-1">This may take up to 4 minutes. Please don't close this window.</p>
            </div>
          </div>
        </Card>
      )}

      {/* File upload + submit */}
      {!results && step < 0 && (
        <>
          {warning && <Alert variant="warning">{warning}</Alert>}
          <div className="grid lg:grid-cols-2 gap-5">
            <Card className="p-5">
              <div className="flex items-center justify-between mb-1">
                <h3 className="font-semibold text-sm">Sources</h3>
                <span className="text-xs text-muted-foreground">
                  {sources.length} files {sources.length < 2 && <span className="text-amber-500">(min 2)</span>}
                </span>
              </div>
              <p className="text-xs text-muted-foreground mb-3">Reference files to compare against</p>
              <div className="space-y-2 mb-3 max-h-52 overflow-y-auto">
                {sources.map(s => <FileRow key={s.id} {...s} onDelete={() => deleteSource(s.id)} />)}
              </div>
              <DropZone onFiles={addSources} label="Add sources (PDF, DOCX, TXT)" />
            </Card>
            <Card className="p-5">
              <div className="flex items-center justify-between mb-1">
                <h3 className="font-semibold text-sm">Documents to Check</h3>
                <span className="text-xs text-muted-foreground">{documents.length} files</span>
              </div>
              <p className="text-xs text-muted-foreground mb-3">Each document gets its own plagiarism score</p>
              <div className="space-y-2 mb-3 max-h-52 overflow-y-auto">
                {documents.map(d => <FileRow key={d.id} {...d} onDelete={() => deleteDocument(d.id)} />)}
              </div>
              <DropZone onFiles={addDocs} label="Add documents (PDF, DOCX, TXT)" />
            </Card>
          </div>
          <Card className="p-4">
            <div className="flex items-center justify-between gap-4 flex-wrap">
              <div>
                <p className="text-sm font-semibold">{canSubmit ? 'Ready to Analyze' : 'Setup Required'}</p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {canSubmit
                    ? `${sources.length} sources · ${documents.length} document${documents.length !== 1 ? 's' : ''}`
                    : `Add ${Math.max(0, 2 - sources.length)} more source(s) and at least 1 document`}
                </p>
              </div>
              <Button onClick={handleSubmit} disabled={!canSubmit} size="lg">
                <Send size={15} /> Submit for Analysis
              </Button>
            </div>
          </Card>
        </>
      )}
    </div>
  )
}
