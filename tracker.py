# tracker.py - Servidor central que gerencia peers e torrents
import socket
import threading
import json
import hashlib
import time
import os
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
            print(f"\nNova conexão de {addr}")
            data = client.recv(4096).decode('utf-8')
            print(f"Dados recebidos: {data}")
            request = json.loads(data)
            response = self.process_request(request)
            client.send(json.dumps(response).encode('utf-8'))
        except Exception as e:
            print(f"Erro com {addr}: {str(e)}")
        finally:
            client.close()
    
    def process_request(self, request):
        action = request.get('action')
    
        if action == 'list_torrents':
            return self.handle_list_torrents()
        elif action == 'announce':
            return self.handle_announce(request)
        elif action == 'get_peers':
            return self.handle_get_peers(request)
        elif action == 'register_torrent':
            return self.handle_register_torrent(request)
        else:
            return {'status': 'error', 'message': 'Ação inválida'}
            
    def handle_list_torrents(self):
        """Retorna lista simplificada de todos os torrents"""
        torrent_list = []
        for torrent_hash, data in self.torrents.items():
            torrent_list.append({
                'hash': torrent_hash,
                'name': data['file_info'].get('name', 'Unknown'),
                'size': data['file_info'].get('size', 0),
                'peers': len(data['peers'])
            })
        return {'status': 'success', 'torrents': torrent_list}
    
    def handle_announce(self, request):
        peer_id = request['peer_id']
        torrent_hash = request['torrent_hash']
        host = request['host']
        port = request['port']
        is_seeder = request.get('is_seeder', False)
    
        # Atualiza ou registra o peer
        self.peers[peer_id] = {
            'host': host,
            'port': port,
            'last_seen': time.time(),
            'is_seeder': is_seeder
        }
    
        # Verifica se o torrent existe
        if torrent_hash not in self.torrents:
            return {'status': 'error', 'message': 'Torrent não registrado'}
    
        # Adiciona peer ao torrent (usando set para evitar duplicatas)
        if is_seeder or torrent_hash in self.torrents:
            self.torrents[torrent_hash]['peers'].add(peer_id)
    
        # Coleta informações dos peers (excluindo o próprio peer)
        active_seeders = []
        for pid in self.torrents[torrent_hash]['peers']:
            peer_info = self.peers.get(pid)
            if (peer_info and 
                peer_info['is_seeder'] and 
                time.time() - peer_info['last_seen'] < 1800):
                active_seeders.append({
                    'peer_id': pid,
                    'host': peer_info['host'],
                    'port': peer_info['port']
                })

        return {'status': 'success', 'peers': active_seeders}
    
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
        
    def interactive_menu(self):
        """Menu interativo para o tracker"""
        print("\n=== MENU DO TRACKER ===")
        print("Comandos disponíveis:")
        print("  list - Listar todos os torrents e peers")
        print("  stats - Mostrar estatísticas do tracker")
        print("  exit - Encerrar o tracker")
    
        while True:
            cmd = input("\nTracker> ").strip().lower()
        
            if cmd == "list":
                print("\nTorrents registrados:")
                if not self.torrents:
                    print("Nenhum torrent registrado.")
                    continue
                
                for torrent_hash, data in self.torrents.items():
                    print(f"\nHash: {torrent_hash}")
                    print(f"Arquivo: {data['file_info'].get('name', 'N/A')}")
                    print(f"Tamanho: {data['file_info'].get('size', 0)} bytes")
                
                    if not data['peers']:
                        print("Peers: Nenhum peer ativo")
                        continue
                    
                    print("Peers ativos:")
                    active_peers = 0
                
                    for peer_id in list(data['peers']):  # Usamos list() para criar uma cópia
                        peer = self.peers.get(peer_id)
                    
                        # Verifica se o peer existe e está ativo (últimos 30 minutos)
                        if peer and time.time() - peer['last_seen'] < 1800:
                            active_peers += 1
                            print(f"  - {peer_id} ({peer['host']}:{peer['port']})")
                        else:
                            # Remove peer inativo
                            data['peers'].discard(peer_id)
                            if peer_id in self.peers:
                                del self.peers[peer_id]
                
                    if active_peers == 0:
                        print("  Nenhum peer ativo no momento")
        
            elif cmd == "stats":
                print(f"\nEstatísticas do Tracker:")
                print(f"- Torrents registrados: {len(self.torrents)}")
                print(f"- Peers conhecidos: {len(self.peers)}")
                print(f"- Peers ativos: {sum(1 for p in self.peers.values() if time.time() - p['last_seen'] < 1800)}")
        
            elif cmd == "exit":
                print("Encerrando tracker...")
                os._exit(0)
        
            else:
                print("Comando inválido. Tente 'list', 'stats' ou 'exit'.")
            
    

if __name__ == "__main__":
    tracker = Tracker()
    # Inicia o menu diferente do servidor
    threading.Thread(target=tracker.interactive_menu, daemon=True).start()
    #servidor
    tracker.start() 
