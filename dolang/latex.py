import re
import ast

def eval_scalar(tree):
    try:
        if isinstance(tree, ast.Num):
            return tree.n
        elif isinstance(tree, ast.UnaryOp):
            if isinstance(tree.op, ast.USub):
                return -tree.operand.n
            elif isinstance(tree.op, ast.UAdd):
                return tree.operand.n
        else:
            raise Exception("Don't know how to do that.")
    except:
        raise Exception("Don't know how to do that.")


def parse(s): return ast.parse(s).body[0].value

class ExprVisitor(ast.NodeVisitor):

    def __init__(self, variables):
        self.variables = variables

    def visit_Call(self, call):
        name = call.func.id
        if name in self.variables:
            assert(len(call.args) == 1)
            n = eval_scalar(call.args[0])
            return self.visit_Variable((name, n))
        else:
            return self.visit_RCall(call)

    def visit_RCall(self, call):
        return self.generic_visit(call)

    def visit_Name(self, cname):
        name = cname.id
        if name in self.variables:
            return self.visit_Variable((name, 0))
        else:
            return self.visit_RName(cname)

    def visit_RName(self, name):
        return self.generic_visit(name)

class ExprTransformer(ast.NodeTransformer):

    def __init__(self, variables):
        self.variables = variables

    def visit_Call(self, call):
        name = call.func.id
        if name in self.variables:
            assert(len(call.args) == 1)
            n = eval_scalar(call.args[0])
            return self.visit_Variable((name, n))
        else:
            return self.generic_visit(call)

    def visit_Name(self, cname):
        name = cname.id
        if name in self.variables:
            return self.visit_Variable((name, 0))
        else:
            return self.generic_visit(cname)


class TimeShift(ExprVisitor):

    def __init__(self, variables, shift):
        self.variables = variables
        self.shift = shift

    def visit_Variable(self, tvar):
        name, t = tvar
        return parse( "{}({})".format(name,t+self.shift))


class Apply(ExprVisitor):

    def __init__(self, variables, fun):
        self.variables = variables
        self.fun = fun

    def visit_Variable(self, tvar):
        return self.fun(tvar)


reg_rad = re.compile("([^_]+)")
reg_sep = re.compile("(&|_)")
reg_bar = re.compile("(.*)(bar|star)")

gl = ['alpha', 'beta', 'gamma', 'delta', 'eta','epsilon', 'iota', 'kappa',
'lambda', 'mu', 'nu', 'rho','pi', 'sigma', 'tau','theta','upsilon','omega','phi','psi','zeta', 'xi', 'chi',
'Gamma', 'Delta', 'Lambda', 'Sigma','Theta','Upsilon','Omega','Xi' , 'Pi' ,'Phi','Psi' ]
gl_special = {
    'lam': '\\lambda'
}
greek_letters = dict([ (x,'\\' + x ) for x in gl ])
greek_letters.update(gl_special)

def greekify(expr):
    m = reg_bar.match(expr)
    if m:
        expr = m.group(1)
        suffix = m.group(2)
    else:
        suffix = None
    if expr in greek_letters:
        res = greek_letters[expr]
    else:
        res = expr
    if suffix=='bar':
        res = "\\overline{{{}}}".format(res)
    elif suffix == 'star':
        res = "{}^{{\\star}}".format(res)
    return res
# greekify('zbar')


def split_name_into_parts(a):
    s = a.replace('__','&')
    m = reg_rad.findall(a)
    rad = m[0]
    cont = m[1:]
    m = reg_sep.findall(s)
    exponents = []
    indices = []
    for i in range(len(cont)):
        if m[i] == '_':
          indices.append(cont[i])
        else:
          exponents.append(cont[i])
    return [rad, indices, exponents]

def name_to_latex(name, date=None):
    [rad, indices, exponents] = split_name_into_parts(name)
    rad = greekify(rad)
    indices = [greekify(r) for r in indices]
    exponents = [greekify(r) for r in exponents]
    up =  '{' + str.join(',', exponents) + '}'
    down =  '{' + str.join(',', indices) + '}'
    sup = '^{0}'.format(up) if up != '{}'  else ''
    sdown = '^{0}'.format(down) if down != '{}' else ''

    up =  '{' + str.join(',', exponents) + '}'

    if date is not None and date != 'S':
        if date == 0:
            times = 't'
        elif date >0:
            times = 't+' + str(date)
        elif date <0:
            times = 't-' + str(-date)
        indices = indices + [times]
    # else:
        # raise(Exception('Time variable {0} has unknown date : {1}.'.format(name,date)))

    down =  '{' + str.join(',', indices) + '}'

    if len(up)>2 and len(down)>2:
        resp = '{0}_{1}^{2}'.format(rad,down,up)
    elif len(up)>2:
        resp = '{0}^{1}'.format(rad,up)
    elif len(down)>2:
        resp = '{0}_{1}'.format(rad,down)
    else:
        resp = '{0}'.format(rad)

    if date == 'S':
        resp = '\\overline{' + resp + '}'
    return resp



