# Cars Race-O-Rama PSP NDS Model Noesis Importer
# By Allen

# Support game:
#   Cars Race-O-Rama PSP
#   Cars Race-O-Rama NDS
#   Cars Mater-National Championship NDS

from inc_noesis import *
import struct

def registerNoesisTypes():
	handle = noesis.register("Cars Race-O-Rama PSP NDS", ".prop;.lod3;.rbh")
	noesis.setHandlerTypeCheck(handle, noepyCheckType)
	noesis.setHandlerLoadModel(handle, propLoadModel)  
	return 1
def noepyCheckType(data):
    bs = NoeBitStream(data)
    idstring = bs.readBytes(4)
    if idstring != b'PIFF':
        return 0

    piffSize = bs.readUInt()
    rbhf = bs.readUInt()

    endOffset = bs.tell() + piffSize - 4
    havePack = False
    while bs.tell() < endOffset :
        chunkType = bs.readBytes(4)
        chunkSize = bs.readUInt()
        nextOffset = bs.tell() + chunkSize
        if(chunkType == b'PACK'): 
            havePack = True
            print("Please decompress rbh file first use the rorpsptool!")
            break
            #return 0
        bs.seek(nextOffset,NOESEEK_ABS)
    fname = ''
    fname = rapi.getInputName()
    fname = fname.lower()
    havePropMesh = fname.find(".prop")
    haveLod3Mesh = fname.find(".lod3")
    haveProps = fname.find("props")
    if havePropMesh < 0 and haveLod3Mesh < 0 and haveProps < 0: return 0
    if havePack: return 0
    haveTex = fname.find(".vram")
    if haveTex > 0 : return 0
    haveTex = fname.find(".skin")
    if haveTex > 0 : return 0    
    haveTex = fname.find(".textures")
    if haveTex > 0 : return 0    
    haveCol = fname.find(".col")    
    if haveCol > 0 : return 0   

    return 1
