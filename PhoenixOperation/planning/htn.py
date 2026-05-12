from __future__ import annotations

from planning.pddl import Action, Problem, apply_action, is_applicable


# ---------------------------------------------------------------------------
# HTN Infrastructure
# ---------------------------------------------------------------------------


class HLA:
    """
    A High-Level Action (HLA) in HTN planning.

    An HLA is an abstract task that can be refined into sequences of
    more primitive actions (or other HLAs). Each refinement is a list
    of HLA or Action objects.

    name:        Human-readable name for display
    refinements: List of possible refinements, each a list of HLA/Action objects
    """

    def __init__(self, name: str, refinements: list[list] | None = None) -> None:
        self.name = name
        self.refinements = refinements or []

    def __repr__(self) -> str:
        return f"HLA({self.name})"


def is_primitive(action: Action | HLA) -> bool:
    """Return True if action is a primitive (grounded Action), False if it is an HLA."""
    return isinstance(action, Action)


def is_plan_primitive(plan: list[Action | HLA]) -> bool:
    """Return True if every step in the plan is a primitive action."""
    return all(is_primitive(step) for step in plan)


# ---------------------------------------------------------------------------
# Punto 5a – hierarchicalSearch
# ---------------------------------------------------------------------------


def hierarchicalSearch(problem: Problem, hlas: list[HLA]) -> list[Action]:
    """
    HTN planning via BFS over hierarchical plan refinements.

    Start with an initial plan containing a single top-level HLA.
    At each step, find the first non-primitive step in the plan and
    replace it with one of its refinements. Continue until the plan
    is fully primitive and achieves the goal when executed from the
    initial state.

    Returns a list of primitive Action objects, or [] if no plan found.

    Tip: The search space consists of (partial plan, current plan index) pairs.
         Use a Queue (BFS) to explore all refinement choices fairly.
         A plan is a solution when:
           1. It contains only primitive actions (is_plan_primitive), AND
           2. Executing it from the initial state reaches a goal state.
         To simulate execution, apply each action in order using apply_action().
    """
    ### Your code here ###
    from planning.utils import Queue

    queue = Queue()
    queue.push(list(hlas))  # initial plan = the top-level HLA sequence

    while not queue.isEmpty():
        plan = queue.pop()

        # Find index of first non-primitive step
        idx = next((i for i, step in enumerate(plan) if not is_primitive(step)), None)

        if idx is None:
            # Plan is fully primitive — simulate execution and check goal
            state = problem.getStartState()
            valid = True
            for action in plan:
                if not is_applicable(state, action):
                    valid = False
                    break
                state = apply_action(state, action)
            if valid and problem.isGoalState(state):
                return plan
        else:
            # Expand the first HLA with each of its refinements
            hla = plan[idx]
            for refinement in hla.refinements:
                new_plan = plan[:idx] + list(refinement) + plan[idx + 1:]
                queue.push(new_plan)

    return []
    ### End of your code ###


# ---------------------------------------------------------------------------
# Punto 5b – HLA Definitions
# ---------------------------------------------------------------------------


