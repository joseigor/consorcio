"""
Consórcio Optimal Cota Strategy Analyzer

Analyzes grupo data to identify optimal cotas based on the alternating search algorithm.

Algorithm: When invalid cota drawn, search alternates: -1, +1, -2, +2, -3, +3...
(searches BELOW first, then ABOVE)
"""

import os
import sys
from typing import List, Tuple, Set, Dict


def load_contempladas(grupo_path: str) -> Set[int]:
    """Load already selected cotas (GREEN) - INVALID for selection"""
    contempladas = set()
    file_path = os.path.join(grupo_path, 'cotas_contempladas.txt')

    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Files contain plain numbers, one per line (no arrow format)
                if line and line.isdigit():
                    contempladas.add(int(line))

    return contempladas


def load_disponiveis(grupo_path: str) -> Set[int]:
    """Load available but not purchased cotas (YELLOW) - INVALID for selection"""
    disponiveis = set()
    file_path = os.path.join(grupo_path, 'cotas_disponiveis.txt')

    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Files contain plain numbers, one per line (no arrow format)
                if line and line.isdigit():
                    disponiveis.add(int(line))

    return disponiveis


def get_active_cotas(total_cotas: int, contempladas: Set[int],
                     disponiveis: Set[int]) -> Set[int]:
    """Active cotas (BLUE+RED) = all - contempladas - disponiveis"""
    all_cotas = set(range(1, total_cotas + 1))
    return all_cotas - contempladas - disponiveis


def find_selected_cota(initial_draw: int, active_cotas: Set[int],
                       max_cota: int) -> int:
    """
    Simulate selection algorithm: -1, +1, -2, +2, -3, +3...
    (searches BELOW first, then ABOVE)
    """
    if initial_draw in active_cotas:
        return initial_draw

    for offset in range(1, max_cota):
        # Try below FIRST (-)
        below = initial_draw - offset
        if below >= 1 and below in active_cotas:
            return below

        # Then try above (+)
        above = initial_draw + offset
        if above <= max_cota and above in active_cotas:
            return above

    return None


def calculate_catchment(cota: int, active_cotas: Set[int],
                        max_cota: int) -> Tuple[int, List[int]]:
    """
    Count how many initial draws result in this cota being selected.
    Returns: (count, list of draws that result in this cota)
    """
    if cota not in active_cotas:
        return 0, []

    draws = []
    for draw in range(1, max_cota + 1):
        if find_selected_cota(draw, active_cotas, max_cota) == cota:
            draws.append(draw)

    return len(draws), draws


def find_gaps(active_cotas: Set[int], contempladas: Set[int],
              disponiveis: Set[int]) -> List[Tuple[int, int, int, int, int]]:
    """
    Find gaps (sequences of invalid cotas).
    Returns: (start, end, size, num_contempladas, num_disponiveis)
    Gaps with more contempladas are safer (less risk of someone buying in the gap)
    """
    sorted_active = sorted(active_cotas)
    gaps = []

    for i in range(len(sorted_active) - 1):
        gap_start = sorted_active[i] + 1
        gap_end = sorted_active[i + 1] - 1

        if gap_end >= gap_start:
            # Count contempladas and disponiveis in this gap
            num_contempladas = sum(1 for c in range(gap_start, gap_end + 1) if c in contempladas)
            num_disponiveis = sum(1 for c in range(gap_start, gap_end + 1) if c in disponiveis)

            gaps.append((gap_start, gap_end, gap_end - gap_start + 1,
                        num_contempladas, num_disponiveis))

    return gaps


