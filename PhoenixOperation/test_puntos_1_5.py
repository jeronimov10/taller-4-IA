"""
test_puntos_1_5.py
Pruebas de validación para Puntos 1 y 5 del Taller 4.
Ejecutar desde cualquier directorio: python test_puntos_1_5.py
"""
from __future__ import annotations

import sys
import os

# Cambiar al directorio del proyecto para que get_layout encuentre layouts/
# (get_layout usa os.walk("layouts") relativo al CWD)
_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(_PROJECT_DIR)
sys.path.insert(0, _PROJECT_DIR)

from planning.pddl import Action, is_applicable, apply_action, get_applicable_actions
from planning.domain import MOVE, PICKUP, PUTDOWN, RESCUE, SETUP_SUPPLIES, DOMAIN


# ---------------------------------------------------------------------------
# Utilidades de reporte
# ---------------------------------------------------------------------------

results: list[dict] = []


def check(requisito: str, caso: str, condition: bool, obs: str = "") -> bool:
    status = "PASS" if condition else "FAIL"
    results.append({"req": requisito, "caso": caso, "res": status, "obs": obs})
    return condition


def print_matrix():
    col_req  = 36
    col_caso = 48
    col_res  = 10
    header = f"{'Requisito':<{col_req}} {'Caso de Prueba':<{col_caso}} {'Resultado':<{col_res}} Observacion"
    sep = "-" * (col_req + col_caso + col_res + 30)
    print("\n" + sep)
    print(header)
    print(sep)
    for r in results:
        marca = "[OK]  " if r["res"] == "PASS" else "[FAIL]"
        print(f"{r['req']:<{col_req}} {r['caso']:<{col_caso}} {marca} {r['res']:<{col_res-2}} {r['obs']}")
    print(sep)
    passed = sum(1 for r in results if r["res"] == "PASS")
    total  = len(results)
    print(f"\n  Total: {passed}/{total} pruebas pasadas", end="")
    print("  -- TODO CORRECTO\n" if passed == total else "  -- HAY FALLOS\n")


# ===========================================================================
# PUNTO 1a — Esquemas de acción (domain.py)
# ===========================================================================

def test_domain_schemas_defined():
    """Todos los ActionSchema del dominio deben estar definidos (no None)."""
    names = ["MOVE", "PICKUP", "PUTDOWN", "RESCUE", "SETUP_SUPPLIES"]
    for name, schema in zip(names, DOMAIN):
        check("P1a — Schemas definidos", f"{name} no es None", schema is not None,
              "ActionSchema instanciado correctamente")


def test_action_schema_parameters():
    """Verificar parámetros y estructura de cada ActionSchema."""
    cases = [
        (MOVE,           "Move",          ["r", "from_cell", "to_cell"]),
        (PICKUP,         "PickUp",        ["r", "obj", "loc"]),
        (PUTDOWN,        "PutDown",       ["r", "obj", "loc"]),
        (RESCUE,         "Rescue",        ["r", "p", "loc"]),
        (SETUP_SUPPLIES, "SetupSupplies", ["r", "s", "loc"]),
    ]
    for schema, expected_name, expected_params in cases:
        check("P1a — Parámetros schemas", f"{expected_name} nombre correcto",
              schema.name == expected_name, f"name='{schema.name}'")
        check("P1a — Parámetros schemas", f"{expected_name} parámetros correctos",
              schema.parameters == expected_params,
              f"params={schema.parameters}")


def test_pickup_precond_and_effects():
    """PickUp debe tener precond_pos con 4 fluentes y del/add correctos."""
    check("P1a — PickUp estructura", "precond_pos tiene 4 fluentes",
          len(PICKUP.precond_pos) == 4, str(PICKUP.precond_pos))
    check("P1a — PickUp estructura", "add_list tiene Holding",
          any(t[0] == "Holding" for t in PICKUP.add_list), str(PICKUP.add_list))
    check("P1a — PickUp estructura", "del_list tiene At",
          any(t[0] == "At" for t in PICKUP.del_list), str(PICKUP.del_list))
    check("P1a — PickUp estructura", "del_list tiene HandsFree",
          any(t[0] == "HandsFree" for t in PICKUP.del_list), str(PICKUP.del_list))


