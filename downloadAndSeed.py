from threading import Thread, get_native_id, Lock
import time
class downloadAndSeed():
    def __init__(self, allPeers, torrentFileInfo):
        self.allBitfields = {}
        self.fileDescriptor=open(torrentFileInfo.nameOfFile,"wb+")
        self.lengthOfFileToBeDownloaded=torrentFileInfo.lengthOfFileToBeDownloaded
        self.allPeers = allPeers
        self.downloadedPiecesBitfields = set()
        self.downloadLock = Lock()
        self.torrentFileInfo = torrentFileInfo
    def writeNullToFile(self):
        data = b"\x00" * self.lengthOfFileToBeDownloaded
        self.fileDescriptor.write(data)


    def getBitfield(self, peer, peerNumber):
        # print("I am in getBitfield", get_native_id(), flush="true")
        retry = 0
        while(1):
            if(peer.doHandshake()):
                print("HandShake Successful .. ")
                response = peer.decodeMsg(peer.receiveMsg())
                peer.handleMessages(response)
                # function call for bitfield
                for pieceNumber in peer.bitfield:
                    if pieceNumber in self.allBitfields:
                        self.allBitfields[pieceNumber].append(peerNumber)
                    else:
                        self.allBitfields[pieceNumber] = [peerNumber] 
                # tryToUnchokePeer(peer)
                break
            else:
                retry += 1
                if retry > 3:
                    break
                continue

    def isDownloadRemaining(self):
        if self.torrentFileInfo.numberOfPieces != len(self.downloadedPiecesBitfields):
            return True
        return False
    def rarestPieceFirstSelection(self):
        rarestPieces = []
        if len(self.allBitfields) == 0:
            return rarestPieces
        rarestCount = min(map(len, self.allBitfields.values()))
        for pieceNumber in self.allBitfields.keys():
            if len(self.allBitfields[pieceNumber]) == rarestCount and pieceNumber not in self.downloadedPiecesBitfields:
                rarestPieces.append(pieceNumber)
        return rarestPieces

    def download(self):
        for peerNumber, peer in enumerate(self.allPeers):
            if peerNumber >= 30:
                break
            thread = Thread( target=self.getBitfield, args=(peer, peerNumber))
            thread.start()
            # self.getBitfield(peer, peerNumber)
        # self.writeNullToFile()
        while self.isDownloadRemaining():
            rarestPieces = self.rarestPieceFirstSelection()
            if len(self.allBitfields) > 0:
                print(self.allBitfields)
            allDonwloadingThreads = []
            if len(self.downloadedPiecesBitfields) > 0:
                print("Donwloaded Number of Pieces .....", len(self.downloadedPiecesBitfields))
            for pieceNumber in rarestPieces:
                peer = self.peerSelection(pieceNumber)
                if peer ==None:

                    print("no peer is free", pieceNumber)
                    continue
                thread = Thread(target=self.downloadPiece, args=(peer, pieceNumber))
                allDonwloadingThreads.append(thread)
                thread.start()
            for thread in allDonwloadingThreads:
                thread.join()
        print("Downloaded File", self.torrentFileInfo.nameOfFile)

    def downloadPiece(self,peer,pieceNumber):
        peer.isDownloading = True
        startTime = time.time()
        isPieceDownloaded, piece = peer.peerFSM(pieceNumber)
        endTime = time.time()
        if isPieceDownloaded == False:
            peer.isDownloading = False
            return
        print("time taken in downloading a piece",endTime-startTime)
        self.downloadLock.acquire()
        # print("I am Acquiring Lock")
        # self.allBitfields.pop(pieceNumber)
        self.downloadedPiecesBitfields.add(pieceNumber)
        self.writePieceInFile(pieceNumber, piece)
        self.downloadLock.release()
        peer.isDownloading = False
        # print("I am Out of Download Piece",get_native_id())
    def writePieceInFile(self,pieceNumber, piece):
        self.fileDescriptor.seek(pieceNumber*self.torrentFileInfo.pieceLength, 0)
        self.fileDescriptor.write(piece) 
    
    def peerSelection(self, pieceNumber):
        for peerNumber in self.allBitfields[pieceNumber]:
            peer = self.allPeers[peerNumber]
            if peer.isDownloading or not peer.isConnectionAlive or not peer.isHandshakeDone:
                print("peerNumber",peerNumber,peer.isDownloading,peer.isConnectionAlive,peer.isHandshakeDone)
                continue
            else:
                return peer
        return None
                



    
