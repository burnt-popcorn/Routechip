"""RouteChip CPU Simulation Module (COA: Computer Organization and Architecture).

Module 2: Instruction Cycle (2.1)
Simulates the classical 4-stage CPU Instruction Processing Cycle:
1. FETCH: Instruction retrieved from instruction memory into IR via MAR/MBR, PC incremented.
2. DECODE: Control Unit decodes instruction, runs DFA parser (FLAT), extracts operands.
3. EXECUTE: Routing Coprocessor / ALU runs Dijkstra's Algorithm (DAA) on network topology.
4. WRITE-BACK: Resulting shortest path cost written to result register (COST) and status flags updated.

Includes Register Transfer Notation (RTN / RTL) micro-operations and full register bank.
"""

from typing import Any, Dict, List, Optional
from automata import validate_command
from routing import GRAPH, dijkstra_detailed, shortest_path


def execute_command(
    command: str,
    graph: Optional[Dict[str, Dict[str, int]]] = None,
    pc_start: int = 0x0100,
) -> Dict[str, Any]:
    """Execute a routing instruction through the complete 4-stage CPU cycle.

    Preserves exact backward-compatible return structure while providing rich
    micro-architectural telemetry and register state.
    """
    if graph is None:
        graph = GRAPH

    # Hardware registers initialization
    registers: Dict[str, Any] = {
        'PC': f'0x{pc_start:04X}',
        'MAR': f'0x{pc_start:04X}',
        'MBR': command,
        'IR': command,
        'SRC': None,
        'DST': None,
        'COST': None,
        'FLAGS': {'Z': 0, 'U': 0, 'V': 0, 'ERR': 0},
    }

    # Stage 1: FETCH
    stages: List[Dict[str, Any]] = [
        {
            'stage': 'FETCH',
            'details': f'Instruction memory → IR: {command}',
            'micro_ops': [
                f'T0: MAR ← PC ({registers["PC"]})',
                f'T1: MBR ← M[MAR] ("{command}"), PC ← PC + 1 (0x{pc_start + 1:04X})',
                'T2: IR ← MBR',
            ],
            'submodule': 'Bus Interface Unit & Instruction Memory',
            'clock_cycles': 3,
            'status': 'SUCCESS',
        }
    ]
    registers['PC'] = f'0x{pc_start + 1:04X}'

    # Validate command using the FLAT DFA module
    valid, states = validate_command(command)

    # Stage 2: DECODE
    if not valid:
        registers['FLAGS'] = {'Z': 0, 'U': 0, 'V': 0, 'ERR': 1}
        stages.append({
            'stage': 'DECODE',
            'details': 'Invalid instruction: DFA rejected command',
            'micro_ops': [
                'T3: CU inspects IR, routes tokens to FLAT DFA coprocessor',
                'T4: DFA entered DEAD state or ended non-accepting → Syntax Exception',
                'T5: FLAGS.V ← 0, FLAGS.ERR ← 1, Halt pipeline execution',
            ],
            'submodule': 'Control Unit & Automata Command Parser',
            'clock_cycles': 2,
            'status': 'REJECTED',
        })
        return {
            'valid': False,
            'states': states,
            'stages': stages,
            'path': [],
            'cost': None,
            'steps': [],
            'registers': registers,
            'detailed_routing': None,
        }

    # Valid instruction: decode opcode and operands
    tokens = command.split(' ')
    opcode, source, destination = tokens[0], tokens[1], tokens[2]
    registers['SRC'] = source
    registers['DST'] = destination
    registers['FLAGS']['V'] = 1

    stages.append({
        'stage': 'DECODE',
        'details': f'Opcode={opcode}, SRC={source}, DST={destination}',
        'micro_ops': [
            f'T3: CU decodes Opcode="{opcode}" (0x1F - Network Shortest Path)',
            f'T4: Extract operand R_SRC ← "{source}" (Memory offset 0x06)',
            f'T5: Extract operand R_DST ← "{destination}" (Memory offset 0x08)',
            'T6: Assert Routing Coprocessor (RPU/ALU) enable signal',
        ],
        'submodule': 'Instruction Decoder & Register File',
        'clock_cycles': 3,
        'status': 'SUCCESS',
    })

    # Stage 3: EXECUTE
    # Run Dijkstra's algorithm (DAA Module)
    detailed_routing = dijkstra_detailed(graph, source, destination)
    path = detailed_routing['path']
    cost = detailed_routing['cost']
    steps = detailed_routing['steps']

    is_unreachable = cost is None
    registers['COST'] = cost if cost is not None else -1

    stages.append({
        'stage': 'EXECUTE',
        'details': 'Run Dijkstra on the network graph',
        'micro_ops': [
            f'T7: Coprocessor loads network graph topology ({len(graph)} nodes)',
            f'T8: Initialize Min-Heap with start node "{source}"',
            f'T9: Execute greedy relaxation loops ({detailed_routing["metrics"]["relaxations_count"]} edge relaxations)',
            f'T10: Terminate on target "{destination}" or exhaustion; compute minimal path cost',
        ],
        'submodule': 'Routing ALU & Graph Coprocessor',
        'clock_cycles': 4 + detailed_routing['metrics']['relaxations_count'],
        'status': 'SUCCESS' if not is_unreachable else 'UNREACHABLE',
    })

    # Stage 4: WRITE-BACK
    # Update CPU registers and Status Flags
    # Z (Zero flag): Cost is 0 (source == destination)
    # U (Unreachable flag): Destination unreachable
    # V (Valid instruction flag): 1
    # ERR (Error flag): 0
    flags = {
        'Z': 1 if cost == 0 else 0,
        'U': 1 if is_unreachable else 0,
        'V': 1,
        'ERR': 0,
    }
    registers['FLAGS'] = flags

    stages.append({
        'stage': 'WRITE-BACK',
        'details': f'Write COST={registers["COST"]} into result register',
        'micro_ops': [
            f'T11: R_COST ← {registers["COST"]} (Shortest path distance)',
            f'T12: Update Status Flags: Z={flags["Z"]}, U={flags["U"]}, V={flags["V"]}, ERR={flags["ERR"]}',
            f'T13: Write route buffer: [{" → ".join(path) if path else "NONE"}]',
        ],
        'submodule': 'Accumulator & Write-Back Bus',
        'clock_cycles': 2,
        'status': 'SUCCESS',
    })

    return {
        'valid': True,
        'states': states,
        'stages': stages,
        'path': path,
        'cost': cost,
        'steps': steps,
        'registers': registers,
        'detailed_routing': detailed_routing,
    }


