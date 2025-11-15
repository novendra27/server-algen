"""
ga_engine.py
GA algorithm wrapper - Konversi dari algen.ipynb ke production code
"""

import pandas as pd
import numpy as np
import time
from typing import Dict, List, Any


# ========================================
# DATA PREPROCESSING
# ========================================

def preprocess_data(df: pd.DataFrame, jumlah_kelompok: int) -> Dict[str, Any]:
    """Preprocess data dan hitung semua statistik yang diperlukan"""
    df_clean = df.copy()
    
    # Normalize HTQ to binary
    df_clean['HTQ'] = df_clean['HTQ'].apply(lambda x: 1 if str(x).lower() in ['ya', 'lulus', '1', 'y', 't', 'true'] else 0)
    
    # Calculate aggregate statistics
    N = len(df_clean)
    L = (df_clean['Jenis_Kelamin'] == 'LK').sum()
    P = (df_clean['Jenis_Kelamin'] == 'PR').sum()
    K = jumlah_kelompok
    
    # Calculate expected proportions
    PL = L / N if N > 0 else 0
    PP = P / N if N > 0 else 0
    
    # Calculate expected sizes per group
    A = N // K
    sisa = N % K
    
    expected_sizes = [A + 1 if i < sisa else A for i in range(K)]
    
    # Max fitness
    max_fitness = K * 4
    
    return {
        'df_clean': df_clean,
        'N': N,
        'L': L,
        'P': P,
        'K': K,
        'PL': PL,
        'PP': PP,
        'A': A,
        'sisa': sisa,
        'expected_sizes': expected_sizes,
        'max_fitness': max_fitness
    }


# ========================================
# CONSTRAINT EVALUATION FUNCTIONS
# ========================================

def evaluate_C1(group_df: pd.DataFrame) -> int:
    """C1: Minimal ada 1 anggota HTQ di kelompok"""
    htq_count = group_df['HTQ'].sum()
    return 1 if htq_count >= 1 else 0


def evaluate_C2(group_df: pd.DataFrame) -> int:
    """C2: Jumlah jurusan berbeda > 50% dari ukuran kelompok"""
    unique_majors = group_df['Jurusan'].nunique()
    threshold = len(group_df) * 0.5
    return 1 if unique_majors > threshold else 0


def evaluate_C3(group_df: pd.DataFrame, PL: float, PP: float) -> int:
    """C3: Proporsi gender menyimpang ±10% dari proporsi ideal"""
    n_group = len(group_df)
    if n_group == 0:
        return 0
    
    lk_count = (group_df['Jenis_Kelamin'] == 'LK').sum()
    pr_count = (group_df['Jenis_Kelamin'] == 'PR').sum()
    
    lk_prop = lk_count / n_group
    pr_prop = pr_count / n_group
    
    lk_dev = abs(lk_prop - PL)
    pr_dev = abs(pr_prop - PP)
    
    return 1 if (lk_dev <= 0.1 and pr_dev <= 0.1) else 0


def evaluate_C4(group_df: pd.DataFrame, expected_size: int) -> int:
    """C4: Ukuran kelompok sesuai expected size"""
    return 1 if len(group_df) == expected_size else 0


# ========================================
# KROMOSOM DECODING & FITNESS
# ========================================

def decode_kromosom(kromosom: np.ndarray, df_clean: pd.DataFrame, expected_sizes: List[int]) -> List[pd.DataFrame]:
    """Decode permutation kromosom into groups"""
    groups = []
    start_idx = 0
    
    for i, size in enumerate(expected_sizes):
        end_idx = start_idx + size
        group_ids = kromosom[start_idx:end_idx]
        group_df = df_clean[df_clean['ID'].isin(group_ids)].copy()
        groups.append(group_df)
        start_idx = end_idx
    
    return groups


def calculate_fitness(kromosom: np.ndarray, df_clean: pd.DataFrame, expected_sizes: List[int], PL: float, PP: float) -> int:
    """Calculate total fitness of a kromosom"""
    groups = decode_kromosom(kromosom, df_clean, expected_sizes)
    total_fitness = 0
    
    for i, group_df in enumerate(groups):
        c1 = evaluate_C1(group_df)
        c2 = evaluate_C2(group_df)
        c3 = evaluate_C3(group_df, PL, PP)
        c4 = evaluate_C4(group_df, expected_sizes[i])
        
        total_fitness += (c1 + c2 + c3 + c4)
    
    return total_fitness


# ========================================
# POPULATION INITIALIZATION
# ========================================

def initialize_population(df_clean: pd.DataFrame, popsize: int) -> List[np.ndarray]:
    """Initialize population with random permutations"""
    student_ids = df_clean['ID'].values
    population = []
    
    for _ in range(popsize):
        kromosom = np.random.permutation(student_ids)
        population.append(kromosom)
    
    return population


