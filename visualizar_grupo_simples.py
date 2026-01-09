"""
Visualização simples de grupo de consórcio.
Mostra matriz com status das cotas:
- Verde: Contempladas
- Azul: Não contempladas (ativas, não disponíveis para compra)
- Amarelo: Disponíveis para compra
- Borda Roxa: Top 3 sequências consecutivas (opcional)
"""

import sys
import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path
import pandas as pd


def find_consecutive_sequences(quotas_list: list) -> list:
    """Encontra sequências consecutivas de cotas."""
    if not quotas_list:
        return []
    
    sorted_quotas = sorted(set(quotas_list))
    sequences = []
    current_seq = [sorted_quotas[0]]
    
    for i in range(1, len(sorted_quotas)):
        prev = sorted_quotas[i - 1]
        curr = sorted_quotas[i]
        
        if curr == prev + 1:
            current_seq.append(curr)
        else:
            if len(current_seq) >= 2:
                sequences.append({
                    'quotas': current_seq.copy(),
                    'start': current_seq[0],
                    'end': current_seq[-1],
                    'length': len(current_seq)
                })
            current_seq = [curr]
    
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
    
    # Carregar lance 25%
    lance_25 = set()
    lance_25_file = grupo_dir / "lance_25.txt"
    if lance_25_file.exists():
        with open(lance_25_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    lance_25.add(int(line))
    
    # Calcular ativas
    all_quotas = set(range(1, total_quotas + 1))
    active = all_quotas - contemplated
    
    return {
        'total_quotas': total_quotas,
        'contemplated': contemplated,
        'active': active,
        'available': available,
        'lance_25': lance_25
    }


def visualizar_simples(grupo_path: str, output_path: str = None, show: bool = False, show_numbers: bool = False, highlight_sequences: bool = False):
    """
    Cria visualização simples em matriz das cotas por status.
    
    Args:
        grupo_path: Caminho para pasta do grupo
        output_path: Caminho para salvar imagem (opcional)
        show: Se True, mostra a janela
        show_numbers: Se True, mostra números das cotas
        highlight_sequences: Se True, destaca as 3 maiores sequências com borda roxa
    """
    grupo_dir = Path(grupo_path)
    if not grupo_dir.exists():
        print(f"❌ Grupo não encontrado: {grupo_path}")
        return
    
    print(f"Criando visualização simples: {grupo_dir.name}")
    print("=" * 70)
    
    # Carregar dados
    try:
        data = load_group_data(str(grupo_dir))
    except Exception as e:
        print(f"Erro ao carregar grupo: {e}")
        return
    
    total_quotas = data['total_quotas']
    contemplated = data['contemplated']
    available = data['available']
    active = data['active']
    lance_25 = data.get('lance_25', set())
    
    available_active = active & available
    
    print(f"Total de cotas: {total_quotas}")
    print(f"Contempladas: {len(contemplated)}")
    print(f"Disponíveis para compra: {len(available_active)}")
    print(f"Ativas (não disponíveis): {len(active) - len(available_active)}")
    if lance_25:
        print(f"Com lance de 25%: {len(lance_25)}")
    print()
    
    # Encontrar sequências se necessário
    top_sequences = []
    if highlight_sequences and available_active:
        # Incluir contempladas porque se sorteadas, a próxima ±1 é usada
        quotas_for_sequence = list(data['available'] | data['contemplated'])
        all_sequences = find_consecutive_sequences(quotas_for_sequence)
        
        # Pegar as top 3 MAIORES sequências (incluindo empates)
        if all_sequences:
            # Encontrar os 3 maiores tamanhos únicos
            unique_lengths = sorted(set(s['length'] for s in all_sequences), reverse=True)[:3]
            # Pegar TODAS as sequências com esses tamanhos
            top_sequences = [s for s in all_sequences if s['length'] in unique_lengths]
            
            print(f"🟣 Destacando sequências com os {len(unique_lengths)} maiores tamanhos (incluindo contempladas):")
            for i, seq in enumerate(top_sequences, 1):
                available_in_seq = len([q for q in seq['quotas'] if q in data['available']])
                contemplated_in_seq = len([q for q in seq['quotas'] if q in data['contemplated']])
                print(f"   #{i}: {seq['start']}-{seq['end']} ({seq['length']} cotas)")
                print(f"        💰 {available_in_seq} disponíveis | 🏆 {contemplated_in_seq} contempladas")
            print()
    
    # Determinar tamanho da matriz (quadrado mais próximo)
    cols = int(np.ceil(np.sqrt(total_quotas)))
    rows = int(np.ceil(total_quotas / cols))
    
    print(f"Matriz: {rows}x{cols}")
    print()
    
    # Criar matriz de valores
    # 0 = vazio, 1 = contemplada (verde), 2 = disponível (amarelo), 3 = ativa não disponível (azul), 4 = lance 25% (vermelho)
    matrix = np.zeros((rows, cols))
    
    for i in range(total_quotas):
        quota = i + 1
        row = i // cols
        col = i % cols
        
        if quota in lance_25:
            matrix[row, col] = 4  # Lance 25% - vermelho (prioridade máxima)
        elif quota in contemplated:
            matrix[row, col] = 1  # Verde
        elif quota in available_active:
            matrix[row, col] = 2  # Amarelo
        elif quota in active:
            matrix[row, col] = 3  # Azul
        else:
            matrix[row, col] = 0  # Não deveria acontecer
    
    # Preencher células vazias com NaN
    for i in range(total_quotas, rows * cols):
        row = i // cols
        col = i % cols
        matrix[row, col] = np.nan
    
    # Criar figura
    fig, ax = plt.subplots(figsize=(16, 12))
    
    # Criar colormap customizado
    from matplotlib.colors import ListedColormap
    
    # Cores: 0=branco (vazio), 1=verde (contemplada), 2=amarelo (disponível), 3=azul (ativa), 4=vermelho (lance 25%)
    colors = ['white', '#28a745', '#ffc107', '#007bff', '#dc3545']  # Verde, Amarelo, Azul, Vermelho
    cmap = ListedColormap(colors)
    
    # Plotar matriz
    im = ax.imshow(matrix, cmap=cmap, vmin=0, vmax=4, alpha=0.9)
    
    # Adicionar grid
    ax.set_xticks(np.arange(-0.5, cols, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, rows, 1), minor=True)
    ax.grid(which='minor', color='gray', linestyle='-', linewidth=0.5, alpha=0.3)
    
    # Destacar top 3 sequências com borda roxa
    if highlight_sequences and top_sequences:
        for seq in top_sequences:
            for quota in seq['quotas']:
                idx = quota - 1
                row = idx // cols
                col = idx % cols
                rect = mpatches.Rectangle((col-0.48, row-0.48), 0.96, 0.96,
                                         linewidth=3, edgecolor='purple',
                                         facecolor='none', zorder=10)
                ax.add_patch(rect)
    
    # Adicionar números das cotas
    if show_numbers:
        # Calcular tamanho da fonte baseado no número de cotas
        if total_quotas <= 100:
            fontsize = 8
        elif total_quotas <= 400:
            fontsize = 6
        elif total_quotas <= 1000:
            fontsize = 4
        else:
            fontsize = 3
        
        for i in range(total_quotas):
            quota = i + 1
            row = i // cols
            col = i % cols
            
            # Cor do texto baseada no fundo
            if quota in lance_25:
                color = 'white'
                weight = 'bold'
            elif quota in contemplated:
                color = 'white'
                weight = 'bold'
            elif quota in available_active:
                color = 'black'
                weight = 'bold'
            elif quota in active:
                color = 'white'
                weight = 'normal'
            else:
                color = 'black'
                weight = 'normal'
            
            ax.text(col, row, str(quota), ha='center', va='center',
                   fontsize=fontsize, color=color, weight=weight)
    
    # Configurar eixos
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_aspect('equal')
    
    # Título
    completion_pct = (len(contemplated) / total_quotas) * 100
    title = f"Grupo: {grupo_dir.name}\n"
    title += f"Total: {total_quotas} | "
    title += f"Contempladas: {len(contemplated)} ({completion_pct:.1f}%) | "
    title += f"Disponíveis: {len(available_active)} | "
    title += f"Ativas (não disp.): {len(active) - len(available_active)}"
    if lance_25:
        title += f" | Lance 25%: {len(lance_25)}"
    
    ax.set_title(title, fontsize=14, weight='bold', pad=20)
    
    # Legenda
    legend_elements = [
        mpatches.Patch(color='#28a745', label='Contempladas'),
        mpatches.Patch(color='#ffc107', label='Disponíveis para Compra'),
        mpatches.Patch(color='#007bff', label='Ativas (não disponíveis)'),
    ]
    
    if lance_25:
        legend_elements.append(
            mpatches.Patch(color='#dc3545', label='Lance de 25%')
        )
    
    if highlight_sequences and top_sequences:
        legend_elements.append(
            mpatches.Patch(facecolor='none', edgecolor='purple', linewidth=3,
                          label=f'Top Sequências (disp+contempl)')
        )
    
    ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1.05, 1),
             fontsize=12, frameon=True)
    
    plt.tight_layout()
    
    # Salvar
    if output_path is None:
        output_path = grupo_dir / "visualizacao_simples.png"
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✅ Visualização salva: {output_path}")
    
    # Mostrar apenas se solicitado
    if show:
        plt.show()
    else:
        plt.close()
    
    return output_path