platform = "PSP"
gameVersion = "ROR"
def propLoadModel(data, mdlList):
    bs = NoeBitStream(data)	
    ctx = rapi.rpgCreateContext()  
    global platform
    global gameVersion
    platform = "PSP"
    gameVersion = "ROR"
    idstring = bs.readBytes(4)
    if idstring != b'PIFF':
        return 0

    fname = ''
    fname = rapi.getInputName()
    fname = fname.lower()
    haveSkinMesh = fname.find(".prop")
    
    haveMapMesh = fname.find(".world")
    if haveSkinMesh < 0: haveSkinMesh = fname.find(".lod3")
    if fname.find(".lod3") > 0: 
        gameVersion = "MNDS"
    if (haveSkinMesh < 0): haveSkinMesh = fname.find("props")
    if fname.find("props") > 0 and fname.find(".prop") < 0 and haveMapMesh < 0:
        gameVersion = "MNDS"
    if haveMapMesh > 0:
        haveSkinMesh = 0
    if haveSkinMesh < 0 and haveMapMesh < 0: return 0
    haveTex = fname.find(".vram")
    if haveTex > 0 : return 0
    haveTex = fname.find(".skin")
    if haveTex > 0 : return 0    
    haveTex = fname.find(".textures")
    if haveTex > 0 : return 0    
    haveCol = fname.find(".col")    
    if haveCol > 0 : return 0      
    piffSize = bs.readUInt()
    rbhf = bs.readUInt()
    endOffset = bs.tell() + piffSize - 4
    

    rbhh = bs.readBytes(4)
    rbhhSize = bs.readInt()
    if rbhh != b'RBHH': return 0
    rbhhOffset = bs.tell()
    

    
    numBodys = rbhhSize // 12

    bodyOffsets = []
    bodyOffset = bs.tell() + rbhhSize + 8
    bodyOffsets.append(bodyOffset)
    for i in range(numBodys):
        unk = bs.readInt()
        bodySize = bs.readUInt()
        bodyOffset += bodySize + 8
        bodyOffsets.append(bodyOffset)
        unk2 = bs.readShort()
        type = bs.readShort() #  4,16
    

      
    # change local offset to global offset
    ext = fname[-4:]  
    if ext == ".rbh" and fname.find("_decmp") > 0:
        backOffset = bs.tell()    
        while bs.tell() < endOffset :
            chunkType = bs.readBytes(4)
            chunkSize = bs.readUInt()
            nextOffset = bs.tell() + chunkSize
            if(chunkType == b'RELC'): 
                dstBodyIndex = bs.readInt()
                baseBodyIndex = bs.readInt()
                numOffsets = (chunkSize - 8) // 4
                for i in range(numOffsets):
                    srcOffsetPionter = bs.readUInt() + bodyOffsets[dstBodyIndex]                
                    nextDataOffset = bs.tell()
                    bs.seek(srcOffsetPionter)
                    globalOffset = bs.readUInt() + bodyOffsets[baseBodyIndex]
                    bs.seek(srcOffsetPionter)
                    bs.writeUInt(globalOffset)
                    bs.seek(nextDataOffset)
            bs.seek(nextOffset,NOESEEK_ABS)
        bs.seek(backOffset)

    copyBoneIDs = []
    numBones = 0
    if haveSkinMesh > 0 or haveMapMesh > 0:
        if haveSkinMesh > 0:
            animOffset = getAnimChunkOffset(bs,numBodys,bodyOffsets)
            if animOffset > 0:
                bs.seek(animOffset)
                bones = readBones(bs,copyBoneIDs)
                numBones = len(bones)
            else:
                haveSkinMesh = 0
                haveMapMesh = 1

        bs.seek(bodyOffsets[0])
        numMesh = bs.readInt()
        if numMesh > 0:
            meshOffset = bs.readUInt()
            bs.seek(meshOffset + 16)
            flag = bs.readInt()
            if flag == 0x1000001: platform = "DS"
            if haveSkinMesh > 0:
                bs.seek(bodyOffsets[3]-4)
                matChunkEnd = bs.tell() + bs.readUInt()
                skeletonNames = readStringChunk(bs)
                animationNames = readStringChunk(bs)
                materialNames = readStringChunk(bs)
                if (bs.tell() < matChunkEnd):
                    try:
                        materialNames = readStringChunk(bs)
                    except:()                
            if haveMapMesh > 0:
                materialBodyIndex = getMaterialBodyIndex(bs,numBodys,bodyOffsets)
                bs.seek(bodyOffsets[materialBodyIndex+1])
                materialNames = readStringChunk(bs)

            
            bs.seek(meshOffset)
            matList = []
            if platform == "PSP":
                readPSPGeometry(bs,matList,materialNames)
            elif platform == "DS":
                readNDSGeometry(bs,matList,materialNames,copyBoneIDs,numBones)
            texList = []  
            texNameList = []
            existTexNameList = []
            path = rapi.getDirForFilePath(rapi.getInputName())
            for m in range(len(matList)):
                texName = matList[m].name
                if texName not in texNameList:
                    texNameList.append(texName)                        
                    fullTexName = path+texName+".tga" if texName != None else ""
                    if rapi.checkFileExists(fullTexName):            
                        texture = noesis.loadImageRGBA(fullTexName)
                        texList.append(texture)
                        existTexNameList.append(texName)
            
            matList = []
            for i in range(len(texList)):
                    matName = existTexNameList[i]
                    material = NoeMaterial(matName, texList[i].name)
                    matList.append(material)  
            mdl = rapi.rpgConstructModel()
            if haveSkinMesh:
                mdl.setBones(bones)                  
            mdl.setModelMaterials(NoeModelMaterials(texList,matList))
            mdlList.append(mdl)
        else:
            mdl = NoeModel()
            mdl.setBones(bones)
            mdlList.append(mdl)

    '''
    for i in range(numBodys):
        chunkType = bs.readBytes(4)
        chunkSize = bs.readUInt()
        nextOffset = bs.tell() + chunkSize
        #if chunkType == b'BODY' and i == 1:
  
        bs.seek(nextOffset,NOESEEK_ABS)
    '''


    return 1
