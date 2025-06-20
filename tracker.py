# tracker.py - Servidor central que gerencia peers e torrents
import socket
import threading
import json
import hashlib
import time
from typing import Dict, List, Set

class Tracker:
    def __init__(self, host='localhost', port=8000):
        self.host = host
        self.port = port
        self.torrents: Dict[str, Dict] = {}  # hash -> {peers: set, file_info: dict}
        self.peers: Dict[str, Dict] = {}     # peer_id -> {host, port, last_seen}
        
    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen(5)
        print(f"Tracker iniciado em {self.host}:{self.port}")
        
        while True:
            client, addr = server.accept()
            thread = threading.Thread(target=self.handle_client, args=(client, addr))
            thread.daemon = True
            thread.start()
    
    def handle_client(self, client, addr):
        try:
            data = client.recv(4096).decode('utf-8')
            request = json.loads(data)
            response = self.process_request(request)
            client.send(json.dumps(response).encode('utf-8'))
        except Exception as e:
            print(f"Erro ao processar cliente {addr}: {e}")
        finally:
            client.close()
    
    def process_request(self, request):
        action = request.get('action')
        
        if action == 'announce':
            return self.handle_announce(request)
        elif action == 'get_peers':
            return self.handle_get_peers(request)
        elif action == 'register_torrent':
            return self.handle_register_torrent(request)
        else:
            return {'status': 'error', 'message': 'Ação inválida'}
    
    def handle_announce(self, request):
        peer_id = request['peer_id']
        torrent_hash = request['torrent_hash']
        host = request['host']
        port = request['port']
        
        # Registra o peer
        self.peers[peer_id] = {
            'host': host,
            'port': port,
            'last_seen': time.time()
        }
        
        # Adiciona peer ao torrent
        if torrent_hash not in self.torrents:
            self.torrents[torrent_hash] = {'peers': set(), 'file_info': {}}
        
        self.torrents[torrent_hash]['peers'].add(peer_id)
        
        # Retorna lista de peers
        peers = []
        for pid in self.torrents[torrent_hash]['peers']:
            if pid != peer_id and pid in self.peers:
                peer_info = self.peers[pid]
                peers.append({
                    'peer_id': pid,
                    'host': peer_info['host'],
                    'port': peer_info['port']
                })
        
        return {'status': 'success', 'peers': peers}
    
    def handle_get_peers(self, request):
        torrent_hash = request['torrent_hash']
        if torrent_hash in self.torrents:
            peers = []
            for pid in self.torrents[torrent_hash]['peers']:
                if pid in self.peers:
                    peer_info = self.peers[pid]
                    peers.append({
                        'peer_id': pid,
                        'host': peer_info['host'],
                        'port': peer_info['port']
                    })
            return {'status': 'success', 'peers': peers}
        return {'status': 'error', 'message': 'Torrent não encontrado'}
    
    def handle_register_torrent(self, request):
        torrent_hash = request['torrent_hash']
        file_info = request['file_info']
        
        if torrent_hash not in self.torrents:
            self.torrents[torrent_hash] = {'peers': set(), 'file_info': file_info}
        
        return {'status': 'success', 'message': 'Torrent registrado'}

if __name__ == "__main__":
    tracker = Tracker()
    tracker.start()