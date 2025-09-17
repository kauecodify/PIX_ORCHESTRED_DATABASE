# PIX_ORCHESTRED_DATABASE

<img width="100" height="100" alt="spyder" src="https://github.com/user-attachments/assets/a073c345-c04a-4411-8d2b-d8e3941f0d5a" />

# INTERFACE

<img width="1190" height="641" alt="image" src="https://github.com/user-attachments/assets/921309ed-ff47-4bca-9208-c99888b698de" />

# DIRETÓRIO

<img width="622" height="141" alt="image" src="https://github.com/user-attachments/assets/45756823-d182-45c8-a7a2-500e3533a82c" />

# DATABASE (pasta backups)

<img width="621" height="343" alt="image" src="https://github.com/user-attachments/assets/7bb71519-33dd-4c7b-933a-d5aef0ee60b6" />

---

🔧 Funcionalidades:

Sistema de Acumulação Inteligente:

Registra timestamp da última execução

Recupera automaticamente períodos não monitorados

Configuração máxima de dias para recuperação 

obs: adc banco, agencia e conta para saldos desviados em via física

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

acumulação de dados mesmo quando não está rodando, 
utilizando a API oficial do BCB Olinda para obter dados reais de transações Pix.
