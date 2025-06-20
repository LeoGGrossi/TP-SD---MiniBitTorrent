# peer.py - Cliente que pode fazer download e upload de arquivos
import socket
import threading
import json
import hashlib
import os
import time
import random

class Peer:
    def __init__(self, peer_id=None, host='localhost', port=None):
        self.peer_id = peer_id or f"peer_{random.randint(1000, 9999)}"
        self.host = host
        self.port = port or random.randint(9000, 9999)
        self.tracker_host = 'localhost'
        self.tracker_port = 8000
        self.files = {}  # hash -> file_path
        self.downloading = {}  # hash -> {pieces: dict, total_pieces: int}
        
    def start(self):
        """Inicia o servidor do peer para aceitar conexões de outros peers"""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen(5)
        print(f"Peer {self.peer_id} iniciado em {self.host}:{self.port}")
        
        while True:
            client, addr = server.accept()
            thread = threading.Thread(target=self.handle_peer, args=(client, addr))
            thread.daemon = True
            thread.start()
    
    def handle_peer(self, client, addr):
        """Processa requisições de outros peers"""
        try:
            data = client.recv(4096).decode('utf-8')
            request = json.loads(data)
            
            if request['action'] == 'get_piece':
                response = self.send_piece(request)
            elif request['action'] == 'get_file_info':
                response = self.send_file_info(request)
            else:
                response = {'status': 'error', 'message': 'Ação inválida'}
            
            client.send(json.dumps(response).encode('utf-8'))
        except Exception as e:
            print(f"Erro ao processar peer {addr}: {e}")
        finally:
            client.close()
    
    def add_file(self, file_path):
        """Adiciona um arquivo para compartilhamento"""
        if not os.path.exists(file_path):
            print(f"Arquivo {file_path} não encontrado")
            return None
        
        # Calcula hash do arquivo
        with open(file_path, 'rb') as f:
            content = f.read()
            file_hash = hashlib.sha1(content).hexdigest()
        
        self.files[file_hash] = file_path
        
        # Registra torrent no tracker
        file_info = {
            'name': os.path.basename(file_path),
            'size': len(content),
            'pieces': self.split_into_pieces(content)
        }
        
        self.register_torrent(file_hash, file_info)
        return file_hash
    
    def split_into_pieces(self, content, piece_size=1024):
        """Divide arquivo em pedaços"""
        pieces = []
        for i in range(0, len(content), piece_size):
            piece = content[i:i+piece_size]
            piece_hash = hashlib.sha1(piece).hexdigest()
            pieces.append({
                'index': len(pieces),
                'hash': piece_hash,
                'size': len(piece)
            })
        return pieces
    
    def register_torrent(self, torrent_hash, file_info):
        """Registra torrent no tracker"""
        request = {
            'action': 'register_torrent',
            'torrent_hash': torrent_hash,
            'file_info': file_info
        }
        self.send_tracker_request(request)
    
    def announce_to_tracker(self, torrent_hash):
        """Anuncia presença no tracker"""
        request = {
            'action': 'announce',
            'peer_id': self.peer_id,
            'torrent_hash': torrent_hash,
            'host': self.host,
            'port': self.port
        }
        return self.send_tracker_request(request)
    
    def send_tracker_request(self, request):
        """Envia requisição para o tracker"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.tracker_host, self.tracker_port))
            sock.send(json.dumps(request).encode('utf-8'))
            response = json.loads(sock.recv(4096).decode('utf-8'))
            sock.close()
            return response
        except Exception as e:
            print(f"Erro ao conectar com tracker: {e}")
            return None
    
    def download_file(self, torrent_hash, save_path):
        """Baixa arquivo usando torrent hash"""
        print(f"Iniciando download do torrent {torrent_hash}")
        
        # Anuncia para o tracker
        response = self.announce_to_tracker(torrent_hash)
        if not response or response.get('status') != 'success':
            print("Erro ao anunciar para tracker")
            return False
        
        peers = response.get('peers', [])
        if not peers:
            print("Nenhum peer disponível")
            return False
        
        # Baixa de peers
        success = self.download_from_peers(torrent_hash, peers, save_path)
        return success
    
    def download_from_peers(self, torrent_hash, peers, save_path):
        """Baixa arquivo de peers disponíveis"""
        for peer in peers:
            try:
                # Conecta com peer
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((peer['host'], peer['port']))
                
                # Solicita informações do arquivo
                request = {
                    'action': 'get_file_info',
                    'torrent_hash': torrent_hash
                }
                sock.send(json.dumps(request).encode('utf-8'))
                response = json.loads(sock.recv(4096).decode('utf-8'))
                sock.close()
                
                if response.get('status') == 'success':
                    file_info = response['file_info']
                    return self.download_pieces(torrent_hash, peers, file_info, save_path)
                    
            except Exception as e:
                print(f"Erro ao conectar com peer {peer['peer_id']}: {e}")
                continue
        
        return False
    
    def download_pieces(self, torrent_hash, peers, file_info, save_path):
        """Baixa pedaços do arquivo"""
        pieces = file_info['pieces']
        downloaded_pieces = {}
        
        for piece_info in pieces:
            piece_index = piece_info['index']
            
            # Tenta baixar o pedaço de algum peer
            for peer in peers:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.connect((peer['host'], peer['port']))
                    
                    request = {
                        'action': 'get_piece',
                        'torrent_hash': torrent_hash,
                        'piece_index': piece_index
                    }
                    sock.send(json.dumps(request).encode('utf-8'))
                    response = json.loads(sock.recv(8192).decode('utf-8'))
                    sock.close()
                    
                    if response.get('status') == 'success':
                        piece_data = response['piece_data'].encode('latin-1')
                        downloaded_pieces[piece_index] = piece_data
                        print(f"Baixado pedaço {piece_index}/{len(pieces)-1}")
                        break
                        
                except Exception as e:
                    print(f"Erro ao baixar pedaço {piece_index} do peer {peer['peer_id']}: {e}")
                    continue
        
        # Reconstrói arquivo
        if len(downloaded_pieces) == len(pieces):
            with open(save_path, 'wb') as f:
                for i in range(len(pieces)):
                    f.write(downloaded_pieces[i])
            print(f"Download concluído: {save_path}")
            return True
        else:
            print(f"Download incompleto: {len(downloaded_pieces)}/{len(pieces)} pedaços")
            return False
    
    def send_piece(self, request):
        """Envia pedaço de arquivo para outro peer"""
        torrent_hash = request['torrent_hash']
        piece_index = request['piece_index']
        
        if torrent_hash not in self.files:
            return {'status': 'error', 'message': 'Arquivo não encontrado'}
        
        file_path = self.files[torrent_hash]
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                pieces = self.split_into_pieces(content)
                
                if piece_index < len(pieces):
                    piece_start = piece_index * 1024
                    piece_end = min(piece_start + 1024, len(content))
                    piece_data = content[piece_start:piece_end]
                    
                    return {
                        'status': 'success',
                        'piece_data': piece_data.decode('latin-1')
                    }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
        
        return {'status': 'error', 'message': 'Pedaço não encontrado'}
    
    def send_file_info(self, request):
        """Envia informações do arquivo"""
        torrent_hash = request['torrent_hash']
        
        if torrent_hash not in self.files:
            return {'status': 'error', 'message': 'Arquivo não encontrado'}
        
        file_path = self.files[torrent_hash]
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                file_info = {
                    'name': os.path.basename(file_path),
                    'size': len(content),
                    'pieces': self.split_into_pieces(content)
                }
                return {'status': 'success', 'file_info': file_info}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}