def test_putdown_precond_and_effects():
    """PutDown debe tener la estructura correcta."""
    check("P1a — PutDown estructura", "precond_pos tiene Holding",
          any(t[0] == "Holding" for t in PUTDOWN.precond_pos), str(PUTDOWN.precond_pos))
    check("P1a — PutDown estructura", "add_list tiene At y HandsFree",
          any(t[0] == "At" for t in PUTDOWN.add_list) and
          any(t[0] == "HandsFree" for t in PUTDOWN.add_list), str(PUTDOWN.add_list))
    check("P1a — PutDown estructura", "del_list elimina Holding",
          any(t[0] == "Holding" for t in PUTDOWN.del_list), str(PUTDOWN.del_list))


def test_rescue_precond_and_effects():
    """Rescue debe requerir MedicalPost y SuppliesReady."""
    pos_names = {t[0] for t in RESCUE.precond_pos}
    check("P1a — Rescue estructura", "precond_pos incluye MedicalPost",
          "MedicalPost" in pos_names, str(RESCUE.precond_pos))
    check("P1a — Rescue estructura", "precond_pos incluye SuppliesReady",
          "SuppliesReady" in pos_names, str(RESCUE.precond_pos))
    check("P1a — Rescue estructura", "add_list tiene Rescued",
          any(t[0] == "Rescued" for t in RESCUE.add_list), str(RESCUE.add_list))
    check("P1a — Rescue estructura", "del_list elimina At(p)",
          any(t[0] == "At" for t in RESCUE.del_list), str(RESCUE.del_list))


def test_setup_supplies_precond_and_effects():
    """SetupSupplies debe requerir Holding y MedicalPost; agregar SuppliesReady."""
    pos_names = {t[0] for t in SETUP_SUPPLIES.precond_pos}
    check("P1a — SetupSupplies estructura", "precond_pos incluye Holding",
          "Holding" in pos_names, str(SETUP_SUPPLIES.precond_pos))
    check("P1a — SetupSupplies estructura", "precond_pos incluye MedicalPost",
          "MedicalPost" in pos_names, str(SETUP_SUPPLIES.precond_pos))
    check("P1a — SetupSupplies estructura", "add_list tiene SuppliesReady",
          any(t[0] == "SuppliesReady" for t in SETUP_SUPPLIES.add_list),
          str(SETUP_SUPPLIES.add_list))
    check("P1a — SetupSupplies estructura", "del_list elimina Holding",
          any(t[0] == "Holding" for t in SETUP_SUPPLIES.del_list),
          str(SETUP_SUPPLIES.del_list))


# ===========================================================================
# PUNTO 1a — Goals de los problemas (problems.py)
# ===========================================================================

def test_simple_rescue_problem_goal():
    """SimpleRescueProblem debe tener goal = {('Rescued', 'patient_0')}."""
    import world.rescue_layout as rescue_layout
    from planning.problems import SimpleRescueProblem
    layout = rescue_layout.get_layout("tinyBase")
    problem = SimpleRescueProblem(layout)
    expected = frozenset({("Rescued", "patient_0")})
    check("P1a — Goals problemas", "SimpleRescueProblem goal correcto",
          problem.goal == expected, f"goal={problem.goal}")


def test_multi_rescue_problem_goal():
    """MultiRescueProblem goal debe contener Rescued para cada paciente."""
    import world.rescue_layout as rescue_layout
    from planning.problems import MultiRescueProblem
    layout = rescue_layout.get_layout("tinyMulti")
    problem = MultiRescueProblem(layout)
    patients = problem.objects["patients"]
    expected = frozenset({("Rescued", p) for p in patients})
    check("P1a — Goals problemas", "MultiRescueProblem goal cubre todos los pacientes",
          problem.goal == expected, f"pacientes={patients}, goal={problem.goal}")
    check("P1a — Goals problemas", "Goal no vacío (no frozenset vacío)",
          len(problem.goal) > 0, f"len={len(problem.goal)}")


def test_goal_not_satisfied_in_initial_state():
    """El estado inicial NO debe satisfacer el goal (no hay rescatados al inicio)."""
    import world.rescue_layout as rescue_layout
    from planning.problems import SimpleRescueProblem
    layout = rescue_layout.get_layout("tinyBase")
    problem = SimpleRescueProblem(layout)
    not_yet = not problem.isGoalState(problem.getStartState())
    check("P1a — Goals problemas", "Estado inicial no satisface el goal",
          not_yet, "Rescued(patient_0) no existe al inicio")


