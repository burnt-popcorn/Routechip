"""RouteChip Automata Module (FLAT: Formal Languages and Automata Theory).

Module 1: Deterministic Finite Automata (1.5)
Designs and simulates a DFA M = (Q, Σ, δ, q0, F) to validate routing commands
before execution by the simulated CPU.

Grammar / Language:
  L = { 'ROUTE <src> <dst>' | <src>, <dst> ∈ {A, B, C, D, E} }
Length of valid command is strictly 9 characters.
"""

from typing import Dict, List, Optional, Tuple
import pandas as pd

# Base transitions dictionary for backwards-compatibility:
# Language: ROUTE <space> [A-E] <space> [A-E]
TRANSITIONS: Dict[Tuple[str, str], str] = {}
for index, char in enumerate('ROUTE'):
    TRANSITIONS[(f'q{index}', char)] = f'q{index + 1}'
TRANSITIONS[('q5', ' ')] = 'q6'
for node in 'ABCDE':
    TRANSITIONS[('q6', node)] = 'q7'
TRANSITIONS[('q7', ' ')] = 'q8'
for node in 'ABCDE':
    TRANSITIONS[('q8', node)] = 'q9'

STATES = [f'q{i}' for i in range(10)] + ['DEAD']
ACCEPT_STATES = {'q9'}
START_STATE = 'q0'
ALPHABET = list('ROUTE ABCDE')

STATE_DESCRIPTIONS = {
    'q0': "Initial state: Waiting for opcode prefix 'R'",
    'q1': "Matched 'R': Waiting for 'O'",
    'q2': "Matched 'RO': Waiting for 'U'",
    'q3': "Matched 'ROU': Waiting for 'T'",
    'q4': "Matched 'ROUT': Waiting for 'E'",
    'q5': "Matched opcode 'ROUTE': Waiting for delimiter space (' ')",
    'q6': "Delimiter passed: Waiting for source router [A-E]",
    'q7': "Source router stored: Waiting for delimiter space (' ')",
    'q8': "Delimiter passed: Waiting for destination router [A-E]",
    'q9': "ACCEPTING STATE: Valid instruction 'ROUTE <src> <dst>' recognized",
    'DEAD': "TRAP / REJECT STATE: Syntax or lexical error encountered",
}


def validate_command(command: str) -> Tuple[bool, List[str]]:
    """Validate a command string using the DFA transition table.

    Returns:
        (is_valid, trace): boolean acceptance flag and the sequence of states.
    """
    state = START_STATE
    trace = [state]
    for char in command:
        state = TRANSITIONS.get((state, char), 'DEAD')
        trace.append(state)
        if state == 'DEAD':
            break
    return state == 'q9', trace


def get_step_by_step_trace(command: str) -> List[Dict[str, str]]:
    """Generate an enriched, human-readable step-by-step trace of the DFA execution."""
    state = START_STATE
    steps = []

    for i, char in enumerate(command):
        from_state = state
        display_char = '␣ (space)' if char == ' ' else char
        next_state = TRANSITIONS.get((from_state, char), 'DEAD')

        if next_state != 'DEAD':
            status = 'VALID'
            explanation = f"Symbol '{display_char}' matched valid transition: {from_state} → {next_state}"
        else:
            status = 'REJECTED'
            expected = _get_expected_symbols(from_state)
            explanation = f"Invalid symbol '{display_char}' at position {i}. Expected {expected}. Transition to DEAD state."

        steps.append({
            'step': i + 1,
            'position': i,
            'symbol': display_char,
            'raw_char': char,
            'from_state': from_state,
            'to_state': next_state,
            'status': status,
            'explanation': explanation,
            'state_meaning': STATE_DESCRIPTIONS.get(next_state, '')
        })

        state = next_state
        if state == 'DEAD':
            # Any remaining unread characters are dropped into DEAD
            for j, remaining_char in enumerate(command[i + 1:], start=i + 1):
                rem_disp = '␣ (space)' if remaining_char == ' ' else remaining_char
                steps.append({
                    'step': j + 1,
                    'position': j,
                    'symbol': rem_disp,
                    'raw_char': remaining_char,
                    'from_state': 'DEAD',
                    'to_state': 'DEAD',
                    'status': 'REJECTED',
                    'explanation': f"Trap state absorbs trailing symbol '{rem_disp}'.",
                    'state_meaning': STATE_DESCRIPTIONS['DEAD']
                })
            break

    # If string ended prematurely before reaching q9
    if state != 'DEAD' and state != 'q9':
        steps.append({
            'step': len(command) + 1,
            'position': len(command),
            'symbol': '␀ (EOF)',
            'raw_char': '',
            'from_state': state,
            'to_state': 'REJECT (Incomplete)',
            'status': 'INCOMPLETE',
            'explanation': f"Input ended prematurely in non-accepting state {state}. Expected {_get_expected_symbols(state)}.",
            'state_meaning': "Incomplete command string"
        })

    return steps


def _get_expected_symbols(state: str) -> str:
    """Helper to retrieve expected symbols for a given state."""
    expected = [char if char != ' ' else "' ' (space)" for (s, char) in TRANSITIONS.keys() if s == state]
    if not expected:
        return 'None (End of Instruction)'
    if len(expected) > 3:
        return '[A, B, C, D, E]'
    return f"[{', '.join(expected)}]"