class LatexVisitor(ExprVisitor):

    def prec(self, n):
        return getattr(self, 'prec_'+n.__class__.__name__, getattr(self, 'generic_prec'))(n)

    def visit_Variable(self, tvar):
        return name_to_latex(tvar[0], tvar[1])

    def visit_RCall(self, n):
        func = self.visit(n.func)
        args = ', '.join(map(self.visit, n.args))
        if func == 'sqrt':
            return '\\sqrt{%s}' % args
        else:
            return r'\operatorname{%s}\left(%s\right)' % (func, args)

    def prec_Call(self, n):
        return 1000
    def prec_RCall(self, n):
        return 1000
    def visit_RName(self, n):
        return name_to_latex( n.id )
    def prec_RName(self, n):
        return 1000

    def prec_Name(self, n):
        return 1000

    def visit_UnaryOp(self, n):
        if self.prec(n.op) > self.prec(n.operand):
            return r'%s \left(%s\right)' % (self.visit(n.op), self.visit(n.operand))
        else:
            return r'%s %s' % (self.visit(n.op), self.visit(n.operand))

    def prec_UnaryOp(self, n):
        return self.prec(n.op)

    def visit_BinOp(self, n):
        if self.prec(n.op) > self.prec(n.left):
            left = r'\left(%s\right)' % self.visit(n.left)
        else:
            left = self.visit(n.left)
        if self.prec(n.op) > self.prec(n.right):
            right = r'\left(%s\right)' % self.visit(n.right)
        elif self.prec(n.op) == self.prec(n.right) and isinstance(n.op, ast.Sub):
            right = r'\left(%s\right)' % self.visit(n.right)
        else:
            right = self.visit(n.right)
        if isinstance(n.op, ast.Div):
            return r'\frac{%s}{%s}' % (self.visit(n.left), self.visit(n.right))
        elif isinstance(n.op, ast.FloorDiv):
            return r'\left\lfloor\frac{%s}{%s}\right\rfloor' % (self.visit(n.left), self.visit(n.right))
        elif isinstance(n.op, ast.Pow):
            return r'%s^{%s}' % (left, self.visit(n.right))
        else:
            return r'%s %s %s' % (left, self.visit(n.op), right)

    def prec_BinOp(self, n):
        return self.prec(n.op)

    def visit_Sub(self, n):
        return '-'

    def prec_Sub(self, n):
        return 300

    def visit_Add(self, n):
        return '+'

    def prec_Add(self, n):
        return 300

    def visit_Mult(self, n):
        return '\\;'

    def prec_Mult(self, n):
        return 400

    def visit_Mod(self, n):
        return '\\bmod'

    def prec_Mod(self, n):
        return 500

    def prec_Pow(self, n):
        return 700

    def prec_Div(self, n):
        return 400

    def prec_FloorDiv(self, n):
        return 400

    def visit_LShift(self, n):
        return '\\operatorname{shiftLeft}'

    def visit_RShift(self, n):
        return '\\operatorname{shiftRight}'

    def visit_BitOr(self, n):
        return '\\operatorname{or}'

    def visit_BitXor(self, n):
        return '\\operatorname{xor}'

    def visit_BitAnd(self, n):
        return '\\operatorname{and}'

    def visit_Invert(self, n):
        return '\\operatorname{invert}'

    def prec_Invert(self, n):
        return 800

    def visit_Not(self, n):
        return '\\neg'

    def prec_Not(self, n):
        return 800

    def visit_UAdd(self, n):
        return '+'

    def prec_UAdd(self, n):
        return 800

    def visit_USub(self, n):
        return '-'

    def prec_USub(self, n):
        return 800

    def visit_Num(self, n):
        return str(n.n)

    def prec_Num(self, n):
        return 1000

    def generic_visit(self, n):
        if isinstance(n, ast.AST):
            return r'' % (n.__class__.__name__, ', '.join(map(self.visit, [getattr(n, f) for f in n._fields])))
        else:
            return str(n)

    def generic_prec(self, n):
        return 0

def expr2tex(variables, s):
    pt = ast.parse(s).body[0].value
    return LatexVisitor(variables).visit(pt)

def eq2tex(variables, s):

    expr = s.replace('==', '=').replace('=','==')
    
    # TEMP FIX
    expr = expr.replace("[t]", "").replace('[t+1]', "(1)").replace('[t-1]','(-1)')
    expr = expr.replace("^", "**")

    if '==' in expr:
        lhs, rhs = [expr2tex(variables,str.strip(e)) for e in str.split(expr,'==')]
        return "{} = {}".format(lhs, rhs)
    else: return expr2tex(variables,expr)

# ast.dump(ast.parse("a == b"))