# ========================================
# PARENT SELECTION
# ========================================

def select_parents_for_crossover(population: List[np.ndarray], cr: float) -> List[tuple]:
    """Select parent pairs for crossover based on CR"""
    num_crossover = int(len(population) * cr)
    if num_crossover % 2 != 0:
        num_crossover += 1
    
    # Need at least 2 individuals for crossover
    if num_crossover < 2 or len(population) < 2:
        return []
    
    # Can't select more than population size
    num_crossover = min(num_crossover, len(population))
    
    indices = np.random.choice(len(population), num_crossover, replace=False)
    parent_pairs = [(population[indices[i]], population[indices[i+1]]) 
                    for i in range(0, num_crossover, 2)]
    return parent_pairs


def select_parents_for_mutation(population: List[np.ndarray], mr: float) -> List[np.ndarray]:
    """Select parents for mutation based on MR"""
    num_mutation = int(len(population) * mr)
    
    # Handle edge cases
    if num_mutation == 0 or len(population) == 0:
        return []
    
    num_mutation = min(num_mutation, len(population))
    indices = np.random.choice(len(population), num_mutation, replace=False)
    return [population[i] for i in indices]


# ========================================
# PMX CROSSOVER
# ========================================

def pmx_crossover(parent1: np.ndarray, parent2: np.ndarray) -> tuple:
    """
    Partially Mapped Crossover (PMX) - Fixed version
    Prevents infinite loops by following the mapping chain properly
    """
    size = len(parent1)
    
    # Choose two random cut points
    cx_point1 = np.random.randint(0, size)
    cx_point2 = np.random.randint(0, size)
    if cx_point1 > cx_point2:
        cx_point1, cx_point2 = cx_point2, cx_point1
    
    # Ensure we have at least some segment to swap
    if cx_point1 == cx_point2:
        cx_point2 = min(cx_point1 + 1, size)
    
    # Initialize offspring as copies
    child1 = parent1.copy()
    child2 = parent2.copy()
    
    # Swap middle segments
    child1[cx_point1:cx_point2] = parent2[cx_point1:cx_point2]
    child2[cx_point1:cx_point2] = parent1[cx_point1:cx_point2]
    
    # Fix conflicts using proper PMX algorithm
    def fix_conflicts_pmx(child, p1, p2, start, end):
        """Fix conflicts by following the mapping relationship"""
        middle_values = set(child[start:end])
        
        for i in range(size):
            if i < start or i >= end:
                if child[i] in middle_values:
                    value = child[i]
                    visited = set()
                    
                    while value in middle_values and value not in visited:
                        visited.add(value)
                        
                        try:
                            idx_in_p2 = np.where(p2[start:end] == value)[0][0] + start
                            value = p1[idx_in_p2]
                        except (IndexError, TypeError):
                            break
                    
                    if value not in middle_values:
                        child[i] = value
    
    fix_conflicts_pmx(child1, parent1, parent2, cx_point1, cx_point2)
    fix_conflicts_pmx(child2, parent2, parent1, cx_point1, cx_point2)
    
    return child1, child2


# ========================================
# RECIPROCAL EXCHANGE MUTATION
# ========================================

def reciprocal_exchange_mutation(parent: np.ndarray) -> np.ndarray:
    """Swap two random genes"""
    child = parent.copy()
    idx1, idx2 = np.random.choice(len(child), 2, replace=False)
    child[idx1], child[idx2] = child[idx2], child[idx1]
    return child


# ========================================
# ELITISM REPLACEMENT STRATEGY
# ========================================

def elitism_replacement_optimized(population: List[np.ndarray], population_fitness: List[int], 
                                   offspring: List[np.ndarray], df_clean: pd.DataFrame, 
                                   expected_sizes: List[int], PL: float, PP: float, 
                                   popsize: int) -> tuple:
    """
    Optimized elitism with fitness caching.
    Only calculates fitness for NEW offspring, reuses existing population fitness.
    """
    # Handle empty offspring case
    if len(offspring) == 0:
        sorted_indices = sorted(range(len(population)), 
                              key=lambda i: population_fitness[i], 
                              reverse=True)
        new_population = [population[i] for i in sorted_indices[:popsize]]
        new_fitness = [population_fitness[i] for i in sorted_indices[:popsize]]
        return new_population, new_fitness
    
    # Calculate fitness ONLY for new offspring
    offspring_fitness = [calculate_fitness(ind, df_clean, expected_sizes, PL, PP) 
                        for ind in offspring]
    
    # Combine populations and fitness scores
    combined = population + offspring
    combined_fitness = population_fitness + offspring_fitness
    
    # Sort by fitness (descending)
    sorted_indices = sorted(range(len(combined)), 
                          key=lambda i: combined_fitness[i], 
                          reverse=True)
    
    # Select top PopSize individuals
    new_population = [combined[i] for i in sorted_indices[:popsize]]
    new_fitness = [combined_fitness[i] for i in sorted_indices[:popsize]]
    
    return new_population, new_fitness


