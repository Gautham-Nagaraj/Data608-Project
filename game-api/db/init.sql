-- Optional: insert initial data or create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Insert initial stock data
INSERT INTO stocks (symbol, company_name, sector, category) VALUES
-- Popular stocks
('AAPL', 'Apple Inc.', 'Technology', 'popular'),
('MSFT', 'Microsoft Corporation', 'Technology', 'popular'),
('GOOGL', 'Alphabet Inc.', 'Technology', 'popular'),
('AMZN', 'Amazon.com Inc.', 'Consumer Discretionary', 'popular'),
('META', 'Meta Platforms Inc.', 'Technology', 'popular'),

-- Volatile stocks
('TSLA', 'Tesla Inc.', 'Consumer Discretionary', 'volatile'),
('GME', 'GameStop Corp.', 'Consumer Discretionary', 'volatile'),
('AMC', 'AMC Entertainment Holdings Inc.', 'Consumer Discretionary', 'volatile'),
('NVDA', 'NVIDIA Corporation', 'Technology', 'volatile'),
('PLTR', 'Palantir Technologies Inc.', 'Technology', 'volatile'),

-- Sector-specific stocks
('JPM', 'JPMorgan Chase & Co.', 'Financial Services', 'sector'),
('JNJ', 'Johnson & Johnson', 'Healthcare', 'sector'),
('PG', 'Procter & Gamble Co.', 'Consumer Staples', 'sector'),
('KO', 'The Coca-Cola Company', 'Consumer Staples', 'sector'),
('XOM', 'Exxon Mobil Corporation', 'Energy', 'sector')
ON CONFLICT (symbol) DO NOTHING;
