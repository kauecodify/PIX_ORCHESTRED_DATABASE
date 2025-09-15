# PIX_ORCHESTRED_DATABASE

<img width="1190" height="641" alt="image" src="https://github.com/user-attachments/assets/921309ed-ff47-4bca-9208-c99888b698de" />

---

🔧 Funcionalidades:

Sistema de Acumulação Inteligente:

Registra timestamp da última execução

Recupera automaticamente períodos não monitorados

Configuração máxima de dias para recuperação 

---

Busca de Dados Reais:

Integração com API Olinda do BCB para transações reais

Fallback para transações anteriores enquanto a API não retorna dados (fica em stand-by)

Formatação adequada dos dados da API -->> configurar link interno via api de autenticação 

---

Interface Aprimorada:

Painel de estatísticas em tempo real

Configurações de recuperação ajustáveis

Controles para forçar recuperação manual

---

Gestão de Erros:

Tratamento robusto de exceções

Logs detalhados para diagnóstico

Sistema de fallback para manter operação

---

📊 Como Funciona:

O sistema verifica periodicamente a API Olinda do BCB 

(alterar para link oficial de controle e mudar periódicamente visando segurança nacional)

Se houver períodos não monitorados, busca dados históricos

Armazena tanto transações reais quanto simuladas (para testes)

Mantém estatísticas atualizadas na interface

---

⚙️ Configuração:

ajustar as configurações através da interface:

Ativar/desativar recuperação de dados

Definir limite máximo de dias para recuperação

Forçar recuperação manual quando necessário

acumulação de dados mesmo quando não está rodando, utilizando a API oficial do BCB Olinda para obter dados reais de transações Pix e rastreamento absoluto de todas as transações incluindo envios para carteiras em cripto
