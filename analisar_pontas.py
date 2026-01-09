"""
Algoritmo para encontrar oportunidades de compra de "pontas".
Identifica sequências onde o MEIO está ocupado (contempladas ou não-disponíveis)
e as PONTAS estão disponíveis para compra.

Estratégia: Se o meio já está bloqueado, comprar só as pontas é suficiente
para capturar qualquer sorteio que caia naquela região!
"""

import sys
import json
from pathlib import Path
import pandas as pd


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
    
    # Calcular ativas e ocupadas (contempladas + não disponíveis)
    all_quotas = set(range(1, total_quotas + 1))
    active = all_quotas - contemplated
    occupied = contemplated | (active - available)  # contempladas + ativas não-disponíveis
    
    return {
        'total_quotas': total_quotas,
        'contemplated': contemplated,
        'active': active,
        'available': available,
        'occupied': occupied  # cotas que não podem ser compradas
    }


def find_edge_opportunities(data: dict, min_length: int = 5, min_occupied_pct: float = 0.5):
    """
    Encontra oportunidades de compra de pontas.
    
    Args:
        data: Dados do grupo
        min_length: Tamanho mínimo da sequência para considerar
        min_occupied_pct: Percentual mínimo do meio que deve estar ocupado
    
    Returns:
        Lista de oportunidades ordenadas por score
    """
    opportunities = []
    
    # Para cada sequência possível de tamanho min_length ou maior
    for start in range(1, data['total_quotas'] - min_length + 2):
        for length in range(min_length, min(51, data['total_quotas'] - start + 2)):
            end = start + length - 1
            
            # Definir pontas (primeira e última) e meio
            left_edge = start
            right_edge = end
            middle = set(range(start + 1, end))
            
            if not middle:  # sequência muito pequena
                continue
            
            # Verificar se ambas as pontas estão disponíveis
            if left_edge not in data['available'] or right_edge not in data['available']:
                continue
            
            # Contar quantas do meio estão ocupadas (contempladas ou não-disponíveis)
            middle_occupied = middle & data['occupied']
            middle_available = middle & data['available']
            
            occupied_pct = len(middle_occupied) / len(middle)
            
            # Filtrar: pelo menos min_occupied_pct do meio deve estar ocupado
            if occupied_pct < min_occupied_pct:
                continue
            
            # Calcular score (quanto mais ocupado o meio, melhor)
            # Score = tamanho * percentual_ocupado * 100
            score = length * occupied_pct * 100
            
            opportunities.append({
                'start': left_edge,
                'end': right_edge,
                'length': length,
                'middle_occupied': len(middle_occupied),
                'middle_available': len(middle_available),
                'middle_total': len(middle),
                'occupied_pct': occupied_pct,
                'score': score,
                'middle_occupied_list': sorted(middle_occupied),
                'middle_available_list': sorted(middle_available)
            })
    
    # Ordenar por score (maior primeiro)
    opportunities.sort(key=lambda x: x['score'], reverse=True)
    
    return opportunities


