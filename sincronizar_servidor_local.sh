#!/bin/bash

# Script para sincronizar alterações do Servidor → Local → GitHub → Servidor
# Uso: Execute este script NO SERVIDOR VPS

echo "=========================================="
echo "🔄 Sincronização: Servidor → GitHub → Local"
echo "=========================================="
echo ""

# Configurações
REPO_DIR="/var/www/financeiro"
BRANCH="main"

# 1. Verificar se estamos no diretório correto
if [ ! -d "$REPO_DIR/.git" ]; then
    echo "❌ Erro: $REPO_DIR não é um repositório Git"
    exit 1
fi

cd "$REPO_DIR" || exit 1

# 2. Configurar safe.directory
echo "🔧 Configurando repositório..."
sudo git config --global --add safe.directory "$REPO_DIR"

# 3. Mostrar arquivos alterados
echo ""
echo "📝 Arquivos modificados no servidor:"
echo "=========================================="
sudo git status --short
echo ""

# 4. Perguntar se quer continuar
echo "Essas alterações serão enviadas para o GitHub."
read -p "Deseja continuar? (s/n): " resposta

if [ "$resposta" != "s" ] && [ "$resposta" != "S" ]; then
    echo "❌ Operação cancelada"
    exit 0
fi

# 5. Adicionar todos os arquivos modificados
echo ""
echo "➕ Adicionando arquivos..."
sudo git add routes/configuracao.py
sudo git add templates/config/usuarios.html
sudo git add routes/auth.py
sudo git add templates/auth/profile.html 2>/dev/null || echo "   (profile.html não encontrado, ok)"

# 6. Fazer commit
echo ""
echo "💾 Fazendo commit..."
sudo git commit -m "$(cat <<'EOF'
Adiciona formulários de gerenciamento de usuários (via Antigravity)

Alterações:
- routes/configuracao.py: Adiciona actions 'criar', 'editar', 'alterar_senha'
  * Formulário de criação de usuários
  * Formulário de edição de dados (username, email)
  * Formulário de alteração de senha
  * Validações de duplicidade

- templates/config/usuarios.html: Adiciona modals para:
  * Cadastrar novo usuário
  * Editar dados do usuário
  * Alterar senha do usuário

- routes/auth.py: (se alterado) Melhorias em autenticação

Editado via Antigravity no servidor VPS

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

# 7. Enviar para GitHub
echo ""
echo "📤 Enviando para GitHub..."
sudo git push origin "$BRANCH"

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ Sucesso!"
    echo "=========================================="
    echo ""
    echo "Agora execute no seu WINDOWS:"
    echo ""
    echo "  cd C:\\Users\\orlei\\OneDrive\\ProjPython\\FINAN"
    echo "  git pull origin main"
    echo ""
    echo "Depois, você pode fazer novas alterações localmente"
    echo "e atualizar o servidor normalmente."
    echo ""
else
    echo ""
    echo "❌ Erro ao enviar para GitHub"
    echo "Verifique suas credenciais Git"
fi
