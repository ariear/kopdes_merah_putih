"""
Control Flow Graph Generator — Robust Statement Coverage
=======================================================
"""

import ast
import json
import networkx as nx
from pyvis.network import Network


# ═══════════════════════════════════════════════════════════════
# UTILITY
# ═══════════════════════════════════════════════════════════════

class _Counter:
    """Monotonically increasing integer — gives every node a unique ID."""
    def __init__(self):
        self._n = 0
    def next(self) -> int:
        self._n += 1
        return self._n


def _unparse(node, maxlen: int = 60) -> str:
    """Safe short unparse — never throws."""
    try:
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and "\n" in node.value:
            # Handle multi-line SQL queries nicely in the graph label
            clean_lines = [line.strip() for line in node.value.split("\n") if line.strip()]
            text = " ".join(clean_lines)
        else:
            text = ast.unparse(node).split("\n")[0]
        return text if len(text) <= maxlen else text[:maxlen - 1] + "…"
    except Exception:
        return node.__class__.__name__


def _call_label(call: ast.Call, prefix: str = "CALL") -> str:
    """
    Build a full, accurate call label including ALL argument forms:
      positional args, *args, keyword args (kw=val), **kwargs.
    Splits into CALL, METHOD, PRINT, or BATCH based on call type.
    """
    func = call.func

    # 1. Klasifikasi Call Type Khusus untuk Print, Method, Executemany, dll.
    if isinstance(func, ast.Name) and func.id == "print":
        prefix = "PRINT"
        name = "print"
    elif isinstance(func, ast.Attribute):
        obj_part = _unparse(func.value)
        if func.attr == "executemany":
            prefix = "BATCH"
        else:
            prefix = "METHOD"
        name = f"{obj_part}.{func.attr}"
    elif isinstance(func, ast.Name):
        name = func.id
    else:
        name = _unparse(func)

    # 2. Ambil Argumen
    parts = []
    for arg in call.args:
        if isinstance(arg, ast.Starred):
            parts.append(f"*{_unparse(arg.value)}")
        else:
            parts.append(_unparse(arg))

    for kw in call.keywords:
        if kw.arg is None:
            parts.append(f"**{_unparse(kw.value)}")
        else:
            parts.append(f"{kw.arg}={_unparse(kw.value)}")

    args_str = ", ".join(parts)
    return f"{prefix}: {name}({args_str})"


def _rhs_hint(value) -> str:
    """Return a short bracketed hint when the RHS has a notable sub-expression."""
    if isinstance(value, ast.ListComp): return " [listcomp]"
    if isinstance(value, ast.SetComp): return " [setcomp]"
    if isinstance(value, ast.DictComp): return " [dictcomp]"
    if isinstance(value, ast.GeneratorExp): return " [genexpr]"
    if isinstance(value, ast.Lambda): return " [lambda]"
    if isinstance(value, ast.Call): return f" [calls {_unparse(value.func)}()]"
    
    calls_inside = [n for n in ast.walk(value) if isinstance(n, ast.Call)]
    if calls_inside:
        names = ", ".join(_unparse(c.func) + "()" for c in calls_inside[:2])
        suffix = ", …" if len(calls_inside) > 2 else ""
        return f" [calls {names}{suffix}]"
    return ""


# ═══════════════════════════════════════════════════════════════
# LABEL BUILDERS
# ═══════════════════════════════════════════════════════════════