def main():
    if len(sys.argv) < 2:
        print("Uso: python visualizar_grupo_simples.py grupos/nome_do_grupo [--show] [--numbers] [--sequences]")
        print()
        print("Opções:")
        print("  --show         Mostrar janela com a imagem")
        print("  --numbers      Mostrar números das cotas")
        print("  --sequences    Destacar top 3 sequências consecutivas com borda roxa")
        print("                 (inclui contempladas, pois se sorteadas usam a próxima ±1)")
        print()
        print("Cores:")
        print("  🟢 Verde:   Contempladas")
        print("  🟡 Amarelo: Disponíveis para compra")
        print("  🔵 Azul:    Ativas (não disponíveis)")
        print("  🔴 Vermelho: Lance de 25%")
        print("  🟣 Roxa:    Top 3 sequências (disponíveis + contempladas, borda)")
        print()
        print("Exemplos:")
        print("  python visualizar_grupo_simples.py grupos/6034")
        print("  python visualizar_grupo_simples.py grupos/6034 --numbers")
        print("  python visualizar_grupo_simples.py grupos/6034 --sequences")
        print("  python visualizar_grupo_simples.py grupos/6034 --numbers --sequences --show")
        return
    
    grupo_path = sys.argv[1]
    show = '--show' in sys.argv
    show_numbers = '--numbers' in sys.argv
    highlight_sequences = '--sequences' in sys.argv
    
    visualizar_simples(grupo_path, show=show, show_numbers=show_numbers, 
                      highlight_sequences=highlight_sequences)


if __name__ == "__main__":
    main()
