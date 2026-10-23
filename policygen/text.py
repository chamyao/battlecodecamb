"""Read and write the .policy text format.

The format is Python-shaped, so parsing reuses Python's own parser after
rewriting `let x = ...` and `keep x = ...` into assignments.
"""
import ast as pyast
import copy
import re

from .blocks import BY_NAME, resolve
from .tree import Call, Const, Do, EndTurn, If, Let, Var, type_of

_KEEP = re.compile(r"^(\s*)keep\s+(\w+)\s*=\s*(.*)$")
_LET = re.compile(r"^(\s*)let\s+(\w+)\s*=")
_BINOP = {pyast.Add: "add", pyast.Sub: "sub", pyast.Mult: "mul", pyast.Div: "div"}
_CMP = {pyast.Lt: "lt", pyast.LtE: "le", pyast.Gt: "gt", pyast.GtE: "ge", pyast.Eq: "eq", pyast.NotEq: "ne"}
_BOOL = {pyast.And: "and", pyast.Or: "or"}


def _preprocess(text):
    lines = []
    for line in text.splitlines():
        line = line.split("#", 1)[0].rstrip()
        m = _KEEP.match(line)
        if m:
            line = f"{m[1]}{m[2]} = __keep__({m[3]})"
        else:
            line = _LET.sub(r"\1\2 =", line)
        lines.append(line)
    return "\n".join(lines)


def parse(text):
    """Parse policy text into a list of steps, type-checking as it goes.

    Top-level `def` macros are expanded inline where they are called: a macro
    whose body is a single `return <expr>` is used as an expression, any other
    is used as a step. Arguments are substituted as expressions (re-evaluated at
    each use; bind them with let first to pay once). Names a macro assigns are
    renamed per expansion. Macros may call other macros but not themselves.
    """
    module = pyast.parse(_preprocess(text))
    macros, body = {}, []
    for node in module.body:
        if isinstance(node, pyast.FunctionDef):
            a = node.args
            if a.vararg or a.kwarg or a.kwonlyargs or a.defaults or node.decorator_list:
                raise SyntaxError(f"line {node.lineno}: macros take plain positional parameters only")
            if node.name in macros:
                raise NameError(f"line {node.lineno}: macro {node.name} defined twice")
            macros[node.name] = node
        else:
            body.append(node)
    return _Parser(macros).steps(body, {})


class _Inline(pyast.NodeTransformer):
    """Substitute macro arguments and rename the macro's own variables."""

    def __init__(self, args, renames):
        self.args, self.renames = args, renames

    def visit_Name(self, node):
        if node.id in self.args:
            return copy.deepcopy(self.args[node.id])
        if node.id in self.renames:
            return pyast.copy_location(pyast.Name(self.renames[node.id], node.ctx), node)
        return node


