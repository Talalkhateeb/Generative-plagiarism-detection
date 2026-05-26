import type { AnalysisResult, Workspace } from '@/types'

export async function downloadPDFReport(result: AnalysisResult, workspace: Workspace) {
  // Dynamic import to keep bundle small
  const { jsPDF } = await import('jspdf')
  const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' })
  const W = 210, margin = 20, lineH = 7

  // ── Header ──────────────────────────────────────────────────
  doc.setFillColor(6, 182, 212)          // cyan
  doc.rect(0, 0, W, 35, 'F')
  doc.setTextColor(255, 255, 255)
  doc.setFontSize(22); doc.setFont('helvetica', 'bold')
  doc.text('GPDetect', margin, 18)
  doc.setFontSize(10); doc.setFont('helvetica', 'normal')
  doc.text('Academic Integrity — Plagiarism Report', margin, 27)

  // Date top-right
  doc.setFontSize(9)
  doc.text(`Generated: ${new Date().toLocaleString()}`, W - margin, 27, { align: 'right' })

  let y = 50
  doc.setTextColor(30, 41, 59)

  // ── Workspace Info ──────────────────────────────────────────
  doc.setFontSize(13); doc.setFont('helvetica', 'bold')
  doc.text('Workspace', margin, y); y += lineH
  doc.setFontSize(10); doc.setFont('helvetica', 'normal')
  doc.text(`Name: ${workspace.name}`, margin, y); y += lineH
  doc.text(`Date: ${new Date().toLocaleDateString()}`, margin, y); y += lineH * 1.5

  // ── Score Summary ──────────────────────────────────────────
  doc.setFontSize(13); doc.setFont('helvetica', 'bold')
  doc.text('Plagiarism Score Summary', margin, y); y += lineH

  // Score box
  const score = result.overall_score
  const scoreColor: [number,number,number] = score < 15 ? [34,197,94] : score < 30 ? [234,179,8] : [239,68,68]
  doc.setFillColor(...scoreColor)
  doc.roundedRect(margin, y, 50, 20, 3, 3, 'F')
  doc.setTextColor(255, 255, 255)
  doc.setFontSize(18); doc.setFont('helvetica', 'bold')
  doc.text(`${score}%`, margin + 25, y + 13, { align: 'center' })
  doc.setFontSize(9); doc.setFont('helvetica', 'normal')
  doc.text('Plagiarism', margin + 25, y + 18, { align: 'center' })

  doc.setFillColor(34, 197, 94)
  doc.roundedRect(margin + 55, y, 50, 20, 3, 3, 'F')
  doc.setFontSize(18); doc.setFont('helvetica', 'bold')
  doc.text(`${result.original_percentage}%`, margin + 80, y + 13, { align: 'center' })
  doc.setFontSize(9); doc.setFont('helvetica', 'normal')
  doc.text('Original', margin + 80, y + 18, { align: 'center' })
  doc.setTextColor(30, 41, 59)
  y += 30

  // ── Source Breakdown ──────────────────────────────────────
  doc.setFontSize(13); doc.setFont('helvetica', 'bold')
  doc.text('Matched Sources', margin, y); y += lineH

  result.breakdown.forEach(b => {
    if (y > 260) { doc.addPage(); y = margin }
    doc.setFontSize(9); doc.setFont('helvetica', 'normal')
    doc.text(`• ${b.source}`, margin, y)
    doc.setFont('helvetica', 'bold')
    doc.text(`${b.match}%`, W - margin, y, { align: 'right' })
    doc.setFont('helvetica', 'normal')
    // Progress bar
    doc.setFillColor(226, 232, 240)
    doc.rect(margin, y + 2, W - margin * 2, 2, 'F')
    const hex = b.color.replace('#', '')
    const r = parseInt(hex.slice(0,2),16), g = parseInt(hex.slice(2,4),16), bl = parseInt(hex.slice(4,6),16)
    doc.setFillColor(r, g, bl)
    doc.rect(margin, y + 2, Math.min(b.match * 4, W - margin * 2), 2, 'F')
    y += lineH * 1.5
  })

  y += 5
  // ── Highlighted Text ─────────────────────────────────────
  if (y > 240) { doc.addPage(); y = margin }
  doc.setFontSize(13); doc.setFont('helvetica', 'bold')
  doc.text('Content Analysis', margin, y); y += lineH

  result.highlighted_segments.forEach(seg => {
    if (y > 270) { doc.addPage(); y = margin }
    const lines = doc.splitTextToSize(seg.text, W - margin * 2)
    if (seg.highlight) {
      doc.setFillColor(254, 243, 199)
      doc.rect(margin - 1, y - 4, W - margin * 2 + 2, lines.length * lineH, 'F')
      doc.setTextColor(146, 64, 14)
      doc.setFont('helvetica', 'bolditalic')
    } else {
      doc.setTextColor(51, 65, 85)
      doc.setFont('helvetica', 'normal')
    }
    doc.setFontSize(9)
    doc.text(lines, margin, y)
    y += lines.length * lineH
  })

  // ── Footer ────────────────────────────────────────────────
  const pages = doc.getNumberOfPages()
  for (let i = 1; i <= pages; i++) {
    doc.setPage(i)
    doc.setFillColor(248, 250, 252)
    doc.rect(0, 285, W, 15, 'F')
    doc.setTextColor(148, 163, 184)
    doc.setFontSize(8); doc.setFont('helvetica', 'normal')
    doc.text('GPDetect Academic Integrity Platform', margin, 292)
    doc.text(`Page ${i} of ${pages}`, W - margin, 292, { align: 'right' })
  }

  doc.save(`GPDetect-report-${workspace.name.replace(/\s+/g, '-')}.pdf`)
}