def getMaterialBodyIndex(bs,numBodys,bodyOffsets):
    offset = -1
    for i in range(1,numBodys):
        bs.seek(bodyOffsets[i])
        magic = bs.readInt()
        if magic > 0:
            magic = bs.readInt()
            magic2 = bs.readInt()
            magic3 = bs.readInt()
            if magic == -1 and magic2 == -1 and magic3 == -1:
                return i
    return offset    
def getAnimChunkOffset(bs,numBodys,bodyOffsets):
    offset = -1
    for i in range(1,numBodys):
        bs.seek(bodyOffsets[i])
        magic = bs.readInt()
        if magic == 1:
            magic = bs.readInt()
            if magic > 0:
                bs.seek(bodyOffsets[i]+8)
                offset = bs.readInt()
                if offset > 0: return offset
    return offset

def readNDSGeometry(bs:NoeBitStream,matList,materialNames,copyBoneIDs,numBones):
    global gameVersion
    colSphereXYZRad = struct.unpack('4i',bs.readBytes(16))
    flag = bs.readUInt()
    skinBoneTableOffset = bs.readUInt()
    unk = bs.readInt()
    colBoundingBoxMinMaxXYZ = struct.unpack('6i',bs.readBytes(24))    
    numSplit = bs.readShort()
    numUnk1 = bs.readShort()
    numUnk2 = bs.readShort() 
    numUnk3 = bs.readShort()
    unk = bs.readInt()
    offset3_scale3 = [(bs.readInt() / 4096.0) for i in range(6)]
    linkOffset = bs.readUInt()
    if gameVersion == "ROR":
        meshID = bs.readInt()
    
    meshInfoOffset = bs.tell()

    bs.seek(skinBoneTableOffset)
    boneMaps = []
    if skinBoneTableOffset:
        for i in range(numSplit):
            boneMap = struct.unpack('32h',bs.readBytes(64))
            boneMaps.append(boneMap)    
    
    bs.seek(meshInfoOffset)
    for i in range(numSplit):
        materialOffset = bs.readUInt()
        offset = bs.readUInt()
        cmdSize = bs.readUInt()
        nextOffset = bs.tell()

        bs.seek((materialOffset+2))
        texNameID = bs.readShort() 
         
        bs.seek(8,NOESEEK_REL)    
        texWidth = bs.readShort()
        texHeight = bs.readShort()
        texName = materialNames[texNameID] if texNameID != -1 else None
        matList.append(NoeMaterial(texName,texName))
        boneMap = boneMaps[i] if skinBoneTableOffset > 0 else None
        bs.seek(offset)
        dsGpu = DSGpuCmd(bs,cmdSize,boneMap,texName,offset3_scale3,[texWidth,texHeight],copyBoneIDs,numBones)
        dsGpu.readGpuCmd()


        bs.seek(nextOffset) 