def analyze_edge_opportunities(grupo_path: str, top_n: int = 10, min_length: int = 5, min_occupied_pct: float = 0.5):
    """
    Analisa oportunidades de compra de pontas.
    
    Args:
        grupo_path: Caminho para pasta do grupo
        top_n: Número de oportunidades para mostrar
        min_length: Tamanho mínimo da sequência
        min_occupied_pct: Percentual mínimo ocupado no meio (0.0 a 1.0)
    """
    grupo_dir = Path(grupo_path)
    if not grupo_dir.exists():
        print(f"❌ Grupo não encontrado: {grupo_path}")
        return
    
    print("=" * 80)
    print(f"ANÁLISE DE OPORTUNIDADES DE COMPRA DE PONTAS - Grupo: {grupo_dir.name}")
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
    print(f"   Disponíveis para compra: {len(available_active)}")
    print(f"   Ocupadas (não compráveis): {len(data['occupied'])}")
    print()
    
    print(f"🔍 Critérios de busca:")
    print(f"   Tamanho mínimo: {min_length} cotas")
    print(f"   Ocupação mínima do meio: {min_occupied_pct*100:.0f}%")
    print()
    
    # Encontrar oportunidades
    opportunities = find_edge_opportunities(data, min_length, min_occupied_pct)
    
    if not opportunities:
        print("⚠️  Nenhuma oportunidade de ponta encontrada com esses critérios.")
        return
    
    print("=" * 80)
    print(f"🎯 TOP {min(top_n, len(opportunities))} OPORTUNIDADES DE COMPRA DE PONTAS")
    print("=" * 80)
    print()
    print("💡 ESTRATÉGIA: Comprar apenas as PONTAS de sequências onde o MEIO")
    print("   já está ocupado (contempladas ou não-disponíveis).")
    print()
    print("✅ VANTAGEM: Investimento mínimo (2 cotas) para cobrir região inteira!")
    print()
    
    # Mostrar top oportunidades
    for i, opp in enumerate(opportunities[:top_n], 1):
        print(f"#{i} Oportunidade: Cotas {opp['start']} e {opp['end']}")
        print(f"   📏 Sequência: {opp['length']} cotas ({opp['start']}-{opp['end']})")
        print(f"   💰 Investimento: 2 cotas (pontas)")
        print(f"   🔒 Meio ocupado: {opp['middle_occupied']}/{opp['middle_total']} ({opp['occupied_pct']*100:.0f}%)")
        print(f"   ⚠️  Meio disponível: {opp['middle_available']} cotas")
        print(f"   ⭐ Score: {opp['score']:.1f}")
        
        # Mostrar detalhes do meio se for pequeno
        if opp['middle_total'] <= 20:
            occupied_str = ', '.join(map(str, opp['middle_occupied_list'][:10]))
            if len(opp['middle_occupied_list']) > 10:
                occupied_str += f", ... (+{len(opp['middle_occupied_list'])-10})"
            print(f"   🔒 Meio ocupado: {occupied_str}")
            
            if opp['middle_available']:
                available_str = ', '.join(map(str, opp['middle_available_list']))
                print(f"   ⚠️  Meio disponível: {available_str}")
                print(f"      (Risco: outra pessoa pode comprar essas)")
        
        print()
    
    # Estatísticas gerais
    print("=" * 80)
    print("📈 ESTATÍSTICAS")
    print("=" * 80)
    print()
    
    print(f"Total de oportunidades encontradas: {len(opportunities)}")
    
    if opportunities:
        avg_length = sum(o['length'] for o in opportunities) / len(opportunities)
        avg_occupied = sum(o['occupied_pct'] for o in opportunities) / len(opportunities)
        best = opportunities[0]
        
        print(f"Tamanho médio das sequências: {avg_length:.1f} cotas")
        print(f"Ocupação média do meio: {avg_occupied*100:.0f}%")
        print(f"Melhor oportunidade: Cotas {best['start']} e {best['end']} (score: {best['score']:.1f})")
    
    print()
    print("=" * 80)
    print("⚠️  ATENÇÃO - RISCO")
    print("=" * 80)
    print()
    print("🚨 Se houver cotas DISPONÍVEIS no meio, outra pessoa pode comprá-las")
    print("   e ganhar antes de você!")
    print()
    print("✅ IDEAL: Escolher sequências onde o meio está 100% ocupado")
    print("   (contempladas ou não-disponíveis)")
    print()
    print("💡 DICA: Use --min-occupied 1.0 para ver apenas oportunidades perfeitas")
    print()


def main():
    if len(sys.argv) < 2:
        print("Uso: python analisar_pontas.py grupos/nome_do_grupo [top_n] [--min-length N] [--min-occupied X.X]")
        print()
        print("Parâmetros:")
        print("  top_n            Número de oportunidades para mostrar (default: 10)")
        print("  --min-length N   Tamanho mínimo da sequência (default: 5)")
        print("  --min-occupied X Percentual mínimo ocupado 0.0-1.0 (default: 0.5 = 50%)")
        print()
        print("Exemplos:")
        print("  python analisar_pontas.py grupos/6032")
        print("  python analisar_pontas.py grupos/6032 20")
        print("  python analisar_pontas.py grupos/6032 10 --min-length 10 --min-occupied 0.8")
        print("  python analisar_pontas.py grupos/6032 5 --min-occupied 1.0  # apenas 100% ocupado")
        print()
        print("Estratégia:")
        print("  Se uma sequência tem o MEIO ocupado (contempladas ou não-disponíveis),")
        print("  basta comprar as PONTAS (2 cotas) para cobrir toda a região!")
        print()
        print("  Exemplo: Sequência 100-110")
        print("    Meio (101-109): 8 contempladas + 1 não-disponível = 100% ocupado")
        print("    Pontas: 100 e 110 disponíveis")
        print("    Investimento: 2 cotas cobrindo 11 posições!")
        return
    
    grupo_path = sys.argv[1]
    top_n = 10
    min_length = 5
    min_occupied_pct = 0.5
    
    # Parse argumentos
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == '--min-length' and i + 1 < len(sys.argv):
            min_length = int(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == '--min-occupied' and i + 1 < len(sys.argv):
            min_occupied_pct = float(sys.argv[i + 1])
            i += 2
        else:
            top_n = int(sys.argv[i])
            i += 1
    
    analyze_edge_opportunities(grupo_path, top_n=top_n, min_length=min_length, 
                              min_occupied_pct=min_occupied_pct)


if __name__ == "__main__":
    main()