def main():
    # Parse command line arguments
    if len(sys.argv) < 2:
        print("Usage: python3 analyze_optimal_cotas.py <grupo_folder> [total_cotas]")
        print("Example: python3 analyze_optimal_cotas.py grupos/6032 2500")
        sys.exit(1)

    grupo = sys.argv[1]
    total_cotas = int(sys.argv[2]) if len(sys.argv) > 2 else 2500

    grupo_name = os.path.basename(grupo)
    print("="*70)
    print(f"CONSÓRCIO STRATEGY ANALYZER - Grupo {grupo_name}")
    print("="*70)

    # Load data
    contempladas = load_contempladas(grupo)
    disponiveis = load_disponiveis(grupo)
    active = get_active_cotas(total_cotas, contempladas, disponiveis)

    print(f"\n📊 Statistics:")
    print(f"  Total cotas: {total_cotas}")
    print(f"  Contempladas (green): {len(contempladas)} ({len(contempladas)/total_cotas*100:.1f}%)")
    print(f"  Disponíveis (yellow): {len(disponiveis)} ({len(disponiveis)/total_cotas*100:.1f}%)")
    print(f"  Active (blue+red): {len(active)} ({len(active)/total_cotas*100:.1f}%)")

    # Find all gaps
    all_gaps = find_gaps(active, contempladas, disponiveis)

    # Analyze gaps - we can buy disponíveis INSIDE gaps even if boundaries are active
    analyzed_gaps = []
    for gap_start, gap_end, size, num_contempladas, num_disponiveis in all_gaps:
        lower_boundary = gap_start - 1
        upper_boundary = gap_end + 1

        lower_buyable = lower_boundary in disponiveis
        upper_buyable = upper_boundary in disponiveis
        lower_active = lower_boundary in active
        upper_active = upper_boundary in active

        # Find buyable cotas inside this gap
        buyable_in_gap = [c for c in range(gap_start, gap_end + 1) if c in disponiveis]

        analyzed_gaps.append({
            'start': gap_start,
            'end': gap_end,
            'size': size,
            'num_contempladas': num_contempladas,
            'num_disponiveis': num_disponiveis,
            'lower_boundary': lower_boundary,
            'upper_boundary': upper_boundary,
            'lower_buyable': lower_buyable,
            'upper_buyable': upper_buyable,
            'lower_active': lower_active,
            'upper_active': upper_active,
            'buyable_in_gap': buyable_in_gap
        })

    # Sort by: 1) size (descending), 2) num_contempladas (descending - safer gaps)
    analyzed_gaps.sort(key=lambda x: (x['size'], x['num_contempladas']), reverse=True)

    print(f"\n{'='*70}")
    print(f"TOP 10 LARGEST GAPS")
    print(f"{'='*70}")
    print(f"\n{'#':<4} {'Gap Range':<18} {'Size':<6} {'Safe':<6} {'Buyable':<9} {'Boundaries':<25}")
    print("-"*70)

    for i, gap in enumerate(analyzed_gaps[:10], 1):
        # Safety = % of gap that is contempladas (safer)
        safety_pct = (gap['num_contempladas'] / gap['size'] * 100) if gap['size'] > 0 else 0

        # Boundary status
        lower_status = "BUY✓" if gap['lower_buyable'] else ("ACT" if gap['lower_active'] else "CON")
        upper_status = "BUY✓" if gap['upper_buyable'] else ("ACT" if gap['upper_active'] else "CON")
        bounds = f"{gap['lower_boundary']}({lower_status}) ← → {gap['upper_boundary']}({upper_status})"

        num_buyable = len(gap['buyable_in_gap'])

        print(f"{i:<4} {gap['start']:4d}-{gap['end']:4d}{'':<8} {gap['size']:<6} {safety_pct:>4.0f}%  {num_buyable:<9} {bounds}")

    # Analyze top 3 gaps in detail
    print(f"\n{'='*70}")
    print(f"DETAILED GAP ANALYSIS (Top 3 Gaps)")
    print(f"{'='*70}")

    for i, gap in enumerate(analyzed_gaps[:3], 1):
        safety_pct = (gap['num_contempladas'] / gap['size'] * 100) if gap['size'] > 0 else 0

        print(f"\n🎯 Gap #{i}: Cotas {gap['start']}-{gap['end']} (size: {gap['size']}, {safety_pct:.0f}% safe)")

        # Boundary status
        if gap['lower_buyable']:
            print(f"   ✓ Lower boundary ({gap['lower_boundary']}) is AVAILABLE TO BUY")
        elif gap['lower_active']:
            print(f"   ✗ Lower boundary ({gap['lower_boundary']}) already ACTIVE (someone owns it)")
        else:
            print(f"   ✗ Lower boundary ({gap['lower_boundary']}) already CONTEMPLADA")

        if gap['upper_buyable']:
            print(f"   ✓ Upper boundary ({gap['upper_boundary']}) is AVAILABLE TO BUY")
        elif gap['upper_active']:
            print(f"   ✗ Upper boundary ({gap['upper_boundary']}) already ACTIVE (someone owns it)")
        else:
            print(f"   ✗ Upper boundary ({gap['upper_boundary']}) already CONTEMPLADA")

        # Show buyable cotas inside the gap
        if len(gap['buyable_in_gap']) > 0:
            print(f"\n   📍 Buyable cotas INSIDE this gap: {len(gap['buyable_in_gap'])} cotas")
            if len(gap['buyable_in_gap']) <= 10:
                print(f"      → {', '.join(map(str, gap['buyable_in_gap']))}")
            else:
                first_5 = ', '.join(map(str, gap['buyable_in_gap'][:5]))
                last_5 = ', '.join(map(str, gap['buyable_in_gap'][-5:]))
                print(f"      → {first_5} ... {last_5}")
            print(f"   💡 Strategy: Buy cotas inside the gap to benefit from draws landing in gap")
        else:
            print(f"\n   ⚠️  No buyable cotas inside this gap (all contempladas)")

    # Find best single cotas FROM DISPONÍVEIS (available to buy)
    print(f"\n{'='*70}")
    print(f"TOP 10 BUYABLE COTAS (Highest Catchment)")
    print(f"{'='*70}")

    buyable_cotas = disponiveis
    print(f"\nCalculating for {len(buyable_cotas)} disponíveis (buyable) cotas...")

    catchments = {}
    draws_map = {}

    for i, cota in enumerate(sorted(buyable_cotas)):
        if i % 100 == 0 and i > 0:
            print(f"  Progress: {i}/{len(buyable_cotas)}")

        # Simulate buying this cota (add to active)
        temp_active = active | {cota}
        catch_count, catch_draws = calculate_catchment(cota, temp_active, total_cotas)
        catchments[cota] = catch_count
        draws_map[cota] = catch_draws

    top_10 = sorted(catchments.items(), key=lambda x: x[1], reverse=True)[:10]

    print(f"\n{'Rank':<6} {'Cota':<8} {'Catchment':<12} {'Probability':<15} {'vs Random'}")
    print("-"*70)

    for rank, (cota, catch) in enumerate(top_10, 1):
        prob = (catch / total_cotas) * 100
        mult = catch
        print(f"{rank:<6} {cota:<8} {catch:<12} {prob:>6.3f}%{'':<8} {mult:.1f}x")

    # Show which draws make each top cota win
    print(f"\n{'='*70}")
    print(f"DRAW ANALYSIS FOR TOP 5 BUYABLE COTAS")
    print(f"{'='*70}")

    for rank, (cota, catch) in enumerate(top_10[:5], 1):
        draws = draws_map[cota]
        print(f"\n#{rank} - Cota {cota} ({catch} draws):")

        # Show draws in compact format
        if len(draws) <= 20:
            print(f"  Draws: {', '.join(map(str, draws))}")
        else:
            # Show first 10 and last 10
            first_10 = ', '.join(map(str, draws[:10]))
            last_10 = ', '.join(map(str, draws[-10:]))
            print(f"  Draws: {first_10} ... {last_10}")
            print(f"  (showing first 10 and last 10 of {len(draws)} total)")

    # Recommendations
    print(f"\n{'='*70}")
    print(f"🎯 STRATEGIC RECOMMENDATIONS")
    print(f"{'='*70}")

    if analyzed_gaps:
        best_gap = analyzed_gaps[0]
        safety_pct = (best_gap['num_contempladas'] / best_gap['size'] * 100) if best_gap['size'] > 0 else 0

        print(f"\n✅ GAP STRATEGY: Target the largest gap")
        print(f"   Gap: Cotas {best_gap['start']}-{best_gap['end']} (size: {best_gap['size']}, {safety_pct:.0f}% safe)")

        if best_gap['lower_buyable'] and best_gap['upper_buyable']:
            print(f"\n   🎯 BEST: Buy BOTH boundaries")
            print(f"   → Cotas: {best_gap['lower_boundary']} AND {best_gap['upper_boundary']}")
            print(f"   → Captures nearly ALL draws landing in gap")
        elif best_gap['lower_buyable']:
            print(f"\n   🎯 Buy lower boundary: Cota {best_gap['lower_boundary']}")
        elif best_gap['upper_buyable']:
            print(f"\n   🎯 Buy upper boundary: Cota {best_gap['upper_boundary']}")
        elif len(best_gap['buyable_in_gap']) > 0:
            print(f"\n   ⚠️  Boundaries already owned by others")
            print(f"   💡 Alternative: Buy cotas INSIDE the gap")
            print(f"   → {len(best_gap['buyable_in_gap'])} buyable cotas available")
            print(f"   → These cotas benefit from proximity to the gap boundaries")
            if len(best_gap['buyable_in_gap']) <= 5:
                print(f"   → Recommended: {', '.join(map(str, best_gap['buyable_in_gap']))}")
            else:
                # Show middle cotas (most benefit from both boundaries)
                middle_idx = len(best_gap['buyable_in_gap']) // 2
                middle_cotas = best_gap['buyable_in_gap'][max(0, middle_idx-2):middle_idx+3]
                print(f"   → Recommended (middle of gap): {', '.join(map(str, middle_cotas))}")

    if top_10:
        best_cota, best_catch = top_10[0]
        best_draws = draws_map[best_cota]
        print(f"\n✅ BEST SINGLE BUYABLE COTA: {best_cota}")
        print(f"   → Catchment: {best_catch} draws")
        print(f"   → Probability: {(best_catch/total_cotas)*100:.2f}%")
        print(f"   → {best_catch}x better than random")
        if len(best_draws) <= 10:
            print(f"   → Wins on draws: {', '.join(map(str, best_draws))}")

    print(f"\n{'='*70}")


if __name__ == "__main__":
    main()
