export interface User {
  id: number; name: string; email: string;
  role: 'user' | 'admin'; plan: string;
  status: 'active' | 'inactive'; date_joined: string;
}

export interface Source   { id: string | number; name: string; size: string; ext: string }
export interface Document { id: string | number; name: string; size: string; ext: string }

export interface MatchedSource {
  source: string        // source filename
  match:  number        // match percentage
  color:  string        // '#ef4444' | '#f97316' | '#eab308' | '#22c55e'
}

export interface HighlightSegment {
  text:      string
  highlight: boolean
  source?:   string
}

/** One document's plagiarism result */
export interface DocumentResult {
  id:                  number
  document_id:         number
  document_name:       string
  plagiarism_score:    number        // 0-100
  original_percentage: number        // 0-100
  matched_sources:     MatchedSource[]  // sorted most suspicious first
  highlighted_segments: HighlightSegment[]
  created_at:          string
}

/** Full result for a submission — one DocumentResult per submitted document */
export interface SubmissionResult {
  submission_id:    number
  status:           string
  document_results: DocumentResult[]
}

export interface Submission {
  id:              number
  date:            string
  status:          string
  sources:         Source[]
  documents:       Document[]
  document_results: DocumentResult[]
}

export interface Workspace {
  id:              number
  name:            string
  created_at:      string
  status:          string
  sources_count:   number
  documents_count: number
  submissions:     Submission[]
}

export interface Plan {
  id: number; name: string; price: number;
  checks_per_month: number; max_sources: number; max_documents: number;
}
