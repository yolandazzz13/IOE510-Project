from gurobipy import *
import gurobipy as gp
import model_data
import matplotlib.pyplot as plt
import numpy as np

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


time_factor = [1, 0.9667, 0.9334, 0.9, 0.8667, 0.8334,
                0.8, 0.8334, 0.8667, 0.9, 0.9334, 0.9667, 
                1, 1.0334, 1.0667, 1.1, 1.1334, 1.1667, 1.2,
                1.1667, 1.1334, 1.1, 1.0667, 1.0334]

            
Hours = range(24)

alpha_values = [0.4 + i * 0.01 for i in range(20)]  # from 0 to 1, incrementing by 0.1
total_disutility = []
risk_values = []

for alpha in [0.49]:
    m = gp.Model("Power")

    ##decision variable
    z = {}
    for i in ZipCodes:
        for j in range(Generators[i]):
            for t in Hours:
                z[i, j, t] = m.addVar(vtype=GRB.BINARY, name="z[{},{},{}]".format(i, j, t))

    # i: all zipcodes, j : all generators in that zipcode, t: time period

    def compute_frac(open, total):
        if total == 0:
            return 0.5
        else:
            return open/ total
        
    def risk(i, t):
        return 0.2* float(model_data.wildfire_probabilities[i]) + 0.8 * float(model_data.wildfire_probabilities[i]) * compute_frac(gp.quicksum(z[i,j,t] for j in range(Generators[i])), Generators[i])

    # Add Objective Function
    m.setObjective(gp.quicksum((alpha * risk(i, t)) * 10000+ 
                                (1 - alpha) * model_data.infrastructure[i]['TotalkWh'] * model_data.importance_metric[i] * time_factor[t] *(1-compute_frac(gp.quicksum(z[i,j,t] for j in range(Generators[i])), Generators[i]))
                                for i in ZipCodes for t in Hours), GRB.MINIMIZE)
        
    # Add Constraints
    # for i in ZipCodes:
    #     for j in range(Generators[i]):
    #             m.addConstr(gp.quicksum(z[i,j,t] for t in Hours) >= 12)
        
    # for i in ZipCodes:
    #     for t in Hours:
    #         m.addConstr( 0.5* float(model_data.wildfire_probabilities[i]) + 0.5 * float(model_data.wildfire_probabilities[i]) * compute_frac(gp.quicksum(z[i,j,t] for j in range(Generators[i])), Generators[i]) <= 0.8* float(model_data.wildfire_probabilities[i]) )


    for i in ZipCodes:
        permissible_risk = 0.8*float(model_data.wildfire_probabilities[i]) * len(Hours)
        m.addConstr(gp.quicksum(risk(i,t) for t in Hours) <= permissible_risk, f"CumulativeRiskLimit_{i}")


    # for i in ZipCodes:
    #     # Transform permissible risk using logarithm
    #     log_permissible_risk = 0.8 * math.log(float(model_data.wildfire_probabilities[i])) * len(Hours)

    #     # Calculate the sum of logarithms of risk values instead of their product
    #     # Note: Gurobi's gp.quicksum and adding a generator for logarithmic transformation
    #     m.addConstr(gp.quicksum(math.log(risk(i, t)) for t in Hours) <= log_permissible_risk, f"CumulativeRiskLimit_{i}")

    # Assuming risk_vars are the gurobi variables corresponding to risk(i, t) computations
    # log_risk_var = {}
    # for i in ZipCodes:
        
    #     log_permissible_risk = math.log(0.1) + math.log(float(model_data.wildfire_probabilities[i])) * len(Hours)
    #     for t in Hours:
    #         # Define breakpoints and their log values
    #         breakpoints = [0.002, 0.02, 0.1, 0.24]  # Example breakpoints
    #         log_values = [math.log(x) for x in breakpoints]
            
    #         # Create a new variable to represent the log of the risk
    #         log_risk_var[i, t] = m.addVar(lb=-GRB.INFINITY, name=f"log_risk_{i}_{t}")
            
    #         # Add piecewise-linear constraint to model the variable's behavior
    #         m.setPWLObj(log_risk_var[i, t], breakpoints, log_values)

    #     m.update()  # Always update model after making changes

    #     # Constraint for the sum of log risks
    #     cumulative_log_risk = gp.quicksum(log_risk_var[i, t] for t in Hours)
    #     m.addConstr(cumulative_log_risk <= log_permissible_risk, f"CumulativeRiskLimit_{i}")


    no_gen_on = {}
    for i in ZipCodes:
        for t in Hours:
            no_gen_on[i, t] = m.addVar(vtype=GRB.BINARY, name=f"no_gen_on[{i},{t}]")

    m.update()  # Important to update the model after adding variables

    # Constraints to control the auxiliary variables
    for i in ZipCodes:
        if Generators[i] > 0:
            for t in Hours:
                sum_generators_on = gp.quicksum(z[i, j, t] for j in range(Generators[i]))
                # Activate no_gen_on[i, t] if no generators are on
                m.addGenConstrIndicator(no_gen_on[i, t], True, sum_generators_on == 0)
                # Set no_gen_on[i, t] to 0 if any generator is on
                m.addGenConstrIndicator(no_gen_on[i, t], False, sum_generators_on >= 1)

    m.update() 
    # Limit the number of hours with no generators on to a maximum of 2 per day per zip code
    for i in ZipCodes:
        if Generators[i] > 0:
            m.addConstr(gp.quicksum(no_gen_on[i, t] for t in Hours) <= 10, name=f"max_no_gen_limit[{i}]")

    
    shortfall = {}
    for i in ZipCodes:
        shortfall[i] = m.addVar(vtype=GRB.CONTINUOUS, name=f"shortfall[{i}]")

    # Update model to integrate new variables
    m.update()

    # Define constraints for shortfall calculations
    for i in ZipCodes:
        if Generators[i] > 0:
            m.addConstr(shortfall[i] == gp.quicksum((1 - compute_frac(gp.quicksum(z[i, j, t] for j in range(Generators[i])),Generators[i] ) )  for t in Hours),
                        name=f"shortfall_calc_{i}")

    # Calculate average shortfall
    total_shortfall = gp.quicksum(shortfall[i] for i in ZipCodes if Generators[i] > 0 )
    average_shortfall = total_shortfall / (len(ZipCodes) -6)

    # Calculate variance of shortfall
    variance = gp.quicksum((shortfall[i] - average_shortfall) * (shortfall[i] - average_shortfall) for i in ZipCodes if Generators[i] > 0) / (len(ZipCodes) - 6)

   

    # Constraint to limit the variance under a specific threshold
    variance_threshold = 10# Example threshold
    m.addConstr(variance <= variance_threshold, name="variance_constraint")
    m.update()

    # Existing model constraints, variables, and objective

    # Step 5: Create constraints to link no_gen_on with total_time_without_power
    # for i in ZipCodes:
    #     if Generators[i] > 0:
    #         m.addConstr(total_time_without_power[i] == gp.quicksum(no_gen_on[i, t] for t in Hours),
    #                     name=f"total_time_without_power_{i}")

    m.optimize()
    # m.computeIIS()
    # m.write("model.ilp")
    if m.status == GRB.Status.OPTIMAL:
        # for i in ZipCodes:
        #     if Generators[i] > 0:  # Only consider regions with generators
        #         print(f"Region {i}: {total_time_without_power[i].X} hours")
        disutility = 0
        # for i in ZipCodes:
            
        #     for t in Hours:
                
        #         active_generators_frac = compute_frac(gp.quicksum(z[i, j, t].X for j in range(Generators[i])), Generators[i])
        #                     # Compute diutility part of the objective function
        #         disutility += (1 - alpha) * model_data.infrastructure[i]['TotalkWh'] * model_data.importance_metric[i] * time_factor[t] * (1 - active_generators_frac)
        
        total_risk =  sum(risk(i, t) for i in ZipCodes for t in Hours).getValue() *10000  # assuming risk is calculated and accessible
        disutility = (m.objVal - alpha * total_risk)/ (1 - alpha)

        total_disutility.append(-disutility)
        risk_values.append(total_risk)

       
        # for i in ZipCodes:
        #      # Only process zip codes with generators
        #     for t in Hours:
        #         # Compute the fraction of generators that are on
        #         active_generators_frac = compute_frac(gp.quicksum(z[i, j, t].X for j in range(Generators[i])), Generators[i])
                
        #         # Calculate the infrastructure-related part of the expression
        #         infrastructure_component = (1 - alpha) * model_data.infrastructure[i]['TotalkWh'] * model_data.importance_metric[i] * time_factor[t] * (1 - active_generators_frac)
                
        #         # Print the result
        #         print(f"Zip Code {i}, Hour {t}: Infrastructure Component = {infrastructure_component}")

        # for i in ZipCodes:
        #     for t in Hours:
        #         # Calculate the value of the expression for current i and t
        #         current_risk_value = risk(i, t)  # This should evaluate the risk based on the current solution
        #         expression_value = alpha * current_risk_value * 50000
                
        #         # Print the result
        #         print(f"Zip Code {i}, Hour {t}:  Expression Value = {expression_value}")
        
        sum_dis = 0
        sum_risk = 0
        for i in ZipCodes:
            day_risk =  gp.quicksum(risk(i, t) for t in Hours).getValue()
            day_disutility = gp.quicksum (model_data.infrastructure[i]['TotalkWh'] * time_factor[t] *(1-compute_frac(gp.quicksum(z[i,j,t] for j in range(Generators[i])), Generators[i])) for t in Hours).getValue()
            sum_dis += day_disutility
            sum_risk += day_risk
            print(f"Risk {i}: {day_risk} ")
            print(f"Disutility {i}: {day_disutility} ")
        
        print(f"total risk : {sum_risk} ")
        print(f"total disutility : {sum_dis} ")
        

        for i in ZipCodes:
            total_time_without_power = gp.quicksum(no_gen_on[i, t] for t in Hours).getValue()
            print(f"Zip Code {i}: {total_time_without_power} hours without power")

        for i in ZipCodes:
            for t in Hours:
                # Calculate the number of open generators for each zip code and time period
                num_open_generators = sum(z[i, j, t].X for j in range(Generators[i])) 
                
                print(f"Zip Code {i}, Hour {t}: {num_open_generators} generators open")
        print('\nCost: %g' % m.objVal)
        # Optionally, print individual variable values
        # for v in m.getVars():
        #     print(f'{v.varName} {v.x}')
        
    
    else:
        print('No solution or suboptimal solution found.')


