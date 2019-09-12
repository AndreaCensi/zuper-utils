from contextlib import contextmanager
from dataclasses import dataclass, field, Field, fields, is_dataclass, MISSING, replace
from datetime import datetime
from decimal import Decimal
from typing import Any, Callable, cast, Dict, List, Optional, Tuple, Type, TypeVar

import termcolor
from frozendict import frozendict

from zuper_commons.text import indent
from zuper_commons.text.coloring import get_length_on_screen, remove_escapes
from zuper_commons.text.table import format_table, Style
from zuper_commons.types.exceptions import ZException
from zuper_commons.ui.colors import (
    color_constant,
    color_float,
    color_int,
    color_ops,
    color_par,
    color_synthetic_types,
    color_typename,
    color_typename2,
    colorize_rgb,
)
from .aliases import TypeLike
from .annotations_tricks import (
    get_Callable_info,
    get_ClassVar_arg,
    get_fields_including_static,
    get_FixedTuple_args,
    get_Optional_arg,
    get_Type_arg,
    get_TypeVar_bound,
    get_Union_args,
    get_VarTuple_arg,
    is_Any,
    is_Callable,
    is_ClassVar,
    is_Dict,
    is_FixedTuple,
    is_ForwardRef,
    is_Iterable,
    is_Iterator,
    is_List,
    is_NewType,
    is_Optional,
    is_Sequence,
    is_Set,
    is_Type,
    is_TypeLike,
    is_TypeVar,
    is_Union,
    is_VarTuple,
    name_for_type_like,
)
from .monkey_patching_typing import (
    DataclassHooks,
    debug_print_bytes,
    debug_print_date,
    debug_print_str,
)
from .my_dict import (
    CustomDict,
    CustomList,
    CustomSet,
    get_CustomDict_args,
    get_CustomList_arg,
    get_CustomSet_arg,
    is_CustomDict,
    is_CustomList,
    is_CustomSet,
)
from .my_intersection import get_Intersection_args, is_Intersection
from .uninhabited import is_Uninhabited

__all__ = ["debug_print"]


@dataclass
class DPOptions:
    obey_print_order: bool = True
    do_special_EV: bool = True
    do_not_display_defaults: bool = True

    compact: bool = False
    abbreviate: bool = False

    # |│┃┆
    default_border_left = "│ "  # <-- note box-drawing

    id_gen: Callable[[object], object] = id  # cid_if_known
    max_initial_levels: int = 20

    omit_type_if_empty: bool = True
    omit_type_if_short: bool = True

    ignores: List[Tuple[str, str]] = field(default_factory=list)

    other_decoration_dataclass: Callable[[object], str] = lambda _: ""

    abbreviate_zuper_lang: bool = False
    ignore_dunder_dunder: bool = False


def get_default_dpoptions() -> DPOptions:
    ignores = []

    id_gen = id

    return DPOptions(ignores=ignores, id_gen=id_gen)


@contextmanager
def no_abbrevs():
    yield
    #
    # prev = Misc.abbreviate
    # try:
    #     Misc.abbreviate = False
    #     yield
    # finally:
    #     Misc.abbreviate = prev


def remove_color_if_no_support(f):
    def f2(*args, **kwargs):
        s = f(*args, **kwargs)

        from zuper_commons.types.exceptions import disable_colored

        if disable_colored():
            s = remove_escapes(s)
        return s

    return f2


@remove_color_if_no_support
def debug_print(x: object, opt: Optional[DPOptions] = None) -> str:
    if opt is None:
        opt = get_default_dpoptions()
    max_levels = opt.max_initial_levels
    already = {}
    stack = ()
    return debug_print0(x, max_levels=max_levels, already=already, stack=stack, opt=opt)


ZException.entries_formatter = debug_print


