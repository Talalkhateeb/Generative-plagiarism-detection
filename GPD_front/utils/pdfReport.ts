import type { DocumentResult } from '@/types'

export async function downloadPDFReport(
  wsName: string,
  results: DocumentResult[]
): Promise<void> {
  const { jsPDF } = await import('jspdf')
  const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' })
  const W = 210
  const M = 18       // left/right margin
  const usable = W - M * 2
  let y = 0

  // ── helpers ────────────────────────────────────────────────────────────
  const checkPage = (needed = 10) => {
    if (y + needed > 280) { doc.addPage(); y = 18 }
  }

  const setColor = (hex: string) => {
    const r = parseInt(hex.slice(1, 3), 16)
    const g = parseInt(hex.slice(3, 5), 16)
    const b = parseInt(hex.slice(5, 7), 16)
    doc.setTextColor(r, g, b)
  }

  const setFill = (hex: string) => {
    const r = parseInt(hex.slice(1, 3), 16)
    const g = parseInt(hex.slice(3, 5), 16)
    const b = parseInt(hex.slice(5, 7), 16)
    doc.setFillColor(r, g, b)
  }

  // ── cover header ────────────────────────────────────────────────────────
  // Teal background bar
  doc.setFillColor(6, 182, 212)
  doc.rect(0, 0, W, 38, 'F')

  doc.setTextColor(255, 255, 255)
  doc.setFontSize(22); doc.setFont('helvetica', 'bold')
  doc.text('GPDetect', M, 16)

  doc.setFontSize(10); doc.setFont('helvetica', 'normal')
  doc.text('Generative Plagiarism Detection — Analysis Report', M, 24)

  doc.setFontSize(8)
  doc.text(`Generated: ${new Date().toLocaleString()}`, W - M, 24, { align: 'right' })
  doc.text(`Workspace: ${wsName}`, W - M, 30, { align: 'right' })

  y = 48

  // ── summary banner ──────────────────────────────────────────────────────
  const worstScore = Math.max(...results.map(r => r.plagiarism_score))
  const avgScore   = Math.round(results.reduce((s, r) => s + r.plagiarism_score, 0) / results.length)

  // Light grey background
  doc.setFillColor(248, 250, 252)
  doc.roundedRect(M, y, usable, 22, 2, 2, 'F')
  doc.setDrawColor(226, 232, 240)
  doc.roundedRect(M, y, usable, 22, 2, 2, 'S')

  doc.setFontSize(9); doc.setTextColor(100, 116, 139)
  doc.setFont('helvetica', 'normal')
  doc.text('Documents analysed', M + 6, y + 8)
  doc.text('Average score', M + 55, y + 8)
  doc.text('Highest score', M + 105, y + 8)

  doc.setFontSize(14); doc.setFont('helvetica', 'bold'); doc.setTextColor(30, 41, 59)
  doc.text(`${results.length}`, M + 6, y + 18)
  colorScore(avgScore)
  doc.text(`${avgScore}%`, M + 55, y + 18)
  colorScore(worstScore)
  doc.text(`${worstScore}%`, M + 105, y + 18)

  y += 30

  // ── per-document sections ───────────────────────────────────────────────
  results.forEach((r, idx) => {
    checkPage(55)

    // Section header
    doc.setFillColor(241, 245, 249)
    doc.rect(M, y, usable, 8, 'F')
    doc.setFontSize(10); doc.setFont('helvetica', 'bold'); doc.setTextColor(30, 41, 59)
    doc.text(`${idx + 1}. ${r.document_name}`, M + 3, y + 5.5)
    y += 12

    // Score pill + risk label
    const sc = r.plagiarism_score
    const pillColor = sc >= 30 ? '#ef4444' : sc >= 15 ? '#f97316' : '#22c55e'
    const risk      = sc >= 30 ? 'HIGH RISK' : sc >= 15 ? 'MEDIUM RISK' : 'LOW RISK'

    setFill(pillColor)
    doc.roundedRect(M, y, 32, 12, 2, 2, 'F')
    doc.setTextColor(255, 255, 255)
    doc.setFontSize(13); doc.setFont('helvetica', 'bold')
    doc.text(`${sc}%`, M + 16, y + 8.5, { align: 'center' })

    doc.setFillColor(240, 253, 250)
    doc.roundedRect(M + 36, y, 38, 12, 2, 2, 'F')
    setColor('#065f46')
    doc.setFontSize(8); doc.setFont('helvetica', 'normal')
    doc.text(`${r.original_percentage}% original`, M + 55, y + 5)
    doc.setFont('helvetica', 'bold')
    doc.text(risk, M + 55, y + 10)

    y += 18

    // Matched sources table
    if (r.matched_sources.length > 0) {
      checkPage(8 + r.matched_sources.length * 10)

      doc.setFontSize(8); doc.setFont('helvetica', 'bold'); doc.setTextColor(71, 85, 105)
      doc.text('MATCHED SOURCES', M, y); y += 5

      r.matched_sources.forEach(ms => {
        checkPage(10)

        // Source name
        doc.setFontSize(8.5); doc.setFont('helvetica', 'normal'); doc.setTextColor(51, 65, 85)
        const nameLines = doc.splitTextToSize(ms.source, usable - 22)
        doc.text(nameLines, M, y + 3)

        // Match % right-aligned
        doc.setFont('helvetica', 'bold')
        setColor(ms.color)
        doc.text(`${ms.match}%`, W - M, y + 3, { align: 'right' })

        // Progress bar track
        doc.setFillColor(226, 232, 240)
        doc.roundedRect(M, y + 5, usable, 2.5, 1, 1, 'F')

        // Progress bar fill — cap at 100% of usable width
        const barW = Math.min((ms.match / 100) * usable, usable)
        setFill(ms.color)
        doc.roundedRect(M, y + 5, barW, 2.5, 1, 1, 'F')

        y += nameLines.length * 4 + 6
      })
    } else {
      doc.setFontSize(8.5); doc.setFont('helvetica', 'italic'); doc.setTextColor(148, 163, 184)
      doc.text('No significant matches found.', M, y); y += 6
    }

    // Highlighted segments (plagiarised spans only)
    const flagged = r.highlighted_segments?.filter((s: any) => s.highlight) ?? []
    if (flagged.length > 0) {
      checkPage(12)
      y += 3
      doc.setFontSize(8); doc.setFont('helvetica', 'bold'); doc.setTextColor(71, 85, 105)
      doc.text('FLAGGED PASSAGES', M, y); y += 5

      flagged.slice(0, 4).forEach((seg: any) => {   // cap at 4 to avoid huge reports
        const lines = doc.splitTextToSize(`"${seg.text}"`, usable - 4)
        checkPage(lines.length * 4 + 8)

        doc.setFillColor(254, 243, 199)
        doc.rect(M, y - 1, usable, lines.length * 4 + 4, 'F')
        doc.setDrawColor(251, 191, 36)
        doc.line(M, y - 1, M, y + lines.length * 4 + 3)

        doc.setFontSize(7.5); doc.setFont('helvetica', 'italic'); doc.setTextColor(120, 53, 15)
        doc.text(lines, M + 3, y + 3)

        if (seg.source) {
          y += lines.length * 4 + 5
          checkPage(5)
          doc.setFontSize(7); doc.setFont('helvetica', 'normal'); doc.setTextColor(161, 98, 7)
          doc.text(`↳ Source: ${seg.source}`, M + 3, y)
        }
        y += 7
      })

      if (flagged.length > 4) {
        doc.setFontSize(7.5); doc.setFont('helvetica', 'normal'); doc.setTextColor(148, 163, 184)
        doc.text(`... and ${flagged.length - 4} more flagged passages.`, M, y); y += 6
      }
    }

    // Divider between documents
    if (idx < results.length - 1) {
      checkPage(10)
      y += 4
      doc.setDrawColor(226, 232, 240)
      doc.line(M, y, W - M, y)
      y += 8
    }
  })

  // ── footer on every page ────────────────────────────────────────────────
  const totalPages = doc.getNumberOfPages()
  for (let p = 1; p <= totalPages; p++) {
    doc.setPage(p)
    doc.setFillColor(248, 250, 252)
    doc.rect(0, 287, W, 12, 'F')
    doc.setTextColor(148, 163, 184)
    doc.setFontSize(7.5); doc.setFont('helvetica', 'normal')
    doc.text('GPDetect — Generative Plagiarism Detection', M, 293)
    doc.text(`Page ${p} of ${totalPages}`, W - M, 293, { align: 'right' })
  }

  doc.save(`GPDetect-report-${wsName.replace(/\s+/g, '-')}.pdf`)

  // ── local helper (needs closure over doc) ──────────────────────────────
  function colorScore(score: number) {
    if (score >= 30) doc.setTextColor(239, 68, 68)
    else if (score >= 15) doc.setTextColor(249, 115, 22)
    else doc.setTextColor(34, 197, 94)
  }
}