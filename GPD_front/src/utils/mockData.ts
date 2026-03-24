import type { Workspace, Plan, User } from '@/types'

// Only pre-existing demo accounts have workspaces
// New registered users start with an empty workspace list
export const MOCK_WORKSPACES_BY_USER: Record<number, Workspace[]> = {
  // user id=2 (Jordan Lee — user@veritas.ai) has sample workspaces
  2: [
    {
      id: 1, name: 'Research Paper Q1', created_at: '2026-02-10',
      status: 'analyzed', sources_count: 4, documents_count: 2,
      submissions: [{
        id: 101, date: '2026-02-15', score: 12, status: 'completed',
        sources: [
          { id: 's1', name: 'source_ref1.pdf', size: '1.2 MB', ext: 'PDF' },
          { id: 's2', name: 'journal_2021.pdf', size: '980 KB', ext: 'PDF' },
          { id: 's3', name: 'textbook_ch3.docx', size: '540 KB', ext: 'DOCX' },
          { id: 's4', name: 'ieee_paper.pdf', size: '760 KB', ext: 'PDF' },
        ],
        documents: [
          { id: 'd1', name: 'my_paper_draft.pdf', size: '890 KB', ext: 'PDF' },
          { id: 'd2', name: 'intro_section.docx', size: '210 KB', ext: 'DOCX' },
        ],
        result: {
          overall_score: 12, original_percentage: 88,
          breakdown: [
            { source: 'Smith, J. (2021) — Nature Journal', match: 8, color: '#f97316' },
            { source: 'Wikipedia — Quantum Computing', match: 3, color: '#eab308' },
            { source: 'Chen et al. (2023) — IEEE', match: 1, color: '#22c55e' },
          ],
          highlighted_segments: [
            { text: 'The fundamental principles of quantum mechanics ', highlight: false },
            { text: 'suggest that particles can exist in multiple states simultaneously', highlight: true, source: 'Smith, J. (2021)' },
            { text: ', a phenomenon known as superposition. This ', highlight: false },
            { text: 'has profound implications for computing architectures', highlight: true, source: 'Chen et al. (2023)' },
            { text: ' as we move into the next decade of technological advancement.', highlight: false },
          ],
        }
      }]
    },
    {
      id: 2, name: 'Thesis Chapter 3', created_at: '2026-03-01',
      status: 'pending', sources_count: 2, documents_count: 1,
      submissions: [{
        id: 102, date: '2026-03-05', score: 27, status: 'completed',
        sources: [
          { id: 's1', name: 'ref_book.pdf', size: '2.1 MB', ext: 'PDF' },
          { id: 's2', name: 'article_2022.pdf', size: '670 KB', ext: 'PDF' },
        ],
        documents: [{ id: 'd1', name: 'chapter3_draft.docx', size: '450 KB', ext: 'DOCX' }],
        result: {
          overall_score: 27, original_percentage: 73,
          breakdown: [
            { source: 'Brown, A. (2022) — Cambridge Press', match: 15, color: '#ef4444' },
            { source: 'Davis et al. (2020) — Springer', match: 12, color: '#f97316' },
          ],
          highlighted_segments: [
            { text: 'The theoretical framework established by ', highlight: false },
            { text: 'Brown demonstrates a clear correlation between variables', highlight: true, source: 'Brown, A. (2022)' },
            { text: '. Further analysis confirms these findings.', highlight: false },
          ],
        }
      }]
    },
  ]
}

export const MOCK_PLANS: Plan[] = [
  { id: 1, name: 'Starter',    price: 9,  checks: 10, max_sources: 5,  max_docs: 3,  allowed_formats: ['pdf','txt'] },
  { id: 2, name: 'Pro',        price: 29, checks: 50, max_sources: 20, max_docs: 10, allowed_formats: ['pdf','docx','txt'] },
  { id: 3, name: 'Enterprise', price: 99, checks: -1, max_sources: -1, max_docs: -1, allowed_formats: ['pdf','docx','txt','doc'] },
]

export const MOCK_ACCOUNTS: (User & { password: string })[] = [
  { id: 1, name: 'Alex Morgan', email: 'admin@veritas.ai', password: 'admin123', role: 'admin', plan: 'Enterprise', status: 'active',   date_joined: '2025-01-15' },
  { id: 2, name: 'Jordan Lee',  email: 'user@veritas.ai',  password: 'user123',  role: 'user',  plan: 'Pro',        status: 'active',   date_joined: '2025-06-20' },
  { id: 3, name: 'Sam Rivera',  email: 'sam@veritas.ai',   password: 'sam123',   role: 'user',  plan: 'Starter',    status: 'inactive', date_joined: '2026-01-10' },
]