def debug_print0(
    x: object,
    *,
    max_levels: int,
    already: Dict[int, str],
    stack: Tuple[int, ...],
    opt: DPOptions,
) -> str:
    if id(x) in stack:
        if hasattr(x, "__name__"):
            n = x.__name__
            return color_typename2(n + "↑")  # ↶'
        return "(recursive)"

    if opt.compact:
        if isinstance(x, type) and is_dataclass(x):
            return color_typename(x.__name__)

    # logger.info(f'stack: {stack}  {id(x)} {type(x)}')
    stack2 = stack + (id(x),)
    args = dict(max_levels=max_levels, already=already, stack=stack2, opt=opt)
    dpa = lambda _: debug_print0(_, **args)
    opt_compact = replace(opt, compact=True)
    dp_compact = lambda _: debug_print0(
        _, max_levels=max_levels, already=already, stack=stack2, opt=opt_compact
    )

    # abbreviate = True
    if not opt.abbreviate:
        prefix = ""
    else:

        if is_dataclass(x) and type(x).__name__ != "Constant":
            # noinspection PyBroadException
            try:
                h = opt.id_gen(x)
            except:
                prefix = termcolor.colored("!!!", "red")
            # except ValueError:
            #     prefix = '!'
            else:
                if h is not None:
                    if h in already:
                        # from . import logger
                        if isinstance(x, type):
                            short = type(x).__name__ + "(...) "
                        else:
                            short = color_typename(type(x).__name__) + "(...) "
                        res = short + termcolor.colored("$" + already[h], "green")
                        # logger.info(f'ok already[h] = {res} already = {already}')
                        return res
                    else:
                        already[h] = f"{len(already)}"
                        prefix = termcolor.colored(
                            "&" + already[h], "green", attrs=["dark"]
                        )
                else:
                    prefix = ""
        else:
            prefix = ""

    postfix = " " + prefix if prefix else ""

    # prefix = prefix + f' L{max_levels}'
    if isinstance(x, int):
        return color_int(str(x))

    if isinstance(x, float):
        return color_float(str(x))

    if x is type:
        return color_ops("type")

    if x is BaseException:
        return color_ops("BaseException")

    if x is tuple:
        return color_ops("tuple")

    if x is object:
        return color_ops("object")

    if x is list:
        return color_ops("list")

    if x is dict:
        return color_ops("dict")

    if x is type(...):
        return color_ops("ellipsis")

    if x is int:
        return color_ops("int")

    if x is float:
        return color_ops("float")

    if x is bool:
        return color_ops("bool")

    if x is str:
        return color_ops("str")

    if x is bytes:
        return color_ops("bytes")

    if x is set:
        return color_ops("set")

    if x is slice:
        return color_ops("slice")

    if x is datetime:
        return color_ops("datetime")

    if x is Decimal:
        return color_ops("Decimal")

    if not isinstance(x, str):
        if is_TypeLike(x):
            x = cast(TypeLike, x)
            return debug_print_typelike(x, dp_compact, dpa, opt, prefix, args)

    if isinstance(x, bytes):
        return debug_print_bytes(x)

    if isinstance(x, str):
        return debug_print_str(x, prefix=prefix)

    if isinstance(x, Decimal):
        return color_ops("Dec") + " " + color_float(str(x))

    if isinstance(x, datetime):
        return debug_print_date(x, prefix=prefix)

    if isinstance(x, set):
        return debug_print_set(x, prefix=prefix, **args)

    if isinstance(x, (dict, frozendict)):
        return debug_print_dict(x, prefix=prefix, **args)

    if isinstance(x, tuple):
        # return '(' + ", ".join([debug_print(_) for _ in x]) + ')' + postfix
        return debug_print_tuple(x, prefix=prefix, **args)
    if isinstance(x, list):
        return debug_print_list(x, prefix=prefix, **args)

    if isinstance(x, (bool, type(None))):
        return color_ops(str(x)) + postfix

    if not isinstance(x, type) and is_dataclass(x):
        return debug_print_dataclass_instance(x, prefix=prefix, **args)

    if "Expr" in type(x).__name__:
        return f"{x!r}\n{x}"

    r = f"instance of {type(x).__name__}:\n{x!r}"
    # assert not 'typing.Union' in r, (r, x, is_Union(x))
    return r


cst = color_synthetic_types