def get_cpu_datapath_dot(active_stage: Optional[str] = None) -> str:
    """Generate Graphviz DOT diagram for the CPU Micro-Architecture Datapath."""
    # Color assignments based on active stage
    fetch_col = "#2563eb" if active_stage == "FETCH" else "#64748b"
    decode_col = "#7c3aed" if active_stage == "DECODE" else "#64748b"
    exec_col = "#059669" if active_stage == "EXECUTE" else "#64748b"
    wb_col = "#d97706" if active_stage == "WRITE-BACK" else "#64748b"

    return f"""digraph CPUDatapath {{
  graph [rankdir=TB, bgcolor="transparent", margin=0.1];
  node [fontname="Helvetica, Arial, sans-serif", fontsize=11, shape=record, style="filled,bold", fillcolor="#f8fafc", color="#64748b", penwidth=1.5];
  edge [fontname="Helvetica, Arial, sans-serif", fontsize=10, color="#64748b", penwidth=1.3];

  subgraph cluster_control {{
    label="Control Unit (Stage 2: DECODE)";
    style=dashed;
    color="{decode_col}";
    fontcolor="{decode_col}";
    CU [label="<f0> Control Unit | <f1> Opcode Decoder | <f2> FLAT DFA Validator", fillcolor="#f3e8ff", color="{decode_col}"];
  }}

  subgraph cluster_registers {{
    label="Internal Register Bank";
    style=dotted;
    color="#0f172a";
    PC [label="PC (Program Counter)", fillcolor="#dbeafe", color="{fetch_col}"];
    MAR [label="MAR (Memory Addr)", fillcolor="#dbeafe", color="{fetch_col}"];
    MBR [label="MBR (Memory Buffer)", fillcolor="#dbeafe", color="{fetch_col}"];
    IR [label="IR (Instruction Reg)", fillcolor="#ede9fe", color="{decode_col}"];
    R_SRC [label="R_SRC (Source)", fillcolor="#ede9fe", color="{decode_col}"];
    R_DST [label="R_DST (Destination)", fillcolor="#ede9fe", color="{decode_col}"];
    R_COST [label="R_COST (Result)", fillcolor="#fef3c7", color="{wb_col}"];
    FLAGS [label="FLAGS (Z, U, V, ERR)", fillcolor="#fee2e2", color="{wb_col}"];
  }}

  subgraph cluster_alu {{
    label="Execution Coprocessor (Stage 3: EXECUTE)";
    style=dashed;
    color="{exec_col}";
    fontcolor="{exec_col}";
    RPU [label="<f0> Routing Coprocessor (ALU) | <f1> DAA Dijkstra Solver | <f2> Min-Heap Priority Queue", fillcolor="#dcfce7", color="{exec_col}"];
    TOPO_MEM [label="Topology Adjacency Matrix", fillcolor="#e0f2fe", color="{exec_col}"];
  }}

  // Datapath connections
  PC -> MAR [label="Fetch Addr", color="{fetch_col}"];
  MAR -> MBR [label="Memory Bus", color="{fetch_col}"];
  MBR -> IR [label="Load Op", color="{fetch_col}"];
  IR -> CU [label="Instruction", color="{decode_col}"];
  CU -> R_SRC [label="Decode SRC", color="{decode_col}"];
  CU -> R_DST [label="Decode DST", color="{decode_col}"];
  R_SRC -> RPU [label="Start Node", color="{exec_col}"];
  R_DST -> RPU [label="End Node", color="{exec_col}"];
  TOPO_MEM -> RPU [label="Graph Weights", color="{exec_col}"];
  RPU -> R_COST [label="Min Cost", color="{wb_col}"];
  RPU -> FLAGS [label="Status (Z, U)", color="{wb_col}"];
}}"""
