# RouteChip: An Integrated Network Routing and CPU Execution Simulator


Project Overview

**RouteChip** is an integrated software simulator that bridges three foundational Computer Science domains into a cohesive, interactive system:

1. **Design and Analysis of Algorithms (DAA) — Module 3 (Topic 3.13):**  
   *Dijkstra's Algorithm* for finding single-source shortest paths on weighted networks using a greedy strategy with a binary min-heap priority queue.
2. **Computer Organization and Architecture (COA) — Module 2 (Topic 2.1):**  
   *Instruction Cycle Simulation* executing the classical 4-stage pipeline (**Fetch**, **Decode**, **Execute**, and **Write-Back**) with live register tracking (`PC`, `MAR`, `MBR`, `IR`, `SRC`, `DST`, `COST`, `FLAGS`) and Register Transfer Notation (RTN/RTL).
3. **Formal Languages and Automata Theory (FLAT) — Module 1 (Topic 1.5):**  
   *Deterministic Finite Automaton (DFA)* $M = (Q, \Sigma, \delta, q_0, F)$ designed to formally validate routing instructions before hardware dispatch.

---

Problem Statement

In academic curricula, network routing algorithms (DAA), processor architectures (COA), and formal language automata (FLAT) are traditionally taught in isolation. However, production network silicon (such as Network Processing Units, TCAMs, and ASIC packet switches) functions through their continuous synergy:
- **FLAT:** Lexical and syntactic command verification at wire speed.
- **COA:** Instruction pipelining, control signal generation, and datapath register write-backs.
- **DAA:** Optimal shortest-path topology computation for hardware routing tables.



## Running the Verification Suite

Run all 22 unit tests directly from the command line:
```bash
python3 -m unittest -v test_routechip.py
```

Or open the **Test Suite & Verification** tab inside the Streamlit web app to execute tests interactively and view the live validation matrix.



# Repo and deployed link
https://github.com/burnt-popcorn/Routechip
https://routechip-zz01.streamlit.app/