def _label_for_stmt(stmt) -> str:
    """Build a descriptive label for any simple / expression statement."""
    if isinstance(stmt, ast.Assign):
        val  = stmt.value
        hint = _rhs_hint(val)

        if len(stmt.targets) > 1:
            chain = " = ".join(_unparse(t) for t in stmt.targets)
            return f"ASSIGN: {chain} = {_unparse(val)}{hint}"

        target = stmt.targets[0]
        if isinstance(target, (ast.Tuple, ast.List)):
            elts = ", ".join(_unparse(e) for e in target.elts)
            return f"UNPACK: ({elts}) = {_unparse(val)}{hint}"

        return f"ASSIGN: {_unparse(target)} = {_unparse(val)}{hint}"

    if isinstance(stmt, ast.AnnAssign):
        target = _unparse(stmt.target)
        ann    = _unparse(stmt.annotation)
        if stmt.value:
            hint = _rhs_hint(stmt.value)
            return f"ASSIGN: {target}: {ann} = {_unparse(stmt.value)}{hint}"
        return f"DECLARE: {target}: {ann}"

    if isinstance(stmt, ast.AugAssign):
        sym = {
            "Add": "+=",  "Sub": "-=",   "Mult": "*=",   "Div":    "/=",
            "Mod": "%=",  "Pow": "**=",  "BitAnd": "&=", "BitOr":  "|=",
            "BitXor": "^=", "LShift": "<<=", "RShift": ">>=",
            "FloorDiv": "//=", "MatMult": "@=",
        }.get(stmt.op.__class__.__name__, "?=")
        hint = _rhs_hint(stmt.value)
        return f"ASSIGN: {_unparse(stmt.target)} {sym} {_unparse(stmt.value)}{hint}"

    if isinstance(stmt, ast.Import):
        parts = [a.name if not a.asname else f"{a.name} as {a.asname}" for a in stmt.names]
        return f"IMPORT: {', '.join(parts)}"

    if isinstance(stmt, ast.ImportFrom):
        mod   = stmt.module or ""
        parts = [a.name if not a.asname else f"{a.name} as {a.asname}" for a in stmt.names]
        return f"IMPORT: from {mod} import {', '.join(parts)}"

    if isinstance(stmt, ast.Delete):
        return f"DEL: {', '.join(_unparse(t) for t in stmt.targets)}"

    if isinstance(stmt, ast.Assert):
        return f"ASSERT: {_unparse(stmt.test)}{f', {_unparse(stmt.msg)}' if stmt.msg else ''}"

    if isinstance(stmt, ast.Global): return f"GLOBAL: {', '.join(stmt.names)}"
    if isinstance(stmt, ast.Nonlocal): return f"NONLOCAL: {', '.join(stmt.names)}"
    if isinstance(stmt, ast.Pass): return "PASS"
    if isinstance(stmt, ast.TypeAlias): return f"TYPE: {_unparse(stmt.name)} = {_unparse(stmt.value)}"

    if isinstance(stmt, ast.Expr):
        val = stmt.value
        if isinstance(val, ast.Call): return _call_label(val)
        if isinstance(val, ast.Await):
            return _call_label(val.value, prefix="AWAIT") if isinstance(val.value, ast.Call) else f"AWAIT: {_unparse(val.value)}"
        if isinstance(val, ast.Yield): return f"YIELD:{f' {_unparse(val.value)}' if val.value else ''}"
        if isinstance(val, ast.YieldFrom): return f"YIELD FROM: {_unparse(val.value)}"
        return f"EXPR: {_unparse(val)}"

    return _unparse(stmt)


# ═══════════════════════════════════════════════════════════════
# CFG BUILDER
# ═══════════════════════════════════════════════════════════════

