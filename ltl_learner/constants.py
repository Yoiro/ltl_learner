# _operators = {'!', 'X', '|', '&', '>', 'U'}
# _binary = {'|', '&', '>', 'U'}

# _operators = {'!', 'X', '|', '&', '>'}
# _binary = {'|', '&', '>'}

_operators = {'U', 'X', '|', '!', '&', 'G', 'F', '>'}
_binary = {'U', '|', '&', '>'}
_unary = _operators - _binary

operators = {
    "all": _operators,
    "binary": _binary,
    "unary": _unary   
}