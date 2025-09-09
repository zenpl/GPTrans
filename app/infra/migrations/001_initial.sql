-- Initial database schema for GPTrans

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Books table
CREATE TABLE books (
    id SERIAL PRIMARY KEY,
    title VARCHAR NOT NULL,
    source_lang VARCHAR(10) NOT NULL,
    target_lang VARCHAR(10) NOT NULL DEFAULT 'zh-CN',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    glossary_id INTEGER
);

-- Pages table
CREATE TABLE pages (
    id SERIAL PRIMARY KEY,
    book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    index INTEGER NOT NULL,
    image_url VARCHAR NOT NULL,
    width INTEGER NOT NULL,
    height INTEGER NOT NULL,
    dpi INTEGER DEFAULT 300
);

-- Blocks table
CREATE TABLE blocks (
    id SERIAL PRIMARY KEY,
    page_id INTEGER NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
    type VARCHAR(20) NOT NULL,
    bbox_x FLOAT NOT NULL,
    bbox_y FLOAT NOT NULL,
    bbox_w FLOAT NOT NULL,
    bbox_h FLOAT NOT NULL,
    "order" INTEGER NOT NULL,
    text_source TEXT NOT NULL,
    text_translated TEXT,
    spans JSONB DEFAULT '[]',
    refs JSONB DEFAULT '[]',
    status VARCHAR(20) DEFAULT 'pending'
);

-- Glossaries table
CREATE TABLE glossaries (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Glossary terms table
CREATE TABLE glossary_terms (
    id SERIAL PRIMARY KEY,
    glossary_id INTEGER NOT NULL REFERENCES glossaries(id) ON DELETE CASCADE,
    src VARCHAR NOT NULL,
    tgt VARCHAR NOT NULL,
    case_sensitive BOOLEAN DEFAULT FALSE,
    notes TEXT
);

-- Jobs table
CREATE TABLE jobs (
    id SERIAL PRIMARY KEY,
    book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    type VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    logs TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    finished_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Exports table
CREATE TABLE exports (
    id SERIAL PRIMARY KEY,
    book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    formats JSONB NOT NULL,
    url VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_pages_book_id ON pages(book_id);
CREATE INDEX idx_blocks_page_id ON blocks(page_id);
CREATE INDEX idx_blocks_order ON blocks("order");
CREATE INDEX idx_glossary_terms_glossary_id ON glossary_terms(glossary_id);
CREATE INDEX idx_jobs_book_id ON jobs(book_id);
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_exports_book_id ON exports(book_id);

-- Foreign key constraint for glossary reference
ALTER TABLE books ADD CONSTRAINT fk_books_glossary 
    FOREIGN KEY (glossary_id) REFERENCES glossaries(id);

-- Insert sample glossary
INSERT INTO glossaries (name, description) VALUES 
('Typography Terms', 'German/Swedish to Chinese typography terminology');

-- Insert sample glossary terms
INSERT INTO glossary_terms (glossary_id, src, tgt, case_sensitive, notes) VALUES
(1, 'Typografie', '字体排印学', false, 'Typography as a field of study'),
(1, 'Schrift', '字体', false, 'Font or typeface'),
(1, 'Serifen', '衬线', false, 'Serifs in typography'),
(1, 'serifenlos', '无衬线', false, 'Sans-serif'),
(1, 'Renaissance', '文艺复兴', true, 'Historical period'),
(1, 'Bauhaus', '包豪斯', true, 'Design movement');