# ===========================================================================
# PUNTO 1b — is_applicable (pddl.py)
# ===========================================================================

def test_move_applicable_all_precond():
    """Move aplicable cuando At, Adjacent y Free están presentes."""
    c0, c1 = (0, 0), (0, 1)
    state = frozenset({("At","robot",c0), ("Adjacent",c0,c1), ("Free",c1)})
    action = MOVE.ground({"r":"robot","from_cell":c0,"to_cell":c1})
    check("P1b — is_applicable", "Move: todas las precond. presentes ->True",
          is_applicable(state, action))


def test_move_not_applicable_free_missing():
    """Move no aplicable si Free(to) está ausente."""
    c0, c1 = (0, 0), (0, 1)
    state = frozenset({("At","robot",c0), ("Adjacent",c0,c1)})  # sin Free(c1)
    action = MOVE.ground({"r":"robot","from_cell":c0,"to_cell":c1})
    check("P1b — is_applicable", "Move: Free(to) ausente ->False",
          not is_applicable(state, action), "Free(c1) no está en el estado")


def test_move_not_applicable_at_missing():
    """Move no aplicable si At(robot, from) está ausente."""
    c0, c1 = (0, 0), (0, 1)
    state = frozenset({("Adjacent",c0,c1), ("Free",c1)})  # sin At(robot,c0)
    action = MOVE.ground({"r":"robot","from_cell":c0,"to_cell":c1})
    check("P1b — is_applicable", "Move: At(robot,from) ausente ->False",
          not is_applicable(state, action))


def test_pickup_applicable():
    """PickUp aplicable con todas las precondiciones."""
    loc = (1, 1)
    state = frozenset({("At","robot",loc), ("At","supplies_0",loc),
                       ("HandsFree","robot"), ("Pickable","supplies_0")})
    action = PICKUP.ground({"r":"robot","obj":"supplies_0","loc":loc})
    check("P1b — is_applicable", "PickUp: todas las precond. ->True",
          is_applicable(state, action))


def test_pickup_not_applicable_no_handsfree():
    """PickUp no aplicable si HandsFree está ausente."""
    loc = (1, 1)
    state = frozenset({("At","robot",loc), ("At","supplies_0",loc),
                       ("Pickable","supplies_0"), ("Holding","robot","other")})
    action = PICKUP.ground({"r":"robot","obj":"supplies_0","loc":loc})
    check("P1b — is_applicable", "PickUp: HandsFree ausente ->False",
          not is_applicable(state, action))


def test_pickup_not_applicable_obj_not_here():
    """PickUp no aplicable si el objeto no está en la celda."""
    loc, other = (1, 1), (2, 2)
    state = frozenset({("At","robot",loc), ("At","supplies_0",other),
                       ("HandsFree","robot"), ("Pickable","supplies_0")})
    action = PICKUP.ground({"r":"robot","obj":"supplies_0","loc":loc})
    check("P1b — is_applicable", "PickUp: At(obj,loc) ausente ->False",
          not is_applicable(state, action))


def test_setup_supplies_applicable():
    """SetupSupplies aplicable con Holding, At(robot) y MedicalPost."""
    loc = (1, 2)
    state = frozenset({("At","robot",loc), ("MedicalPost",loc),
                       ("Holding","robot","supplies_0")})
    action = SETUP_SUPPLIES.ground({"r":"robot","s":"supplies_0","loc":loc})
    check("P1b — is_applicable", "SetupSupplies: todas las precond. ->True",
          is_applicable(state, action))


def test_setup_supplies_not_applicable_no_holding():
    """SetupSupplies no aplicable si el robot no está cargando suministros."""
    loc = (1, 2)
    state = frozenset({("At","robot",loc), ("MedicalPost",loc), ("HandsFree","robot")})
    action = SETUP_SUPPLIES.ground({"r":"robot","s":"supplies_0","loc":loc})
    check("P1b — is_applicable", "SetupSupplies: Holding ausente ->False",
          not is_applicable(state, action))


def test_rescue_applicable():
    """Rescue aplicable con At(robot), At(patient), MedicalPost, SuppliesReady."""
    loc = (1, 2)
    state = frozenset({("At","robot",loc), ("At","patient_0",loc),
                       ("MedicalPost",loc), ("SuppliesReady",loc)})
    action = RESCUE.ground({"r":"robot","p":"patient_0","loc":loc})
    check("P1b — is_applicable", "Rescue: todas las precond. ->True",
          is_applicable(state, action))