def debug_print_typelike(x: TypeLike, dp_compact, dpa, opt, prefix, args) -> str:
    assert is_TypeLike(x), x
    if is_Any(x):
        s = name_for_type_like(x)
        return termcolor.colored(s, on_color="on_magenta")
    if is_Uninhabited(x):
        s = "Nothing"
        return termcolor.colored(s, on_color="on_magenta")

    if (
        (x is type(None))
        or is_List(x)
        or is_Dict(x)
        or is_Set(x)
        or is_ClassVar(x)
        # or is_Type(x)
        or is_Iterator(x)
        or is_Sequence(x)
        or is_Iterable(x)
        or is_NewType(x)
        or is_ForwardRef(x)
        or is_Uninhabited(x)
    ):
        return color_ops(name_for_type_like(x))

    if is_TypeVar(x):
        assert isinstance(x, TypeVar), x

        name = x.__name__

        bound = get_TypeVar_bound(x)
        covariant = getattr(x, "__covariant__")
        contravariant = getattr(x, "__contravariant__")
        if covariant:
            n = name + "+"
        elif contravariant:
            n = name + "-"
        else:
            n = name + "="
        n = cst(n)
        if bound is not object:
            n += color_ops("<") + dp_compact(bound)
        return n

    if is_CustomDict(x):
        x = cast(Type[CustomDict], x)
        K, V = get_CustomDict_args(x)
        s = cst("Dict") + cst("[") + dp_compact(K) + cst(",") + dp_compact(V) + cst("]")
        return s
    if is_Type(x):
        V = get_Type_arg(x)

        s = cst("Type") + cst("[") + dp_compact(V) + cst("]")
        return s
    if is_ClassVar(x):
        V = get_ClassVar_arg(x)

        s = color_ops("ClassVar") + cst("[") + dp_compact(V) + cst("]")
        return s

    if is_CustomSet(x):
        x = cast(Type[CustomSet], x)
        V = get_CustomSet_arg(x)
        s = cst("Set") + cst("[") + dp_compact(V) + cst("]")
        return s

    if is_CustomList(x):
        x = cast(Type[CustomList], x)
        V = get_CustomList_arg(x)
        s = cst("List") + cst("[") + dp_compact(V) + cst("]")
        return s

    if is_Optional(x):
        V = get_Optional_arg(x)
        s0 = dp_compact(V)
        s = color_ops("Optional") + cst("[") + s0 + cst("]")
        return s

    if is_FixedTuple(x):
        ts = get_FixedTuple_args(x)
        ss = []
        for t in ts:
            ss.append(dp_compact(t))
        args = color_ops(",").join(ss)

        s = color_ops("Tuple") + cst("[") + args + cst("]")
        return s

    if is_VarTuple(x):
        t = get_VarTuple_arg(x)
        s = color_ops("Tuple") + cst("[") + dp_compact(t) + ", ..." + cst("]")
        return s

    if is_Union(x):
        Ts = get_Union_args(x)

        if opt.compact or len(Ts) <= 3:
            ss = list(dp_compact(v) for v in Ts)
            inside = color_ops(",").join(ss)
            s = color_ops("Union") + cst("[") + inside + cst("]")
        else:
            ss = list(dpa(v) for v in Ts)
            s = color_ops("Union")
            for v in ss:
                s += "\n" + indent(v, "", color_ops(f"* "))
        return s

    if is_Intersection(x):
        Ts = get_Intersection_args(x)

        if opt.compact or len(Ts) <= 3:
            ss = list(dp_compact(v) for v in Ts)
            inside = color_ops(",").join(ss)
            s = color_ops("Intersection") + cst("[") + inside + cst("]")
        else:
            ss = list(dpa(v) for v in Ts)
            s = color_ops("Intersection")
            for v in ss:
                s += "\n" + indent(v, "", color_ops(f"* "))
        return s

    if is_Callable(x):
        info = get_Callable_info(x)

        def ps(k, v):
            if k.startswith("__"):
                return dp_compact(v)
            else:
                return f"NamedArg({dp_compact(v)},{k!r})"

        params = color_ops(",").join(
            ps(k, v) for k, v in info.parameters_by_name.items()
        )
        ret = dp_compact(info.returns)
        return (
            color_ops("Callable")
            + cst("[[")
            + params
            + color_ops("],")
            + ret
            + cst("]")
        )

    if isinstance(x, type) and is_dataclass(x):
        return debug_print_dataclass_type(x, prefix=prefix, **args)

    return repr(x)


