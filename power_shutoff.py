from gurobipy import *


Blood_type={'A','B','O','AB'}

Node={'1','2','3'}

Pair, Cost=multidict({
        ('1','2'):1,
        ('1','3'):2,
        ('2','3'):3,
        ('2','1'):1,
        ('3','1'):2,
        ('3','2'):3
        })

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


m = Model("Blood")

##INSERT MODEL HERE

m.optimize()

if m.status == GRB.Status.OPTIMAL:
    print('\nCost: %g' % m.objVal)
    for v in m.getVars():
        print('%s %g' % (v.varName, v.x))
else:
    print('No solution')