class CFGBuilder:
    def __init__(self):
        self.G    = nx.DiGraph()
        self._ctr = _Counter()

    def _node(self, label: str) -> str:
        uid     = self._ctr.next()
        node_id = f"{uid}:{label}"
        self.G.add_node(node_id, label=label)
        return node_id

    def _edge(self, src: str, dst: str, label: str = ""):
        self.G.add_edge(src, dst, label=label)

    def _connect_all(self, srcs: set, dst: str, label: str = ""):
        for s in srcs:
            self._edge(s, dst, label)

    def visit_stmts(self, stmts, entry_nodes: set) -> tuple:
        """Sequential structural block analysis."""
        current   = set(entry_nodes)
        terminals = set()

        for stmt in stmts:
            if not current:
                break
            normal, term = self._visit(stmt, current)
            terminals   |= term
            current      = normal

        return current, terminals

    def _visit(self, stmt, entry_nodes: set) -> tuple:
        if isinstance(stmt, ast.If):
            return self._if(stmt, entry_nodes)
        if isinstance(stmt, (ast.For, ast.AsyncFor)):
            return self._for(stmt, entry_nodes)
        if isinstance(stmt, ast.While):
            return self._while(stmt, entry_nodes)
        if isinstance(stmt, ast.Match):
            return self._match(stmt, entry_nodes)
        if isinstance(stmt, (ast.Try, ast.TryStar)):
            return self._try(stmt, entry_nodes)
        if isinstance(stmt, (ast.With, ast.AsyncWith)):
            return self._with(stmt, entry_nodes)
        if isinstance(stmt, (ast.Return, ast.Raise, ast.Break, ast.Continue)):
            return self._terminal(stmt, entry_nodes)
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            n = self._node(f"DEF: {stmt.name}")
            self._connect_all(entry_nodes, n)
            return {n}, set()

        return self._simple(stmt, entry_nodes)

    def _simple(self, stmt, entry_nodes: set) -> tuple:
        label = _label_for_stmt(stmt)
        n = self._node(label)
        
        # Selesaikan pending edge jika ada statement sekuensial setelah IF-tanpa-else
        for src in list(entry_nodes):
            if self.G.has_edge(src, "PENDING_NEXT"):
                self.G.remove_edge(src, "PENDING_NEXT")
                self._edge(src, n, label="False")
            else:
                self._edge(src, n)
        return {n}, set()

    def _terminal(self, stmt, entry_nodes: set) -> tuple:
        if isinstance(stmt, ast.Return):
            label = f"RETURN:{f' {_unparse(stmt.value)}' if stmt.value else ''}"
        elif isinstance(stmt, ast.Raise):
            label = f"RAISE:{f' {_unparse(stmt.exc)}' if stmt.exc else ''}"
        elif isinstance(stmt, ast.Break):
            label = "BREAK"
        else:
            label = "CONTINUE"

        n = self._node(label)
        
        for src in list(entry_nodes):
            if self.G.has_edge(src, "PENDING_NEXT"):
                self.G.remove_edge(src, "PENDING_NEXT")
                self._edge(src, n, label="False")
            else:
                self._edge(src, n)
                
        return set(), {n}

    def _if(self, stmt: ast.If, entry_nodes: set, branch_label: str = "") -> tuple:
        cond = _unparse(stmt.test)
        c_node = self._node(f"IF: {cond}")
        
        for src in list(entry_nodes):
            if self.G.has_edge(src, "PENDING_NEXT"):
                self.G.remove_edge(src, "PENDING_NEXT")
                self._edge(src, c_node, label="False")
            else:
                self._edge(src, c_node, label=branch_label)

        all_normal   = set()
        all_terminal = set()

        # ── Branch True ──
        true_normal, true_term = self.visit_stmts(stmt.body, {c_node})
        for _, dst in self.G.out_edges(c_node):
            if self.G[c_node][dst].get("label") == "":
                self.G[c_node][dst]["label"] = "True"
                break
        all_normal   |= true_normal
        all_terminal |= true_term

        # ── Branch False / Elif / Else ──
        if stmt.orelse:
            if len(stmt.orelse) == 1 and isinstance(stmt.orelse[0], ast.If):
                elif_stmt = stmt.orelse[0]
                elif_normal, elif_term = self._if(elif_stmt, {c_node}, branch_label=f"False → elif {_unparse(elif_stmt.test)}")
                all_normal   |= elif_normal
                all_terminal |= elif_term
            else:
                else_normal, else_term = self.visit_stmts(stmt.orelse, {c_node})
                for _, dst in self.G.out_edges(c_node):
                    if self.G[c_node][dst].get("label") == "":
                        self.G[c_node][dst]["label"] = "False"
                all_normal   |= else_normal
                all_terminal |= else_term
            
            if all_normal:
                merge = self._node("MERGE")
                self._connect_all(all_normal, merge)
                return {merge}, all_terminal
        else:
            # JIKA TIDAK ADA ELSE: C_node (jalur False) digabung bersama normal exits dari True branch
            all_normal.add(c_node)
            self.G.add_edge(c_node, "PENDING_NEXT", label="False") 

        return all_normal, all_terminal

    def _for(self, stmt, entry_nodes: set) -> tuple:
        target_node = stmt.target
        target = f"({', '.join(_unparse(e) for e in target_node.elts)})" if isinstance(target_node, (ast.Tuple, ast.List)) else _unparse(target_node)
        iter_ = _call_label(stmt.iter) if isinstance(stmt.iter, ast.Call) else _unparse(stmt.iter)

        prefix = "ASYNC FOR" if isinstance(stmt, ast.AsyncFor) else "FOR"
        header = self._node(f"{prefix} {target} IN {iter_}")
        
        for src in list(entry_nodes):
            if self.G.has_edge(src, "PENDING_NEXT"):
                self.G.remove_edge(src, "PENDING_NEXT")
                self._edge(src, header, label="False")
            else:
                self._edge(src, header)

        if stmt.body:
            body_normal, body_terminal = self.visit_stmts(stmt.body, {header})
            for _, dst in list(self.G.out_edges(header)):
                if self.G[header][dst].get("label") == "":
                    self.G[header][dst]["label"] = "body"
                    break
        else:
            body_normal, body_terminal = set(), set()

        for n in body_normal:
            self._edge(n, header, label="next iter")

        continues   = {n for n in body_terminal if ":CONTINUE" in n}
        breaks      = {n for n in body_terminal if ":BREAK"    in n}
        returns_etc = body_terminal - continues - breaks

        for n in continues:
            self._edge(n, header, label="continue")

        loop_exit = self._node(f"{prefix} DONE")
        self._edge(header, loop_exit, label="done")
        after = {loop_exit} | breaks

        if stmt.orelse:
            else_normal, else_term = self.visit_stmts(stmt.orelse, {loop_exit})
            after        = else_normal | breaks
            returns_etc |= else_term

        return after, returns_etc

    def _while(self, stmt: ast.While, entry_nodes: set) -> tuple:
        cond   = _unparse(stmt.test)
        header = self._node(f"WHILE: {cond}")
        
        for src in list(entry_nodes):
            if self.G.has_edge(src, "PENDING_NEXT"):
                self.G.remove_edge(src, "PENDING_NEXT")
                self._edge(src, header, label="False")
            else:
                self._edge(src, header)

        if stmt.body:
            body_normal, body_terminal = self.visit_stmts(stmt.body, {header})
            for _, dst in list(self.G.out_edges(header)):
                if self.G[header][dst].get("label") == "":
                    self.G[header][dst]["label"] = "body"
                    break
        else:
            body_normal, body_terminal = set(), set()

        for n in body_normal:
            self._edge(n, header, label="loop back")

        continues   = {n for n in body_terminal if ":CONTINUE" in n}
        breaks      = {n for n in body_terminal if ":BREAK"    in n}
        returns_etc = body_terminal - continues - breaks

        for n in continues:
            self._edge(n, header, label="continue")

        loop_exit = self._node("WHILE DONE")
        self._edge(header, loop_exit, label="done")
        after = {loop_exit} | breaks

        if stmt.orelse:
            else_normal, else_term = self.visit_stmts(stmt.orelse, {loop_exit})
            after       = else_normal | breaks
            returns_etc |= else_term

        return after, returns_etc

    def _match(self, stmt: ast.Match, entry_nodes: set) -> tuple:
        m_node = self._node(f"MATCH: {_unparse(stmt.subject)}")
        
        for src in list(entry_nodes):
            if self.G.has_edge(src, "PENDING_NEXT"):
                self.G.remove_edge(src, "PENDING_NEXT")
                self._edge(src, m_node, label="False")
            else:
                self._edge(src, m_node)

        all_normal   = set()
        all_terminal = set()

        for i, case in enumerate(stmt.cases):
            pattern = _unparse(case.pattern)
            c_node  = self._node(f"CASE {i + 1}: {pattern}")
            self._edge(m_node, c_node, label=f"case {i + 1}")

            entry = {c_node}
            if case.guard:
                g_node = self._node(f"GUARD: {_unparse(case.guard)}")
                self._edge(c_node, g_node)
                entry = {g_node}

            normal, term = self.visit_stmts(case.body, entry)
            all_normal   |= normal
            all_terminal |= term

        if all_normal:
            merge = self._node("MATCH MERGE")
            self._connect_all(all_normal, merge)
            return {merge}, all_terminal

        return set(), all_terminal

    def _try(self, stmt, entry_nodes: set) -> tuple:
        try_node = self._node("TRY")
        
        for src in list(entry_nodes):
            if self.G.has_edge(src, "PENDING_NEXT"):
                self.G.remove_edge(src, "PENDING_NEXT")
                self._edge(src, try_node, label="False")
            else:
                self._edge(src, try_node)

        body_normal, body_terminal = self.visit_stmts(stmt.body, {try_node})
        all_normal   = set()
        all_terminal = set(body_terminal)

        for handler in stmt.handlers:
            exc_label = f"EXCEPT {_unparse(handler.type)}{f' as {handler.name}' if handler.name else ''}" if handler.type else "EXCEPT *"
            exc_node = self._node(exc_label)
            self._edge(try_node, exc_node, label="exception")
            h_normal, h_term = self.visit_stmts(handler.body, {exc_node})
            all_normal   |= h_normal
            all_terminal |= h_term

        if stmt.orelse:
            else_node = self._node("TRY ELSE")
            self._connect_all(body_normal, else_node)
            e_normal, e_term = self.visit_stmts(stmt.orelse, {else_node})
            all_normal   |= e_normal
            all_terminal |= e_term
        else:
            all_normal |= body_normal

        if stmt.finalbody:
            fin_node = self._node("FINALLY")
            self._connect_all(all_normal, fin_node)
            fin_normal, fin_term = self.visit_stmts(stmt.finalbody, {fin_node})
            return fin_normal, all_terminal | fin_term

        return all_normal, all_terminal

    def _with(self, stmt, entry_nodes: set) -> tuple:
        """Refactored: Menghilangkan WITH EXIT node."""
        items = ", ".join(_unparse(item.context_expr) + (f" as {_unparse(item.optional_vars)}" if item.optional_vars else "") for item in stmt.items)
        prefix = "ASYNC WITH" if isinstance(stmt, ast.AsyncWith) else "WITH"
        enter  = self._node(f"{prefix}: {items}")
        
        for src in list(entry_nodes):
            if self.G.has_edge(src, "PENDING_NEXT"):
                self.G.remove_edge(src, "PENDING_NEXT")
                self._edge(src, enter, label="False")
            else:
                self._edge(src, enter)

        body_normal, body_terminal = self.visit_stmts(stmt.body, {enter})
        return body_normal, body_terminal


