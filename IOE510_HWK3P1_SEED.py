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
    92014: 1,
    92037: 3,
    92064: 3,
    92065: 6,
    92101: 6,
    92102: 3,
    92103: 1,
    92104: 2,
    92105: 3,
    92106: 4,
    92107: 2,
    92108: 2,
    92109: 2,
    92110: 3,
    92111: 2,
    92113: 7,
    92114: 3,
    92115: 1,
    92116: 1,
    92117: 2,
    92119: 2,
    92120: 2,
    92121: 15,
    92122: 2,
    92123: 10,
    92124: 5,
    92126: 4,
    92127: 2,
    92128: 2,
    92129: 4,
    92130: 5,
    92131: 2,
    92139: 1,
    92154: 16,
    92173: 1
}


            
Hours = range(24)

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

# Demand={}
# Supply={}

# for n in Zip:
#     for k in Blood_type:
#         Demand[(n,k)]=0
#         Supply[(n,k)]=0

# Demand[('1','A')]=1
# Demand[('1','O')]=3
# Demand[('2','AB')]=6
# Demand[('2','A')]=4
# Demand[('3','O')]=1


# Supply[('1','B')]=3
# Supply[('2','O')]=10
# Supply[('3','AB')]=4
# Supply[('3','A')]=5


m = gp.Model("Wildfire")
ZipCodes = {int(z) for z in ZipCodes} 
importance_metric = {int(k): v for k, v in model_data.importance_metric.items()}
infrastructure = {int(k): v for k, v in model_data.infrastructure.items()}


time_factor = [1, 0.9667, 0.9334, 0.9, 0.8667, 0.8334,
                0.8, 0.8334, 0.8667, 0.9, 0.9334, 0.9667, 
                1, 1.0334, 1.0667, 1.1, 1.1334, 1.1667, 1.2,
                1.1667, 1.1334, 1.1, 1.0667, 1.0334]

##decision variable
z = {}
for i in ZipCodes:
    for j in range(Generators[i]):
        for t in Hours:
            z[i, j, t] = m.addVar(vtype=GRB.BINARY, name=f"z[{i},{j},{t}]") 

# i: all zipcodes, j : all generators in that zipcode, t: time period

#fraction of open generators in a subregion at any time
openG = (gp.quicksum(z[i,j,t] for j in range(Generators[i]) )/ Generators[i])
	
# Add Objective Function
m.setObjective(gp.quicksum((alpha * float(model_data.wildfire_probabilities[i]) * (gp.quicksum(z[i,j,t] for j in range(Generators[i])) / Generators[i]) * 200000 + 
                            (1 - alpha) * model_data.infrastructure[i]['TotalkWh'] * model_data.importance_metric[i] * time_factor[t] * (1 - gp.quicksum(z[i,j,t] for j in range(Generators[i])) / Generators[i])
                            for i in ZipCodes for t in Hours)), GRB.MINIMIZE)
	
# Add Constraints
for i in ZipCodes:
    for j in range(Generators[i]):
            m.addConstr(gp.quicksum(z[i,j,t] for t in Hours) >= 12)
    
for i in ZipCodes:
    for t in Hours:
        m.addConstr( model_data.wildfire_probabilities[i] * (gp.quicksum(z[i,j,t] for j in range(Generators[i])) / Generators[i]) <= 0.15)

for i in ZipCodes:
    for t in Hours:
        m.addConstr( (gp.quicksum(z[i,j,t] for j in range(Generators[i])) / Generators[i]) >= 0.2)



#m.addConstrs(x[i,i,j] == 0 for i in Node for j in Blood_type)

m.optimize()

if m.status == GRB.Status.OPTIMAL:
    print('\nCost: %g' % m.objVal)
    for v in m.getVars():
        print('%s %g' % (v.varName, v.x))
    print("\nSum of all decision variables by zip code and time:")
    for i in ZipCodes:
        for t in Hours :

            sum_z = sum(v.x for j in range(Generators[i]) for v in [z[i, j, t]])
            print(f"Zip code {i}, time {t}: Total sum of z variables = {sum_z}")

elif m.status == GRB.INFEASIBLE:
    print('Model is infeasible')
elif m.status == GRB.UNBOUNDED:
    print('Model is unbounded')
else:
    print('Optimization ended with status %d' % m.status)