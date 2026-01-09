"""
Algoritmo para encontrar sequências ininterruptas de cotas disponíveis.
Identifica as maiores sequências consecutivas para estratégia de "bloqueio".
"""

import sys
import json
from pathlib import Path
import pandas as pd


def find_consecutive_sequences(quotas_list: list) -> list:
    """
    Encontra todas as sequências consecutivas em uma lista de cotas.
    
    Args:
        quotas_list: Lista de números de cotas (não precisa estar ordenada)
    
    Returns:
        Lista de dicionários com informações de cada sequência:
        - quotas: lista das cotas na sequência
        - start: primeira cota
        - end: última cota
        - length: tamanho da sequência
    """
    if not quotas_list:
        return []
    
    # Ordenar e remover duplicatas
    sorted_quotas = sorted(set(quotas_list))
    
    sequences = []
    current_seq = [sorted_quotas[0]]
    
    for i in range(1, len(sorted_quotas)):
        prev = sorted_quotas[i - 1]
        curr = sorted_quotas[i]
        
        # Se for consecutivo, adiciona à sequência atual
        if curr == prev + 1:
            current_seq.append(curr)
        else:
            # Salva sequência atual e começa nova
            if len(current_seq) >= 2:  # Só sequências com 2+ cotas
                sequences.append({
                    'quotas': current_seq.copy(),
                    'start': current_seq[0],
                    'end': current_seq[-1],
                    'length': len(current_seq)
                })
            current_seq = [curr]
    
    # Adicionar última sequência
    if len(current_seq) >= 2:
        sequences.append({
            'quotas': current_seq.copy(),
            'start': current_seq[0],
            'end': current_seq[-1],
            'length': len(current_seq)
        })
    
    # Ordenar por tamanho (maior primeiro) e depois por início (menor primeiro)
    sequences.sort(key=lambda s: (-s['length'], s['start']))
    
    return sequences