def test_rescue_not_applicable_no_supplies():
    """Rescue no aplicable si SuppliesReady está ausente."""
    loc = (1, 2)
    state = frozenset({("At","robot",loc), ("At","patient_0",loc),
                       ("MedicalPost",loc)})  # sin SuppliesReady
    action = RESCUE.ground({"r":"robot","p":"patient_0","loc":loc})
    check("P1b — is_applicable", "Rescue: SuppliesReady ausente ->False",
          not is_applicable(state, action))


def test_rescue_not_applicable_patient_not_here():
    """Rescue no aplicable si el paciente no está en el puesto."""
    loc, other = (1, 2), (3, 3)
    state = frozenset({("At","robot",loc), ("At","patient_0",other),
                       ("MedicalPost",loc), ("SuppliesReady",loc)})
    action = RESCUE.ground({"r":"robot","p":"patient_0","loc":loc})
    check("P1b — is_applicable", "Rescue: paciente no en loc ->False",
          not is_applicable(state, action))


# ===========================================================================
# PUNTO 1b — apply_action / semántica RESULT (pddl.py)
# ===========================================================================

def test_result_order_del_before_add():
    """RESULT: primero eliminar del_list, luego agregar add_list (orden STRIPS)."""
    # Caso: fluente en del_list NO debe estar en el resultado
    # aunque estuviera en el estado original
    c0, c1 = (0, 0), (0, 1)
    state = frozenset({("At","robot",c0), ("Adjacent",c0,c1), ("Free",c1)})
    action = MOVE.ground({"r":"robot","from_cell":c0,"to_cell":c1})
    new_state = apply_action(state, action)
    # At(robot,c0) debe estar eliminado y At(robot,c1) agregado
    check("P1b — apply_action STRIPS", "del_list aplicado: At(robot,c0) ausente",
          ("At","robot",c0) not in new_state)
    check("P1b — apply_action STRIPS", "add_list aplicado: At(robot,c1) presente",
          ("At","robot",c1) in new_state)
    # Free debe invertirse: c0 libre ahora, c1 ocupada
    check("P1b — apply_action STRIPS", "Free(c0) agregado tras Move",
          ("Free",c0) in new_state)
    check("P1b — apply_action STRIPS", "Free(c1) eliminado tras Move",
          ("Free",c1) not in new_state)


def test_apply_pickup_full():
    """apply_action(PickUp): verifica add y del completos."""
    loc = (2, 2)
    state = frozenset({("At","robot",loc), ("At","supplies_0",loc),
                       ("HandsFree","robot"), ("Pickable","supplies_0")})
    action = PICKUP.ground({"r":"robot","obj":"supplies_0","loc":loc})
    ns = apply_action(state, action)
    check("P1b — apply_action PickUp", "Holding(robot,obj) en nuevo estado",
          ("Holding","robot","supplies_0") in ns)
    check("P1b — apply_action PickUp", "At(obj,loc) eliminado",
          ("At","supplies_0",loc) not in ns)
    check("P1b — apply_action PickUp", "HandsFree eliminado",
          ("HandsFree","robot") not in ns)
    check("P1b — apply_action PickUp", "Pickable persiste (no en del_list)",
          ("Pickable","supplies_0") in ns)


def test_apply_putdown_full():
    """apply_action(PutDown): objeto vuelve a la celda, robot libre."""
    loc = (1, 2)
    state = frozenset({("At","robot",loc), ("Holding","robot","patient_0")})
    action = PUTDOWN.ground({"r":"robot","obj":"patient_0","loc":loc})
    ns = apply_action(state, action)
    check("P1b — apply_action PutDown", "At(obj,loc) agregado",
          ("At","patient_0",loc) in ns)
    check("P1b — apply_action PutDown", "HandsFree restaurado",
          ("HandsFree","robot") in ns)
    check("P1b — apply_action PutDown", "Holding eliminado",
          ("Holding","robot","patient_0") not in ns)