# ═══════════════════════════════════════════════════════════════
# NODE COLOUR MAP
# ═══════════════════════════════════════════════════════════════

def _node_color(label: str) -> str:
    if label.startswith("START"):              return "#00b894"
    if label.startswith("END"):                return "#d63031"
    if label.startswith("IF"):                 return "#fdcb6e"
    if label.startswith("WHILE DONE"):         return "#636e72"
    if label.startswith("WHILE"):              return "#fdcb6e"
    if label.startswith("FOR DONE"):           return "#636e72"
    if label.startswith("ASYNC FOR"):          return "#74b9ff"
    if label.startswith("FOR"):                return "#74b9ff"
    if label.startswith("MATCH"):              return "#0984e3"
    if label.startswith("CASE"):               return "#81ecec"
    if label.startswith("GUARD"):              return "#55efc4"
    if label.startswith("RETURN"):             return "#e17055"
    if label.startswith("RAISE"):              return "#e17055"
    if label.startswith("BREAK"):              return "#fab1a0"
    if label.startswith("CONTINUE"):           return "#ffeaa7"
    if label.startswith("MERGE"):              return "#a29bfe"
    if label.startswith("EXCEPT"):             return "#fd79a8"
    if label.startswith("TRY"):                return "#e84393"
    if label.startswith("FINALLY"):            return "#fd79a8"
    if label.startswith("PRINT"):              return "#ffeaa7"  # Soft yellow for print log
    if label.startswith("BATCH"):              return "#ff7675"  # Salmon-pink for bulk db execution
    if label.startswith("METHOD"):             return "#00cec9"
    if label.startswith("CALL"):               return "#00b8d4"
    if label.startswith("ASSIGN"):             return "#b2bec3"
    return "#636e72"


