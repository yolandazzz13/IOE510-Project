from gurobipy import *
import gurobipy as gp
import model_data

Blood_type={'A','B','O','AB'}

ZipCodes = {92014, 92037, 92064, 92065, 92101, 92102,
              92103, 92104, 92105, 92106, 92107, 92108, 92109, 
              92110, 92111, 92113, 92114, 92115, 92116, 92117, 
              92119, 92120, 92121, 92122, 92123, 92124, 92126,
              92127, 92128, 92129, 92130, 92131, 92139, 92154, 92173}

Generators = {
    92014: 0,
    92037: 2,
    92064: 2,
    92065: 5,
    92101: 5,
    92102: 2,
    92103: 0,
    92104: 1,
    92105: 2,
    92106: 3,
    92107: 1,
    92108: 1,
    92109: 1,
    92110: 2,
    92111: 1,
    92113: 6,
    92114: 2,
    92115: 0,
    92116: 0,
    92117: 1,
    92119: 1,
    92120: 1,
    92121: 14,
    92122: 1,
    92123: 9,
    92124: 4,
    92126: 3,
    92127: 1,
    92128: 1,
    92129: 3,
    92130: 4,
    92131: 1,
    92139: 0,
    92154: 15,
    92173: 0
}

            
Hours = range(1, 25)

alpha = 1/2

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

for n in Zip:
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


time_factor = [1, 0.9667, 0.9334, 0.9, 0.8667, 0.8334,
                0.8, 0.8334, 0.8667, 0.9, 0.9334, 0.9667, 
                1, 1.0334, 1.0667, 1.1, 1.1334, 1.1667, 1.2,
                1.1667, 1.1334, 1.1, 1.0667, 1.0334, 1]

##decision variable
z = {}
for i in ZipCodes:
    for j in Generators[i]:
        for t in Hours:
            z[i, j, t] = m.addVar(name="z[{},{}, {}]".format(i, j, t))

# i: all zipcodes, j : all generators in that zipcode, t: time period

#fraction of open generators in a subregion at any time
openG = (gp.quicksum(z[i,j,t] for j in Generators[i]) / Generators[i])
	
# Add Objective Function
m.setObjective(gp.quicksum((alpha * model_data.wildfire_probabilities[i] * (gp.quicksum(z[i,j,t] for j in Generators[i]) / Generators[i]) * 200000 + 
                            (1 - alpha) * model_data.infrastructure[i]['TotalkWh'] * model_data.importance_metric[i] * time_factor[t] * (1 - gp.quicksum(z[i,j,t] for j in Generators[i]) / Generators[i])
                            for i in ZipCodes for t in Hours)), GRB.MINIMIZE)
	
# Add Constraints
for i in ZipCodes:
    for j in Generators[i]:
            m.addConstr(gp.quicksum(z[i,j,t] for t in Hours) >= 22)
    
for i in ZipCodes:
    for t in Hours:
        m.addConstr( model_data.wildfire_probabilities[i] * (gp.quicksum(z[i,j,t] for j in Generators[i]) / Generators[i]) <= 0.15)



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


