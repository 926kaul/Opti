import gurobipy as gp
from gurobipy import GRB
import json

file_path = 'C:\MyCode\opti\stage1_problems\STAGE1_1.json'
with open(file_path, 'r', encoding='utf-8') as file:
    data = json.load(file)

k = int(data['K'])
bike = {'cap':data['RIDERS'][0][2], 'spd':data['RIDERS'][0][1], 'vrc':data['RIDERS'][0][3], 'fxc':data['RIDERS'][0][4], 'svt':data['RIDERS'][0][5]}
walk = {'cap':data['RIDERS'][1][2], 'spd':data['RIDERS'][1][1], 'vrc':data['RIDERS'][1][3], 'fxc':data['RIDERS'][1][4], 'svt':data['RIDERS'][1][5]}
car = {'cap':data['RIDERS'][2][2], 'spd':data['RIDERS'][2][1], 'vrc':data['RIDERS'][2][3], 'fxc':data['RIDERS'][2][4], 'svt':data['RIDERS'][2][5]}
wbc = [walk,bike,car]
bn = data['RIDERS'][0][6]
wn = data['RIDERS'][1][6]
cn = data['RIDERS'][2][6]
n = wn + bn + cn

def tsp(px,rider_id):
    pickup = []
    pickdown = []
    for j in range(k):
        if px[rider_id,j]:
            pickup.append(j)
            pickdown.append(j)
    
    return (pickup,pickdown)
    

try:
    m = gp.Model("mip1")
    x = m.addVars(n, k, vtype=GRB.BINARY, name="x")

    for j in range(k): #every ORDERS should assign to only one rider
        constr = gp.LinExpr()
        for i in range(n):
            constr += x[i,j]
        m.addConstr(constr==1)

    for i in range(n): # sum of ORDERS volume is less than rider capacity
        if i < wn: #walk rider
            mode = 0
        elif i < wn+bn: #bike rider
            mode = 1
        else: #car rider
            mode = 2
        constr = gp.LinExpr()
        for j in range(k):
            constr += data['ORDERS'][j][7]*x[i,j]
        m.addConstr(constr <= wbc[mode]['cap'])
    
    total_cost = gp.LinExpr()
    for i in range(n):
        if i < wn: #walk rider
            r = 0
        elif i < wn+bn: #bike rider
            r = 1
        else: #car rider
            r = 2
        distance = gp.LinExpr()
        pickup_time = gp.LinExpr()
        up, down = tsp(x, i)
        if not up: # case that this rider don't get any ORDERS
            continue
        pickup_time += data['ORDERS'][up[0]][1] #prepare time of first pickup (ORDERS start + ready)
        pickup_time += data['ORDERS'][up[0]][6] 
        for loc in range(len(up)-1):
            pickup_time += data['DIST'][up[loc]][up[loc+1]]//wbc[mode]['spd'] + wbc[mode]['svt'] #time spent for pick ups
            distance += data['DIST'][up[loc]][up[loc+1]]
        pickup_time += data['DIST'][up[len(up)-1]][down[0]]//wbc[mode]['spd'] + wbc[mode]['svt'] 
        distance += data['DIST'][up[len(up)-1]][down[0]]
        m.addConstr(pickup_time <= data['ORDERS'][down[0]][8]) #time should be earlier than dead line of first ORDERS
        for loc in range(1,len(down)):
            pickup_time += data['DIST'][down[loc-1]][down[loc]]//wbc[mode]['spd'] + wbc[mode]['svt']
            distance += data['DIST'][down[loc-1]][down[loc]]
            m.addConstr(pickup_time <= data['ORDERS'][down[loc]][8])
        total_cost += distance * wbc[mode]['vrc']
        total_cost += wbc[mode]['fxc']

    m.setObjective(total_cost,GRB.MINIMIZE)

    m.optimize()

    for i in range(n):
        print(x[i])

    
except gp.GurobiError as e:
    print('Error code ' + str(e.errno) + ': ' + str(e))

except AttributeError:
    print('Encountered an attribute error')

