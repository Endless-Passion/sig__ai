import sys
input = sys.stdin.readline

t = int(input())
for _ in range(t):
    n = int(input())
    graph = [0] * (n+1) # 자기 부모를 저장해야하는 그래프
    for _ in range(n-1):
        a, b = map(int, input().split())
        graph[b] = a

    a, b = map(int, input().split())
    a_papa = [a]
    b_papa = [b]
    while graph[a] != 0:
        a_papa.append(graph[a])
        a = graph[a]
    
    while graph[b] != 0:
        b_papa.append(graph[b])
        b = graph[b]
    
    flag = True
    for i in range(len(a_papa)):
        for j in range(len(b_papa)):
            if a_papa[i] == b_papa[j]:
                print(a_papa[i])
                flag = False
                break
        
        if flag == False:
            break
    
