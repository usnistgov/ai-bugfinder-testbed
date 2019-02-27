
def set_ast_prop(ast_update_dict):
    command = """
        UNWIND %s as data
        MERGE (n) WHERE id(n) = data.id
        SET n.ast = data.ast
    """ % ast_update_dict

