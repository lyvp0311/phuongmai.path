import osmnx as ox
from shapely.geometry import LineString
from math import radians, sin, cos, acos
from random import randint

# Đọc danh sách ID
random_id = [int(x) for x in open('random_id.txt').readlines()]
G = ox.graph_from_place("Phương Mai, Đống Đa, Hà Nội, Vietnam", network_type='walk')

max_length = 6  # mét
MAX_EDGE_LENGTH = 500  # Giới hạn cạnh thêm thủ công tối đa 500m

nodes = dict()
cnt = 0

# Lưu node để dễ tra
for node in G.nodes(data=True):
    nodes[node[0]] = node[1]

def get_coordinates(node_id):
    node = G.nodes[node_id]
    return node['y'], node['x']

def calculate_distance(pa, pb):
    lat1, lon1 = radians(pa[0]), radians(pa[1])
    lat2, lon2 = radians(pb[0]), radians(pb[1])
    return acos(sin(lat1)*sin(lat2) + cos(lat1)*cos(lat2)*cos(lon2 - lon1)) * 6371000

def add_edge(node1, node2):
    global G
    pa, pb = get_coordinates(node1), get_coordinates(node2)
    dist = calculate_distance(pa, pb)
    if dist > MAX_EDGE_LENGTH:
        print(f"⚠️ Bỏ qua cạnh dài bất thường: {dist:.1f}m giữa {node1} và {node2}")
        return
    G.add_edge(node1, node2, length=dist, oneway=False)
    G.add_edge(node2, node1, length=dist, oneway=False)

# ⚠️ Bỏ dòng này nếu nghi ngờ node sai vùng
# add_edge(10130399575, 104782499)
# add_edge(10130399571, 104782499)
# add_edge(10130399573, 104782499)

def process_edge_linestring(edge):
    global G, cnt
    pa = get_coordinates(edge[0])
    pb = get_coordinates(edge[1])
    data = edge[2]
    one_way = data.get('oneway', False)

    if 'geometry' in data:
        G.remove_edge(edge[0], edge[1])
        l = list(data['geometry'].coords)
        idx = [edge[0]]
        for i in range(1, len(l)-1):
            G.add_node(random_id[cnt], y=l[i][1], x=l[i][0])
            nodes[random_id[cnt]] = {'y': l[i][1], 'x': l[i][0]}
            G.add_edge(random_id[cnt], idx[-1], length=calculate_distance(l[i], l[i-1]), oneway=one_way)
            if not one_way:
                G.add_edge(idx[-1], random_id[cnt], length=calculate_distance(l[i], l[i-1]), oneway=False)
            idx.append(random_id[cnt])
            cnt += 1
        G.add_edge(edge[1], idx[-1], length=calculate_distance(l[-1], l[-2]), oneway=one_way)
        if not one_way:
            G.add_edge(idx[-1], edge[1], length=calculate_distance(l[-1], l[-2]), oneway=False)

def process_long_edge(edge):
    global G, cnt
    pa = get_coordinates(edge[0])
    pb = get_coordinates(edge[1])
    data = edge[2]
    one_way = data.get('oneway', False)
    length = calculate_distance(pa, pb)
    if length <= 2 * max_length:
        return
    try:
        G.remove_edge(edge[0], edge[1])
        G.remove_edge(edge[1], edge[0])
    except:
        pass

    increment = max_length / length
    dy = (pb[0] - pa[0]) * increment
    dx = (pb[1] - pa[1]) * increment
    newnodes_id = [edge[0]]
    newnodes_coor = [pa]

    for i in range(1, int(length / max_length)):
        coor = (pa[0] + dy * i, pa[1] + dx * i)
        G.add_node(random_id[cnt], y=coor[0], x=coor[1])
        nodes[random_id[cnt]] = {'y': coor[0], 'x': coor[1]}
        G.add_edge(random_id[cnt], newnodes_id[-1], length=calculate_distance(newnodes_coor[-1], coor), oneway=one_way)
        if not one_way:
            G.add_edge(newnodes_id[-1], random_id[cnt], length=calculate_distance(newnodes_coor[-1], coor), oneway=False)
        newnodes_coor.append(coor)
        newnodes_id.append(random_id[cnt])
        cnt += 1

    G.add_edge(edge[1], newnodes_id[-1], length=calculate_distance(newnodes_coor[-1], pb), oneway=one_way)
    if not one_way:
        G.add_edge(newnodes_id[-1], edge[1], length=calculate_distance(newnodes_coor[-1], pb), oneway=False)

# Xử lý toàn bộ edge
from copy import deepcopy
for edge in deepcopy(G.edges(data=True)):
    process_edge_linestring(edge)
for edge in deepcopy(G.edges(data=True)):
    process_long_edge(edge)

ox.save_graphml(G, "phuongmai.graphml")
print("✅ Đã tạo lại phuongmai.graphml an toàn.")