def load_group_data(grupo_path: str):
    """Carrega dados do grupo."""
    grupo_dir = Path(grupo_path)
    
    # Carregar total de cotas
    config_file = grupo_dir / "configuracao.json"
    total_file = grupo_dir / "total_cotas.txt"
    
    if config_file.exists():
        with open(config_file, 'r') as f:
            config = json.load(f)
        total_quotas = config['total_cotas']
    elif total_file.exists():
        with open(total_file, 'r') as f:
            total_quotas = int(f.read().strip())
    else:
        raise FileNotFoundError("Arquivo de configuração não encontrado")
    
    # Carregar contempladas
    contemplated = set()
    contemplated_csv = grupo_dir / "cotas_contempladas.csv"
    contemplated_txt = grupo_dir / "cotas_contempladas.txt"
    
    if contemplated_csv.exists():
        df = pd.read_csv(contemplated_csv)
        for cotas_str in df['cotas']:
            if pd.notna(cotas_str):
                for cota in str(cotas_str).split('-'):
                    contemplated.add(int(cota.strip()))
    elif contemplated_txt.exists():
        with open(contemplated_txt, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    contemplated.add(int(line))
    
    # Carregar disponíveis
    available = set()
    available_file = grupo_dir / "cotas_disponiveis.txt"
    if available_file.exists():
        with open(available_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    available.add(int(line))
    
    # Calcular ativas
    all_quotas = set(range(1, total_quotas + 1))
    active = all_quotas - contemplated
    
    return {
        'total_quotas': total_quotas,
        'contemplated': contemplated,
        'active': active,
        'available': available
    }


def analyze_consecutive_sequences(grupo_path: str, top_n: int = 3):
    """
    Analisa as maiores sequências consecutivas de cotas disponíveis.
    
    Args:
        grupo_path: Caminho para pasta do grupo
        top_n: Número de top sequências para mostrar
    """
    grupo_dir = Path(grupo_path)
    if not grupo_dir.exists():
        print(f"❌ Grupo não encontrado: {grupo_path}")
        return
    
    print("=" * 80)
    print(f"ANÁLISE DE SEQUÊNCIAS CONSECUTIVAS - Grupo: {grupo_dir.name}")
    print("=" * 80)
    print()
    
    # Carregar dados
    try:
        data = load_group_data(str(grupo_dir))
    except Exception as e:
        print(f"Erro ao carregar grupo: {e}")
        return
    
    # Resumo
    available_active = data['active'] & data['available']
    print(f"📊 Resumo:")
    print(f"   Total de cotas: {data['total_quotas']}")
    print(f"   Contempladas: {len(data['contemplated'])}")
    print(f"   Ativas: {len(data['active'])}")
    print(f"   Disponíveis para compra: {len(available_active)}")
    print()
    
    if len(available_active) == 0:
        print("⚠️  Nenhuma cota disponível para análise.")
        return
    
    # Considerar contempladas como disponíveis para análise de sequências
    # Porque se uma contemplada for sorteada, a próxima ±1 é usada
    quotas_for_sequence_analysis = data['available'] | data['contemplated']
    available_quotas = list(quotas_for_sequence_analysis)
    
    # Encontrar sequências consecutivas
    sequences = find_consecutive_sequences(available_quotas)
    
    if not sequences:
        print("⚠️  Nenhuma sequência consecutiva encontrada.")
        print("   Todas as cotas disponíveis estão isoladas (sem vizinhas consecutivas).")
        return
    
    print("=" * 80)
    print(f"🎯 TOP {min(top_n, len(sequences))} SEQUÊNCIAS CONSECUTIVAS")
    print("=" * 80)
    print()
    print("Sequências consecutivas = cotas disponíveis + contempladas em sequência numérica.")
    print("Contempladas são incluídas porque se sorteadas, a próxima cota ±1 é usada.")
    print("Exemplo: 6, 7, 8 é uma sequência de 3 cotas.")
    print()
    
    # Mostrar top sequências
    for i, seq in enumerate(sequences[:top_n], 1):
        # Identificar quais são disponíveis e quais são contempladas
        available_in_seq = [q for q in seq['quotas'] if q in data['available']]
        contemplated_in_seq = [q for q in seq['quotas'] if q in data['contemplated']]
        
        print(f"#{i} Sequência: {seq['start']} até {seq['end']}")
        print(f"   📏 Tamanho: {seq['length']} cotas consecutivas")
        print(f"   💰 Disponíveis: {len(available_in_seq)} | 🏆 Contempladas: {len(contemplated_in_seq)}")
        
        # Mostrar as cotas (limite de 30 para não poluir)
        if seq['length'] <= 30:
            quotas_display = []
            for q in seq['quotas']:
                if q in data['contemplated']:
                    quotas_display.append(f"{q}★")
                else:
                    quotas_display.append(str(q))
            quotas_str = ', '.join(quotas_display)
            print(f"   📋 Cotas: {quotas_str}")
            print(f"      (★ = contemplada)")
        else:
            first_10_display = []
            for q in seq['quotas'][:10]:
                if q in data['contemplated']:
                    first_10_display.append(f"{q}★")
                else:
                    first_10_display.append(str(q))
            last_10_display = []
            for q in seq['quotas'][-10:]:
                if q in data['contemplated']:
                    last_10_display.append(f"{q}★")
                else:
                    last_10_display.append(str(q))
            first_10 = ', '.join(first_10_display)
            last_10 = ', '.join(last_10_display)
            print(f"   📋 Cotas: {first_10} ... {last_10}")
            print(f"      (★ = contemplada)")
        print()
    
    # Estatísticas gerais
    print("=" * 80)
    print("📈 ESTATÍSTICAS")
    print("=" * 80)
    print()
    
    total_in_sequences = sum(s['length'] for s in sequences)
    total_available = len(available_quotas)
    isolated_quotas = total_available - total_in_sequences
    
    if total_available > 0:
        print(f"Total de cotas disponíveis: {total_available}")
        print(f"Cotas em sequências (≥2): {total_in_sequences} ({100*total_in_sequences/total_available:.1f}%)")
        print(f"Cotas isoladas: {isolated_quotas} ({100*isolated_quotas/total_available:.1f}%)")
        print(f"Número de sequências encontradas: {len(sequences)}")
        print()
    
    if sequences:
        avg_length = sum(s['length'] for s in sequences) / len(sequences)
        max_length = sequences[0]['length']
        print(f"Tamanho médio das sequências: {avg_length:.1f} cotas")
        print(f"Maior sequência: {max_length} cotas ({sequences[0]['start']}-{sequences[0]['end']})")
    
    print()
    print("=" * 80)
    print("💡 ESTRATÉGIA DE BLOQUEIO")
    print("=" * 80)
    print()
    print("✅ VANTAGEM de comprar sequências consecutivas:")
    print("   - Qualquer sorteio que cair na região vai encontrar SUA cota")
    print("   - Método radial (B, B±1, B±2...) favorece sequências")
    print("   - Bloqueia outras pessoas de ganhar naquela faixa")
    print()
    
    if sequences:
        best = sequences[0]
        print(f"🎯 MELHOR OPORTUNIDADE:")
        print(f"   Comprar cotas {best['start']} até {best['end']} ({best['length']} cotas)")
        print(f"   Qualquer bola sorteada próxima a essa faixa resultará em SUA contemplação!")
    
    print()


def main():
    if len(sys.argv) < 2:
        print("Uso: python analisar_sequencias.py grupos/nome_do_grupo [top_n]")
        print()
        print("Parâmetros:")
        print("  top_n    Número de sequências para mostrar (default: 3)")
        print()
        print("Exemplos:")
        print("  python analisar_sequencias.py grupos/6034")
        print("  python analisar_sequencias.py grupos/6034 10")
        print()
        print("Exemplo de sequência:")
        print("  Cotas disponíveis: 1, 2, 6, 7, 8, 12, 13, 14, 34, 35, 36, 39")
        print("  Sequências encontradas:")
        print("    #1: 6, 7, 8 (3 cotas)")
        print("    #2: 12, 13, 14 (3 cotas)")
        print("    #3: 34, 35, 36 (3 cotas)")
        return
    
    grupo_path = sys.argv[1]
    top_n = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    
    analyze_consecutive_sequences(grupo_path, top_n=top_n)


if __name__ == "__main__":
    main()
