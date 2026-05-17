from __future__ import annotations

from collections.abc import Callable

from planning.pddl import (
    Action,
    ActionSchema,
    Problem,
    State,
    Objects,
    get_all_groundings,
)
from planning.utils import Queue, PriorityQueue
from planning.heuristics import nullHeuristic


# ---------------------------------------------------------------------------
# Reference implementation – read and understand before coding the rest.
# ---------------------------------------------------------------------------


def tinyBaseSearch(problem: Problem) -> list[Action]:
    """
    Hardcoded plan for the tinyBase layout.
    The robot at (1,4) must: pick up supplies at (1,3), set them up at (1,2),
    pick up the patient at (1,1), bring them to (1,2), and execute Rescue.

    Useful to understand the Action object format and plan structure.
    """
    robot = "robot"
    supplies = "supplies_0"
    patient = "patient_0"

    c14 = (1, 4)  # robot start
    c13 = (1, 3)  # supplies
    c12 = (1, 2)  # medical post
    c11 = (1, 1)  # patient

    plan = [
        Action(
            "Move(robot,(1,4),(1,3))",
            [("At", robot, c14), ("Adjacent", c14, c13), ("Free", c13)],
            [],
            [("At", robot, c13), ("Free", c14)],
            [("At", robot, c14), ("Free", c13)],
        ),
        Action(
            "PickUp(robot,supplies_0,(1,3))",
            [
                ("At", robot, c13),
                ("At", supplies, c13),
                ("HandsFree", robot),
                ("Pickable", supplies),
            ],
            [],
            [("Holding", robot, supplies)],
            [("At", supplies, c13), ("HandsFree", robot)],
        ),
        Action(
            "Move(robot,(1,3),(1,2))",
            [("At", robot, c13), ("Adjacent", c13, c12), ("Free", c12)],
            [],
            [("At", robot, c12), ("Free", c13)],
            [("At", robot, c13), ("Free", c12)],
        ),
        Action(
            "SetupSupplies(robot,supplies_0,(1,2))",
            [("At", robot, c12), ("MedicalPost", c12), ("Holding", robot, supplies)],
            [("SuppliesReady", c12)],
            [("SuppliesReady", c12), ("HandsFree", robot)],
            [("Holding", robot, supplies)],
        ),
        Action(
            "Move(robot,(1,2),(1,1))",
            [("At", robot, c12), ("Adjacent", c12, c11), ("Free", c11)],
            [],
            [("At", robot, c11), ("Free", c12)],
            [("At", robot, c12), ("Free", c11)],
        ),
        Action(
            "PickUp(robot,patient_0,(1,1))",
            [
                ("At", robot, c11),
                ("At", patient, c11),
                ("HandsFree", robot),
                ("Pickable", patient),
            ],
            [],
            [("Holding", robot, patient)],
            [("At", patient, c11), ("HandsFree", robot)],
        ),
        Action(
            "Move(robot,(1,1),(1,2))",
            [("At", robot, c11), ("Adjacent", c11, c12), ("Free", c12)],
            [],
            [("At", robot, c12), ("Free", c11)],
            [("At", robot, c11), ("Free", c12)],
        ),
        Action(
            "PutDown(robot,patient_0,(1,2))",
            [("At", robot, c12), ("Holding", robot, patient)],
            [],
            [("At", patient, c12), ("HandsFree", robot)],
            [("Holding", robot, patient)],
        ),
        Action(
            "Rescue(robot,patient_0,(1,2))",
            [
                ("At", robot, c12),
                ("At", patient, c12),
                ("MedicalPost", c12),
                ("SuppliesReady", c12),
            ],
            [],
            [("Rescued", patient)],
            [("At", patient, c12)],
        ),
    ]
    return plan


# ---------------------------------------------------------------------------
# Punto 2 – Forward Planning
# ---------------------------------------------------------------------------


def forwardBFS(problem: Problem) -> list[Action]:
    """
    Forward BFS in state space.

    Explore states reachable from the initial state by applying actions,
    in breadth-first order, until a goal state is found.

    Returns a list of Action objects forming a valid plan, or [] if no plan exists.

    Tip: The state is a frozenset of fluents. Use problem.getSuccessors(state)
         to get (next_state, action, cost) triples. Track visited states to
         avoid revisiting the same state twice (graph search, not tree search).
    """
    ### Your code here ###
    start = problem.getStartState()

    # Caso base: el estado inicial ya satisface el objetivo
    if problem.isGoalState(start):
        return []

    # Frontera BFS: cada elemento es (estado, lista_de_acciones_hasta_aquí)
    frontier = Queue()
    frontier.push((start, []))

    # Conjunto de estados ya visitados (graph search, no tree search)
    visited = {start}

    while not frontier.isEmpty():
        state, actions = frontier.pop()

        for next_state, action, _cost in problem.getSuccessors(state):
            if next_state not in visited:
                new_actions = actions + [action]

                if problem.isGoalState(next_state):
                    return new_actions

                visited.add(next_state)
                frontier.push((next_state, new_actions))

    # No se encontró ningún plan
    return []
    ### End of your code ###


# ---------------------------------------------------------------------------
# Punto 3 – Backward Planning
# ---------------------------------------------------------------------------


