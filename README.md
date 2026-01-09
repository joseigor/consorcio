# 🇧🇷 Brazilian Consórcio Quota Analyzer

Sistema para analisar e escolher a melhor cota de consórcio para comprar em grupos em andamento.

## 🎯 Objetivo

**Responde:** "Qual a melhor cota para comprar em um consórcio já iniciado?"

Baseado no **Índice de Posicionamento (IP)** e simulação **Monte Carlo**, o sistema considera:
- ✅ **Sorteios aleatórios** (busca radial - IP importa!)
- ✅ **Lances fixos** (empates desempatados por busca radial - IP importa!)

## 📋 Pré-requisitos

```bash
Python 3.11+
```

## 🚀 Instalação

```bash
# 1. Criar ambiente virtual
python -m venv venv

# 2. Ativar ambiente
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 3. Instalar dependências
pip install -r requirements.txt
```

## 📊 Formato do CSV

Crie um arquivo CSV com as seguintes colunas:

```csv
cota,contemplada,mes_contemplacao,disponivel_compra
1,0,,0
2,0,,0
3,0,,1
4,0,,1
5,1,3,0
...
```

**Colunas:**
- `cota`: Número da cota (obrigatório)
- `contemplada`: 1 se já foi contemplada, 0 caso contrário (obrigatório)
- `mes_contemplacao`: Mês em que foi contemplada (opcional)
- `disponivel_compra`: 1 se está disponível para compra, 0 caso contrário (opcional)

## 🎯 Como Usar

### **Opção 1: Análise Rápida (IP apenas)**

```bash
python analyze_csv.py seu_consorcio.csv
```

Mostra:
- Ranking geral de todas cotas ativas
- Ranking apenas de cotas disponíveis para compra
- Baseado no IP (Índice de Posicionamento)

### **Opção 2: Análise Completa com Simulação (RECOMENDADO)**

```bash
python refined_montecarlo.py seu_consorcio.csv
```

Será solicitado:
- Duração do consórcio (ex: 180 meses)
- Sorteios por mês (ex: 1)
- Lances fixos por mês (ex: 1)
- Número de simulações (ex: 1000)

Escolha opção **2** para comparar todas cotas disponíveis.

**Saída:**
- Tempo médio esperado de contemplação
- Probabilidade de ser contemplado em 12/24 meses
- % de contemplação por sorteio vs lance fixo
- CSV com ranking completo

## 📈 Entendendo os Resultados

### **IP (Índice de Posicionamento)**

```
IP = (L + R) / média(L + R)

Onde:
- L: distância para cota ativa à esquerda
- R: distância para cota ativa à direita
```

**Interpretação:**
- **IP > 1.3**: Excelente posição (isolada, perto de "buracos")
- **IP 1.0-1.3**: Boa posição
- **IP < 1.0**: Posição abaixo da média

### **Tempo Médio (Monte Carlo)**

Baseado em 1000 simulações:
- Considera sorteios aleatórios + lances fixos
- Ambos usam busca radial (IP importa!)
- Mais realista que apenas IP

### **Estratégia de Compra**

| IP | Tempo Esperado | Estratégia |
|----|----------------|------------|
| > 1.3 | ~20-22 meses | ✅ COMPRAR! Alta chance sorteio + lance fixo |
| 1.0-1.3 | ~23-25 meses | ✅ Bom negócio, considerar |
| < 1.0 | ~26+ meses | ⚠️ Avaliar preço vs tempo |

## 📁 Estrutura do Projeto

```
consorcio/
├── venv/                          # Ambiente virtual
├── consorcio.py                   # Motor de cálculo do IP
├── analyze_csv.py                 # Análise rápida por IP
├── refined_montecarlo.py          # Simulação Monte Carlo completa
├── exemplo_consorcio.csv          # Exemplo de dados
├── requirements.txt               # Dependências
└── README.md                      # Este arquivo
```

## 🔬 Como Funciona

### **1. Busca Radial**

Quando um número base B é sorteado:
```
Ordem de busca: B → B-1 → B+1 → B-2 → B+2 → B-3 → B+3 ...
Primeira cota ATIVA encontrada ganha
```

### **2. IP (Índice de Posicionamento)**

Cotas isoladas ou próximas a "buracos" (contempladas) têm:
- Mais espaço (L+R maior)
- Maior chance de serem encontradas
- IP > 1.0

### **3. Monte Carlo**

Para cada simulação:
1. Sorteia base para sorteio aleatório → busca radial
2. Sorteia base para lance fixo → busca radial entre participantes (25%)
3. Repete até cota de interesse ser contemplada
4. Estatísticas após 1000 simulações

## 💡 Exemplo Prático

```bash
$ python refined_montecarlo.py exemplo_consorcio.csv

# Configuração:
Duration: 180 months
Draws/month: 1
Fixed bids/month: 1
Simulations: 1000

# Escolher opção 2 (comparar todas)

# Resultado:
🏆 TOP AVAILABLE QUOTAS FOR PURCHASE
Rank  Cota  IP    Tempo Médio  Prob.12m  % Sorteio  % Lance
1     4     1.41  21.6 meses   32.2%     60%        40%
2     44    1.41  21.0 meses   34.5%     58%        42%
3     24    1.41  23.1 meses   27.5%     54%        46%
...

✅ Recomendação: Comprar cota 4 ou 44
```

## 🎯 Validação

- **Correlação IP vs Tempo:** -0.76 (forte)
- **R²:** 0.58 (IP explica 58% da variação)
- **Modelo validado** com análise estatística

## 📚 Documentação Técnica

Ver `consorcio_model_summary.md` para detalhes do modelo matemático.

## ⚠️ Limitações

**O modelo NÃO considera:**
- Lances livres (decisão financeira, não sorteio)
- Desistências de cotas
- Múltiplos sorteios no mesmo mês (configurável)
- Mudanças no grupo ao longo do tempo

**O modelo CONSIDERA:**
- Sorteios aleatórios com busca radial
- Lances fixos com desempate por busca radial
- IP como fator principal
- Simulação probabilística realista

## 🤝 Suporte

Sistema desenvolvido para análise de consórcios brasileiros com foco em seleção de cota inicial.

---

**Made with ❤️ for smart consortium quota buyers**
