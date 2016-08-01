def StronglyConnectedComponents(graph):
    ## For each node in the graph the following two information must be set namely index and lowlinks according to tarjan algorithm
    ## eg: If there is node 'A' then Node A should contain A(index,lowlink)
    index_counter =[0]
    stack = []
    lowlinks = {}
    index = {}
    result = []
    def strongconnect(node):
        ## set the index and lowlink of starting Node to be 0
        ## eg: if A is the starting node in the graph then set A(0,0) and increment the index and lowlink for each successor of a node

        index[node] = index_counter[0]
        lowlinks[node] = index_counter[0]
        index_counter[0] += 1
        stack.append(node)

        # Get successors of 'node'
        try:
            successors = graph[node]
        except:
            successors = []

        for successor in successors:
            if successor not in lowlinks:
                # Successor has not yet been visited;
                strongconnect(successor)
                lowlinks[node] = min(lowlinks[node],lowlinks[successor])
            elif successor in stack:
                # the successor is in the stack and hence in the current strongly connected component (SCC)
                lowlinks[node] = min(lowlinks[node],index[successor])

        # If `node` is a root node, pop the stack and generate an SCC
        if lowlinks[node] == index[node]:
            connected_component = []
            while True:
                successor = stack.pop()
                connected_component.append(successor)
                if successor == node:
                    break
            component = tuple(connected_component)
            # storing the result
            result.append(component)

    for node in graph:
        if node not in lowlinks:
            strongconnect(node)

    ## End of the Algorithm, get the Strongly connected component list and pass it to Topological Sort function to get the order of execution
    orderedlist=GetNodeComponentOrder(result,graph)
    return orderedlist

def GetNodeComponentOrder(result,graph):
    ## This Function is used to get Strongly connected Components list from Tarjan algorithm and create a New Graph components information
    ## to find the order of execution of a Directed Graph using Topological Sort Algorithm

    components = result

    node_component = {}
    for component in components:
        for node in component:
            node_component[node] = component

    component_graph = {}
    for component in components:
        component_graph[component] = []

    for node in graph:
        node_c = node_component[node]
        for successor in graph[node]:
            successor_c = node_component[successor]
            if node_c != successor_c:
                component_graph[node_c].append(successor_c)

    return topological_sort(component_graph)

def topological_sort(graph):
    ### Find the order of execution from the Connected Graph components ###

    ## As a first step, Assign each node in Graph with number of incoming edges set to 0
    count = { }
    for node in graph:
        count[node] = 0

    ## For each node in the graph determine the number of incoming edges and set the count,
    ## In this phase we determine the root node, A node with no incoming edge will be the start node
    for node in graph:
        for successor in graph[node]:
            count[successor] += 1

    startnode = [ node for node in graph if count[node] == 0 ]

    ## After finding the start node, append it to list until all the successor of graph is completed which gives the order of execution
    result = [ ]
    while startnode:
        node = startnode.pop(-1)
        result.append(node)

        for successor in graph[node]:
            count[successor] -= 1
            if count[successor] == 0:
                startnode.append(successor)

    return result
    
 
if __name__ == '__main__':
    #graph={'Modelica_Blocks_Continuous_TransferFunction1.y': ['Modelica_Blocks_Math_Feedback1.u2'], 'Modelica_Blocks_Continuous_PI1.y': ['Modelica_Blocks_Continuous_TransferFunction1.u'], 'Modelica_Blocks_Continuous_PI1.u': ['Modelica_Blocks_Continuous_PI1.y'], 'Modelica_Blocks_Continuous_TransferFunction1.u': ['Modelica_Blocks_Continuous_TransferFunction1.y'], 'Modelica_Blocks_Sources_Step1.y': ['Modelica_Blocks_Math_Feedback1.u1'], 'Modelica_Blocks_Math_Feedback1.y': ['Modelica_Blocks_Continuous_PI1.u'], 'Modelica_Blocks_Continuous_PI1._StatesForOutputs.x': ['Modelica_Blocks_Continuous_PI1.y', 'Modelica_Blocks_Continuous_PI1.x'], 'Modelica_Blocks_Math_Feedback1.u2': ['Modelica_Blocks_Math_Feedback1.y'], 'Modelica_Blocks_Math_Feedback1.u1': ['Modelica_Blocks_Math_Feedback1.y']}
    graph={'step_y':['feed_u1'],
            'feed_u1':['feed_y'],
            'feed_y':['PI_u'],
            'PI_u':['PI_y'],
            'PI_y':['transform_u'],
            'transform_u':['transform_y'],
            'transform_y':['feed_u2'],
            'feed_u2':['feed_y']}
    print StronglyConnectedComponents(graph) 
    