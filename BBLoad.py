import sys, os, zlib, traceback, struct, math, base64, json
from RCRPDataTypes import *

def main():
	targetPath = sys.argv[1]

	if os.path.isdir(targetPath):
		level = int(sys.argv[2])
		flags = sys.argv[3:]
		levelFilePath = f"{targetPath}\\{level // 10}\\{level % 10}.BBK"
		decompressed_levelFolderPath = f"{targetPath}\\..\\Decompressed\\{level // 10}\\{level % 10}\\"
	else:
		flags = sys.argv[2:]
		level = 98 if "FRONT_END" in flags else -1
		levelFilePath = targetPath
		decompressed_levelFolderPath = f"{os.path.split(targetPath)[0]}\\Decompressed\\"

	if not os.path.exists(decompressed_levelFolderPath):
		os.makedirs(decompressed_levelFolderPath)

	with open(levelFilePath, "rb") as file:
		bbHeader = sBBHeader(file)

		if not flags or "NO_SRAM" not in flags and ("SFX_AMBIENT" in flags or "SFX_GENERIC" in flags):
			compressedSize = struct.unpack("<I", file.read(4))[0]
			compressedData = file.read(compressedSize)
			sRAM = zlib.decompress(compressedData)
			with open(decompressed_levelFolderPath + "sRAM.BBK", "wb") as dfile:
				dfile.write(sRAM)

		if not flags or "NO_VRAM" not in flags:
			compressedSize = struct.unpack("<I", file.read(4))[0]
			compressedData = file.read(compressedSize)
			vRAM = zlib.decompress(compressedData)
			with open(decompressed_levelFolderPath + "vRAM.BBK", "wb") as dfile:
				dfile.write(vRAM)

		if not flags or "NO_DRAM" not in flags:
			compressedSize = struct.unpack("<I", file.read(4))[0]
			compressedData = file.read(compressedSize)
			dRAM = zlib.decompress(compressedData)
			with open(decompressed_levelFolderPath + "dRAM.BBK", "wb") as dfile:
				dfile.write(dRAM)

	with open(decompressed_levelFolderPath + "dRAM.BBK", "rb") as file:
		if level == 98:
			FELevelData = sFELevelData(file)
			file.seek(FELevelData.pLvl - bbHeader.dRAMHeader.pCurr, os.SEEK_SET)
		else:
			file.seek(- 0x70, os.SEEK_END)

		Lvl = sLevelData(file)

		if Lvl.pGeneralText != 0:
			generalText = []
			# pointer jump
			rpGeneralText = Lvl.pGeneralText - bbHeader.dRAMHeader.pCurr + 4
			try: # Get all available strings before failing on null or non utf-8 character
				while True:
					file.seek(rpGeneralText, os.SEEK_SET)

					# pointer jump
					pTextTranslations = struct.unpack("<I", file.read(4))[0]
					if pTextTranslations == 0:
						break
					else:
						rpTextTranslations = pTextTranslations - bbHeader.dRAMHeader.pCurr
						file.seek(rpTextTranslations, os.SEEK_SET)
						generalText.append(TextGroup(file))

					rpGeneralText += 4
			except Exception:
				traceback.print_exc()

			with open(decompressed_levelFolderPath + f"generalText.json", "w") as text_file:
				text_file.write(json.dumps([textTranslations.json() for textTranslations in generalText], ensure_ascii=True, indent="\t"))

		if Lvl.pAColGrid != 0:
			rpAColGrid = Lvl.pAColGrid - bbHeader.dRAMHeader.pCurr
			file.seek(rpAColGrid, os.SEEK_SET)
			ColGrid = sColGridPXS(file)

			collisionPolys: list[ColPoly] = []

			rpPoly = ColGrid.pPoly - bbHeader.dRAMHeader.pCurr
			file.seek(rpPoly, os.SEEK_SET)
			for p in range(ColGrid.numPolys):
				collisionPolys.append(ColPoly(file))

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

			#surfaces = dict(sorted(surfaces.items()))

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
						"children": [
							1
						],
						"matrix": [
							-0.001, 0.0, 0.0, 0.0,
							0.0, 0.0, 0.001, 0.0,
							0.0, 0.001, 0.0, 0.0,
							0.0, 0.0, 0.0, 1.0
						],
						"name": "Lvl"
					},
					{
						"mesh": 0
					}
				],
				"meshes": [
					{
						"primitives": [],
						"name": "Col"
					}
				],
				"accessors": [],
				"materials": [
					{
						"name": material.name
					} for material in surfaces.keys()
				],
				"bufferViews": [],
				"buffers": []
			}

			gltf["meshes"][0]["primitives"].extend([{
				"attributes": {
					"POSITION": s * 3 + 1,
					"NORMAL": s * 3 + 2
				},
				"indices": s * 3,
				"mode": 4,
				"material": s
			} for s in range(len(surfaces))])

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
				
			with open(decompressed_levelFolderPath + f"model.gltf", "w") as model_file:
				model_file.write(json.dumps(gltf, ensure_ascii=True, indent="\t"), )
			
if __name__ == "__main__":
	main()