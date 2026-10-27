# RouteChip: An Integrated Network Routing and CPU Execution Simulator


## 📌 Project Overview

**RouteChip** is an integrated software simulator that bridges three foundational Computer Science domains into a cohesive, interactive system:

1. **Design and Analysis of Algorithms (DAA) — Module 3 (Topic 3.13):**  
   *Dijkstra's Algorithm* for finding single-source shortest paths on weighted networks using a greedy strategy with a binary min-heap priority queue.
2. **Computer Organization and Architecture (COA) — Module 2 (Topic 2.1):**  
   *Instruction Cycle Simulation* executing the classical 4-stage pipeline (**Fetch**, **Decode**, **Execute**, and **Write-Back**) with live register tracking (`PC`, `MAR`, `MBR`, `IR`, `SRC`, `DST`, `COST`, `FLAGS`) and Register Transfer Notation (RTN/RTL).
3. **Formal Languages and Automata Theory (FLAT) — Module 1 (Topic 1.5):**  
   *Deterministic Finite Automaton (DFA)* $M = (Q, \Sigma, \delta, q_0, F)$ designed to formally validate routing instructions before hardware dispatch.

---

## 🎯 Problem Statement

In academic curricula, network routing algorithms (DAA), processor architectures (COA), and formal language automata (FLAT) are traditionally taught in isolation. However, production network silicon (such as Network Processing Units, TCAMs, and ASIC packet switches) functions through their continuous synergy:
- **FLAT:** Lexical and syntactic command verification at wire speed.
- **COA:** Instruction pipelining, control signal generation, and datapath register write-backs.
- **DAA:** Optimal shortest-path topology computation for hardware routing tables.

**RouteChip** demonstrates this integration interactively using Python and Streamlit, providing real-time visualizations, step-by-step traces, datapath schematics, and an automated verification suite.

---

## 🏗️ System Architecture & Dataflow

```
   [ User Instruction String: e.g. "ROUTE A D" ]
                        │
                        ▼
┌────────────────────────────────────────────────────────┐
│  STAGE 1: FETCH (COA 2.1)                              │
│  • MAR ← PC; MBR ← M[MAR]; PC ← PC + 1; IR ← MBR       │
└───────────────────────┬────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────────────┐
│  STAGE 2: DECODE (COA 2.1 & FLAT 1.5)                  │
│  • FLAT DFA M = (Q, Σ, δ, q0, F) parses IR             │
│  • If Rejected → Trap state DEAD, Assert FLAGS.ERR     │
│  • If Accepted → Extract operands: R_SRC, R_DST        │
└───────────────────────┬────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────────────┐
│  STAGE 3: EXECUTE (COA 2.1 & DAA 3.13)                 │
│  • Routing Coprocessor executes Dijkstra's Algorithm   │
│  • Priority Queue (Min-Heap) extracts min distances    │
│  • Edge Relaxation: dist[v] = min(dist[v], d[u] + w)   │
└───────────────────────┬────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────────────┐
│  STAGE 4: WRITE-BACK (COA 2.1)                         │
│  • R_COST ← Shortest Path Cost (or -1 if unreachable)  │
│  • FLAGS ← { Z (Zero/Same Node), U (Unreachable), V }  │
│  • Routing Table Buffer updated with optimal path      │
└────────────────────────────────────────────────────────┘
```

---

## 📂 Repository Structure

```
routechip/
├── app.py              # Streamlit interactive application with 6 tabs & visualizations
├── automata.py         # FLAT: DFA specification, transition matrix, Graphviz generator
├── cpu.py              # COA: 4-stage instruction cycle, RTL micro-operations, register bank
├── routing.py          # DAA: Dijkstra engine, priority queue, preset topologies, network DOT
├── test_routechip.py   # Comprehensive automated test suite (22 unit tests)
├── requirements.txt    # Application dependencies (streamlit, pandas)
└── README.md           # Project documentation and user guide
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10 or newer.

### 2. Installation
Activate the existing virtual environment or create a new one:
```bash
# Using existing virtual environment:
source .venv/bin/activate

# Or install dependencies:
pip install -r requirements.txt
```

### 3. Running the Simulator
Launch the Streamlit web application:
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 🧪 Running the Verification Suite

Run all 22 unit tests directly from the command line:
```bash
python3 -m unittest -v test_routechip.py
```

Or open the **🧪 Test Suite & Verification** tab inside the Streamlit web app to execute tests interactively and view the live validation matrix.

---

## 🔬 Syllabus Module Alignment

| Discipline | Syllabus Module | Concept / Topic | Implementation in RouteChip |
| :--- | :--- | :--- | :--- |
| **FLAT** | Module 1 (1.5) | Deterministic Finite Automata (DFA) | 10-state DFA $M = (Q, \Sigma, \delta, q_0, F)$ validating `^ROUTE [A-E] [A-E]$`, character transition trace, and Graphviz state machine graph. |
| **COA** | Module 2 (2.1) | Instruction Processing Cycle | 4-stage pipeline (Fetch, Decode, Execute, Write-Back), internal register bank (`PC`, `IR`, `MAR`, `MBR`, `SRC`, `DST`, `COST`, `FLAGS`), and RTL micro-operations ($T_0 \dots T_{13}$). |
| **DAA** | Module 3 (3.13) | Dijkstra's Algorithm | Min-heap greedy single-source shortest path, edge relaxation logs, distance table snapshots, $\mathcal{O}((V + E) \log V)$ complexity analysis. |