def test_apply_setup_supplies_full():
    """apply_action(SetupSupplies): SuppliesReady agregado, Holding eliminado."""
    loc = (1, 2)
    state = frozenset({("At","robot",loc), ("MedicalPost",loc),
                       ("Holding","robot","supplies_0")})
    action = SETUP_SUPPLIES.ground({"r":"robot","s":"supplies_0","loc":loc})
    ns = apply_action(state, action)
    check("P1b — apply_action SetupSupplies", "SuppliesReady agregado",
          ("SuppliesReady",loc) in ns)
    check("P1b — apply_action SetupSupplies", "HandsFree restaurado",
          ("HandsFree","robot") in ns)
    check("P1b — apply_action SetupSupplies", "Holding eliminado",
          ("Holding","robot","supplies_0") not in ns)
    check("P1b — apply_action SetupSupplies", "MedicalPost persiste",
          ("MedicalPost",loc) in ns)


def test_apply_rescue_full():
    """apply_action(Rescue): Rescued agregado, At(p) eliminado."""
    loc = (1, 2)
    state = frozenset({("At","robot",loc), ("At","patient_0",loc),
                       ("MedicalPost",loc), ("SuppliesReady",loc)})
    action = RESCUE.ground({"r":"robot","p":"patient_0","loc":loc})
    ns = apply_action(state, action)
    check("P1b — apply_action Rescue", "Rescued(p) agregado",
          ("Rescued","patient_0") in ns)
    check("P1b — apply_action Rescue", "At(p,loc) eliminado",
          ("At","patient_0",loc) not in ns)
    check("P1b — apply_action Rescue", "SuppliesReady persiste",
          ("SuppliesReady",loc) in ns)


# ===========================================================================
# PUNTO 1b — get_applicable_actions (pddl.py)
# ===========================================================================

def test_get_applicable_actions_basic():
    """get_applicable_actions debe retornar acciones aplicables en un estado real."""
    import world.rescue_layout as rescue_layout
    from planning.problems import SimpleRescueProblem
    layout = rescue_layout.get_layout("tinyBase")
    problem = SimpleRescueProblem(layout)
    state = problem.getStartState()
    actions = get_applicable_actions(state, problem.domain, problem.objects)
    check("P1b — get_applicable_actions", "Retorna lista no vacía desde estado inicial",
          len(actions) > 0, f"{len(actions)} acciones aplicables")
    check("P1b — get_applicable_actions", "Todas las acciones son instancias de Action",
          all(isinstance(a, Action) for a in actions))


def test_get_applicable_actions_all_valid():
    """Cada acción devuelta por get_applicable_actions debe ser realmente aplicable."""
    import world.rescue_layout as rescue_layout
    from planning.problems import SimpleRescueProblem
    layout = rescue_layout.get_layout("tinyBase")
    problem = SimpleRescueProblem(layout)
    state = problem.getStartState()
    actions = get_applicable_actions(state, problem.domain, problem.objects)
    all_applicable = all(is_applicable(state, a) for a in actions)
    check("P1b — get_applicable_actions", "Cada acción retornada es aplicable",
          all_applicable, "is_applicable(state, a) == True para todas")


def test_get_applicable_actions_move_present():
    """Estado inicial de tinyBase: debe haber al menos un Move aplicable."""
    import world.rescue_layout as rescue_layout
    from planning.problems import SimpleRescueProblem
    layout = rescue_layout.get_layout("tinyBase")
    problem = SimpleRescueProblem(layout)
    state = problem.getStartState()
    actions = get_applicable_actions(state, problem.domain, problem.objects)
    moves = [a for a in actions if a.name.startswith("Move")]
    check("P1b — get_applicable_actions", "Al menos un Move en estado inicial",
          len(moves) > 0, f"{len(moves)} Move(s) aplicables")


def test_get_applicable_actions_rescue_not_present():
    """En el estado inicial, Rescue NO debe ser aplicable (faltan precondiciones)."""
    import world.rescue_layout as rescue_layout
    from planning.problems import SimpleRescueProblem
    layout = rescue_layout.get_layout("tinyBase")
    problem = SimpleRescueProblem(layout)
    state = problem.getStartState()
    actions = get_applicable_actions(state, problem.domain, problem.objects)
    rescues = [a for a in actions if a.name.startswith("Rescue")]
    check("P1b — get_applicable_actions", "Rescue NO aparece en estado inicial",
          len(rescues) == 0, "SuppliesReady y At(p,post) aún no se cumplen")


