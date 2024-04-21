from gurobipy import *
import gurobipy as gp

Blood_type={'A','B','O','AB'}

Node={'1','2','3'}

Pair, Cost=multidict({
        ('1','2'):1,
        ('1','3'):2,
        ('2','3'):3,
        ('2','1'):1,
        ('3','1'):2,
        ('3','2'):3,
        ('3','3'):0,
        ('2','2'):0,
        ('1','1'):0
        })

match = {
    'A': ['A', 'O'],
    'B': ['B', 'O'],
    'AB': ['A', 'B', 'O', 'AB'],
    'O': ['O']
}
same_match = {
    'A': ['O'],
    'B': [ 'O'],
    'AB': ['A', 'B', 'O']
   
}

Demand={}
Supply={}

for n in Node:
    for k in Blood_type:
        Demand[(n,k)]=0
        Supply[(n,k)]=0

Demand[('1','A')]=1
Demand[('1','O')]=3
Demand[('2','AB')]=6
Demand[('2','A')]=4
Demand[('3','O')]=1


Supply[('1','B')]=3
Supply[('2','O')]=10
Supply[('3','AB')]=4
Supply[('3','A')]=5


m = gp.Model("Blood")

##INSERT MODEL HERE
x = {}
for i in Node:
    for k in Node:

        for j in Blood_type:
            x[i, k, j] = m.addVar(name="x[{},{}, {}]".format(i, k, j))


	
# Add Objective Function
m.setObjective(gp.quicksum((Cost[i, k] * x[i, k,j ] for j in Blood_type for (i,k) in Pair)), GRB.MINIMIZE)
	
# Add Constraints
for i in Node:
    for j in Blood_type:
        if j != 'O':
            m.addConstr(gp.quicksum(x[k, i, mj] for k in Node if k != i for mj in match[j]) + 
                gp.quicksum(x[i, i, mj] for mj in same_match[j]) >= Demand[i, j])
        else:
            m.addConstr(gp.quicksum(x[k, i, mj] for k in Node if k != i for mj in match[j]) >= Demand[i, j])


for i in Node:
    m.addConstr(gp.quicksum(x[k, i, j] for k in Node for j in Blood_type) >= gp.quicksum(Demand[i, j] for j in Blood_type))


for i in Node:
    for j in Blood_type:

        m.addConstr(gp.quicksum(x[i, k, j] for k in Node ) <= Supply[i,j])
    

m.addConstrs(x[i,k,j] >= 0 for (i,k) in Pair for j in Blood_type)

#m.addConstrs(x[i,i,j] == 0 for i in Node for j in Blood_type)

m.optimize()

if m.status == GRB.Status.OPTIMAL:
    print('\nCost: %g' % m.objVal)
    for v in m.getVars():
        print('%s %g' % (v.varName, v.x))
else:
    print('No solution')


