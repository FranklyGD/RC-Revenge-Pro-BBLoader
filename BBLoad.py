import sys, os, zlib, traceback, struct, math, base64, json
from RCRPDataTypes import *
from ModelExporter import export

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

	with open(levelFilePath, "rb") as file:
		if not os.path.exists(decompressed_levelFolderPath):
			os.makedirs(decompressed_levelFolderPath)

		bbHeader = sBBHeader(file)

		if not flags or "NO_SRAM" not in flags and ("SFX_AMBIENT" in flags or "SFX_GENERIC" in flags):
			compressedSize = struct.unpack("<I", file.read(4))[0]
			compressedData = file.read(compressedSize)
			sRAM = zlib.decompress(compressedData)
			with open(decompressed_levelFolderPath + "sRAM.BBK", "wb") as dfile:
				dfile.write(sRAM)
			
			print("SRAM extracted and decompressed...")

		if not flags or "NO_VRAM" not in flags:
			compressedSize = struct.unpack("<I", file.read(4))[0]
			compressedData = file.read(compressedSize)
			vRAM = zlib.decompress(compressedData)
			with open(decompressed_levelFolderPath + "vRAM.BBK", "wb") as dfile:
				dfile.write(vRAM)
			
			print("VRAM extracted and decompressed...")

		if not flags or "NO_DRAM" not in flags:
			compressedSize = struct.unpack("<I", file.read(4))[0]
			compressedData = file.read(compressedSize)
			dRAM = zlib.decompress(compressedData)
			with open(decompressed_levelFolderPath + "dRAM.BBK", "wb") as dfile:
				dfile.write(dRAM)
			
			print("DRAM extracted and decompressed...")

	with open(decompressed_levelFolderPath + "dRAM.BBK", "rb") as file:
		if level == 98:
			print("Reading Front End...")
			FELevelData = sFELevelData(file)
			file.seek(FELevelData.pLvl - bbHeader.dRAMHeader.pCurr, os.SEEK_SET)
		else:
			print(f"Reading level {level}...")
			file.seek(- 0x70, os.SEEK_END)

		Lvl = sLevelData(file)

		if Lvl.pGeneralText != 0:
			print(f"Reading text...")
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
				print(f"Saving text...")
				text_file.write(json.dumps([textTranslations.json() for textTranslations in generalText], ensure_ascii=True, indent="\t"))

		# Collision

		collisionPolys: list[ColPoly] = []
		if Lvl.pAColGrid != 0:
			print(f"Reading collision mesh...")
			rpAColGrid = Lvl.pAColGrid - bbHeader.dRAMHeader.pCurr
			file.seek(rpAColGrid, os.SEEK_SET)
			ColGrid = sColGridPXS(file)


			rpPoly = ColGrid.pPoly - bbHeader.dRAMHeader.pCurr
			file.seek(rpPoly, os.SEEK_SET)
			for p in range(ColGrid.numPolys):
				collisionPolys.append(ColPoly(file))

		# AI

		aiNodes = []
		if Lvl.pAINode != 0:
			print(f"Reading AI...")
			rpAINodeClass = Lvl.pAINode - bbHeader.dRAMHeader.pCurr
			file.seek(rpAINodeClass, os.SEEK_SET)

			# Apparently most of the data within the class seems not used properly in the BBK file
			# The whole structure is used more in live RAM than stored. Only 3 pieces of data is stored here:
			# Node Count, Node Links, Array of Nodes

			# AINodeClass = sAINodeClass(file) # <- That ain't it chief

			# This is how we actually read...

			noNodesSingle = struct.unpack("<H", file.read(2))[0]
			noNodesLink = struct.unpack("<H", file.read(2))[0] # Currently unused

			rpfirstNode = file.tell()
			aiNodes = [sAINode(file) for i in range(noNodesSingle)]

			# Convert AINode pointers to indices
			for aiNode in aiNodes:
				next = aiNode.next
				prev = aiNode.prev
				aiNode.next = [-1,-1]
				aiNode.prev = [-1,-1]
				for i in range(2):
					pNextNode = next[i]
					if pNextNode != 0:
						aiNode.next[i] = (pNextNode - rpfirstNode - bbHeader.dRAMHeader.pCurr) // 0x6c

					pPrevNode = prev[i]
					if pPrevNode != 0:
						aiNode.prev[i] = (pPrevNode - rpfirstNode - bbHeader.dRAMHeader.pCurr) // 0x6c

			with open(decompressed_levelFolderPath + f"ai.json", "w") as text_file:
				print(f"Saving AI...")
				text_file.write(json.dumps([aiNode.json() for aiNode in aiNodes], ensure_ascii=True, indent="\t"))

		pickupPoss = []
		if Lvl.pPickUpPosData != 0:
			print(f"Reading pickup positions...")
			rpPickUpPosData = Lvl.pPickUpPosData - bbHeader.dRAMHeader.pCurr
			file.seek(rpPickUpPosData, os.SEEK_SET)

			PickupRes = sPickupRes(file)

			pickupPoss = [sPickupPos(file) for i in range(PickupRes.numPickups)]

			with open(decompressed_levelFolderPath + f"pickups.json", "w") as text_file:
				print(f"Saving pickup positions...")
				text_file.write(json.dumps([vars(pickupPos) for pickupPos in pickupPoss], ensure_ascii=True, indent="\t"))
	
		triangles = []
		if Lvl.pALFData != 0:
			print(f"Reading visual mesh...")
			rpALFData = Lvl.pALFData - bbHeader.dRAMHeader.pCurr
			file.seek(rpALFData, os.SEEK_SET)

			RdrVUShape = sRdrVUShape(file)
			
			rpTri = RdrVUShape.pTri - bbHeader.dRAMHeader.pCurr
			rpDma = rpTri
			
			for i in range(800):
				file.seek(rpDma, os.SEEK_SET)
				DmaTag = sDmaTag(file)

				# SOURCE MODE
				id = DmaTagID((DmaTag.id >> 4) & 0b111)

				match id:
					case DmaTagID.CNT:
						rpDma += (1 + DmaTag.qwc) * 0x10
					case DmaTagID.NEXT:
						rpDma = DmaTag.next - bbHeader.dRAMHeader.pCurr
					case DmaTagID.RET:
						break # Currently reaches here, seems all opaque/solid triangles are read by this points
					case DmaTagID.END:
						break # Have not reached here yet
				
				vifCodeUnpack = DmaTag.vif[1] # UNPACK (initial)

				vifData = io.BytesIO() # shape data

				while file.tell() < rpDma and vifCodeUnpack.cmd != 0:
					vifPacketSize = 0x0
					if vifCodeUnpack.num == 0:
						vifPacketSize = 0x1000
					else:
						vifPacketSize = (vifCodeUnpack.num + 1) * 0x10
					
					vifData.write(file.read(vifPacketSize))
					vifCodeUnpack = VIFcode(file)
				
				vifData.seek(0, os.SEEK_SET)

				while True:
					test = struct.unpack("<I", vifData.read(4))[0]
					if test == 0:
						break

					vifData.seek(0x4, os.SEEK_CUR)
					triCount = struct.unpack("<I", vifData.read(4))[0]

					vifData.seek(0x34, os.SEEK_CUR)

					for t in range(triCount):
						triNorm = Vector.read(vifData, True)
						triVert = [Vector.read(vifData, True) for i in range(3)]
						triUV = [Vector.read(vifData, True) for i in range(3)]
						triCol = [struct.unpack("<4I", vifData.read(16)) for i in range(3)]

						triangles.append({
							"texture": 0,
							"normal": triNorm,
							"vertices": triVert,
							"uvs": triUV,
							"colors": triCol,
						})
			
			print(f"Expecting {RdrVUShape.numTri} triangles but got {len(triangles)} triangles for now...")
		
		# Export to a model!
		export(decompressed_levelFolderPath, collisionPolys, aiNodes, pickupPoss, triangles)
		print(f"All related files are stored at \"{os.path.abspath(decompressed_levelFolderPath)}\"")
	
if __name__ == "__main__":
	main()