def test_get_successors_uses_applicable_actions():
    """Problem.getSuccessors usa get_applicable_actions correctamente."""
    import world.rescue_layout as rescue_layout
    from planning.problems import SimpleRescueProblem
    layout = rescue_layout.get_layout("tinyBase")
    problem = SimpleRescueProblem(layout)
    state = problem.getStartState()
    successors = problem.getSuccessors(state)
    check("P1b — getSuccessors", "Retorna lista de (estado, acción, costo)",
          len(successors) > 0, f"{len(successors)} sucesores")
    check("P1b — getSuccessors", "Cada sucesor tiene costo 1",
          all(cost == 1 for _, _, cost in successors))
    check("P1b — getSuccessors", "Cada estado sucesor es frozenset",
          all(isinstance(s, frozenset) for s, _, _ in successors))


# ===========================================================================
# PUNTO 5a — HTN: build_htn_hierarchy y hierarchicalSearch
# ===========================================================================

def _run_htn_test(layout_name: str, problem_class, label: str):
    """Helper: carga layout, resuelve con HTN, verifica plan primitivo y goal."""
    import world.rescue_layout as rescue_layout
    from planning.htn import build_htn_hierarchy, hierarchicalSearch

    layout = rescue_layout.get_layout(layout_name)
    if layout is None:
        check(label, f"Layout {layout_name} cargado", False, "Layout no encontrado")
        return None, None

    check(label, f"Layout {layout_name} cargado", True,
          f"{layout.width}×{layout.height}")
    problem = problem_class(layout)
    hlas = build_htn_hierarchy(problem)

    check(label, "build_htn_hierarchy retorna HLAs no vacío",
          len(hlas) > 0, f"{len(hlas)} HLA(s) raíz")

    plan = hierarchicalSearch(problem, hlas)
    check(label, "hierarchicalSearch retorna plan no vacío",
          len(plan) > 0, f"Longitud: {len(plan)} pasos")

    all_prim = all(isinstance(s, Action) for s in plan)
    check(label, "Plan 100% primitivo (solo Action, no HLA)",
          all_prim, "Todos los pasos son instancias de Action")

    # Simular ejecución
    state = problem.getStartState()
    valid = True
    for a in plan:
        if not is_applicable(state, a):
            valid = False
            break
        state = apply_action(state, a)
    check(label, "Ejecución paso a paso sin acción inválida", valid)
    goal_ok = valid and problem.isGoalState(state)
    check(label, "Estado final satisface isGoalState", goal_ok)
    return problem, plan


def test_htn_tinyHTN():
    """P5a: HTN resuelve SimpleRescueProblem en tinyHTN (layout del enunciado)."""
    from planning.problems import SimpleRescueProblem
    _run_htn_test("tinyHTN", SimpleRescueProblem, "P5a — HTN tinyHTN")


def test_htn_htnBase():
    """P5a: HTN resuelve SimpleRescueProblem en htnBase (layout más grande del enunciado)."""
    from planning.problems import SimpleRescueProblem
    _run_htn_test("htnBase", SimpleRescueProblem, "P5a — HTN htnBase")


def test_htn_hierarchy_structure():
    """P5a: La jerarquía debe contener FullRescueMission con refinamientos correctos."""
    import world.rescue_layout as rescue_layout
    from planning.problems import SimpleRescueProblem
    from planning.htn import build_htn_hierarchy, HLA

    layout = rescue_layout.get_layout("tinyHTN")
    problem = SimpleRescueProblem(layout)
    hlas = build_htn_hierarchy(problem)

    top = hlas[0]
    check("P5a — Estructura HTN", "HLA raíz es FullRescueMission",
          "FullRescueMission" in top.name, f"nombre={top.name}")
    check("P5a — Estructura HTN", "FullRescueMission tiene exactamente 1 refinamiento",
          len(top.refinements) == 1)

    ref = top.refinements[0]
    check("P5a — Estructura HTN", "Refinamiento tiene al menos 3 pasos",
          len(ref) >= 3, f"{len(ref)} pasos en el refinamiento")

    # El último paso del refinamiento debe ser una acción Rescue primitiva
    last = ref[-1]
    check("P5a — Estructura HTN", "Último paso de FullRescueMission es Rescue primitivo",
          isinstance(last, Action) and last.name.startswith("Rescue"),
          f"último paso = {last}")

    # Los primeros pasos deben ser PrepareSupplies y ExtractPatient (HLAs)
    check("P5a — Estructura HTN", "Primer sub-paso es PrepareSupplies HLA",
          isinstance(ref[0], HLA) and "PrepareSupplies" in ref[0].name,
          f"ref[0]={ref[0]}")
    check("P5a — Estructura HTN", "Segundo sub-paso es ExtractPatient HLA",
          isinstance(ref[1], HLA) and "ExtractPatient" in ref[1].name,
          f"ref[1]={ref[1]}")