def get_dfa_metadata() -> Dict[str, object]:
    """Return the formal 5-tuple M = (Q, Σ, δ, q0, F) and properties."""
    return {
        'states_Q': STATES,
        'alphabet_Sigma': ['R', 'O', 'U', 'T', 'E', '␣ (space)', 'A', 'B', 'C', 'D', 'E'],
        'start_state_q0': START_STATE,
        'accept_states_F': list(ACCEPT_STATES),
        'trap_state': 'DEAD',
        'regular_expression': r'^ROUTE [A-E] [A-E]$',
        'formal_description': (
            "DFA M = (Q, Σ, δ, q0, F) recognizing the regular language of network routing instructions. "
            "A deterministic finite automaton transitions across 10 defined operational states "
            "and 1 non-recovering dead/trap state. Exactly 9 valid characters lead to accepting state q9."
        )
    }


def get_transition_matrix_df() -> pd.DataFrame:
    """Return the complete transition table δ: Q × Σ → Q as a formatted pandas DataFrame."""
    columns = ['R', 'O', 'U', 'T', 'E', '␣ (space)', 'A..E', 'Other']
    matrix = []

    for s in STATES:
        row = {'State': s, 'Description': STATE_DESCRIPTIONS.get(s, '')}
        for col in columns:
            if col == '␣ (space)':
                val = TRANSITIONS.get((s, ' '), 'DEAD' if s != 'DEAD' else 'DEAD')
            elif col == 'A..E':
                # Check for router symbols
                trans = [TRANSITIONS.get((s, node)) for node in 'ABCDE']
                val = trans[0] if trans[0] is not None else ('DEAD' if s != 'DEAD' else 'DEAD')
            elif col == 'Other':
                val = 'DEAD'
            else:
                val = TRANSITIONS.get((s, col), 'DEAD' if s != 'DEAD' else 'DEAD')
            row[col] = val
        matrix.append(row)

    df = pd.DataFrame(matrix)
    df.set_index('State', inplace=True)
    return df


def get_dfa_dot(command: Optional[str] = None) -> str:
    """Generate Graphviz DOT representation of the DFA with execution trace highlighting."""
    trace: List[str] = []
    is_valid = False
    traversed_edges: set = set()
    dead_transition = None

    if command:
        is_valid, trace = validate_command(command)
        # Identify traversed transitions
        curr = START_STATE
        for char in command:
            nxt = TRANSITIONS.get((curr, char), 'DEAD')
            traversed_edges.add((curr, nxt, char))
            if nxt == 'DEAD':
                dead_transition = (curr, char)
                break
            curr = nxt

    # Build DOT
    dot_lines = [
        'digraph RouteChipDFA {',
        '  graph [rankdir=LR, bgcolor="transparent", margin=0.1];',
        '  node [fontname="Helvetica, Arial, sans-serif", fontsize=11, shape=circle, style="filled,bold", fillcolor="#f8fafc", color="#64748b", penwidth=1.5];',
        '  edge [fontname="Helvetica, Arial, sans-serif", fontsize=10, color="#64748b", penwidth=1.2];',
        '',
        '  // Start pointer',
        '  __start [shape=point, width=0.1, color="#0f172a"];',
        '  __start -> q0 [label=" start", color="#0f172a", penwidth=2.0];',
        '',
        '  // Accept State',
        '  q9 [shape=doublecircle];',
    ]

    # Style nodes based on trace
    active_nodes = set(trace) if trace else set()
    for s in STATES:
        if s == 'DEAD':
            continue
        if s in active_nodes:
            if is_valid:
                dot_lines.append(f'  {s} [fillcolor="#dcfce7", color="#16a34a", fontcolor="#14532d", penwidth=2.5];')
            else:
                dot_lines.append(f'  {s} [fillcolor="#fef3c7", color="#d97706", fontcolor="#78350f", penwidth=2.0];')

    # Trap state inclusion
    if 'DEAD' in active_nodes or command is None:
        dot_lines.append('  DEAD [shape=octagon, fillcolor="#fee2e2", color="#dc2626", fontcolor="#991b1b", penwidth=2.5];')
        if 'DEAD' in active_nodes:
            dot_lines.append('  DEAD -> DEAD [label=" any", color="#dc2626", fontcolor="#dc2626", penwidth=2.0];')
        else:
            dot_lines.append('  DEAD -> DEAD [label=" any", color="#94a3b8", fontcolor="#64748b"];')

    # Primary pipeline transitions
    transitions_spec = [
        ('q0', 'q1', 'R'),
        ('q1', 'q2', 'O'),
        ('q2', 'q3', 'U'),
        ('q3', 'q4', 'T'),
        ('q4', 'q5', 'E'),
        ('q5', 'q6', '␣'),
        ('q6', 'q7', '[A-E]'),
        ('q7', 'q8', '␣'),
        ('q8', 'q9', '[A-E]'),
    ]

    for u, v, lbl in transitions_spec:
        # Check if traversed
        edge_traversed = False
        if command:
            for eu, ev, echar in traversed_edges:
                if eu == u and ev == v:
                    edge_traversed = True
                    break

        if edge_traversed:
            color = "#16a34a" if is_valid else "#d97706"
            dot_lines.append(f'  {u} -> {v} [label=" {lbl}", color="{color}", fontcolor="{color}", penwidth=3.0];')
        else:
            dot_lines.append(f'  {u} -> {v} [label=" {lbl}"];')

    # If a dead transition happened, draw it distinctly
    if dead_transition:
        u, char = dead_transition
        disp = '␣' if char == ' ' else char
        dot_lines.append(f'  {u} -> DEAD [label=" \'{disp}\' (bad)", color="#dc2626", fontcolor="#dc2626", penwidth=2.5, style="dashed"];')

    dot_lines.append('}')
    return '\n'.join(dot_lines)
