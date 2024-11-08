# Until, Globally, Finally, Next, And, Or, Not
_operators = {'U', 'X', 'v', '!'}
_binary = {'U', 'v'}
_unary = _operators - _binary

operators = {
    "all": _operators,
    "binary": _binary,
    "unary": _unary   
}