def regress(goal_set: State, action: Action) -> State | None:
    """
    Compute the regression of goal_set through action.

    Given a goal description (set of fluents that must be true) and an action,
    return the new goal description that, if satisfied, guarantees the original
    goal is satisfied after executing action.

    REGRESS(g, a) = (g − ADD(a)) ∪ PRECOND_pos(a)
        IF:  ADD(a) ∩ g ≠ ∅   (action is relevant: contributes to the goal)
        AND: DEL(a) ∩ g = ∅   (action does not undo any goal fluent)
    Returns None if the action is not relevant or creates a contradiction.

    Tip: Use frozenset operations: intersection (&), difference (-), union (|).
         Check relevance first, then check for contradictions, then compute.
    """
    add_list = frozenset(action.add_list)
    del_list = frozenset(action.del_list)
    precond_pos = frozenset(action.precond_pos)

    # Condicion 1: la accion es relevante (contribuye al objetivo)
    if not (add_list & goal_set):
        return None

    # Condicion 2: la accion no elimina fluentes que deben ser verdaderos
    if del_list & goal_set:
        return None

    # Regresion: quitar lo que la accion anade, agregar precondiciones positivas
    return (goal_set - add_list) | precond_pos


def backwardSearch(problem: Problem) -> list[Action]:
    """
    Backward search (regression search) from the goal.

    Start from the goal description and apply action regressions until
    the resulting goal is satisfied by the initial state.

    Returns a list of Action objects forming a valid plan (in forward order),
    or [] if no plan exists.

    Tip: The "state" in backward search is a frozenset of fluents that must
         be true (a partial goal description). The initial state is reached
         when all fluents in the current goal are satisfied by problem.initial_state.
         Only consider actions whose add_list has at least one unsatisfied goal fluent
         (relevant actions). Use regress() to compute the new subgoal.
         Skip subgoals that contain static predicates (MedicalPost, Adjacent,
         Pickable) that are false in the initial state — these are dead ends.
    """
    STATIC_PREDICATES = {"MedicalPost", "Adjacent", "Pickable"}

    initial = problem.getStartState()
    goal = frozenset(problem.goal)

    # Caso base: el estado inicial ya satisface el objetivo
    if goal.issubset(initial):
        return []

    # Frontera BFS: cada elemento es (subgoal_actual, plan_hacia_adelante)
    frontier = Queue()
    frontier.push((goal, []))

    visited = {goal}

    while not frontier.isEmpty():
        current_goal, actions = frontier.pop()

        # Generar todas las groundings de acciones del dominio
        for action in get_all_groundings(problem.domain, problem.objects):
            regressed = regress(current_goal, action)

            if regressed is None:
                continue

            # Se podan los callejones sin salida, los predicados estaticos falsos en el estado inicial
            dead_end = False
            for fluent in regressed:
                predicate = fluent[0]
                if predicate in STATIC_PREDICATES and fluent not in initial:
                    dead_end = True
                    break
            if dead_end:
                continue

            # El plan se construye agregando la accion al inicio (orden forward)
            new_plan = [action] + actions

            # Condicion de exito: el subgoal regresado esta satisfecho por el estado inicial
            if regressed.issubset(initial):
                return new_plan

            if regressed not in visited:
                visited.add(regressed)
                frontier.push((regressed, new_plan))

    return []


# ---------------------------------------------------------------------------
# Punto 4 – A* Planner
# ---------------------------------------------------------------------------

# Heuristic signature:  heuristic(state, goal, domain, objects) -> float
Heuristic = Callable[[State, State, list[ActionSchema], Objects], float]


def aStarPlanner(
    problem: Problem,
    heuristic: Heuristic = nullHeuristic,
) -> list[Action]:
    """
    Forward A* search guided by a heuristic.

    Combines the real accumulated cost g(n) with the heuristic estimate h(n)
    to prioritize which state to expand next: f(n) = g(n) + h(n).

    Returns a list of Action objects forming a valid plan, or [] if no plan exists.

    Tip: The heuristic signature is heuristic(state, goal, domain, objects) → float.
         Use PriorityQueue with priority = g + h(next_state).
         Track the best g-cost seen for each state to avoid stale expansions.
    """
    start = problem.getStartState()
    if problem.isGoalState(start):
        return []
    
    frontier = PriorityQueue()    
    
    h_start = heuristic(start, problem.goal, problem.domain, problem.objects)
    frontier.push((start, [], 0), 0 + h_start)
    
    visited = {start: 0}

    while not frontier.isEmpty():
        state, path, g_cost = frontier.pop()

        if problem.isGoalState(state):
            return path
        
        if visited.get(state, float('inf')) < g_cost:
            continue

        for next_state, action, step_cost in problem.getSuccessors(state):
            new_g = g_cost + step_cost            
            
            if new_g < visited.get(next_state, float('inf')):
                visited[next_state] = new_g
                h_cost = heuristic(next_state, problem.goal, problem.domain, problem.objects)
                f_cost = new_g + h_cost                
                
                frontier.push((next_state, path + [action], new_g), f_cost)

    return []


# Aliases used by the command-line argument parser
tinyBaseSearch = tinyBaseSearch
forwardBFS = forwardBFS
backwardSearch = backwardSearch
aStarPlanner = aStarPlanner