# ═══════════════════════════════════════════════════════════════
# PARSE ENGINE
# ═══════════════════════════════════════════════════════════════

def generate_interactive_cfg(file_path: str):
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()

    tree = ast.parse(source)

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        func_name = node.name
        print(f"\nProcessing: {func_name}()")

        builder = CFGBuilder()
        start   = builder._node(f"START: {func_name}()")

        normal_exits, terminal_exits = builder.visit_stmts(node.body, {start})
        end = builder._node(f"END: {func_name}()")
        
        for n in list(normal_exits):
            if builder.G.has_edge(n, "PENDING_NEXT"):
                builder.G.remove_edge(n, "PENDING_NEXT")
                builder._edge(n, end, label="False")
            else:
                builder._edge(n, end)

        for n in terminal_exits:
            builder._edge(n, end)

        G = builder.G
        if G.has_node("PENDING_NEXT"):
            G.remove_node("PENDING_NEXT")

        # Output JSON
        json_data = nx.node_link_data(G)
        with open(f"cfg_{func_name}.json", "w", encoding="utf-8") as jf:
            json.dump(json_data, jf, indent=4)

        # Output HTML PyVis Visual
        net = Network(height="750px", width="100%", directed=True, bgcolor="#1a1a2e", font_color="white")
        net.force_atlas_2based(gravity=-60, central_gravity=0.005, spring_length=130, spring_strength=0.06)

        for nid, data in G.nodes(data=True):
            lbl = data.get("label", nid)
            net.add_node(nid, label=lbl, color=_node_color(lbl), title=lbl, font={"size": 12})

        for src, dst, data in G.edges(data=True):
            elbl = data.get("label", "")
            net.add_edge(src, dst, label=elbl, title=elbl, color={"color": "#636e72", "highlight": "#ffffff"}, arrows="to")

        net.write_html(f"cfg_{func_name}.html")
        print(f"   -> Rendered visual and graph schema successfully.")

if __name__ == "__main__":
    generate_interactive_cfg("backend/main.py")