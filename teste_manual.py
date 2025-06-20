import threading
import time
import os
from tracker import Tracker
from peer import Peer

def teste_passo_a_passo():
    """Teste manual para entender cada etapa"""
    print("=== TESTE PASSO A PASSO ===\n")
    
    # 1. Criar arquivo de teste
    print("1. Criando arquivo de teste...")
    os.makedirs('teste', exist_ok=True)
    with open('teste/meu_arquivo.txt', 'w') as f:
        f.write("Olá! Este é um arquivo de teste para o sistema BitTorrent.\n" * 20)
    print("✓ Arquivo criado: teste/meu_arquivo.txt")
    
    # 2. Iniciar tracker
    print("\n2. Iniciando tracker...")
    tracker = Tracker()
    tracker_thread = threading.Thread(target=tracker.start)
    tracker_thread.daemon = True
    tracker_thread.start()
    time.sleep(1)
    print("✓ Tracker rodando em localhost:8000")
    
    # 3. Iniciar peer seeder
    print("\n3. Iniciando peer seeder...")
    seeder = Peer("SEEDER_1", port=9001)
    seeder_thread = threading.Thread(target=seeder.start)
    seeder_thread.daemon = True
    seeder_thread.start()
    time.sleep(1)
    print("✓ Seeder rodando em localhost:9001")
    
    # 4. Adicionar arquivo ao seeder
    print("\n4. Adicionando arquivo ao seeder...")
    torrent_hash = seeder.add_file('teste/meu_arquivo.txt')
    print(f"✓ Arquivo adicionado com hash: {torrent_hash}")
    
    # 5. Anunciar para o tracker
    print("\n5. Anunciando para o tracker...")
    response = seeder.announce_to_tracker(torrent_hash)
    print(f"✓ Resposta do tracker: {response}")
    
    # 6. Verificar peers no tracker
    print("\n6. Verificando peers disponíveis no tracker...")
    response = seeder.send_tracker_request({
        'action': 'get_peers',
        'torrent_hash': torrent_hash
    })
    print(f"Peers disponíveis: {response}")
    
    # 7. Iniciar peer downloader
    print("\n7. Iniciando peer downloader...")
    downloader = Peer("DOWNLOADER_1", port=9002)
    downloader_thread = threading.Thread(target=downloader.start)
    downloader_thread.daemon = True
    downloader_thread.start()
    time.sleep(1)
    print("✓ Downloader rodando em localhost:9002")
    
    # 8. Downloader consulta tracker
    print("\n8. Downloader consultando tracker...")
    response = downloader.send_tracker_request({
        'action': 'get_peers',
        'torrent_hash': torrent_hash
    })
    print(f"Peers encontrados pelo downloader: {response}")
    
    # 9. Fazer download
    print("\n9. Iniciando download...")
    os.makedirs('resultado', exist_ok=True)
    success = downloader.download_file(torrent_hash, 'resultado/arquivo_baixado.txt')
    
    if success:
        print("✓ Download concluído com sucesso!")
        
        # 10. Verificar integridade
        print("\n10. Verificando integridade...")
        with open('teste/meu_arquivo.txt', 'r') as f1:
            original = f1.read()
        with open('resultado/arquivo_baixado.txt', 'r') as f2:
            baixado = f2.read()
        
        if original == baixado:
            print("✓ Arquivos são idênticos!")
            print(f"Tamanho: {len(original)} caracteres")
        else:
            print("✗ Arquivos são diferentes!")
    else:
        print("✗ Falha no download")
    
    print("\n=== TESTE CONCLUÍDO ===")
    return seeder, downloader, torrent_hash

def teste_multiplos_peers():
    """Teste com múltiplos peers para demonstrar escalabilidade"""
    print("\n=== TESTE COM MÚLTIPLOS PEERS ===\n")
    
    # Criar arquivo maior
    print("1. Criando arquivo maior...")
    with open('teste/arquivo_grande.txt', 'w') as f:
        for i in range(100):
            f.write(f"Linha {i+1}: Este é um arquivo maior para testar múltiplos peers.\n")
    print("✓ Arquivo grande criado")
    
    # Iniciar tracker
    tracker = Tracker(port=8001)  # Porta diferente para não conflitar
    tracker_thread = threading.Thread(target=tracker.start)
    tracker_thread.daemon = True
    tracker_thread.start()
    time.sleep(1)
    print("✓ Tracker iniciado na porta 8001")
    
    # Iniciar múltiplos seeders
    seeders = []
    torrent_hash = None
    
    for i in range(3):  # 3 seeders
        print(f"\n2.{i+1} Iniciando seeder {i+1}...")
        seeder = Peer(f"SEEDER_{i+1}", port=9010+i)
        seeder.tracker_port = 8001  # Usar o tracker na porta 8001
        
        # Iniciar servidor
        seeder_thread = threading.Thread(target=seeder.start)
        seeder_thread.daemon = True
        seeder_thread.start()
        time.sleep(0.5)
        
        # Adicionar arquivo
        if i == 0:  # Apenas o primeiro seeder adiciona o arquivo
            torrent_hash = seeder.add_file('teste/arquivo_grande.txt')
            print(f"  ✓ Arquivo adicionado com hash: {torrent_hash}")
        else:
            # Outros seeders "simulam" ter o arquivo
            seeder.files[torrent_hash] = 'teste/arquivo_grande.txt'
        
        # Anunciar para tracker
        seeder.announce_to_tracker(torrent_hash)
        print(f"  ✓ Seeder {i+1} anunciado")
        
        seeders.append(seeder)
    
    # Verificar quantos peers estão disponíveis
    print(f"\n3. Verificando peers disponíveis...")
    response = seeders[0].send_tracker_request({
        'action': 'get_peers',
        'torrent_hash': torrent_hash
    })
    peers = response.get('peers', []) if response else []
    print(f"✓ {len(peers)} peers disponíveis")
    for peer in peers:
        print(f"  - {peer['peer_id']} em {peer['host']}:{peer['port']}")
    
    # Iniciar downloader
    print(f"\n4. Iniciando downloader...")
    downloader = Peer("DOWNLOADER_MULTI", port=9020)
    downloader.tracker_port = 8001
    
    downloader_thread = threading.Thread(target=downloader.start)
    downloader_thread.daemon = True
    downloader_thread.start()
    time.sleep(1)
    
    # Fazer download
    success = downloader.download_file(torrent_hash, 'resultado/arquivo_multi.txt')
    
    if success:
        print("✓ Download de múltiplos peers concluído!")
    else:
        print("✗ Falha no download")
    
    return seeders, downloader

def main():
    """Executa todos os testes"""
    # Teste básico
    seeder, downloader, hash1 = teste_passo_a_passo()
    
    # Aguardar um pouco
    print("\nAguardando 3 segundos...")
    time.sleep(3)
    
    # Teste com múltiplos peers
    seeders, downloader_multi = teste_multiplos_peers()
    
    # Manter sistema rodando
    print("\n" + "="*50)
    print("SISTEMA ATIVO - Pressione Ctrl+C para sair")
    print("Você pode verificar os arquivos em:")
    print("  - teste/          (arquivos originais)")
    print("  - resultado/      (arquivos baixados)")
    print("="*50)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nSistema encerrado pelo usuário")

if __name__ == "__main__":
    main()