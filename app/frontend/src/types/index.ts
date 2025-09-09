export interface Book {
  id: number;
  title: string;
  source_lang: string;
  target_lang: string;
  created_at: string;
  glossary_id?: number;
}

export interface Page {
  id: number;
  book_id: number;
  index: number;
  image_url: string;
  width: number;
  height: number;
  dpi: number;
}

export interface Block {
  id: number;
  page_id: number;
  type: 'heading' | 'paragraph' | 'caption' | 'footnote' | 'figure' | 'page-number';
  bbox_x: number;
  bbox_y: number;
  bbox_w: number;
  bbox_h: number;
  order: number;
  text_source: string;
  text_translated?: string;
  spans: any[];
  refs: string[];
  status: 'pending' | 'translating' | 'translated' | 'typeset';
}

export interface Glossary {
  id: number;
  name: string;
  description?: string;
  terms: GlossaryTerm[];
}

export interface GlossaryTerm {
  id: number;
  glossary_id: number;
  src: string;
  tgt: string;
  case_sensitive: boolean;
  notes?: string;
}

export interface Job {
  id: number;
  book_id: number;
  type: 'ocr' | 'translate' | 'typeset' | 'export';
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  logs?: string;
  started_at?: string;
  finished_at?: string;
}

export interface UploadResponse {
  book: Book;
}

export interface TranslationRequest {
  glossary_id?: number;
  style?: string;
  length_hint?: 'normal' | 'concise';
}

export interface ExportRequest {
  formats: string[];
}