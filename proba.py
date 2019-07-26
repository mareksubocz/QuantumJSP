import dwavebinarycsp


def defineX(machines):
    X = machines[1]
    for machine in machines:  # ? bitwise OR
        X = machine or X
    return X


def oneOperationOneStartpoint(X):  # Constraints (3)
    Eall = 0
    for job in X:
        for operation in job:
            Esingle = 0  # checking if this operation starts once
            for startpoint in operation:
                Esingle += startpoint
            Eall += (Esingle - 1) ** 2
    return Eall


def oneMachineOneOperation(machines, P):  # Constraints (4)
    Eall = 0
    for machine in machines:
        for i in range(len(machine)):  # all jobs
            for j in range(len(machine[i])):  # all operations
                for i2 in range(i, len(machine)):
                    for j2 in range(len(machine[i])):
                        for t in range(len(machine[i][j])):
                            for t2 in range(t, t + P[i][j]):
                                Eall += machine[i][j][t] * machine[i2][j2][t2]
    return Eall


def operationOrder(X, P):  # Constraints (5)
    Eall = 0
    for j in range(len(X)):
        for i in range(len(X[j]) - 1):
            for i2 in range(i + 1, len(X[j])):
                for t in range(len(X[j][i])):
                    for t2 in range(t, t + P[j][i]):
                        Eall += X[j][i][t] * X[j][i2][t2]
    return Eall


# machines{jobs{operations{startpoint}}} - machines
# jobs{operations{length}} - P
# jobs{operations{startpoint}} - X

machines = [[[]]]  # wypełnia komputer
P = [[2, 1, 1], [2, 1, 2], [1, 1, 2]]


def scheduling(machines, P):
    X = defineX(machines)
    h1 = operationOrder(X, P)
    h2 = oneMachineOneOperation(machines, P)
    h3 = oneOperationOneStartpoint(X)
    return h1 + h2 + h3


csp = dwavebinarycsp.ConstraintSatisfactionProblem(dwavebinarycsp.BINARY)
csp.add_constraint(scheduling, ["machines"])

bqm = dwavebinarycsp.stitch(csp)
bqm.linear
bqm.quadratic
