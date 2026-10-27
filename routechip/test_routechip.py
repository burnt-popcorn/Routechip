"""RouteChip Test Suite.

Verifies correctness across all three integrated modules:
1. FLAT: DFA Command Validation (Module 1.5)
2. COA: CPU Instruction Cycle Simulation (Module 2.1)
3. DAA: Dijkstra's Shortest Path Algorithm (Module 3.13)
"""

import unittest
from automata import (
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


class RouteChipTests(unittest.TestCase):
    # --- FLAT: Automata & DFA Tests ---
    def test_valid_command(self):
        self.assertTrue(validate_command('ROUTE A D')[0])

    def test_invalid_opcode(self):
        self.assertFalse(validate_command('FIND A D')[0])

    def test_invalid_router(self):
        self.assertFalse(validate_command('ROUTE A Z')[0])

    def test_malformed_command(self):
        self.assertFalse(validate_command('ROUTE A')[0])

    def test_lowercase_opcode_rejected(self):
        self.assertFalse(validate_command('route A D')[0])

    def test_lowercase_router_rejected(self):
        self.assertFalse(validate_command('ROUTE a D')[0])
        self.assertFalse(validate_command('ROUTE A d')[0])

    def test_extra_spaces_rejected(self):
        self.assertFalse(validate_command('ROUTE  A D')[0])
        self.assertFalse(validate_command(' ROUTE A D')[0])
        self.assertFalse(validate_command('ROUTE A D ')[0])

    def test_dfa_step_by_step_trace(self):
        steps = get_step_by_step_trace('ROUTE A D')
        self.assertEqual(len(steps), 9)
        self.assertEqual(steps[-1]['to_state'], 'q9')
        self.assertEqual(steps[-1]['status'], 'VALID')

    def test_dfa_metadata_and_transition_matrix(self):
        meta = get_dfa_metadata()
        self.assertEqual(meta['start_state_q0'], 'q0')
        self.assertIn('q9', meta['accept_states_F'])
        matrix_df = get_transition_matrix_df()
        self.assertEqual(len(matrix_df), 11)  # q0..q9 and DEAD

    # --- DAA: Dijkstra Algorithm Tests ---
    def test_shortest_path(self):
        self.assertEqual(shortest_path(GRAPH, 'A', 'D')[:2], (['A', 'C', 'D'], 4))

    def test_same_router(self):
        self.assertEqual(shortest_path(GRAPH, 'B', 'B')[:2], (['B'], 0))

    def test_unreachable_router(self):
        self.assertEqual(shortest_path(GRAPH, 'A', 'E')[:2], ([], None))

    def test_dijkstra_detailed_metrics(self):
        result = dijkstra_detailed(GRAPH, 'A', 'D')
        self.assertEqual(result['path'], ['A', 'C', 'D'])
        self.assertEqual(result['cost'], 4)
        self.assertTrue(len(result['history']) > 0)
        self.assertTrue(result['metrics']['relaxations_count'] > 0)

    def test_negative_weight_safeguard(self):
        negative_graph = {'A': {'B': -2}, 'B': {'A': -2}}
        with self.assertRaises(ValueError):
            shortest_path(negative_graph, 'A', 'B')

    def test_unknown_router_exception(self):
        with self.assertRaises(ValueError):
            shortest_path(GRAPH, 'A', 'X')

    def test_preset_topologies(self):
        ring = PRESET_TOPOLOGIES['Ring Network (A-B-C-D-E)']
        path, cost, _ = shortest_path(ring, 'A', 'E')
        # Ring: A-E is 6 direct, but A-B(3)-C(2)-D(4)-E(1) is 10. Direct is 6.
        self.assertEqual(cost, 6)
        self.assertEqual(path, ['A', 'E'])

    # --- COA: CPU Instruction Cycle Tests ---
    def test_cpu_stages(self):
        result = execute_command('ROUTE A D')
        self.assertEqual(
            [s['stage'] for s in result['stages']],
            ['FETCH', 'DECODE', 'EXECUTE', 'WRITE-BACK'],
        )

    def test_register_writeback(self):
        self.assertEqual(execute_command('ROUTE A D')['registers']['COST'], 4)

    def test_invalid_command_not_executed(self):
        result = execute_command('ROUTE Z D')
        self.assertFalse(result['valid'])
        self.assertEqual([s['stage'] for s in result['stages']], ['FETCH', 'DECODE'])
        self.assertEqual(result['registers']['FLAGS']['ERR'], 1)

    def test_cpu_flags_zero_on_same_router(self):
        result = execute_command('ROUTE B B')
        self.assertTrue(result['valid'])
        self.assertEqual(result['registers']['COST'], 0)
        self.assertEqual(result['registers']['FLAGS']['Z'], 1)

    def test_cpu_flags_unreachable_router(self):
        result = execute_command('ROUTE A E')
        self.assertTrue(result['valid'])
        self.assertEqual(result['registers']['COST'], -1)
        self.assertEqual(result['registers']['FLAGS']['U'], 1)

    # --- Visual Dot Generators Tests ---
    def test_graphviz_dot_generators(self):
        dfa_dot = get_dfa_dot('ROUTE A D')
        self.assertIn('digraph RouteChipDFA', dfa_dot)
        net_dot = get_network_dot(GRAPH, path=['A', 'C', 'D'], source='A', destination='D')
        self.assertIn('graph NetworkTopology', net_dot)
        cpu_dot = get_cpu_datapath_dot('EXECUTE')
        self.assertIn('digraph CPUDatapath', cpu_dot)


if __name__ == '__main__':
    unittest.main()
