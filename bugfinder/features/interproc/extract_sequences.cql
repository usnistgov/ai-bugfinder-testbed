// Extract all possible longest control flow sequences.
// The sequences stop on program exit or on bug sinks.
// A sequence that leads to a bug is labelled as "bad" (bad=true).
match (tc:GenericNode {type:"Testcase"})<-[:IS_FILE_OF]-(:GenericNode {type:"File"})-[:IS_FILE_OF]->(:GenericNode {type:"Function",code:"main"})-[:IS_FUNCTION_OF_CFG]->(e:UpstreamNode {type:"CFGEntryNode"})
where id(tc)=1812208 // FIXME
with distinct e
match p=((e)-[:FLOWS_TO*]->(n:GenericNode))
where e<>n and (not (n)-[:FLOWS_TO]->() or "BugSinkNode" in labels(n))
return p, "BugSinkNode" in labels(n) as bad

// Same for the data flow.
// FIXME: REACHES relationships have a "var" property that we should use
match (tc:GenericNode {type:"Testcase"})<-[:IS_FILE_OF]-(:GenericNode {type:"File"})-[:IS_FILE_OF]->(:GenericNode {type:"Function"})-[:IS_FUNCTION_OF_CFG]->(e:UpstreamNode {type:"CFGEntryNode"})
where id(tc)=1812208 // FIXME
with distinct e
match (e)-[:CONTROLS*]->(src:GenericNode)
where e<>src
with distinct src
match (src)-[:REACHES]->()
where not (src)<-[:REACHES]-()
match p=(src)-[:REACHES*]->(snk:GenericNode)
where src<>snk and (not (snk)-[:REACHES]->() or "BugSinkNode" in labels(snk))
with distinct p, "BugSinkNode" in labels(snk) as bad
return p, bad

// Connect nodes that on the same common data/control flow graph with META relationships
// FIXME: same as above
match (tc:GenericNode {type:"Testcase"})<-[:IS_FILE_OF]-(:GenericNode {type:"File"})-[:IS_FILE_OF]->(:GenericNode {type:"Function",code:"main"})-[:IS_FUNCTION_OF_CFG]->(main:UpstreamNode {type:"CFGEntryNode"})
where id(tc)=1812208 // FIXME
with distinct main
match (main)-[:FLOWS_TO*]->(src:GenericNode)
where (src)-[:FLOWS_TO]->() and (src)-[:REACHES]->() and not (src)<-[:REACHES]-()
with distinct src
match pdf=(src)-[:REACHES*]->(dst:GenericNode), pcf=(src)-[:FLOWS_TO*]->(dst)
where src<>dst and (not (dst)-[:REACHES]->() or "BugSinkNode" in labels(dst))
with distinct pdf,pcf
with filter(n in nodes(pdf) where n in nodes(pcf)) as meta
with meta[..-1] as meta1, meta[1..] as meta2
unwind range(0,size(meta1)-1) as idx
with meta1[idx] as m1, meta2[idx] as m2
merge (m1)-[r:META]->(m2)

// Display the newly created relationships
match (tc:GenericNode {type:"Testcase"})<-[:IS_FILE_OF]-(:GenericNode {type:"File"})-[:IS_FILE_OF]->(:GenericNode {type:"Function",code:"main"})-[:IS_FUNCTION_OF_CFG]->(main:UpstreamNode {type:"CFGEntryNode"})
where id(tc)=1812208 // FIXME
with distinct main
match (main)-[:FLOWS_TO*]->(src:GenericNode)
where (src)-[:FLOWS_TO]->() and (src)-[:REACHES]->() and not (src)<-[:REACHES]-()
with distinct src
match pdf=(src)-[:REACHES*]->(dst:GenericNode), pcf=(src)-[:FLOWS_TO*]->(dst)
where src<>dst and (not (dst)-[:REACHES]->() or "BugSinkNode" in labels(dst))
with distinct pdf,pcf
unwind nodes(pcf) as cfn
optional match (cfn)-[r:META]->()
return pdf,pcf,r

match p=(src)-[:META*]->(dst)
where not (src)<-[:META]-() and not (dst)-[:META]->() or "BugSinkNode" in labels(dst)
return distinct p

// FIXME For sizes, we probably need to count in bytes. Right now, we 
// count in unit size (e.g. "int a[10]" counts as 10, not 10 x sizeof int).

// Add size to dataflow relationshipis for arrays, including
// all downstream nodes carrying the same variable name.
match (n:GenericNode {type:"IdentifierDeclStatement"})
where n.code =~ '.* \\[ [0-9]* \\].*'
with n, split(split(n.code," [")[0]," ")[-1] as var, toInteger(split(split(n.code,"[ ")[1]," ]")[0]) as sz
match p=(n)-[:REACHES* {var:var}]->()
unwind relationships(p) as r
set r.size=sz

// Add size to dataflow for some the allocation functions, including
// all downstream nodes carrying the same variable names.
// FIXME This is untested on "realloc"
// FIXME This only works when the allocation size is constant. Allocation of variable size is not handled.
match (xpr:DownstreamNode)-[:IS_AST_PARENT*]->(cal:GenericNode {type:"CallExpression"})-[:IS_AST_PARENT]->(alc:GenericNode {type:"Callee"})
where id(alc)=755378 and xpr.type in ["IdentifierDeclStatement","ExpressionStatement"]
  and alc.code in ["malloc","ALLOCA","realloc","calloc"]
with xpr, cal, case alc.code when "realloc" then "1" else "0" end as argnum
match (cal)-[:IS_AST_PARENT]->(:GenericNode {type:"ArgumentList"})-[:IS_AST_PARENT]->(arg:GenericNode {type:"Argument",childNum:argnum})
with xpr, arg
match (arg)-[:IS_AST_PARENT*]->(operand:GenericNode)
where substring(operand.type,0,6)<>"Sizeof" and not (operand)-[:IS_AST_PARENT]->()
with xpr, collect(operand) as oplist
where size(oplist)=1 and oplist[0].type="PrimaryExpression"
match (xpr)-[:DEF]->(sym:GenericNode {type:"Symbol"})
match dfp=(xpr)-[:REACHES* {var:sym.code}]->()
unwind relationships(dfp) as dfr
set dfr.size=tointeger(oplist[0].code)

// Forward size to new variable data flow on assignments,
// including all downstream nodes carrying the same variable name.
// FIXME Perhaps handle *var as well.
match (axpr:GenericNode {type:"AssignmentExpression"})<-[:IS_AST_PARENT*]-(expr:DownstreamNode)
where expr.type in ["ExpressionStatement","IdentifierDeclStatement","ForInit"]
match (axpr)-[:USE]->(ssym:GenericNode {type:"Symbol"})
match (expr)<-[src:REACHES {var:ssym.code}]-() where exists(src.size)
match (axpr)-[:DEF]->(dsym:GenericNode {type:"Symbol"})
match p=(expr)-[r:REACHES* {var:dsym.code}]->()
unwind relationships(p) as dst
set dst.size=src.size