DataclassHooks.dc_str = debug_print


def clipped():
    return " " + termcolor.colored("...", "blue", on_color="on_yellow")


def debug_print_dict(
    x: dict,
    *,
    prefix,
    max_levels: int,
    already: Dict,
    stack: Tuple[int],
    opt: DPOptions,
):
    dpa = lambda _: debug_print0(
        _, max_levels=max_levels - 1, already=already, stack=stack, opt=opt
    )
    opt_compact = replace(opt, compact=True)
    dps = lambda _: debug_print0(
        _, max_levels=max_levels, already={}, stack=stack, opt=opt_compact
    )
    ps = " " + prefix if prefix else ""
    if len(x) == 0:
        if opt.omit_type_if_empty:
            return color_ops("{}") + ps
        else:
            return dps(type(x)) + " " + color_ops("{}") + ps
        # s = color_ops(type(x).__name__) + postfix
    s = dps(type(x)) + ps
    if max_levels == 0:
        return s + clipped()

    r = {}
    for k, v in x.items():
        if isinstance(k, str):

            if k.startswith("zd"):
                k = "zd..." + k[-4:]
            k = termcolor.colored(k, "yellow")
        else:
            k = dpa(k)
        # ks = debug_print(k)
        # if ks.startswith("'"):
        #     ks = k
        r[k] = dpa(v)

    ss = [k + ": " + v for k, v in r.items()]
    nlines = sum(_.count("\n") for _ in ss)
    tlen = sum(get_length_on_screen(_) for _ in ss)
    if nlines == 0 and tlen < 50:
        # x = "," if len(x) == 1 else ""
        res = color_ops("{") + color_ops(", ").join(ss) + color_ops("}") + ps

        if opt.omit_type_if_short:
            return res
        else:
            return dps(type(x)) + " " + res

    leftmargin = color_ops(opt.default_border_left)
    return pretty_dict_compact(s, r, leftmargin=leftmargin, indent_value=0)


def debug_print_dataclass_type(
    x: Type[dataclass],
    prefix: str,
    max_levels: int,
    already: Dict,
    stack: Tuple,
    opt: DPOptions,
) -> str:
    dpa = lambda _: debug_print0(
        _, max_levels=max_levels - 1, already=already, stack=stack, opt=opt
    )
    ps = " " + prefix if prefix else ""
    # ps += f" {id(x)}  {type(x)}" # note breaks string equality
    if opt.abbreviate_zuper_lang:
        if x.__module__.startswith("zuper_lang."):
            return color_constant(x.__name__)
    more = ""
    if x.__name__ != x.__qualname__:
        more += f" ({x.__qualname__})"
    mod = x.__module__ + "."
    s = (
        color_ops("dataclass") + " " + mod + color_typename(x.__name__) + more + ps
    )  # + f' {id(x)}'

    cells = {}
    # FIXME: what was the unique one ?
    seen_fields = set()
    row = 0
    all_fields: Dict[str, Field] = get_fields_including_static(x)
    for name, f in all_fields.items():
        T = f.type
        if opt.ignore_dunder_dunder:
            if f.name.startswith("__"):
                continue

        cells[(row, 0)] = color_ops("field")
        cells[(row, 1)] = f.name
        cells[(row, 2)] = color_ops(":")
        cells[(row, 3)] = dpa(T)

        if f.default != MISSING:
            cells[(row, 4)] = color_ops("=")
            cells[(row, 5)] = dpa(f.default)

        elif f.default_factory != MISSING:
            cells[(row, 4)] = color_ops("=")
            cells[(row, 5)] = f"factory {dpa(f.default_factory)}"

        if is_ClassVar(T):
            if not hasattr(T, name):
                cells[(row, 6)] = "no attribute set"
            else:
                v = getattr(T, name)
                # cells[(row, 4)] = color_ops("=")
                cells[(row, 6)] = dpa(v)

        seen_fields.add(f.name)
        row += 1
    # for k, ann in x.__annotations__.items():
    #     if k in seen_fields:
    #         continue
    #     if not is_ClassVar(ann):
    #         continue
    #     T = get_ClassVar_arg(ann)
    #
    #     cells[(row, 0)] = color_ops("classvar")
    #     cells[(row, 1)] = k
    #     cells[(row, 2)] = color_ops(':')
    #     cells[(row, 3)] = dpa(T)
    #
    #     if hasattr(x, k):
    #         cells[(row, 4)] = color_ops('=')
    #         cells[(row, 5)] = dpa(getattr(x, k))
    #     else:
    #         cells[(row, 5)] = '(no value)'
    #
    #     row += 1

    if not cells:
        return s + ": (no fields)"

    align_right = Style(halign="right")
    col_style = {0: align_right, 1: align_right}
    res = format_table(cells, style="spaces", draw_grid_v=False, col_style=col_style)
    return s + "\n" + res  # indent(res, ' ')