risk_levels = np.array(risk_values)
diutility_values = np.array(total_disutility)

# Calculate differences between consecutive points
risk_differences = np.diff(risk_levels)
diutility_differences = np.diff(diutility_values)

# Compute gradients between adjacent points
# Note: This will return an array of gradients, where each gradient corresponds to the slope between two adjacent points.
gradients = diutility_differences / risk_differences

# If you need to pair each gradient with its corresponding segment (defined by starting risk level),
# you can do the following:
gradient_pairs = list(zip(risk_levels[:-1], gradients))

# Now print or process the gradients as needed
for i, (risk, gradient) in enumerate(gradient_pairs):
    print(f"Segment {i}: Risk Level = {risk}, Gradient = {gradient}")

# If you want to identify the segment with the largest gradient (sharpest increase in diutility for change in risk),
# you can find the maximum gradient:
max_gradient_index = np.argmax(gradients)
max_gradient = gradients[max_gradient_index]
print(f"The largest gradient is {max_gradient} between the risk levels {risk_levels[max_gradient_index]} and {risk_levels[max_gradient_index + 1]}")

plt.figure(figsize=(10, 6))
plt.plot(risk_values, total_disutility, marker='o')
plt.title('Efficiency Frontier')
plt.xlabel('Total Risk')
plt.ylabel('Total disutility')
plt.grid(True)
plt.show()