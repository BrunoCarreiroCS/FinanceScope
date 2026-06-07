-- FinanceScope - schema inicial (MVP)
-- Padroes: type aceita apenas 'income' ou 'expense'; valores monetarios sempre positivos.

DROP TABLE IF EXISTS purchase_simulations;
DROP TABLE IF EXISTS goals;
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    monthly_income REAL NOT NULL DEFAULT 0,
    monthly_hours REAL NOT NULL DEFAULT 0,
    monthly_limit REAL NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('income', 'expense')),
    color TEXT NOT NULL DEFAULT '#22c55e',
    is_default INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('income', 'expense')),
    description TEXT NOT NULL,
    category_id INTEGER,
    amount REAL NOT NULL CHECK (amount > 0),
    date DATE NOT NULL,
    payment_method TEXT,
    is_recurring INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

CREATE TABLE goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    target_amount REAL NOT NULL CHECK (target_amount > 0),
    current_amount REAL NOT NULL DEFAULT 0 CHECK (current_amount >= 0),
    monthly_contribution REAL NOT NULL DEFAULT 0 CHECK (monthly_contribution >= 0),
    priority INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE purchase_simulations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    item_name TEXT NOT NULL,
    amount REAL NOT NULL CHECK (amount > 0),
    category_id INTEGER,
    installments INTEGER NOT NULL DEFAULT 1,
    risk_level TEXT NOT NULL CHECK (risk_level IN ('baixo', 'medio', 'alto')),
    result_json TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

-- Seed: categorias padrao (globais, compartilhadas por todos os usuarios).
-- Usuarios sao criados via cadastro (/registro).
INSERT INTO categories (name, type, color, is_default) VALUES
    ('Salário',        'income',  '#22c55e', 1),
    ('Freelance',      'income',  '#10b981', 1),
    ('Outras receitas','income',  '#14b8a6', 1),
    ('Alimentação',    'expense', '#ef4444', 1),
    ('Moradia',        'expense', '#f97316', 1),
    ('Transporte',     'expense', '#eab308', 1),
    ('Lazer',          'expense', '#a855f7', 1),
    ('Saúde',          'expense', '#06b6d4', 1),
    ('Educação',       'expense', '#3b82f6', 1),
    ('Assinaturas',    'expense', '#ec4899', 1),
    ('Outros',         'expense', '#64748b', 1);