def debug_print_list(
    x: list, prefix: str, max_levels: int, already: Dict, stack: Tuple, opt: DPOptions
) -> str:
    dpa = lambda _: debug_print0(
        _, max_levels=max_levels - 1, already=already, stack=stack, opt=opt
    )
    dps = lambda _: debug_print0(
        _, opt=opt, max_levels=max_levels, already={}, stack=stack
    )
    ps = " " + prefix if prefix else ""
    s = dps(type(x)) + ps

    if max_levels <= 0:
        return s + clipped()

    if len(x) == 0:
        if opt.omit_type_if_empty:
            return color_ops("[]") + ps
        else:
            return dps(type(x)) + " " + color_ops("[]") + ps

    ss = [dpa(v) for v in x]
    nlines = sum(_.count("\n") for _ in ss)
    tlen = sum(get_length_on_screen(_) for _ in ss)
    if nlines == 0 and tlen < 50:
        # x = "," if len(x) == 1 else ""
        res = color_ops("[") + color_ops(", ").join(ss) + color_ops("]") + ps
        return res

    for i, si in enumerate(ss):
        # s += '\n' + indent(debug_print(v), '', color_ops(f'#{i} '))
        s += "\n" + indent(si, "", color_ops(f"#{i} "))
    return s


def debug_print_set(
    x: set, *, prefix: str, max_levels: int, already: Dict, stack: Tuple, opt: DPOptions
) -> str:
    dpa = lambda _: debug_print0(
        _, max_levels=max_levels - 1, already=already, stack=stack, opt=opt
    )
    dps = lambda _: debug_print0(
        _, max_levels=max_levels, already={}, stack=stack, opt=opt
    )

    ps = " " + prefix if prefix else ""

    if len(x) == 0:
        if opt.omit_type_if_empty:
            return color_ops("∅") + ps
        else:
            return dps(type(x)) + " " + color_ops("∅") + ps

    s = dps(type(x)) + ps

    if max_levels <= 0:
        return s + clipped()

    ss = [dpa(v) for v in x]
    nlines = sum(_.count("\n") for _ in ss)
    tlen = sum(get_length_on_screen(_) for _ in ss)
    if nlines == 0 and tlen < 50:
        res = color_ops("{") + color_ops(", ").join(ss) + color_ops("}") + ps
        if opt.omit_type_if_short:
            return res
        else:
            return dps(type(x)) + " " + res

    for vi in ss:
        # s += '\n' + indent(debug_print(v), '', color_ops(f'#{i} '))
        s += "\n" + indent(dpa(vi), "", color_ops(f"* "))
    return s


