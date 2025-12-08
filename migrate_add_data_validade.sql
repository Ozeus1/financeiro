-- Migração: Adicionar campo data_validade na tabela users
-- Data: 2025-12-08
-- Descrição: Permite que admin defina data de validade para acesso de usuários normais

-- Adicionar coluna data_validade (pode ser NULL)
ALTER TABLE users ADD COLUMN IF NOT EXISTS data_validade DATE;

-- Comentário na coluna
COMMENT ON COLUMN users.data_validade IS 'Data de validade do acesso (apenas para usuários normais). NULL = sem validade';

-- Admin nunca tem data de validade (garantir que seja NULL)
UPDATE users SET data_validade = NULL WHERE nivel_acesso = 'admin';

-- Verificar resultado
SELECT id, username, nivel_acesso, ativo, data_validade
FROM users
ORDER BY id;