def build_htn_hierarchy(problem: Problem) -> list[HLA]:
    """
    Build HTN HLAs for the rescue domain.

    The hierarchy defines four HLA types:
      - Navigate(from, to):       Move the robot step by step from one cell to another
      - PrepareSupplies(s, m):    Collect supplies and set them up at the medical post
      - ExtractPatient(p, m):     Pick up the patient and bring them to the medical post
      - FullRescueMission(s,p,m): Complete one rescue: prepare supplies + extract + rescue

    Refinements are built from the ground state to generate concrete Action objects.

    Tip: Refinements for Navigate are all single-step Move sequences between
         adjacent cells. PrepareSupplies and ExtractPatient chain Navigate HLAs
         with primitive PickUp, SetupSupplies, PutDown, and Rescue actions.
    """
    ### Your code here ###
    from collections import deque
    from planning.domain import MOVE, PICKUP, PUTDOWN, RESCUE, SETUP_SUPPLIES

    state = problem.getStartState()
    objects = problem.objects
    robot = "robot"

    # --- Extract initial positions of all entities ---
    positions = {}
    for f in state:
        if f[0] == "At":
            positions[f[1]] = f[2]

    robot_pos = positions[robot]

    # --- Build adjacency map from state fluents ---
    adj: dict = {}
    for f in state:
        if f[0] == "Adjacent":
            adj.setdefault(f[1], []).append(f[2])

    # --- BFS path finder (returns list of cells, including start and end) ---
    def bfs_path(start, end):
        if start == end:
            return [start]
        visited = {start}
        queue = deque([(start, [start])])
        while queue:
            curr, path = queue.popleft()
            for nxt in sorted(adj.get(curr, [])):  # sorted for determinism
                if nxt not in visited:
                    new_path = path + [nxt]
                    if nxt == end:
                        return new_path
                    visited.add(nxt)
                    queue.append((nxt, new_path))
        return None  # no path exists

    # --- Convert a cell path into a list of grounded Move actions ---
    def path_to_moves(path):
        return [
            MOVE.ground({"r": robot, "from_cell": path[i], "to_cell": path[i + 1]})
            for i in range(len(path) - 1)
        ]

    # --- Navigate HLAs: one per pair of cells reachable from each other.
    #     Each Navigate(a→b) has one refinement: the BFS shortest path as
    #     primitive Move actions. Encoding paths statically avoids infinite
    #     recursive expansion in hierarchicalSearch. ---
    navigate_hlas: dict = {}
    all_cells = objects["cells"]
    for start in all_cells:
        for end in all_cells:
            if start == end:
                continue
            path = bfs_path(start, end)
            if path and len(path) > 1:
                moves = path_to_moves(path)
                hla = HLA(f"Navigate({start}->{end})", refinements=[moves])
                navigate_hlas[(start, end)] = hla

    def navigate(start, end):
        """Return [Navigate HLA] for going from start to end, or [] if same cell."""
        if start == end:
            return []
        hla = navigate_hlas.get((start, end))
        return [hla] if hla else []

    # --- Build one FullRescueMission per (supply, patient) pair.
    #     Track where the robot ends up after each mission so Navigate
    #     HLAs in subsequent missions start from the right position. ---
    medical_post = objects["medical_posts"][0]
    supplies_list = objects["supplies"]
    patients_list = objects["patients"]

    full_missions: list[HLA] = []
    current_robot_pos = robot_pos

    for s, p in zip(supplies_list, patients_list):
        s_pos = positions[s]
        p_pos = positions[p]

        # PrepareSupplies: go to supply → pick up → go to post → setup
        prep_refinement = (
            navigate(current_robot_pos, s_pos)
            + [PICKUP.ground({"r": robot, "obj": s, "loc": s_pos})]
            + navigate(s_pos, medical_post)
            + [SETUP_SUPPLIES.ground({"r": robot, "s": s, "loc": medical_post})]
        )
        prepare_hla = HLA(
            f"PrepareSupplies({s},{medical_post})",
            refinements=[prep_refinement],
        )

        # After PrepareSupplies the robot is at medical_post.
        # ExtractPatient: go to patient → pick up → go to post → put down
        extract_refinement = (
            navigate(medical_post, p_pos)
            + [PICKUP.ground({"r": robot, "obj": p, "loc": p_pos})]
            + navigate(p_pos, medical_post)
            + [PUTDOWN.ground({"r": robot, "obj": p, "loc": medical_post})]
        )
        extract_hla = HLA(
            f"ExtractPatient({p},{medical_post})",
            refinements=[extract_refinement],
        )

        # Rescue primitive action at the medical post
        rescue_action = RESCUE.ground({"r": robot, "p": p, "loc": medical_post})

        # FullRescueMission chains the three sub-tasks
        full_hla = HLA(
            f"FullRescueMission({s},{p},{medical_post})",
            refinements=[[prepare_hla, extract_hla, rescue_action]],
        )
        full_missions.append(full_hla)

        # After this mission the robot is at medical_post (just did the rescue there)
        current_robot_pos = medical_post

    return full_missions
    ### End of your code ###