class DSGpuCmd(object):
    def __init__(self,bs:NoeBitStream,cmdSize,boneMap,texName,offset3_scale3,textureFactor,copyBoneIDs,numBones):
        self.cmdSize = cmdSize
        self.bs = bs
        self.boneMap = boneMap
        self.texName = texName
        self.offset3_scale3 = offset3_scale3
        self.textureFactor = textureFactor
        self.copyBoneIDs = copyBoneIDs
        self.numBones = numBones
    def readGpuCmd(self):
        endOffset = self.bs.tell() + self.cmdSize * 4
        vertexAttr = None
        tempBoneID = 0
        haveBoneWeight = False
        haveColor = False
        haveNormal = False
        haveUV = False
        tempNormal = None
        tempColor = None
        tempUV = None
        while self.bs.tell() < endOffset:
            cmds = self.bs.readBytes(4)
            #print("cmd offset:0x%X" %self.bs.tell(), "%X"  %endOffset)

            for i in range(4): 
                cmd = cmds[i]
                # NOP
                if cmd == 0x0:()
                
                # BEGIN_VTXS               
                elif cmd == 0x40:
                    vertexAttr = DSVertexAttr()
                    vertexAttr.primitive = self.bs.readInt()
                # MTX_RESTORE
                elif cmd == 0x14:
                    vertexAttr.haveSkin = True
                    haveBoneWeight = True
                    boneID = self.boneMap[self.bs.readInt()&0x1f]
                    if boneID > (self.numBones -1):
                        boneID = self.copyBoneIDs[boneID]                     
                    tempBoneID = boneID
                    #print("boneID:%d"%boneID,"CurOffset:0x%x"%(self.bs.tell()-4))
                    vertexAttr.boneids += struct.pack('h',boneID)
                    vertexAttr.weights += struct.pack('f',1.0)
                # COLOR
                elif cmd == 0x20:
                    vertexAttr.haveColor = True
                    haveColor = True
                    color = self.bs.readUInt() & 0x7FFF
                    vertexAttr.colors += decodeBGR555toRGBA8888(color)
                    tempColor = decodeBGR555toRGBA8888(color)
                # NORMAL
                elif cmd == 0x21:
                    vertexAttr.haveNormal = True
                    haveNormal = True
                    value = self.bs.readUInt()
                    x = readFixedPoint32(value & 0x3ff,1,0,9)
                    y = readFixedPoint32((value >> 10) & 0x3ff,1,0,9)
                    z = readFixedPoint32((value >> 20) & 0x3ff,1,0,9)
                    vertexAttr.normals += struct.pack('3f',x,y,z)
                    tempNormal = struct.pack('3f',x,y,z)
                # UV TEXCOORD
                elif cmd == 0x22:
                    vertexAttr.haveUV = True
                    haveUV = True
                    u = readFixedPoint32(self.bs.readUShort(),1,11,4) / self.textureFactor[0]
                    v = readFixedPoint32(self.bs.readUShort(),1,11,4) / self.textureFactor[1]
                    vertexAttr.uvs += struct.pack('2f',u,v)
                    tempUV = struct.pack('2f',u,v)
                # VTX_16
                elif cmd == 0x23:                    
                    x = readFixedPoint32(self.bs.readUShort(),1,3,12) * self.offset3_scale3[3] + self.offset3_scale3[0]
                    y = readFixedPoint32(self.bs.readUShort(),1,3,12) * self.offset3_scale3[4] + self.offset3_scale3[1]
                    z = readFixedPoint32(self.bs.readUShort(),1,3,12) * self.offset3_scale3[5] + self.offset3_scale3[2]
                    pad = self.bs.readShort()
                    vertexAttr.vertices += struct.pack('3f',x,y,z)     
                    curNumVert = len(vertexAttr.vertices) // 12
                    if haveUV:
                        curNumUV = len(vertexAttr.uvs) // 8
                        if curNumUV < curNumVert:
                            vertexAttr.uvs += tempUV
                    if haveNormal:
                        curNumNormal = len(vertexAttr.normals) // 12
                        if curNumNormal < curNumVert:
                            vertexAttr.normals += tempNormal
                    if haveColor:
                        curNumColor = len(vertexAttr.colors) // 4
                        if curNumColor < curNumVert:
                            vertexAttr.colors += tempColor
                    if haveBoneWeight:
                        curNumBoneWeight = len(vertexAttr.boneids) // 2
                        if curNumBoneWeight < curNumVert:
                            prevBoneID = tempBoneID                           
                            vertexAttr.boneids += struct.pack('h',prevBoneID)
                            vertexAttr.weights += struct.pack('f',1.0)                           
                # VTX_10
                elif cmd == 0x24:
                    value = self.bs.readUInt()
                    x = readFixedPoint32(value & 0x3ff,1,3,6) * self.offset3_scale3[3] + self.offset3_scale3[0]
                    y = readFixedPoint32((value >> 10) & 0x3ff,1,3,6)* self.offset3_scale3[4] + self.offset3_scale3[1]
                    z = readFixedPoint32((value >> 20) & 0x3ff,1,3,6)* self.offset3_scale3[5] + self.offset3_scale3[2]
                    vertexAttr.vertices += struct.pack('3f',x,y,z) 
                    curNumVert = len(vertexAttr.vertices) // 12
                    if haveUV:
                        curNumUV = len(vertexAttr.uvs) // 8
                        if curNumUV < curNumVert:
                            vertexAttr.uvs += tempUV
                    if haveNormal:
                        curNumNormal = len(vertexAttr.normals) // 12
                        if curNumNormal < curNumVert:
                            vertexAttr.normals += tempNormal
                    if haveColor:
                        curNumColor = len(vertexAttr.colors) // 4
                        if curNumColor < curNumVert:
                            vertexAttr.colors += tempColor
                    if haveBoneWeight:
                        curNumBoneWeight = len(vertexAttr.boneids) // 2
                        if curNumBoneWeight < curNumVert:
                            prevBoneID = tempBoneID                           
                            vertexAttr.boneids += struct.pack('h',prevBoneID)
                            vertexAttr.weights += struct.pack('f',1.0)    

                # END_VTXS
                elif cmd == 0x41:
                    numVert = len(vertexAttr.vertices) // 12
                    numUV = len(vertexAttr.uvs) // 8
                    numNormal = len(vertexAttr.normals) // 12
                    numBoneID = len(vertexAttr.boneids) // 2
                    numColor = len(vertexAttr.colors) // 4
                    faceBuffer = bytes()

                    if self.texName != None: rapi.rpgSetMaterial(self.texName) 
                    rapi.rpgBindPositionBuffer(vertexAttr.vertices, noesis.RPGEODATA_FLOAT, 12)   
                    if len(vertexAttr.uvs): rapi.rpgBindUV1Buffer(vertexAttr.uvs, noesis.RPGEODATA_FLOAT, 8)
                    if len(vertexAttr.boneids): rapi.rpgBindBoneIndexBuffer(vertexAttr.boneids, noesis.RPGEODATA_SHORT, 2, 1)
                    if len(vertexAttr.weights): rapi.rpgBindBoneWeightBuffer(vertexAttr.weights, noesis.RPGEODATA_FLOAT, 4, 1) 
                    if len(vertexAttr.normals): rapi.rpgBindNormalBuffer(vertexAttr.normals, noesis.RPGEODATA_FLOAT, 12)
                    if len(vertexAttr.colors): rapi.rpgBindColorBuffer(vertexAttr.colors, noesis.RPGEODATA_UBYTE, 4, 4) 

                    # Triangle Strips
                    if vertexAttr.primitive == 2:
                        f1 = 0
                        f2 = 1
                        for v in range(numVert):
                            if v > 1:
                                f3 = v
                                if v % 2:
                                    face = [f1,f3,f2]
                                else:
                                    face = [f1,f2,f3]
                                f1 = f2
                                f2 = f3
                                faceBuffer += struct.pack('3I',face[0],face[1],face[2])
                        rapi.rpgCommitTriangles(faceBuffer, noesis.RPGEODATA_INT, len(faceBuffer)//4, noesis.RPGEO_TRIANGLE, 1)

                    # Quadliteral Strips
                    elif vertexAttr.primitive == 3:                        
                        f1 = 0
                        f2 = 1
                        for v in range(numVert):
                            if v > 1:
                                f3 = v
                                if v % 2:
                                    face = [f1,f3,f2]
                                else:
                                    face = [f1,f2,f3]
                                f1 = f2
                                f2 = f3
                                faceBuffer += struct.pack('3I',face[0],face[1],face[2])

                        rapi.rpgCommitTriangles(faceBuffer, noesis.RPGEODATA_INT, len(faceBuffer)//4, noesis.RPGEO_TRIANGLE, 1)
                    rapi.rpgClearBufferBinds()  


def readFixedPoint32(x,sign_bits,int_bits,frac_bits):
    sign_mask = 1 << (int_bits + frac_bits)            
    y = 0.0
    if (x & sign_mask) != 0:
        y = int(x | ~(sign_mask - 1))
    else:
        y = x
    y = y / (1 << frac_bits)
    return y
class DSVertexAttr(object):
    def __init__(self):
        self.primitive = None
        self.vertices = bytes()
        self.colors = bytes()
        self.boneids = bytes()
        self.weights = bytes()
        self.uvs = bytes()
        self.normals = bytes() 
        self.haveColor = False
        self.haveNormal = False
        self.haveUV = False   
        self.haveSkin = False    
        
def readPSPGeometry(bs:NoeBitStream,matList,materialNames):
    colSphereXYZWRad = struct.unpack('5f',bs.readBytes(20))
    flag = bs.readUInt()
    skinBoneTableOffset = bs.readUInt()
    unk = bs.readInt()
    colBoundingBoxMinMaxXYZW = struct.unpack('8f',bs.readBytes(32))
    numSplit = bs.readShort()
    numUnk1 = bs.readShort()
    numUnk2 = bs.readInt() 
    bs.seek(8,NOESEEK_REL)
    transformMatrix = NoeMat44.fromBytes(bs.readBytes(64)).toMat43()#.inverse()
    bs.seek(4,NOESEEK_REL)
    meshInfoOffset = bs.tell()

    bs.seek(skinBoneTableOffset)
    boneMaps = []
    if skinBoneTableOffset:
        for i in range(numSplit):
            boneMap = struct.unpack('8b',bs.readBytes(8))
            boneMaps.append(boneMap)
    
    bs.seek(meshInfoOffset)
    for i in range(numSplit):
        materialOffset = bs.readUInt()
        unk = bs.readInt()
        offset = bs.readUInt()
        format = bs.readUInt()
        nextOffset = bs.tell()

        bs.seek((materialOffset+2))
        texNameID = bs.readShort()        
        texName = materialNames[texNameID] if texNameID != -1 else None
        matList.append(NoeMaterial(texName,texName))
        bs.seek(offset)
        vertexInfoOffset = bs.readUInt()
        vertexDataOffset = bs.readUInt()
        bs.seek((vertexInfoOffset+8))
        format = bs.readUInt()
        vertFormat = decodeVTypePSP(format)
        
        dataOffset = vertexDataOffset
        numWeights = vertFormat.numWeights
        
        numVert = bs.readShort()
        u1 = bs.readByte()
        u2 = bs.readByte()
        while (numVert != 0):
            nextVertInfoOffset = bs.tell()
            bs.seek(dataOffset)
            weights = bytes()
            boneids = bytes()
            vertexBuffer = bytes()
            normalBuffer = bytes()
            colorBuffer = bytes()
            uvBuffer = bytes()
            faceBuffer = bytes()
            for v in range(numVert):
                if vertFormat.WeightFormat == 1:
                    for w in range(numWeights):
                        weight = bs.readUByte() / 128.0
                        if weight > 0: 
                            weights += struct.pack('f',weight)
                            boneids += struct.pack('b',boneMaps[i][w])
                        else:
                            weights += struct.pack('f',0)
                            boneids += struct.pack('B',0)
                    if vertFormat.UVFormat !=0 :
                        if (bs.tell() % 2) > 0: bs.seek(1,NOESEEK_REL)
                if vertFormat.UVFormat == 2:
                    tu = bs.readShort() / 4096.0
                    tv = bs.readShort() / 4096.0
                    uvBuffer += struct.pack('2f',tu,tv)
                if vertFormat.ColorFormat == 4:
                    colorRGB565 = bs.readUShort()
                    colorBuffer += decodeBGR565toRGBA8888(colorRGB565)
                elif vertFormat.ColorFormat == 6:
                    colorRGBA4444 = bs.readUShort()
                    colorBuffer += decodeABGR4444toRGBA8888(colorRGBA4444)
                if vertFormat.NormalFormat == 1:
                    nx = bs.readByte() / 128.0
                    ny = bs.readByte() / 128.0
                    nz = bs.readByte() / 128.0
                    normal = NoeVec3((nx,ny,nz))
                    normal *= transformMatrix.toQuat().toMat43()                        
                    #normalBuffer += struct.pack('3f',nx,ny,nz)
                    normalBuffer += struct.pack('3f',normal.vec3[0],normal.vec3[1],normal.vec3[2])                        
                    if vertFormat.UVFormat !=0 :
                        if (bs.tell() % 2) > 0: bs.seek(1,NOESEEK_REL)
                if vertFormat.PositionFormat == 2:
                    vx = bs.readShort() / 32768.0
                    vy = bs.readShort() / 32768.0
                    vz = bs.readShort() / 32768.0                  
                    vertex = NoeVec3((vx,vy,vz))
                    vertex *= transformMatrix
                    vertexBuffer += struct.pack('3f',vertex.vec3[0],vertex.vec3[1],vertex.vec3[2])
            
            f1 = 0
            f2 = 1
            for v in range(numVert):
                if v > 1:
                    f3 = v
                    if v % 2:
                        face = [f1,f3,f2]
                    else:
                        face = [f1,f2,f3]
                    f1 = f2
                    f2 = f3
                    faceBuffer += struct.pack('3I',face[0],face[1],face[2])
            
            if len(boneids): rapi.rpgBindBoneIndexBuffer(boneids, noesis.RPGEODATA_UBYTE, numWeights, numWeights)
            if len(weights): rapi.rpgBindBoneWeightBuffer(weights, noesis.RPGEODATA_FLOAT, numWeights * 4, numWeights) 

            rapi.rpgBindPositionBuffer(vertexBuffer, noesis.RPGEODATA_FLOAT, 12) 

            if len(normalBuffer): rapi.rpgBindNormalBuffer(normalBuffer, noesis.RPGEODATA_FLOAT, 12)

            if len(uvBuffer): rapi.rpgBindUV1Buffer(uvBuffer, noesis.RPGEODATA_FLOAT, 8)  

            if len(colorBuffer): rapi.rpgBindColorBuffer(colorBuffer, noesis.RPGEODATA_UBYTE, 4, 4)   

            if texName != None: rapi.rpgSetMaterial(texName)     
    
            rapi.rpgCommitTriangles(faceBuffer, noesis.RPGEODATA_INT, len(faceBuffer)//4, noesis.RPGEO_TRIANGLE, 1)
            rapi.rpgClearBufferBinds()                           
            dataOffset = bs.tell()  
            bs.seek(nextVertInfoOffset)
            numVert = bs.readShort()
            u1 = bs.readByte()
            u2 = bs.readByte()

        bs.seek(nextOffset)
def decodeABGR4444toRGBA8888(color16):   
    r = (color16 & 0xf)
    g = (color16 >> 4) & 0xf
    b = (color16 >> 8) & 0xf
    a = (color16 >> 12) & 0xf
    r = (r << 4) | (r >> 3)
    g = (g << 4) | (r >> 3)
    b = (b << 4) | (b >> 3)
    a = (a << 4) | (a >> 3)
    return struct.pack('4B',r,g,b,a)     
def decodeBGR565toRGBA8888(color16):
    r = (color16 & 0x1f)
    g = (color16 >> 5) & 0x3f
    b = (color16 >> 11) & 0x1f
    r = (r << 3) | (r >> 2)
    g = (g << 2) | (r >> 1)
    b = (b << 3) | (b >> 2)
    a = 255
    return struct.pack('4B',r,g,b,a)
def decodeBGR555toRGBA8888(color16):
    r = (color16 & 0x1f)
    g = (color16 >> 5) & 0x1f
    b = (color16 >> 10) & 0x1f
    r = (r << 3) | (r >> 2)
    g = (g << 3) | (r >> 2)
    b = (b << 3) | (b >> 2)
    a = 255
    return struct.pack('4B',r,g,b,a)    
class decodeVTypePSP(object):
    def __init__(self,VTYPE:int):
        self.UVFormat = VTYPE & 3
        self.ColorFormat = (VTYPE >> 2) & 7 
        self.NormalFormat = (VTYPE >> 5) & 3
        self.PositionFormat = (VTYPE >> 7) & 3
        self.WeightFormat = (VTYPE >> 9) & 3
        self.IndexFormat = (VTYPE >> 11) & 3
        self.numWeights = ((VTYPE >> 14) & 7) + 1 # Number of weights (Skinning)
        self.numVertices =((VTYPE >> 18) & 7) + 1 # Number of vertices (Morphing)
        self.coordType = (VTYPE >> 23) & 1 # Bypass Transform Pipeline. 1 -Transformed Coordinates . 0-Raw Coordinates.
        
def readStringChunk(bs:NoeBitStream):

    nameOffsets = []
    offset = bs.readUInt()
    if offset > 0: nameOffsets.append(offset)
    while offset != 0:
        offset = bs.readUInt()
        if offset > 0: 
            nameOffsets.append(offset)

    names = []
    for i in range(len(nameOffsets)):
        bs.seek(nameOffsets[i])
        names.append(bs.readString())
    if (bs.tell() % 4) > 0:
        padLen = 4 - (bs.tell() % 4)
        bs.seek(padLen,NOESEEK_REL)
    return names

def readBones(bs,copyBoneIDs):
    global platform
    boneTableOffset = bs.readUInt()
    boneEndOffset = bs.readUInt()
    bboxOffset = bs.readUInt()
    numBones = bs.readShort()
    numExtraBones = bs.readShort()
    
    pad = bs.readInt()
    numAnimationFile = bs.readInt()
    animFileInfoOffset = bs.readUInt()
    matrixOffset = bs.readUInt()
    boneNamesInfoOffset = bs.readUInt()
    animationNamesInfoOffset = bs.readUInt()
    if boneNamesInfoOffset == 0:            
        platform = "DS"
        DSBoneNamesInfoOffset = bs.readUInt()
        DSAnimationNamesInfoOffset = bs.readUInt()
    unk = bs.readInt()

    bs.seek(boneTableOffset)
    bones = []
    parentIDList = []
    matrixList = []
    for b in range(numBones):
        unk1 = bs.readShort()
        flag = bs.readShort()        
        parentID = bs.readShort()
        unkCount = bs.readShort()
        parentIDList.append(parentID) 
        copyBoneIDs.append(b)       
    if numExtraBones > 0:        
        bs.seek(boneEndOffset)
        for b in range(numExtraBones):
            unk1 = bs.readInt()
            unk2 = bs.readShort()
            unk3 = bs.readShort()
            unk4 = bs.readShort()
            id = bs.readShort()
            copyBoneIDs.append(id)
    
    bs.seek( matrixOffset)            
    for m in range(numBones) :
        if platform == "PSP":                    
            mat44 = NoeMat44.fromBytes(bs.readBytes(64))
            mat43 = mat44.toMat43().inverse()
            matrixList.append(mat43)
        else:
            m43 = bytes()
            for f in range(12):
                value = bs.readInt() / 4096.0
                m43 += struct.pack('f',value)
                
            mat43 = NoeMat43.fromBytes(m43).transpose().inverse()
            matrixList.append(mat43)


    if platform == "PSP":
        bs.seek(boneNamesInfoOffset)
    else:
        bs.seek(DSBoneNamesInfoOffset)
    boneNameOffset = bs.readUInt()
    numName = bs.readInt()
    boneNameMappingOffset = bs.tell()

    bs.seek(boneNameOffset)
    bnameOffsets = []
    bnameOffset = bs.readUInt()
    bnameOffsets.append(bnameOffset)
    while bnameOffset != 0:
        bnameOffset = bs.readUInt()
        if bnameOffset > 0 :
            bnameOffsets.append(bnameOffset)
    boneNames = []
    for b in range(len(bnameOffsets)):
        bs.seek(bnameOffsets[b])
        boneNames.append(bs.readString())

    for j in range(numBones):                
            boneIndex = j
            boneName = None
            boneMat = matrixList[j]
            bonePIndex = parentIDList[j]
            bone = NoeBone(boneIndex, boneName, boneMat, None, bonePIndex)
            bones.append(bone)  

    bs.seek(boneNameMappingOffset,NOESEEK_ABS)
    for n in range(numName):
        boneID = bs.readShort()
        boneNameID = bs.readShort()
        bones[boneID].name = boneNames[boneNameID]

    bs.seek( animFileInfoOffset)
    animFileOffsets = [(bs.readUInt() ) for o in range(numAnimationFile)]

    return bones