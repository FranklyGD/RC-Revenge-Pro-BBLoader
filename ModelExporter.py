import base64, json
from RCRPDataTypes import *

def export(output_path: str, collisionPolys: list[ColPoly], aiNodes: list[sAINode], pickupPoss: list[sPickupPos], vuShape):
	gltf = {
		"asset": {
			"generator": "BBLoader",
			"version": "2.0"
		},
		"scene": 0,
		"scenes": [
			{
				"nodes": [
					0
				]
			}
		],
		"nodes": [
			{
				"children": [],
				"matrix": [
					-0.001, 0.0, 0.0, 0.0,
					0.0, 0.0, 0.001, 0.0,
					0.0, 0.001, 0.0, 0.0,
					0.0, 0.0, 0.0, 1.0
				],
				"name": "Lvl"
			}
		],
		"meshes": [],
		"accessors": [],
		"materials": [],
		"bufferViews": [],
		"buffers": []
	}

	rootNode = gltf["nodes"][0]

	if collisionPolys:
		surfaces = {}

		for collisionPoly in collisionPolys:
			if collisionPoly.material not in surfaces:
				indices = []
				vertices = []
				normals = []

				mesh = {
					"indices": indices,
					"vertices": vertices,
					"normals": normals
				}
				surfaces[collisionPoly.material] = mesh
			else:
				mesh = surfaces[collisionPoly.material]

				indices = mesh["indices"]
				vertices = mesh["vertices"]
				normals = mesh["normals"]

			polyVertexCount = collisionPoly.vertexCount
			polyVertices = collisionPoly.vertices[:polyVertexCount]
			polyNormal = collisionPoly.normal
			polyNormal = Vector([polyNormal.x, polyNormal.z, polyNormal.y])

			oi = len(vertices)
			if Vector.dot(Vector.cross(polyVertices[1] - polyVertices[0], polyVertices[2] - polyVertices[0]), polyNormal) < 0:
				for i in range(polyVertexCount - 2):
					indices.extend([oi, oi + 2 + i, oi + 1 + i])
			else:
				for i in range(polyVertexCount - 2):
					indices.extend([oi, oi + 1 + i, oi + 2 + i])

			vertices.extend(polyVertices)
			normals.extend([polyNormal] * polyVertexCount)

		rootNode["children"].append(len(gltf["nodes"]))

		gltf["nodes"].append({
			"mesh": len(gltf["meshes"])
		})

		gltf["meshes"].append({
			"primitives": [{
				"attributes": {
					"POSITION": s * 3 + 1,
					"NORMAL": s * 3 + 2
				},
				"indices": s * 3,
				"mode": 4,
				"material": s
			} for s in range(len(surfaces))],
			"name": "Col"
		})

		surface_index = 0
		for (material, mesh) in surfaces.items():
			indices = mesh["indices"]
			vertices = mesh["vertices"]
			normals = mesh["normals"]

			indexCount = len(indices)
			vertexCount = len(vertices)

			Xs = [vertex.x for vertex in vertices]
			Ys = [vertex.y for vertex in vertices]
			Zs = [vertex.z for vertex in vertices]

			boundsMax = [max(Xs), max(Ys), max(Zs)]
			boundsMin = [min(Xs), min(Ys), min(Zs)]

			buffer = []
			for i in indices:
				buffer.extend(struct.pack("<i", i))

			for v in range(vertexCount):
				buffer.extend(struct.pack("<3f", vertices[v].x, vertices[v].y, vertices[v].z))

			for v in range(vertexCount):
				normal = normals[v]
				length = normal.length()
				buffer.extend(struct.pack("<3f", normal.x / length, normal.y / length, normal.z / length))

			gltf["materials"].append({
				"name": material.name if type(material) is MaterialType else f"MTL_{material}"
			})

			gltf["accessors"].extend([
				{
					"bufferView": surface_index * 2,
					"byteOffset": 0,
					"componentType": 5125,
					"count": indexCount,
					"max": [
						max(indices)
					],
					"min": [
						0
					],
					"type": "SCALAR"
				},
				{
					"bufferView": surface_index * 2 + 1,
					"byteOffset": 0,
					"componentType": 5126,
					"count": vertexCount,
					"max": boundsMax,
					"min": boundsMin,
					"type": "VEC3"
				},
				{
					"bufferView": surface_index * 2 + 1,
					"byteOffset": vertexCount * (4 * 3),
					"componentType": 5126,
					"count": vertexCount,
					"max": [
						1.0,
						1.0,
						1.0
					],
					"min": [
						-1.0,
						-1.0,
						-1.0
					],
					"type": "VEC3"
				}
			])

			gltf["bufferViews"].extend([
				{
					"buffer": surface_index,
					"byteOffset": 0,
					"byteLength": indexCount * 4,
					"target": 34963
				},
				{
					"buffer": surface_index,
					"byteOffset": indexCount * 4,
					"byteLength": vertexCount * (4 * 3) * 2,
					"byteStride": (4 * 3),
					"target": 34962
				}
			])

			gltf["buffers"].append({
				"byteLength": len(buffer),
				"uri": "data:application/octet-stream;base64," + base64.b64encode(bytes(buffer)).decode(),
			})

			surface_index += 1

	if aiNodes:
		indices = []
		vertices = []

		i = 0
		for aiNode in aiNodes:
			for nodeIndex in aiNode.next:
				if nodeIndex > -1:
					indices.extend([
						i * 4 + 0, nodeIndex * 4 + 0,
						i * 4 + 1, nodeIndex * 4 + 1,
						i * 4 + 2, nodeIndex * 4 + 2,
						i * 4 + 3, nodeIndex * 4 + 3
					])
			i += 1

			vertices.extend([
				aiNode.node[0],
				aiNode.node[1],
				aiNode.centre,
				aiNode.overCentre
			])

		indexCount = len(indices)
		vertexCount = len(vertices)

		Xs = [vertex[0] for vertex in vertices]
		Ys = [vertex[1] for vertex in vertices]
		Zs = [vertex[2] for vertex in vertices]

		boundsMax = [max(Xs), max(Ys), max(Zs)]
		boundsMin = [min(Xs), min(Ys), min(Zs)]

		rootNode["children"].append(len(gltf["nodes"]))

		gltf["nodes"].append({
			"mesh": len(gltf["meshes"])
		})

		accessorsCount = len(gltf["accessors"])
		gltf["meshes"].append({
			"primitives": [{
				"attributes": {
					"POSITION": accessorsCount + 1,
				},
				"indices": accessorsCount,
				"mode": 1,
			}],
			"name": "AI"
		})

		buffer = []
		for i in indices:
			buffer.extend(struct.pack("<i", i))

		for v in range(vertexCount):
			buffer.extend(struct.pack("<3f", vertices[v][0], vertices[v][2], vertices[v][1]))

		bufferViewCount = len(gltf["bufferViews"])
		gltf["accessors"].extend([
			{
				"bufferView": bufferViewCount,
				"byteOffset": 0,
				"componentType": 5125,
				"count": indexCount,
				"max": [
					max(indices)
				],
				"min": [
					0
				],
				"type": "SCALAR"
			},
			{
				"bufferView": bufferViewCount + 1,
				"byteOffset": 0,
				"componentType": 5126,
				"count": vertexCount,
				"max": boundsMax,
				"min": boundsMin,
				"type": "VEC3"
			}
		])

		bufferCount = len(gltf["buffers"])
		gltf["bufferViews"].extend([
			{
				"buffer": bufferCount,
				"byteOffset": 0,
				"byteLength": indexCount * 4,
				"target": 34963
			},
			{
				"buffer": bufferCount,
				"byteOffset": indexCount * 4,
				"byteLength": vertexCount * (4 * 3),
				"byteStride": (4 * 3),
				"target": 34962
			}
		])

		gltf["buffers"].append({
			"byteLength": len(buffer),
			"uri": "data:application/octet-stream;base64," + base64.b64encode(bytes(buffer)).decode(),
		})
	
	if pickupPoss:
		for pickupPos in pickupPoss:
			rootNode["children"].append(len(gltf["nodes"]))

			gltf["nodes"].append({
				"translation": [pickupPos.x, pickupPos.z, pickupPos.y],
				"name" : "Pickup"
			})

	if vuShape:
		surfaces = {}

		for triangle in vuShape:
			if triangle["texture"] not in surfaces:
				indices = []
				vertices = []
				normals = []
				uvs = []
				colors = []

				mesh = {
					"indices": indices,
					"vertices": vertices,
					"normals": normals,
					"uvs": uvs,
					"colors": colors
				}
				surfaces[triangle["texture"]] = mesh
			else:
				mesh = surfaces[triangle["texture"]]

				indices = mesh["indices"]
				vertices = mesh["vertices"]
				normals = mesh["normals"]
				uvs = mesh["uvs"]
				colors = mesh["colors"]

			oi = len(vertices)
			indices.extend([oi, oi + 2, oi + 1])

			vertices.extend(triangle["vertices"])
			normals.extend([triangle["normal"]] * 3)
			uvs.extend(triangle["uvs"])
			colors.extend(triangle["colors"])

		rootNode["children"].append(len(gltf["nodes"]))

		gltf["nodes"].append({
			"mesh": len(gltf["meshes"])
		})

		accessorsCount = len(gltf["accessors"])
		materialCount = len(gltf["materials"])
		gltf["meshes"].append({
			"primitives": [{
				"attributes": {
					"POSITION": accessorsCount + s * 5 + 1,
					"NORMAL": accessorsCount + s * 5 + 2,
					"COLOR_0": accessorsCount + s * 5 + 3,
                	"TEXCOORD_0": accessorsCount + s * 5 + 4,
				},
				"indices": accessorsCount + s * 5,
				"mode": 4,
				"material": materialCount + s
			} for s in range(len(surfaces))],
			"name": "Shape"
		})

		surface_index = 0
		for (material, mesh) in surfaces.items():
			indices = mesh["indices"]
			vertices = mesh["vertices"]
			normals = mesh["normals"]

			indexCount = len(indices)
			vertexCount = len(vertices)

			Xs = [vertex.x for vertex in vertices]
			Ys = [vertex.y for vertex in vertices]
			Zs = [vertex.z for vertex in vertices]

			boundsMax = [max(Xs), max(Ys), max(Zs)]
			boundsMin = [min(Xs), min(Ys), min(Zs)]

			buffer = []
			for i in indices:
				buffer.extend(struct.pack("<i", i))

			for v in range(vertexCount):
				buffer.extend(struct.pack("<3f", vertices[v].x, vertices[v].z, vertices[v].y))

			for v in range(vertexCount):
				normal = normals[v]
				length = normal.length()
				if length == 0:
					length = 1
				buffer.extend(struct.pack("<3f", normal.x / length, normal.z / length, normal.y / length))
			
			for v in range(vertexCount):
				uv = uvs[v]
				buffer.extend(struct.pack("<3f", uv.x, uv.y, uv.z))
				
			for v in range(vertexCount):
				color = colors[v]
				buffer.extend(struct.pack("<4f", color[0] / 255, color[1] / 255, color[2] / 255, color[3] / 255))

			gltf["materials"].append({
				"name": f"MAT_{material}"
			})

			bufferViewCount = len(gltf["bufferViews"])
			gltf["accessors"].extend([
				{
					"bufferView": bufferViewCount + surface_index * 3,
					"byteOffset": 0,
					"componentType": 5125,
					"count": indexCount,
					"max": [
						max(indices)
					],
					"min": [
						0
					],
					"type": "SCALAR"
				},
				{
					"bufferView": bufferViewCount + surface_index * 3 + 1,
					"byteOffset": 0,
					"componentType": 5126,
					"count": vertexCount,
					"max": boundsMax,
					"min": boundsMin,
					"type": "VEC3"
				},
				{
					"bufferView": bufferViewCount + surface_index * 3 + 1,
					"byteOffset": vertexCount * (4 * 3),
					"componentType": 5126,
					"count": vertexCount,
					"max": [
						1.0,
						1.0,
						1.0
					],
					"min": [
						-1.0,
						-1.0,
						-1.0
					],
					"type": "VEC3"
				},
				{
					"bufferView": bufferViewCount + surface_index * 3 + 2,
					"byteOffset": 0,
					"componentType": 5126,
					"count": vertexCount,
					"max": [
						1.0,
						1.0,
						1.0,
						1.0
					],
					"min": [
						0.0,
						0.0,
						0.0,
						0.0
					],
					"type": "VEC4"
				},
				{
					"bufferView": bufferViewCount + surface_index * 3 + 1,
					"byteOffset": 2 * vertexCount * (4 * 3),
					"componentType": 5126,
					"count": vertexCount,
					"max": [
						1.0,
						1.0
					],
					"min": [
						0.0,
						0.0
					],
					"type": "VEC2"
				}
			])

			bufferCount = len(gltf["buffers"])
			gltf["bufferViews"].extend([
				{
					"buffer": bufferCount + surface_index,
					"byteOffset": 0,
					"byteLength": indexCount * 4,
					"target": 34963
				},
				{
					"buffer": bufferCount + surface_index,
					"byteOffset": indexCount * 4,
					"byteLength": vertexCount * (4 * 3) * 3,
					"byteStride": (4 * 3),
					"target": 34962
				},
				{
					"buffer": bufferCount + surface_index,
					"byteOffset": indexCount * 4 + vertexCount * (4 * 3) * 3,
					"byteLength": vertexCount * (4 * 4),
					"byteStride": (4 * 4),
					"target": 34962
				}
			])

			gltf["buffers"].append({
				"byteLength": len(buffer),
				"uri": "data:application/octet-stream;base64," + base64.b64encode(bytes(buffer)).decode(),
			})

			surface_index += 1

	with open(output_path + f"model.gltf", "w") as model_file:
		model_file.write(json.dumps(gltf, ensure_ascii=True, indent="\t"))