# ===========================================================================
# PUNTO 5b — HTN Multi-rescate
# ===========================================================================

def test_htn_multi_tinyMulti():
    """P5b: HTN resuelve MultiRescueProblem en tinyMulti (2 pacientes)."""
    from planning.problems import MultiRescueProblem
    problem, plan = _run_htn_test("tinyMulti", MultiRescueProblem,
                                  "P5b — HTN Multi tinyMulti")
    if plan:
        check("P5b — HTN Multi tinyMulti", "Plan cubre ambos rescates (>15 pasos)",
              len(plan) > 15, f"Longitud={len(plan)}")


def test_htn_multi_root_hlas_count():
    """P5b: build_htn_hierarchy debe generar una misión por paciente."""
    import world.rescue_layout as rescue_layout
    from planning.problems import MultiRescueProblem
    from planning.htn import build_htn_hierarchy

    layout = rescue_layout.get_layout("tinyMulti")
    problem = MultiRescueProblem(layout)
    hlas = build_htn_hierarchy(problem)
    n_patients = len(problem.objects["patients"])
    check("P5b — HTN Multi estructura", "Un FullRescueMission por paciente",
          len(hlas) == n_patients,
          f"pacientes={n_patients}, HLAs raíz={len(hlas)}")
    check("P5b — HTN Multi estructura", "Cada HLA raíz es FullRescueMission",
          all("FullRescueMission" in h.name for h in hlas),
          str([h.name for h in hlas]))


def test_htn_multi_smallMulti():
    """P5b: HTN resuelve MultiRescueProblem en smallMulti."""
    from planning.problems import MultiRescueProblem
    _run_htn_test("smallMulti", MultiRescueProblem, "P5b — HTN Multi smallMulti")


# ===========================================================================
# MAIN
# ===========================================================================

if __name__ == "__main__":
    print("=" * 90)
    print("  TEST PUNTOS 1 Y 5 - Taller 4: Planificacion Automatizada  |  Operacion Fenix")
    print("=" * 90)

    print("\n--- PUNTO 1a: Esquemas de accion (domain.py) ---")
    test_domain_schemas_defined()
    test_action_schema_parameters()
    test_pickup_precond_and_effects()
    test_putdown_precond_and_effects()
    test_rescue_precond_and_effects()
    test_setup_supplies_precond_and_effects()

    print("\n--- PUNTO 1a: Goals de los problemas (problems.py) ---")
    test_simple_rescue_problem_goal()
    test_multi_rescue_problem_goal()
    test_goal_not_satisfied_in_initial_state()

    print("\n--- PUNTO 1b: is_applicable (pddl.py) ---")
    test_move_applicable_all_precond()
    test_move_not_applicable_free_missing()
    test_move_not_applicable_at_missing()
    test_pickup_applicable()
    test_pickup_not_applicable_no_handsfree()
    test_pickup_not_applicable_obj_not_here()
    test_setup_supplies_applicable()
    test_setup_supplies_not_applicable_no_holding()
    test_rescue_applicable()
    test_rescue_not_applicable_no_supplies()
    test_rescue_not_applicable_patient_not_here()

    print("\n--- PUNTO 1b: apply_action / semantica RESULT (pddl.py) ---")
    test_result_order_del_before_add()
    test_apply_pickup_full()
    test_apply_putdown_full()
    test_apply_setup_supplies_full()
    test_apply_rescue_full()

    print("\n--- PUNTO 1b: get_applicable_actions + getSuccessors (pddl.py) ---")
    test_get_applicable_actions_basic()
    test_get_applicable_actions_all_valid()
    test_get_applicable_actions_move_present()
    test_get_applicable_actions_rescue_not_present()
    test_get_successors_uses_applicable_actions()

    print("\n--- PUNTO 5a: HTN simple - build_htn_hierarchy + hierarchicalSearch ---")
    test_htn_tinyHTN()
    test_htn_htnBase()
    test_htn_hierarchy_structure()

    print("\n--- PUNTO 5b: HTN multi-rescate ---")
    test_htn_multi_tinyMulti()
    test_htn_multi_root_hlas_count()
    test_htn_multi_smallMulti()

    print_matrix()
