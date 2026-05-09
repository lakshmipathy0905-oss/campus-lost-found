-- SQL to set up the 'items' table in Supabase

CREATE TABLE items (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    location TEXT NOT NULL,
    type TEXT CHECK (type IN ('lost', 'found')) NOT NULL,
    contact TEXT,
    category TEXT,
    resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable Row Level Security (RLS)
ALTER TABLE items ENABLE ROW LEVEL SECURITY;

-- Create policy to allow anyone to read items
CREATE POLICY "Allow public read" ON items FOR SELECT USING (true);

-- Create policy to allow anyone to insert items (for this simple demo)
CREATE POLICY "Allow public insert" ON items FOR INSERT WITH CHECK (true);

-- Create policy to allow anyone to update items (for this simple demo)
CREATE POLICY "Allow public update" ON items FOR UPDATE USING (true);
