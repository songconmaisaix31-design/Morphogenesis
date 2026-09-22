"""Conservative syntax gate for this fixed, pure three-function exercise only.

This intentionally rejects general Python programs. It is an extra application
constraint before independent evaluation, not an operating-system sandbox.
"""

import ast


def validate_sample(source: str) -> None:
    tree = ast.parse(source)
    functions: dict[str, ast.FunctionDef] = {}
    for statement in tree.body:
        if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Constant) and isinstance(statement.value.value, str):
            continue
        if not isinstance(statement, ast.FunctionDef) or statement.name in functions:
            raise ValueError("sample may only define the three repair functions")
        functions[statement.name] = statement
    if set(functions) != {"clamp", "mean", "unique"}:
        raise ValueError("sample must preserve clamp, mean and unique")
    allowed = (ast.Module, ast.FunctionDef, ast.arguments, ast.arg, ast.Expr, ast.Constant,
               ast.Return, ast.If, ast.Raise, ast.Assign, ast.AnnAssign, ast.AugAssign,
               ast.For, ast.Compare, ast.BoolOp, ast.UnaryOp, ast.BinOp, ast.Name,
               ast.Load, ast.Store, ast.List, ast.Tuple, ast.Set, ast.Dict, ast.Subscript,
               ast.Slice, ast.Call, ast.Attribute, ast.keyword, ast.ListComp, ast.SetComp,
               ast.GeneratorExp, ast.comprehension, ast.operator, ast.unaryop, ast.cmpop,
               ast.boolop, ast.Pass, ast.Break, ast.Continue)
    safe_calls = {"min", "max", "sum", "len", "list", "set", "dict", "ValueError", "range", "enumerate", "abs"}
    signatures = {"clamp": ["value", "lower", "upper"], "mean": ["values"], "unique": ["items"]}
    for function in functions.values():
        if function.decorator_list or function.args.defaults or function.args.kw_defaults:
            raise ValueError("decorators/default argument evaluation are outside the exercise")
        if ([arg.arg for arg in function.args.args] != signatures[function.name]
                or function.args.posonlyargs or function.args.kwonlyargs
                or function.args.vararg or function.args.kwarg):
            raise ValueError("sample must preserve the fixed function signatures")
        local_names = {node.id for node in ast.walk(function) if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)}
        permitted_names = local_names | set(signatures[function.name]) | safe_calls | {"float", "str", "int", "bool"}
        for node in ast.walk(function):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id not in permitted_names:
                raise ValueError("sample references a capability outside the fixed pure exercise")
    for node in ast.walk(tree):
        if not isinstance(node, allowed):
            raise ValueError(f"unsupported sample syntax: {type(node).__name__}")
        if isinstance(node, ast.Name) and node.id.startswith("_"):
            raise ValueError("private runtime names are outside the exercise")
        if isinstance(node, ast.Attribute) and node.attr not in {"append", "add", "fromkeys"}:
            raise ValueError("only list/set accumulation and dict.fromkeys are allowed")
        if isinstance(node, ast.Call):
            target = node.func
            if isinstance(target, ast.Name) and target.id in safe_calls:
                continue
            if isinstance(target, ast.Attribute) and target.attr in {"append", "add", "fromkeys"}:
                continue
            raise ValueError("sample called a function outside the fixed pure exercise")