def debug_print_tuple(
    x: tuple, prefix: str, max_levels: int, already: Dict, stack: Tuple, opt: DPOptions
) -> str:
    dpa = lambda _: debug_print0(
        _, max_levels=max_levels - 1, already=already, stack=stack, opt=opt
    )
    dps = lambda _: debug_print0(
        _, max_levels=max_levels, already={}, stack=stack, opt=opt
    )
    ps = " " + prefix if prefix else ""

    if len(x) == 0:
        if opt.omit_type_if_empty:
            return color_ops("()") + ps
        else:
            return dps(type(x)) + " " + color_ops("()") + ps

    s = dps(type(x)) + ps
    if max_levels <= 0:
        return s + clipped()

    ss = [dpa(v) for v in x]
    tlen = sum(get_length_on_screen(_) for _ in ss)
    nlines = sum(_.count("\n") for _ in ss)
    if nlines == 0 and tlen < 50:
        x = "," if len(x) == 1 else ""
        res = color_ops("(") + color_ops(", ").join(ss) + x + color_ops(")") + ps
        if opt.omit_type_if_short:
            return res
        else:
            return dps(type(x)) + " " + res

    for i, si in enumerate(ss):
        s += "\n" + indent(si, "", color_ops(f"#{i} "))
    return s


def debug_print_dataclass_instance(
    x: dataclass,
    prefix: str,
    max_levels: int,
    already: Dict,
    stack: Tuple,
    opt: DPOptions,
) -> str:
    assert is_dataclass(x)
    fields_x = fields(x)
    dpa = lambda _: debug_print0(
        _, max_levels=max_levels - 1, already=already, stack=stack, opt=opt
    )

    # noinspection PyArgumentList
    other = opt.other_decoration_dataclass(x)

    CN = type(x).__name__
    special_colors = {
        "EV": "#77aa77",
        "ZFunction": "#ffffff",
        "ArgRef": "#00ffff",
        "ZArg": "#00ffff",
        "ATypeVar": "#00ffff",
        "MakeProcedure": "#ffffff",
        "IF": "#fafaaf",
    }

    if CN in special_colors:
        cn = colorize_rgb(CN, special_colors[CN])
    else:
        cn = color_typename(CN)

    ps = " " + prefix if prefix else ""
    s = cn + ps + other

    if max_levels <= 0:
        return s + clipped()

    if opt.obey_print_order and hasattr(x, "__print_order__"):
        options = x.__print_order__
    else:
        options = []
        for f in fields_x:
            options.append(f.name)

    if opt.do_not_display_defaults:
        same = []
        for f in fields_x:
            att = getattr(x, f.name)
            if f.default != MISSING:
                if f.default == att:
                    same.append(f.name)
            elif f.default_factory != MISSING:
                default = f.default_factory()
                if default == att:
                    same.append(f.name)

        to_display = [_ for _ in options if _ not in same]
    else:
        to_display = options
    r = {}
    dpa_result = {}
    for k in to_display:

        # for k, v in x.__annotations__.items():
        # v = x.__annotations__[k]
        if k == "expect":
            att = getattr(x, k)
            # logger.info(f'CN {CN} k {k!r} {getattr(att, "val", None)}')
            if CN == "EV" and k == "expect" and getattr(att, "val", None) is type:
                expects_type = True
                continue

        if not k in to_display:
            continue
        if k.startswith("__"):  # TODO: make configurable
            continue

        if (CN, k) in opt.ignores:
            continue
            # r[color_par(k)] = "(non visualized)"
        else:
            att = getattr(x, k)
            r[color_par(k)] = dpa_result[k] = dpa(att)
        # r[(k)] = debug_print(att)

    expects_type = False
    if len(r) == 0:
        return cn + f"()" + prefix + other

    if type(x).__name__ == "Constant":
        s0 = dpa_result["val"]
        if not "\n" in s0:
            # 「 」‹ ›
            return color_constant("⟬") + s0 + color_constant("⟭")
        else:
            l = color_constant("│ ")  # ║")
            f = color_constant("C ")
            return indent(s0, l, f)

    if type(x).__name__ == "QualifiedName":
        module_name = x.module_name
        qual_name = x.qual_name
        return (
            color_typename("QN") + " " + module_name + "." + color_typename(qual_name)
        )

    if type(x).__name__ == "ATypeVar":
        if len(r) == 1:  # only if no other stuff
            return color_synthetic_types(x.typevar_name)

    if CN == "EV" and opt.do_special_EV:

        if len(r) == 1:
            res = list(r.values())[0]
        else:
            res = pretty_dict_compact("", r, leftmargin="")

        if x.pr is not None:
            color_to_use = x.pr.get_color()

        else:
            color_to_use = "#f0f0f0"

        def colorit(_):

            return colorize_rgb(_, color_to_use)

        if expects_type:
            F = "ET "
        else:
            F = "E "
        l = colorit("┋ ")
        f = colorit(F)

        return indent(res, l, f)
    if len(r) == 1:
        k0 = list(r)[0]
        v0 = r[k0]
        if not "\n" in v0 and not "(" in v0:
            return cn + f"({k0}={v0.rstrip()})" + prefix + other
    ss = list(r.values())
    tlen = sum(get_length_on_screen(_) for _ in ss)
    nlines = sum(_.count("\n") for _ in ss)
    # npars = sum(_.count("(") for _ in ss)
    if nlines == 0 and tlen < 70:
        # ok, we can do on one line
        if type(x).__name__ == "MakeUnion":
            assert len(r) == 1
            ts = x.utypes
            v = [dpa(_) for _ in ts]
            return "(" + color_ops(" ∪ ").join(v) + ")"
        if type(x).__name__ == "MakeIntersection":
            assert len(r) == 1
            ts = x.inttypes
            v = [dpa(_) for _ in ts]
            return "(" + color_ops(" ∩ ").join(v) + ")"

        contents = ", ".join(k + "=" + v for k, v in r.items())
        res = cn + "(" + contents + ")" + ps
        return res

    if CN == "MakeProcedure":
        M2 = "┇ "
    else:
        M2 = opt.default_border_left
    if CN in special_colors:
        leftmargin = colorize_rgb(M2, special_colors[CN])
    else:
        leftmargin = color_typename(M2)

    return pretty_dict_compact(s, r, leftmargin=leftmargin, indent_value=0)


