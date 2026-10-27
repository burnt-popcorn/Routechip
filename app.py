"""RouteChip: An Integrated Network Routing and CPU Execution Simulator.

Integrated Academic Project:
- DAA (Module 3.13): Dijkstra's Shortest Path Algorithm (Greedy, Min-Heap)
- COA (Module 2.1): CPU Instruction Cycle (Fetch, Decode, Execute, Write-back)
- FLAT (Module 1.5): Deterministic Finite Automaton (DFA) Command Validator

Built with Python and Streamlit.
"""

from copy import deepcopy
import io
import time
import unittest
import pandas as pd
import streamlit as st

from automata import (
    STATE_DESCRIPTIONS,
    get_dfa_dot,
    get_dfa_metadata,
    get_step_by_step_trace,
    get_transition_matrix_df,
    validate_command,
)
from cpu import execute_command, get_cpu_datapath_dot
from routing import (
    GRAPH,
    PRESET_TOPOLOGIES,
    dijkstra_detailed,
    get_network_dot,
    shortest_path,
)
import test_routechip

# ---------------------------------------------------------
# Page Configuration & Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title='RouteChip — Network Routing & CPU Simulator',
    page_icon='01.png',
    layout='wide',
    initial_sidebar_state='expanded',
)

# Custom Styling
st.markdown(
    """
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        background: #1d4ed8;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #475569;
        margin-bottom: 1.2rem;
    }
    .badge-flat {
        background-color: #ede9fe;
        color: #6d28d9;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 0.8rem;
        border: 1px solid #c4b5fd;
    }
    .badge-coa {
        background-color: #dbeafe;
        color: #1d4ed8;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 0.8rem;
        border: 1px solid #93c5fd;
    }
    .badge-daa {
        background-color: #dcfce7;
        color: #15803d;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 0.8rem;
        border: 1px solid #86efac;
    }
    .register-box {
        background: #0f172a;
        color: #38bdf8;
        font-family: 'Courier New', Courier, monospace;
        padding: 12px;
        border-radius: 8px;
        border-left: 4px solid #38bdf8;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .metric-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 12px;
        text-align: center;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------
if 'command' not in st.session_state:
    st.session_state.command = 'ROUTE A D'

if 'selected_topology_name' not in st.session_state:
    st.session_state.selected_topology_name = 'Default (5 Routers, Isolated E)'

if 'active_graph' not in st.session_state:
    st.session_state.active_graph = deepcopy(
        PRESET_TOPOLOGIES['Default (5 Routers, Isolated E)']
    )

# ---------------------------------------------------------
# Sidebar: Controls, Presets & Topology
# ---------------------------------------------------------
with st.sidebar:
    st.markdown('## ⚡ RouteChip Simulator')
    st.caption('Integrated Multi-Disciplinary Dashboard')

    st.markdown('---')
    st.markdown('####  Routing Instruction')

    # Preset selection buttons
    st.markdown('**Quick Presets:**')
    c1, c2 = st.columns(2)
    with c1:
        if st.button('🟢 ROUTE A D', use_container_width=True):
            st.session_state.command = 'ROUTE A D'
        if st.button('🟡 ROUTE A E (Unreach)', use_container_width=True):
            st.session_state.command = 'ROUTE A E'
        if st.button('🔵 ROUTE B B (Zero)', use_container_width=True):
            st.session_state.command = 'ROUTE B B'
    with c2:
        if st.button('🟣 ROUTE C D', use_container_width=True):
            st.session_state.command = 'ROUTE C D'
        if st.button('🔴 PING A D (DFA Fail)', use_container_width=True):
            st.session_state.command = 'PING A D'
        if st.button('🔴 ROUTE A Z (Bad Node)', use_container_width=True):
            st.session_state.command = 'ROUTE A Z'

    cmd_input = st.text_input(
        'Command Input (Format: ROUTE <src> <dst>)',
        value=st.session_state.command,
        help='Valid routers in DFA: A, B, C, D, E. Strict uppercase syntax.',
    )
    st.session_state.command = cmd_input

    st.markdown('---')
    st.markdown('#### Network Topology')

    topology_choice = st.selectbox(
        'Choose Network Topology',
        options=list(PRESET_TOPOLOGIES.keys()) + ['Custom Topology Builder'],
        index=list(PRESET_TOPOLOGIES.keys()).index(
            st.session_state.selected_topology_name
        )
        if st.session_state.selected_topology_name in PRESET_TOPOLOGIES
        else 0,
    )

    if topology_choice != 'Custom Topology Builder':
        if topology_choice != st.session_state.selected_topology_name:
            st.session_state.selected_topology_name = topology_choice
            st.session_state.active_graph = deepcopy(
                PRESET_TOPOLOGIES[topology_choice]
            )
    else:
        st.session_state.selected_topology_name = 'Custom Topology Builder'
        st.markdown('**Edge Weight Editor:**')
        node_u = st.selectbox(
            'Node 1', options=['A', 'B', 'C', 'D', 'E'], index=0
        )
        node_v = st.selectbox(
            'Node 2', options=['A', 'B', 'C', 'D', 'E'], index=1
        )
        weight_val = st.number_input(
            'Edge Weight (≥ 0)', min_value=0, max_value=50, value=3
        )
        if st.button('Set / Add Edge'):
            if node_u != node_v:
                st.session_state.active_graph.setdefault(node_u, {})[
                    node_v
                ] = int(weight_val)
                st.session_state.active_graph.setdefault(node_v, {})[
                    node_u
                ] = int(weight_val)
                st.success(f'Added edge {node_u}—{node_v} with weight {weight_val}')
            else:
                st.warning('Self-edges are not needed.')

    if st.button('🔄 Reset Topology to Default', use_container_width=True):
        st.session_state.selected_topology_name = (
            'Default (5 Routers, Isolated E)'
        )
        st.session_state.active_graph = deepcopy(GRAPH)
        st.session_state.command = 'ROUTE A D'
        st.rerun()

    st.markdown('---')
    st.markdown(
        """
    **Academic Syllabus Alignment:**
    - 🟣 **FLAT 1.5:** DFA Parser
    - 🔵 **COA 2.1:** Instruction Cycle
    - 🟢 **DAA 3.13:** Dijkstra Shortest Path
    """
    )

# ---------------------------------------------------------
# Execution Engine Pipeline
# ---------------------------------------------------------
command_to_run = st.session_state.command.strip()
graph_to_use = st.session_state.active_graph

# Execute via simulated CPU
exec_result = execute_command(command_to_run, graph=graph_to_use)
is_valid = exec_result['valid']
registers = exec_result['registers']
stages = exec_result['stages']
path = exec_result['path']
cost = exec_result['cost']
steps = exec_result['steps']
states = exec_result['states']
detailed_routing = exec_result.get('detailed_routing')

# ---------------------------------------------------------
# Main Page Header & Top Metrics
# ---------------------------------------------------------
st.markdown(
    '<div class="main-header">RouteChip: Integrated Network & CPU Simulator</div>',
    unsafe_allow_html=True,
)
st.markdown(
    """
<div class="sub-header">
    <span class="badge-flat">FLAT: DFA Command Validation (1.5)</span> &nbsp;⨁&nbsp;
    <span class="badge-coa">COA: CPU Instruction Cycle (2.1)</span> &nbsp;⨁&nbsp;
    <span class="badge-daa">DAA: Dijkstra Shortest Path (3.13)</span>
</div>
""",
    unsafe_allow_html=True,
)

# Top KPI Metric Row
m1, m2, m3, m4, m5 = st.columns(5)
with m1:
    if is_valid:
        st.metric('FLAT DFA Status', 'ACCEPTED', delta='Valid Syntax')
    else:
        st.metric(
            'FLAT DFA Status',
            'REJECTED',
            delta='Syntax Error',
            delta_color='inverse',
        )

with m2:
    stage_count = len(stages)
    st.metric(
        'COA Pipeline Stages',
        f'{stage_count} / 4 Stages',
        delta='Fetch ➔ WB' if is_valid else 'Halted at Decode',
    )

with m3:
    if is_valid:
        cost_str = str(cost) if cost is not None else '∞ (Unreachable)'
        st.metric(
            'DAA Shortest Cost',
            cost_str,
            delta='Optimized' if cost is not None else 'No Path',
        )
    else:
        st.metric('DAA Shortest Cost', 'N/A', delta='Execution Skipped')

with m4:
    if is_valid and path:
        st.metric('Calculated Route', ' ➔ '.join(path))
    elif is_valid:
        st.metric('Calculated Route', 'None (Isolated)')
    else:
        st.metric('Calculated Route', 'N/A')

with m5:
    total_cycles = sum(s.get('clock_cycles', 1) for s in stages)
    st.metric(
        'Total Clock Cycles',
        f'{total_cycles} Cycles',
        delta='Hardware Execution Time',
    )

st.markdown('')

# ---------------------------------------------------------
# Primary Tabs
# ---------------------------------------------------------
tab_overview, tab_flat, tab_coa, tab_daa, tab_tests, tab_theory = st.tabs([
    'Integrated Architecture',
    'FLAT: DFA Command Validator',
    'COA: CPU Instruction Cycle',
    'DAA: Dijkstra Shortest Path',
    'Test Suite & Verification',
    'Academic Theory & Mapping',
])

# =========================================================
# TAB 1: INTEGRATED ARCHITECTURE
# =========================================================
with tab_overview:
    st.subheader('System Architecture & Cross-Module Dataflow')
    st.markdown(
        """
    **RouteChip** unifies three core computer science disciplines into an end-to-end processing pipeline:
    1. **FLAT (Automata):** Validates raw command strings using a **Deterministic Finite Automaton ($M$)**. Rejects illegal opcodes or parameters before CPU dispatch.
    2. **COA (Architecture):** Carries valid instructions through the classical **Fetch-Decode-Execute-WriteBack** cycle, maintaining internal CPU registers (`PC`, `IR`, `MAR`, `MBR`, `SRC`, `DST`, `COST`, `FLAGS`).
    3. **DAA (Algorithms):** The CPU execution coprocessor solves the shortest path across the network topology using **Dijkstra's Greedy Algorithm with a Min-Heap Priority Queue**.
    """
    )

    col_diag, col_reg = st.columns([1.3, 1])

    with col_diag:
        st.markdown('##### Real-Time Network Routing Visualization')
        source_node = registers.get('SRC')
        dest_node = registers.get('DST')
        visited_nodes = detailed_routing['visited'] if detailed_routing else set()

        net_dot = get_network_dot(
            graph_to_use,
            path=path if is_valid else [],
            source=source_node,
            destination=dest_node,
            visited=visited_nodes,
        )
        st.graphviz_chart(net_dot, use_container_width=True)

        if is_valid:
            if path:
                st.success(
                    f"✅ **Optimal Path Discovered:** `{' ➔ '.join(path)}` with minimal latency cost **{cost}**."
                )
            else:
                st.warning(
                    f"⚠️ Destination **{dest_node}** is mathematically unreachable from source **{source_node}** in this topology."
                )
        else:
            st.error(
                '❌ Instruction validation failed in FLAT DFA. Coprocessor was not dispatched.'
            )

    with col_reg:
        st.markdown('##### Live CPU Datapath & Register File')
        flags_data = registers.get(
            'FLAGS', {'Z': 0, 'U': 0, 'V': 0, 'ERR': 0}
        )

        st.markdown(
            f"""
        <div class="register-box">
            <b>CPU REGISTER FILE (Cycle State):</b><br>
            ------------------------------------<br>
            <b>PC   (Program Counter)       :</b> {registers['PC']}<br>
            <b>MAR  (Memory Address Reg)    :</b> {registers['MAR']}<br>
            <b>MBR  (Memory Buffer Reg)     :</b> "{registers['MBR']}"<br>
            <b>IR   (Instruction Reg)       :</b> "{registers['IR']}"<br>
            <b>SRC  (Source Router Reg)     :</b> {registers['SRC'] or 'NONE'}<br>
            <b>DST  (Destination Router Reg):</b> {registers['DST'] or 'NONE'}<br>
            <b>COST (Shortest Path Reg)     :</b> {registers['COST'] if registers['COST'] is not None else 'NULL'}<br>
            ------------------------------------<br>
            <b>STATUS FLAGS (ALU / RPU):</b><br>
            • Z (Zero Flag, Same Node)     : <b>{flags_data['Z']}</b><br>
            • U (Unreachable Flag)         : <b>{flags_data['U']}</b><br>
            • V (Valid Instruction Flag)   : <b>{flags_data['V']}</b><br>
            • ERR (DFA Lexical/Syntax Err) : <b>{flags_data['ERR']}</b>
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.markdown('##### Pipeline Stages Summary')
        for stage_info in stages:
            stage_name = stage_info['stage']
            stage_stat = stage_info.get('status', 'SUCCESS')
            color = (
                '🟢'
                if stage_stat == 'SUCCESS'
                else ('🟡' if stage_stat == 'UNREACHABLE' else '🔴')
            )
            st.write(
                f"{color} **{stage_name}** ({stage_info.get('clock_cycles', 1)} cycles) — *{stage_info['details']}*"
            )

# =========================================================
# TAB 2: FLAT - DFA COMMAND VALIDATOR
# =========================================================
with tab_flat:
    st.subheader(
        'FLAT (Module 1.5): Deterministic Finite Automaton (DFA) Command Validator'
    )
    st.markdown(
        r"""
    Before any instruction can be fetched and decoded by the simulated CPU hardware, it must strictly satisfy the 
    formal routing command grammar validated by a Deterministic Finite Automaton $M = (Q, \Sigma, \delta, q_0, F)$.
    """
    )

    dfa_meta = get_dfa_metadata()

    # Formal 5-Tuple Description Card
    with st.expander('Formal 5-Tuple Specification of DFA M', expanded=True):
        fcol1, fcol2 = st.columns(2)
        with fcol1:
            st.markdown(r"""
            - **Finite Set of States ($Q$):** $\{q_0, q_1, q_2, q_3, q_4, q_5, q_6, q_7, q_8, q_9, \text{DEAD}\}$
            - **Input Alphabet ($\Sigma$):** $\{R, O, U, T, E, \text{' '}, A, B, C, D, E\}$
            - **Start / Initial State ($q_0$):** $q_0$
            """)
        with fcol2:
            st.markdown(r"""
            - **Accept / Final States ($F$):** $\{q_9\}$
            - **Trap State:** $\text{DEAD}$ (absorbs illegal characters)
            - **Regular Expression ($L$):** `^ROUTE [A-E] [A-E]$`
            - **Exact Valid Length:** 9 characters
            """)

    st.markdown('#### 🔍 Visual State Diagram with Execution Trace')
    st.caption(
        'Green paths indicate valid state transitions. Orange/Red paths indicate trap transitions.'
    )
    dfa_dot = get_dfa_dot(command_to_run)
    st.graphviz_chart(dfa_dot, use_container_width=True)

    # Step-by-Step Character Trace Table
    st.markdown('#### Step-by-Step Lexical Analysis & Transition Trace')
    trace_steps = get_step_by_step_trace(command_to_run)

    trace_df = pd.DataFrame(trace_steps)[
        [
            'step',
            'symbol',
            'from_state',
            'to_state',
            'status',
            'explanation',
            'state_meaning',
        ]
    ]
    st.dataframe(
        trace_df.rename(
            columns={
                'step': 'Step #',
                'symbol': 'Input Symbol',
                'from_state': 'Current State',
                'to_state': 'Next State',
                'status': 'Status',
                'explanation': 'Transition Event',
                'state_meaning': 'State Significance',
            }
        ),
        use_container_width=True,
    )

    # Full Transition Matrix
    with st.expander('Full State Transition Matrix δ: Q × Σ → Q'):
        matrix_df = get_transition_matrix_df()
        st.dataframe(matrix_df, use_container_width=True)

    # Interactive DFA Sandbox
    st.markdown('#### 🧪 Interactive DFA Sandbox')
    st.caption(
        'Type any experimental command string to test the DFA response in real time:'
    )
    sandbox_input = st.text_input(
        'Sandbox Input',
        value='ROUTE B C',
        key='sandbox_dfa_input',
        label_visibility='collapsed',
    )
    sb_valid, sb_trace = validate_command(sandbox_input)
    if sb_valid:
        st.success(
            f"✅ Accepted! State path: `{' ➔ '.join(sb_trace)}` (Landed in final state q9)"
        )
    else:
        st.error(
            f"❌ Rejected! State path: `{' ➔ '.join(sb_trace)}` (Did not terminate in accept state q9)"
        )

# =========================================================
# TAB 3: COA - CPU INSTRUCTION CYCLE
# =========================================================
with tab_coa:
    st.subheader(
        'COA (Module 2.1): CPU Instruction Cycle Simulation & Datapath'
    )
    st.markdown(
        """
    This module simulates the hardware instruction execution pipeline: **Fetch**, **Decode**, **Execute**, and **Write-Back**.
    Instructions are processed through internal registers using explicit **Register Transfer Notation (RTN / RTL)**.
    """
    )

    # 4 Pipeline Stages Cards
    st.markdown('#### Four-Stage Instruction Pipeline')
    p1, p2, p3, p4 = st.columns(4)

    with p1:
        st.markdown(
            """
        <div class="metric-card">
            <h4>1. FETCH</h4>
            <p>Load instruction from memory at PC into Instruction Register (IR).</p>
            <code>MAR ← PC<br>MBR ← M[MAR]<br>PC ← PC + 1<br>IR ← MBR</code>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with p2:
        st.markdown(
            """
        <div class="metric-card">
            <h4>2. DECODE</h4>
            <p>Control Unit validates syntax via FLAT DFA and extracts operands.</p>
            <code>CU decodes IR<br>Invoke DFA(IR)<br>R_SRC ← IR[6]<br>R_DST ← IR[8]</code>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with p3:
        st.markdown(
            """
        <div class="metric-card">
            <h4>3. EXECUTE</h4>
            <p>Routing ALU/Coprocessor executes Dijkstra's greedy algorithm on network graph.</p>
            <code>Coprocessor loads graph<br>Init Min-Heap<br>Relax edges<br>Find min path</code>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with p4:
        st.markdown(
            """
        <div class="metric-card">
            <h4>4. WRITE-BACK</h4>
            <p>Write shortest distance to R_COST and set condition flags (Z, U, V).</p>
            <code>R_COST ← Result<br>FLAGS.Z ← (Cost==0)<br>FLAGS.U ← (Cost==∞)<br>Store Route Buffer</code>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown('---')
    st.markdown('#### Micro-Operations & Register Transfer Language (RTL)')

    rtl_rows = []
    for stage_data in stages:
        s_name = stage_data['stage']
        submod = stage_data.get('submodule', 'CPU Core')
        cycles = stage_data.get('clock_cycles', 1)
        for op in stage_data.get('micro_ops', []):
            parts = op.split(': ', 1)
            clock = parts[0] if len(parts) == 2 else 'T'
            desc = parts[1] if len(parts) == 2 else op
            rtl_rows.append({
                'Stage': s_name,
                'Clock Phase': clock,
                'Micro-Operation / RTL Action': desc,
                'Submodule Involved': submod,
            })

    rtl_df = pd.DataFrame(rtl_rows)
    st.dataframe(rtl_df, use_container_width=True)

    # CPU Micro-Architecture Datapath Graphviz
    st.markdown('#### CPU Micro-Architecture & Bus Interconnect')
    active_stage_name = stages[-1]['stage'] if stages else 'FETCH'
    cpu_dot = get_cpu_datapath_dot(active_stage=active_stage_name)
    st.graphviz_chart(cpu_dot, use_container_width=True)

# =========================================================
# TAB 4: DAA - DIJKSTRA SHORTEST PATH
# =========================================================
with tab_daa:
    st.subheader(
        "DAA (Module 3.13): Dijkstra's Shortest Path Algorithm (Greedy)"
    )
    st.markdown(
        r"""
    **Dijkstra's Algorithm** finds the single-source shortest path on a weighted graph with non-negative edge weights $w(u, v) \ge 0$.
    It uses a **Greedy Strategy**, repeatedly selecting the vertex with the minimum tentative distance from a **Min-Heap Priority Queue**.
    """
    )

    if not is_valid:
        st.warning(
            '⚠️ Dijkstra routing was not executed because the command failed FLAT DFA validation.'
        )
    elif detailed_routing is None:
        st.info('Select a valid command to run Dijkstra simulation.')
    else:
        # Metrics Row
        d_metrics = detailed_routing['metrics']
        dm1, dm2, dm3, dm4 = st.columns(4)
        with dm1:
            st.metric('Total Vertices |V|', d_metrics['total_vertices'])
        with dm2:
            st.metric('Total Edges |E|', d_metrics['total_edges'])
        with dm3:
            st.metric(
                'Edge Relaxations', f"{d_metrics['relaxations_count']} Ops"
            )
        with dm4:
            st.metric('Time Complexity', d_metrics['time_complexity'])

        # Graph Visualization
        st.markdown('#### 🌐 Network Shortest Path Graph')
        net_dot_daa = get_network_dot(
            graph_to_use,
            path=path,
            source=registers['SRC'],
            destination=registers['DST'],
            visited=detailed_routing['visited'],
        )
        st.graphviz_chart(net_dot_daa, use_container_width=True)

        # Step-by-Step Priority Queue & Relaxation Execution History
        st.markdown('#### Step-by-Step Execution Log & Distance Table Snapshots')

        history_records = []
        for item in detailed_routing['history']:
            heap_str = ', '.join(f'({c}, {n})' for c, n in item['heap_contents'])
            dist_str = ', '.join(
                f"{k}: {v if v != float('inf') else '∞'}"
                for k, v in sorted(item['distances_snapshot'].items())
            )
            history_records.append({
                'Step': item['step_num'],
                'Action': item['action'],
                'Current Node': item['current_node'] or '-',
                'Neighbor': item['neighbor'] or '-',
                'Edge Weight': item['edge_weight']
                if item['edge_weight'] is not None
                else '-',
                'Priority Queue (Min-Heap)': f'[{heap_str}]',
                'Distance Array dist[]': f'{{{dist_str}}}',
                'Algorithmic Explanation': item['explanation'],
            })

        hist_df = pd.DataFrame(history_records)
        st.dataframe(hist_df, use_container_width=True)

        # Theoretical Complexity Breakdown
        with st.expander('Theoretical Analysis & Complexity Proofs', expanded=True):
            st.markdown(r"""
            ##### 1. Greedy Choice Property
            At every iteration, Dijkstra's algorithm extracts vertex $u = \arg\min_{v \notin S} dist[v]$.
            Since all edge weights are non-negative ($w(x, y) \ge 0$), any other path to $u$ via unvisited vertices
            must have a length at least $dist[u]$. Hence, $dist[u]$ is globally optimal and can be finalized immediately.

            ##### 2. Optimal Substructure
            If a shortest path from source $s$ to destination $d$ passes through intermediate router $k$,
            the subpath from $s$ to $k$ and the subpath from $k$ to $d$ must themselves be shortest paths.

            ##### 3. Complexity Derivation
            - **Binary Min-Heap Implementation:**
              - Extract-Min operation: $O(\log V)$, executed at most $|V|$ times $\implies O(V \log V)$.
              - Decrease-Key / Push relaxation operation: $O(\log V)$, executed at most $|E|$ times $\implies O(E \log V)$.
              - Total Time Complexity: $\mathcal{O}((V + E) \log V)$.
              - Space Complexity: $\mathcal{O}(V + E)$ for adjacency storage, distance arrays, and predecessor pointers.
            """)

# =========================================================
# TAB 5: AUTOMATED TEST SUITE & VERIFICATION
# =========================================================
with tab_tests:
    st.subheader('Integrated Test Suite & Verification Matrix')
    st.markdown(
        """
    The RouteChip test suite tests all three academic topics:
    - **FLAT:** Opcode validation, syntax limits, illegal routers, uppercase constraints, whitespace checks.
    - **COA:** 4-stage pipeline execution, CPU register file updates, status flags ($Z, U, V, ERR$).
    - **DAA:** Dijkstra shortest path correctness, zero cost self-loops, unreachable node detection, negative weight rejection.
    """
    )

    if st.button('Run All Automated Unit Tests', type='primary'):
        # Run unittest suite in memory
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(
            test_routechip.RouteChipTests
        )
        stream = io.StringIO()
        runner = unittest.TextTestRunner(stream=stream, verbosity=2)
        start_time = time.time()
        result = runner.run(suite)
        elapsed = time.time() - start_time

        st.markdown('---')
        tc1, tc2, tc3 = st.columns(3)
        with tc1:
            st.metric('Total Tests Executed', result.testsRun)
        with tc2:
            st.metric(
                'Passed Tests',
                result.testsRun - len(result.failures) - len(result.errors),
            )
        with tc3:
            st.metric('Execution Time', f'{elapsed * 1000:.2f} ms')

        if result.wasSuccessful():
            st.success(
                f'All {result.testsRun} unit tests PASSED successfully without any regressions!'
            )
        else:
            st.error(
                f'❌ Test failures detected: {len(result.failures)} failures, {len(result.errors)} errors.'
            )

        # Parse test results into a table
        output_text = stream.getvalue()
        lines = output_text.strip().split('\n')
        test_details = []
        for line in lines:
            if ' ... ' in line:
                name, status = line.split(' ... ', 1)
                test_name = name.split(' ')[0]
                category = (
                    'FLAT (Automata)'
                    if 'dfa' in test_name
                    or 'command' in test_name
                    or 'opcode' in test_name
                    or 'router' in test_name
                    or 'spaces' in test_name
                    else (
                        'COA (CPU Cycle)'
                        if 'cpu' in test_name or 'register' in test_name
                        else 'DAA (Dijkstra)'
                    )
                )
                test_details.append({
                    'Test Method': test_name,
                    'Module Category': category,
                    'Status': 'PASSED ✅' if 'ok' in status else 'FAILED ❌',
                })

        if test_details:
            st.dataframe(pd.DataFrame(test_details), use_container_width=True)

        with st.expander('📄 Raw Test Execution Output'):
            st.text(output_text)
    else:
        st.info(
            "Click the button above to execute the 22-test automated verification suite and view the live validation matrix."
        )

# =========================================================
# TAB 6: ACADEMIC THEORY & SYSTEM DOCUMENTATION
# =========================================================
with tab_theory:
    st.subheader('📚 Integrated Academic Concepts & Topic Mapping')

    tcol1, tcol2, tcol3 = st.columns(3)

    with tcol1:
        st.markdown(
            r"""
        #### 1. DAA (Module 3.13)
        **Dijkstra's Algorithm**
        - **Greedy Strategy:** Locally optimal choice of min tentative distance guarantees global shortest path.
        - **Data Structure:** Binary Min-Heap Priority Queue.
        - **Key Formula:**
          $$dist[v] \leftarrow \min(dist[v], dist[u] + w(u, v))$$
        - **Complexity:**
          - Time: $\mathcal{O}((V + E) \log V)$
          - Space: $\mathcal{O}(V + E)$
        - **Preconditions:** All edge weights non-negative ($w \ge 0$).
        """
        )

    with tcol2:
        st.markdown(
            r"""
        #### 2. COA (Module 2.1)
        **Instruction Cycle**
        - **Fetch Stage:**
          - $MAR \leftarrow PC$
          - $MBR \leftarrow M[MAR], PC \leftarrow PC + 1$
          - $IR \leftarrow MBR$
        - **Decode Stage:**
          - Opcode identification & DFA parsing.
          - Operand separation: $R_{SRC}, R_{DST}$.
        - **Execute Stage:**
          - Routing coprocessor invokes graph search.
        - **Write-Back Stage:**
          - $R_{COST} \leftarrow \text{Result}$
          - Condition flags: $Z, U, V, ERR$.
        """
        )

    with tcol3:
        st.markdown(
            r"""
        #### 3. FLAT (Module 1.5)
        **Deterministic Finite Automata**
        - **5-Tuple:**
          $$M = (Q, \Sigma, \delta, q_0, F)$$
        - **States:**
          - $Q = \{q_0, \dots, q_9, \text{DEAD}\}$
        - **Transitions:**
          - Opcode: $q_0 \dots q_5$ for `'ROUTE'`
          - Delimiters: $q_5 \to q_6$ and $q_7 \to q_8$ for `' '`
          - Routers: $q_6 \to q_7$ and $q_8 \to q_9$ for $[A-E]$
        - **Acceptance:**
          - String accepted iff state $\in F = \{q_9\}$.
        """
        )

    st.markdown('---')
    st.markdown(
        """
    ### Problem Statement & Resolution
    In computer science curricula, networking algorithms (DAA), processor architectures (COA), and formal language automata (FLAT)
    are frequently taught in silos. Real-world network routing silicon (e.g. ASIC routing chips, TCAMs, and network processing units)
    fundamentally relies on the continuous interplay of:
    - **Lexical and syntactic command validation** at line rate (Automata theory).
    - **Instruction pipelining and register manipulation** within hardware datapaths (Computer organization).
    - **Optimal shortest-path topology computation** for packet forwarding tables (Design & analysis of algorithms).

    **RouteChip** demonstrates this integration interactively, providing students and evaluators with a visual and quantitative simulation.
    """
    )

st.markdown('---')
st.caption(
    'RouteChip: An Integrated Network Routing and CPU Execution Simulator • Python + Streamlit • DAA + COA + FLAT'
)