class _Parser:
    MAX_EXPANSION_DEPTH = 16

    def __init__(self, macros=None):
        self.macros = macros or {}
        self.expanding = []
        self.n_expansions = 0

    def _expand(self, call):
        """The body of macro `call` with arguments substituted (a list of nodes)."""
        name = call.func.id
        fdef = self.macros[name]
        params = [a.arg for a in fdef.args.args]
        if call.keywords or len(call.args) != len(params):
            raise TypeError(f"line {call.lineno}: macro {name} takes {len(params)} argument(s)")
        if name in self.expanding or len(self.expanding) >= self.MAX_EXPANSION_DEPTH:
            raise SyntaxError(f"line {call.lineno}: macro {name} is recursive")
        self.n_expansions += 1
        assigned = {t.id for n in pyast.walk(fdef) if isinstance(n, pyast.Assign)
                    for t in n.targets if isinstance(t, pyast.Name)}
        renames = {v: f"{v}__{name}{self.n_expansions}" for v in assigned}
        body = copy.deepcopy(fdef.body)
        inline = _Inline(dict(zip(params, call.args)), renames)
        return [inline.visit(n) for n in body]

    def _is_macro_call(self, node):
        return (isinstance(node, pyast.Call) and isinstance(node.func, pyast.Name)
                and node.func.id in self.macros)

    def steps(self, body, scope):
        scope = dict(scope)
        out = []
        for node in body:
            if isinstance(node, pyast.Pass):
                continue
            if isinstance(node, pyast.Expr) and self._is_macro_call(node.value):
                expanded = self._expand(node.value)
                if any(isinstance(n, pyast.Return) for n in expanded):
                    raise TypeError(f"line {node.lineno}: macro {node.value.func.id} returns a value; use it in an expression")
                self.expanding.append(node.value.func.id)
                try:
                    # the macro's steps run in the caller's scope (its own names are renamed)
                    for n in expanded:
                        if not isinstance(n, pyast.Pass):
                            out.append(self.step(n, scope))
                finally:
                    self.expanding.pop()
                continue
            out.append(self.step(node, scope))
        return out

    def step(self, node, scope):
        if isinstance(node, pyast.Return):
            raise SyntaxError(f"line {node.lineno}: return is only allowed as a macro's whole body")
        if isinstance(node, pyast.Expr) and isinstance(node.value, pyast.Call):
            if isinstance(node.value.func, pyast.Name) and node.value.func.id == "end_turn":
                return EndTurn()
            call = self.expr(node.value, scope)
            if not call.block.effect:
                raise TypeError(f"line {node.lineno}: {call.block.key} is not an effect")
            return Do(call)
        if isinstance(node, pyast.Assign):
            (target,) = node.targets
            value, keep = node.value, False
            if isinstance(value, pyast.Call) and getattr(value.func, "id", None) == "__keep__":
                (value,), keep = value.args, True
            if target.id in scope:
                raise NameError(f"line {node.lineno}: {target.id} already defined")
            expr = self.expr(value, scope)
            scope[target.id] = type_of(expr)
            return Let(target.id, expr, keep)
        if isinstance(node, pyast.If):
            cond = self.expr(node.test, scope)
            if type_of(cond) != "Bool":
                raise TypeError(f"line {node.lineno}: if needs a Bool")
            return If(cond, self.steps(node.body, scope), self.steps(node.orelse, scope))
        raise SyntaxError(f"line {node.lineno}: unsupported step {type(node).__name__}")

    def call(self, name, args):
        return Call(resolve(name, [type_of(a) for a in args]), args)

    def expr(self, node, scope):
        if isinstance(node, pyast.Constant):
            if isinstance(node.value, bool):
                return self.call("true" if node.value else "false", [])
            if isinstance(node.value, str):
                return Const("Bytes", node.value.encode())
            if isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
                return Const("Num", node.value)
        elif isinstance(node, pyast.Name):
            if node.id in scope:
                return Var(node.id, scope[node.id])
            return self.call(node.id, [])
        elif self._is_macro_call(node):
            expanded = self._expand(node)
            if len(expanded) != 1 or not isinstance(expanded[0], pyast.Return) or expanded[0].value is None:
                raise TypeError(f"line {node.lineno}: macro {node.func.id} is a step; only a macro whose body is "
                                f"'return <expr>' can be used as a value")
            self.expanding.append(node.func.id)
            try:
                return self.expr(expanded[0].value, scope)
            finally:
                self.expanding.pop()
        elif isinstance(node, pyast.Call) and isinstance(node.func, pyast.Name):
            return self.call(node.func.id, [self.expr(a, scope) for a in node.args])
        elif isinstance(node, pyast.BinOp) and type(node.op) in _BINOP:
            return self.call(_BINOP[type(node.op)], [self.expr(node.left, scope), self.expr(node.right, scope)])
        elif isinstance(node, pyast.Compare) and len(node.ops) == 1 and type(node.ops[0]) in _CMP:
            return self.call(_CMP[type(node.ops[0])],
                             [self.expr(node.left, scope), self.expr(node.comparators[0], scope)])
        elif isinstance(node, pyast.BoolOp):
            result = self.expr(node.values[0], scope)
            for value in node.values[1:]:
                result = self.call(_BOOL[type(node.op)], [result, self.expr(value, scope)])
            return result
        elif isinstance(node, pyast.UnaryOp):
            if isinstance(node.op, pyast.Not):
                return self.call("not", [self.expr(node.operand, scope)])
            if isinstance(node.op, pyast.USub):
                if isinstance(node.operand, pyast.Constant) and not isinstance(node.operand.value, bool):
                    return Const("Num", -node.operand.value)
                return self.call("sub", [Const("Num", 0), self.expr(node.operand, scope)])
        raise SyntaxError(f"line {node.lineno}: unsupported expression {pyast.unparse(node)}")


def format_expr(expr):
    if isinstance(expr, Const):
        if expr.type == "Bytes":
            return '"' + expr.value.decode() + '"'
        value = expr.value
        return str(int(value)) if float(value).is_integer() else repr(float(value))
    if isinstance(expr, Var):
        return expr.name
    blk, args = expr.block, [format_expr(a) for a in expr.args]
    if blk.infix:
        return f"({args[0]} {blk.infix} {args[1]})"
    if blk.name == "not":
        return f"(not {args[0]})"
    return f"{blk.name}({', '.join(args)})"


def format_steps(steps, indent=0):
    pad = "    " * indent
    lines = []
    for step in steps:
        if isinstance(step, EndTurn):
            lines.append(f"{pad}end_turn()")
        elif isinstance(step, Do):
            lines.append(pad + format_expr(step.call))
        elif isinstance(step, Let):
            lines.append(f"{pad}{'keep' if step.keep else 'let'} {step.name} = {format_expr(step.expr)}")
        elif isinstance(step, If):
            lines.append(f"{pad}if {format_expr(step.cond)}:")
            lines.extend(format_steps(step.then, indent + 1) or [f"{pad}    pass"])
            if step.orelse:
                lines.append(f"{pad}else:")
                lines.extend(format_steps(step.orelse, indent + 1))
    return lines


def format_policy(steps):
    return "\n".join(format_steps(steps)) + "\n"