#
# def debug_print_dataclass_compact(
#     x, max_levels: int, already: Dict, stack: Tuple,
#     opt: DPOptions
# ):
#     dpa = lambda _: debug_print0(_, max_levels=max_levels - 1, already=already, stack=stack, opt=opt)
#     # dps = lambda _: debug_print(_, max_levels, already={}, stack=stack)
#     s = color_typename(type(x).__name__) + color_par("(")
#     ss = []
#     for k, v in x.__annotations__.items():
#         att = getattr(x, k)
#         ss.append(f'{color_par(k)}{color_par("=")}{dpa(att)}')
#
#     s += color_par(", ").join(ss)
#     s += color_par(")")
#     return s


def pretty_dict_compact(
    head: Optional[str], d: Dict[str, Any], leftmargin="│", indent_value: int = 0
):  # | <-- note box-making
    if not d:
        return head + ":  (empty dict)" if head else "(empty dict)"
    s = []
    # n = max(get_length_on_screen(str(_)) for _ in d)

    ordered = list(d)
    # ks = sorted(d)
    for k in ordered:
        v = d[k]

        heading = str(k) + ":"
        # if isinstance(v, TypeVar):
        #     # noinspection PyUnresolvedReferences
        #     v = f'TypeVar({v.__name__}, bound={v.__bound__})'
        # if isinstance(v, dict):
        #     v = pretty_dict_compact("", v)

        # vs = v
        if "\n" in v:
            vs = indent(v, " " * indent_value)
            s.append(heading)
            s.append(vs)
        else:
            s.append(heading + " " + v)

        # s.extend(.split('\n'))

    # return (head + ':\n' if head else '') + indent("\n".join(s), '| ')
    indented = indent("\n".join(s), leftmargin)
    return (head + "\n" if head else "") + indented
