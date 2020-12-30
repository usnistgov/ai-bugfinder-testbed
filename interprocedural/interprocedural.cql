// Create index on node type to speed up queries
CREATE INDEX ON :GenericNode(type)

// Create testcase nodes to facilitate handling multiple source files
match (file:GenericNode {type:"File"})
with split(file.code,"/")[2..4] as tc, collect(distinct file) as files
create (testcase:GenericNode { type: "Testcase", label: tc[0], name: tc[1]})
with testcase, files
unwind files as file
with testcase, file
create (testcase)<-[r:IS_FILE_OF]-(file)
return count(*)

// Inline functions' control flow graph when called (i.e. insert a callee function's control flow graph inside the caller's control flow graph, so that the control flow is seemlessly interprocedural)
match (tc:GenericNode {type: "Testcase"})<-[:IS_FILE_OF]-(:GenericNode {type:"File"})-[:IS_FILE_OF]->(func:GenericNode {type:"Function"})-[:IS_FUNCTION_OF_CFG]->(callee:UpstreamNode {type:"CFGEntryNode"}) // Get all function declarations in the testcase
with tc, func, callee
match (tc)<-[:IS_FILE_OF]-(:GenericNode {type:"File"})-[:IS_FILE_OF]->(:GenericNode {type:"Function"})-[:IS_FUNCTION_OF_CFG]->(:UpstreamNode {type:"CFGEntryNode"})-[:CONTROLS]->(caller:DownstreamNode)-[:IS_AST_PARENT*1..10]->(:GenericNode {type:"CallExpression"})-[:IS_AST_PARENT]->(target:GenericNode {type:"Callee"}) // Get all function calls within the testcase
where caller.type in ["ExpressionStatement", "Condition"] and target.code=func.code // Match function call to function declaration
with caller, callee
create unique (caller)-[interprocedural_call:FLOWS_TO]->(callee) // Connect the callee's entry point (head) to where it is called
with callee, caller, interprocedural_call
match (callee)-[:CONTROLS]->(:DownstreamNode)-[:FLOWS_TO|DOM]->(exit:DownstreamNode {type:"CFGExitNode"}) // Find the callee's exit point (tail)
with caller, exit, interprocedural_call
match (caller)-[nr:FLOWS_TO]->(next:DownstreamNode) // Find the caller's next node in its control flow graph
where next.type<>"CFGEntryNode"
create unique (exit)-[interprocedural_return:FLOWS_TO {callerid:id(interprocedural_call)}]->(next) // Connect the callee's tail to the caller's next node
delete nr // Delete the edge between the function call and its next step, so that the control flow graph now goes through the callee and returns to the callers next step


// TODO
// Check if Joern includes global variables in data flow
// Add REACHES rel on function calls and returns
// Check return FLOWS_TO with multiple returns and value return
// Delete/Re-type FLOWS_TO relationship between caller and next node
// Handle nested function calls in the control flow graph
// For calls nested in a condition for example, check if it makes sense to return to the next statement


// Add missing dataflow relationships from last assignment/use to function call
// CAUTION: Might need some tweaking

// Connect last expression to argument
match (arg:GenericNode)-[r11:USE]->(sym:GenericNode)<-[r12:USE]-(expr1:DownstreamNode),
      (arg)<-[r21:IS_AST_PARENT]-(argl:GenericNode)<-[r22:IS_AST_PARENT]-(callexpr:GenericNode)<-[r23:IS_AST_PARENT]-(expr2:DownstreamNode),
      (expr1)-[r31:FLOWS_TO]->(expr2)
where arg.type="Argument" and sym.type="Symbol" and expr1.type="ExpressionStatement"
  and argl.type="ArgumentList" and callexpr.type="CallExpression" and expr2.type="ExpressionStatement"
create (expr1)-[r41:REACHES]->(arg)
return arg,r11,sym,r12,expr1,r21,argl,r22,callexpr,r23,expr2,r31,r41

match (identifier:DownstreamNode)-[r1:REACHES]->(assignment:DownstreamNode), (identifier)-[r2:REACHES]->(fcall:DownstreamNode), (assignment)-[r3:FLOWS_TO]->(fcall)
where identifier.type="IdentifierDeclStatement" and assignment.type="ExpressionStatement" and fcall.type="ExpressionStatement"
  and r1.var=r2.var
create (assignment)-[r4:REACHES {var:r1.var}]->(fcall)
return identifier, fcall, assignment, r1, r2, r3

// Connect callee's arguments to function's parameters (dataflow)
match (fd_file:GenericNode)-[:IS_FILE_OF]->(fd_func:GenericNode)
where fd_file.type="File"
  and fd_func.type="Function"
  and fd_func.code="CWE121_Stack_Based_Buffer_Overflow__CWE805_struct_alloca_memmove_66b_badSink"
with fd_func, split(fd_file.code,"/")[2..4] as testcase
match (fc_file:GenericNode)-[:IS_FILE_OF]->(fc_func:GenericNode)-[:IS_FUNCTION_OF_CFG]->(:UpstreamNode)-[*1..10]->(fc_call:GenericNode)-[:IS_AST_PARENT]->(fc_callee:GenericNode)
where fc_file.type="File" and testcase=split(fc_file.code,"/")[2..4]
  and fc_func.type="Function"
  and fc_call.type="CallExpression"
  and fc_callee.type="Callee" and fc_callee.code=fd_func.code
with fd_func, fc_callee
match (fd_func)-[:IS_FUNCTION_OF_AST]->(fd_decl:GenericNode)-[:IS_AST_PARENT]->(fd_plist:GenericNode)-[:IS_AST_PARENT]->(fd_param:DownstreamNode)
where fd_decl.type="FunctionDef"
  and fd_plist.type="ParameterList"
  and fd_param.type="Parameter"
return fd_func,fd_param,fc_callee
limit 10

// Connect return control flow and dataflow
// TODO
// This is going to be challenging, because a function can return to several different callers

