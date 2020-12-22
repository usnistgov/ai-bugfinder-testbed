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

// Connect all function calls within the testcase to their callee with a FLOW_TO relationship
match (tc:GenericNode {type: "Testcase"})<-[:IS_FILE_OF]-(:GenericNode {type:"File"})-[:IS_FILE_OF]->(func:GenericNode {type:"Function"})-[:IS_FUNCTION_OF_CFG]->(callee:UpstreamNode {type:"CFGEntryNode"}) // Get all function declarations in the testcase
// FIXME where tc.name=~"CWE121_Stack_Based_Buffer_Overflow__CWE805_char_declare_memcpy_.*"
with tc, func, callee
match (tc)<-[:IS_FILE_OF]-(:GenericNode {type:"File"})-[:IS_FILE_OF]->(:GenericNode {type:"Function"})-[:IS_FUNCTION_OF_CFG]->(:UpstreamNode {type:"CFGEntryNode"})-[:CONTROLS]->(caller:DownstreamNode {type:"ExpressionStatement"})-[:IS_AST_PARENT*1..10]->(:GenericNode {type:"CallExpression"})-[:IS_AST_PARENT]->(target:GenericNode {type:"Callee"}) // Get all function calls within the testcase
where target.code=func.code // Match function call to function declaration
with caller, callee
create unique (caller)-[interprocedural_call:FLOWS_TO]->(callee) // Create a new control flow relationship from the function call to the function declaration
return count(*)

// Create the return FLOW_TO relationship from the callee to the callers' next node and tag the new relationship with the ID of the call FLOW_TO relationship (created above)
match (tc:GenericNode {type:"Testcase"})-[*0..3]-(:UpstreamNode {type:"CFGEntryNode"})-[:CONTROLS]->(caller:DownstreamNode {type:"ExpressionStatement"})-[cr:FLOWS_TO]->(callee:UpstreamNode {type:"CFGEntryNode"})-[:CONTROLS]->(:DownstreamNode)-[:FLOWS_TO]->(exit:DownstreamNode {type:"CFGExitNode"})
with caller, exit, cr
create unique (caller)-[nr:FLOWS_TO]->(next:DownstreamNode)<-[retflow:FLOWS_TO {callerid:id(cr)}]-(exit)
return count(*)

// TODO
// Check if Joern includes global variables in data flow
// Add REACHES rel on function calls and returns
// Check return FLOWS_TO with multiple returns


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

