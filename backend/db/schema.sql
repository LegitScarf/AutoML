CREATE TABLE IF NOT EXISTS runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    dataset_name VARCHAR(255) NOT NULL,
    target_variable VARCHAR(255) NOT NULL,
    task_type VARCHAR(50) NOT NULL,
    selected_model VARCHAR(100),
    min_threshold FLOAT,
    status VARCHAR(50) DEFAULT 'pending', -- pending, profiling, generating, training, complete, failed
    metrics JSONB DEFAULT '{}'::jsonb,
    logs TEXT[] DEFAULT ARRAY[]::text[],
    bundle_url VARCHAR(512)
);
