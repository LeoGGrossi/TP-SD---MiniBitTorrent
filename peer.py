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
        self.connect_to_tracker()
    
    
    def connect_to_tracker(self):
        """Conecta ao tracker e lista torrents disponíveis"""
        response = self.send_tracker_request({'action': 'list_torrents'})
        if response and response.get('status') == 'success':
            print("\nTorrents disponíveis no tracker:")
            for torrent in response['torrents']:
                print(f"  {torrent['name']} ({torrent['size']} bytes)")
                print(f"  Hash: {torrent['hash']}")
                print(f"  Peers: {torrent['peers']}\n")
        else:
            print("Não foi possível obter a lista de torrents")
        
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
        """Adiciona arquivo e se torna seeder"""
        if not os.path.exists(file_path):
            print(f"Arquivo {file_path} não encontrado")
            return None
        
        with open(file_path, 'rb') as f:
            content = f.read()
            file_hash = hashlib.sha1(content).hexdigest()
    
        self.files[file_hash] = file_path
    
        file_info = {
            'name': os.path.basename(file_path),
            'size': len(content),
            'pieces': self.split_into_pieces(content)
        }
    
        self.register_torrent(file_hash, file_info)
    
        self.announce_as_seeder(file_hash)
        return file_hash
    
    
    def announce_as_seeder(self, torrent_hash):
        """Anuncia como seeder para o tracker"""
        request = {
            'action': 'announce',
            'peer_id': self.peer_id,
            'torrent_hash': torrent_hash,
            'host': self.host,
            'port': self.port,
            'is_seeder': True  # Indica que tem o arquivo completo
        }
        return self.send_tracker_request(request)
    
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
        """Anuncia presença no tracker e atualiza"""
        response = self._send_announce(torrent_hash)
        
        
        if not response or not isinstance(response, dict):
            print("Resposta inválida do tracker")
            return None
        
        if response and response.get('status') == 'success':
            # Agenda próximo anúncio (a cada 15 minutos)
            threading.Timer(900, self.announce_to_tracker, [torrent_hash]).start()
        return response
    
    def _send_announce(self, torrent_hash):
        request = {
            'action': 'announce',
            'peer_id': self.peer_id,
            'torrent_hash': torrent_hash,
            'host': self.host,
            'port': self.port
        }
        return self.send_tracker_request(request)
    
    def send_tracker_request(self, request):
        try:
            print(f"Conectando ao tracker em {self.tracker_host}:{self.tracker_port}")  # Log 1
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)  # Timeout de 5 segundos
            sock.connect((self.tracker_host, self.tracker_port))
            print(f"Enviando requisição: {request}")  # Log 2
            sock.send(json.dumps(request).encode('utf-8'))
            
            response_data = sock.recv(4096).decode('utf-8')
            try:
                response = json.loads(response_data)  # Converte string JSON para dict
            except json.JSONDecodeError:
                print(f"Resposta inválida do tracker: {response_data}")
                return None
            
            sock.close()
            return response
        except Exception as e:
            print(f"Erro ao conectar com tracker: {e}")
            return None
    
    def download_file(self, torrent_hash, save_path):
        """Baixa arquivo e só se anuncia como peer se conseguir completar"""
        print(f"Iniciando download do torrent {torrent_hash}")
    
        # Primeiro verifica se há seeders disponíveis
        response = self.send_tracker_request({
            'action': 'get_peers',
            'torrent_hash': torrent_hash
        })
    
        if not response or not response.get('peers'):
            print("Nenhum seeder disponível para este torrent")
            return False
    
        # Tenta baixar o arquivo
        success = self.download_from_peers(torrent_hash, response['peers'], save_path)
    
        # Só anuncia como peer se o download for bem-sucedido
        if success:
            self.files[torrent_hash] = save_path
            self.announce_as_seeder(torrent_hash)
            print("✓ Download concluído e agora você é um seeder!")
        else:
            print("✗ Download falhou")
    
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
        if torrent_hash not in self.files:
            return {'status': 'error', 'message': 'Arquivo não encontrado'}
        
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
            
    def interactive_menu(self):
        """Menu interativo para o peer"""
        print("\n=== MENU DO PEER ===")
        print("Comandos disponíveis:")
        print("  refresh - Atualizar lista de torrents")
        print("  share <arquivo> - Compartilhar arquivo")
        print("  download <hash> <destino> - Baixar arquivo")
        print("  exit - Sair")
    
        while True:
            cmd = input(f"\nPeer {self.peer_id}> ").strip().lower()
            parts = cmd.split()
        
            if not parts:
                continue
                
            if parts[0] == "refresh":
                self.connect_to_tracker()

            elif parts[0] == "share" and len(parts) == 2:
                file_path = parts[1]
                if not os.path.exists(file_path):
                    print(f"Erro: Arquivo '{file_path}' não encontrado.")
                    continue
                torrent_hash = self.add_file(file_path)
                if torrent_hash:
                    print(f"Arquivo compartilhado com hash: {torrent_hash}")
        
            elif parts[0] == "download" and len(parts) == 3:
                torrent_hash, save_path = parts[1], parts[2]
                print(f"Iniciando download do torrent {torrent_hash}...")
                success = self.download_file(torrent_hash, save_path)
                print("Download concluído com sucesso!" if success else "Falha no download.")
        
            elif parts[0] == "list":
                print("\nArquivos compartilhados:")
                for torrent_hash, file_path in self.files.items():
                    print(f"  - {file_path} (Hash: {torrent_hash})")
        
            elif parts[0] == "exit":
                print("Encerrando peer...")
                os._exit(0)
        
            else:
                print("Comando inválido. Use:")
                print("  share <caminho_arquivo>")
                print("  download <hash> <saida>")
                print("  list")
                print("  refresh")
                print("  exit")
            
if __name__ == "__main__":
    peer_id = input("Digite um ID para este peer: ").strip() or f"peer_{random.randint(1000, 9999)}"
    port = int(input("Digite a porta para este peer (ex: 9001): ") or random.randint(9000, 9999))
    
    peer = Peer(peer_id=peer_id, port=port)
    threading.Thread(target=peer.interactive_menu, daemon=True).start()
    peer.start()  # Inicia o servidor