# ========================================
# MAIN GA FUNCTION
# ========================================

def run_genetic_algorithm(data: List[Dict[str, Any]], parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main function untuk menjalankan Algoritma Genetika
    
    Args:
        data: List of dict mahasiswa data
        parameters: Dict of GA parameters (popsize, generation, cr, mr, kriteria_penghentian, jumlah_kelompok)
        
    Returns:
        Dict containing kelompok_list, statistics, and kelompok_details
    """
    # Extract parameters with backward compatibility
    jumlah_kelompok = parameters.get('jumlah_kelompok')
    popsize = parameters.get('popsize')
    cr = parameters.get('cr')
    mr = parameters.get('mr')
    max_generation = parameters.get('generation', parameters.get('max_generation'))  # Support both
    target_fitness = parameters.get('kriteria_penghentian', parameters.get('target_fitness'))  # Support both
    
    # Convert data to DataFrame
    df = pd.DataFrame(data)
    
    # Preprocess
    preprocessed = preprocess_data(df, jumlah_kelompok)
    df_clean = preprocessed['df_clean']
    N = preprocessed['N']
    K = preprocessed['K']
    PL = preprocessed['PL']
    PP = preprocessed['PP']
    expected_sizes = preprocessed['expected_sizes']
    max_fitness = preprocessed['max_fitness']
    
    # Validation
    if len(data) < jumlah_kelompok:
        raise ValueError(f"Jumlah mahasiswa ({len(data)}) harus >= jumlah kelompok ({jumlah_kelompok})")
    
    # Initialize
    start_time = time.time()
    population = initialize_population(df_clean, popsize)
    
    # Calculate initial fitness
    population_fitness = []
    for kromosom in population:
        fitness = calculate_fitness(kromosom, df_clean, expected_sizes, PL, PP)
        population_fitness.append(fitness)
    
    # Track best solution
    best_overall_fitness = max(population_fitness)
    best_overall_solution = population[population_fitness.index(best_overall_fitness)].copy()
    
    # Main GA Loop
    generation = 0
    for generation in range(1, max_generation + 1):
        # Crossover
        parent_pairs = select_parents_for_crossover(population, cr)
        offspring_cx = []
        for p1, p2 in parent_pairs:
            c1, c2 = pmx_crossover(p1, p2)
            offspring_cx.extend([c1, c2])
        
        # Mutation
        parents_mut = select_parents_for_mutation(population, mr)
        offspring_mut = [reciprocal_exchange_mutation(p) for p in parents_mut]
        
        # Combine offspring
        offspring = offspring_cx + offspring_mut
        
        # Replacement
        population, population_fitness = elitism_replacement_optimized(
            population, population_fitness, offspring, 
            df_clean, expected_sizes, PL, PP, popsize
        )
        
        # Track best
        best_fitness = population_fitness[0]
        
        # Update best overall
        if best_fitness > best_overall_fitness:
            best_overall_fitness = best_fitness
            best_overall_solution = population[0].copy()
        
        # Check termination
        if best_fitness >= target_fitness * max_fitness:
            break
    
    # Calculate execution time
    total_time = time.time() - start_time
    
    # Decode best solution
    best_groups = decode_kromosom(best_overall_solution, df_clean, expected_sizes)
    
    # Prepare kelompok_list
    kelompok_list = []
    for group_df in best_groups:
        kelompok_list.append(group_df['ID'].tolist())
    
    # Prepare kelompok_details
    kelompok_details = []
    for i, group_df in enumerate(best_groups, start=1):
        c1 = evaluate_C1(group_df)
        c2 = evaluate_C2(group_df)
        c3 = evaluate_C3(group_df, PL, PP)
        c4 = evaluate_C4(group_df, expected_sizes[i-1])
        
        kelompok_details.append({
            'kelompok_id': i,
            'anggota': group_df['ID'].tolist(),
            'jumlah_anggota': len(group_df),
            'constraints': {
                'C1_HTQ': c1,
                'C2_Heterogenitas_Jurusan': c2,
                'C3_Proporsi_Gender': c3,
                'C4_Jumlah_Anggota': c4
            },
            'score': c1 + c2 + c3 + c4
        })
    
    # Prepare result
    result = {
        'kelompok_list': kelompok_list,
        'statistics': {
            'best_fitness': int(best_overall_fitness),
            'best_normalized_fitness': float(best_overall_fitness / max_fitness),
            'total_generations': generation,
            'execution_time_seconds': round(total_time, 2),
            'max_fitness': int(max_fitness)
        },
        'kelompok_details': kelompok_details
    }
    
    return result
