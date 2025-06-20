# Sistema BitTorrent Simplificado

Este projeto implementa uma versão didática e simplificada do protocolo BitTorrent, demonstrando os conceitos fundamentais de sistemas distribuídos peer-to-peer.

## Arquitetura do Sistema

O sistema é composto por três componentes principais:

### 1. Tracker (`tracker.py`)
- Servidor central que coordena a comunicação entre peers
- Mantém registro de quais peers possuem quais arquivos
- Fornece lista de peers disponíveis para download
- Funciona como um "índice" do sistema

### 2. Peer (`peer.py`)
- Cliente que pode atuar como seeder (compartilha arquivos) ou leecher (baixa arquivos)
- Comunica-se com o tracker para anunciar presença e descobrir outros peers
- Comunica-se diretamente com outros peers para transferência de dados
- Divide arquivos em pedaços (pieces) para download paralelo

### 3. Teste Manual (`teste_manual.py`)
- Script de demonstração que executa todo o sistema automaticamente
- Cria arquivos de teste, inicia tracker e peers
- Demonstra o processo completo de compartilhamento e download


## Conceitos Demonstrados

- **Descentralização**: Dados são transferidos diretamente entre peers
- **Tolerância a falhas**: Sistema continua funcionando mesmo se alguns peers saírem
- **Eficiência**: Arquivos são divididos em pedaços para download paralelo
- **Descoberta de peers**: Tracker facilita a descoberta de peers com arquivos desejados

## Pré-requisitos

- Python 3.6 ou superior
- Bibliotecas padrão do Python (socket, threading, json, hashlib)

## Estrutura de Arquivos

```
projeto_torrent/
├── tracker.py      # Servidor tracker
├── peer.py         # Cliente peer
├── teste_manual.py         # Demonstração completa
├── README.md       # Este arquivo
├── teste/     # Arquivos de teste (criados automaticamente)
└── resultado/      # Arquivos baixados (criados automaticamente)
```

## Como Executar

### Opção 1: Demo Automática (Recomendada)

Execute o script de demonstração que roda tudo automaticamente:

```bash
python teste_manual.py
```

Este comando irá:
1. Criar arquivos de teste
2. Iniciar o tracker
3. Iniciar um peer seeder com arquivos para compartilhar
4. Iniciar um peer downloader que baixa os arquivos
5. Mostrar o progresso de todo o processo

### Opção 2: Execução Manual

Para entender melhor o funcionamento, você pode executar cada componente separadamente:

#### 1. Inicie o Tracker
```bash
python -c "
from tracker import Tracker
tracker = Tracker()
tracker.start()
"
```

#### 2. Inicie um Peer Seeder (Terminal 2)
```bash
python -c "
import threading
import time
from peer import Peer

# Cria arquivo de teste
with open('arquivo_teste.txt', 'w') as f:
    f.write('Conteúdo do arquivo de teste\n' * 100)

# Inicia peer
peer = Peer('seeder1', port=9001)

# Inicia servidor em thread separada
server_thread = threading.Thread(target=peer.start)
server_thread.daemon = True
server_thread.start()

time.sleep(1)

# Adiciona arquivo para compartilhamento
torrent_hash = peer.add_file('arquivo_teste.txt')
print(f'Arquivo disponível com hash: {torrent_hash}')

# Mantém peer ativo
input('Pressione Enter para sair...')
"
```

#### 3. Inicie um Peer Downloader (Terminal 3)
```bash
python -c "
import threading
import time
from peer import Peer

# Inicia peer
peer = Peer('downloader1', port=9002)

# Inicia servidor em thread separada
server_thread = threading.Thread(target=peer.start)
server_thread.daemon = True
server_thread.start()

time.sleep(1)

# Baixa arquivo (substitua HASH pelo hash mostrado pelo seeder)
torrent_hash = input('Digite o hash do torrent: ')
success = peer.download_file(torrent_hash, 'arquivo_baixado.txt')

if success:
    print('Download concluído com sucesso!')
else:
    print('Falha no download')
"
```

## Testando o Sistema

### Teste 1: Demonstração Básica
```bash
# Execute a demo automática
python teste_manual.py

# Verifique os arquivos criados
ls teste/      # Arquivos originais  
ls resultado/       # Arquivos baixados

# Compare os arquivos
diff teste/arquivo1.txt downloads/arquivo1_downloaded.txt
```

### Teste 2: Múltiplos Peers

Execute múltiplas instâncias para simular uma rede maior:

```bash
# Terminal 1: Tracker
python -c "from tracker import Tracker; Tracker().start()"

# Terminal 2: Seeder 1
python -c "
import threading, time
from peer import Peer
with open('arquivo1.txt', 'w') as f: f.write('Arquivo 1\n' * 50)
peer = Peer('seeder1', port=9001)
threading.Thread(target=peer.start, daemon=True).start()
time.sleep(1)
hash1 = peer.add_file('arquivo1.txt')
print(f'Hash: {hash1}')
input('Enter para sair...')
"

# Terminal 3: Seeder 2  
python -c "
import threading, time
from peer import Peer
with open('arquivo2.txt', 'w') as f: f.write('Arquivo 2\n' * 30)
peer = Peer('seeder2', port=9002)
threading.Thread(target=peer.start, daemon=True).start()
time.sleep(1)
hash2 = peer.add_file('arquivo2.txt')
print(f'Hash: {hash2}')
input('Enter para sair...')
"

# Terminal 4: Downloader
python -c "
import threading, time
from peer import Peer
peer = Peer('downloader', port=9003)
threading.Thread(target=peer.start, daemon=True).start()
time.sleep(1)
# Use os hashes dos seeders
peer.download_file('HASH_DO_ARQUIVO1', 'download1.txt')
peer.download_file('HASH_DO_ARQUIVO2', 'download2.txt')
"
```

## Solução de Problemas

### Erro "Address already in use"
```bash
# Mude a porta do tracker ou peer
# No código, altere port=8001 ou port=9001 para valores diferentes
```

### Peers não se conectam
```bash
# Verifique se o tracker está rodando
netstat -an | grep 8000

# Verifique se os peers estão rodando
netstat -an | grep 900[0-9]
```

### Download falha
- Verifique se o arquivo existe no seeder
- Confirme se o hash está correto
- Verifique se os peers estão na mesma rede

## Limitações (Propositais para Fins Didáticos)

1. **Sem persistência**: Dados são perdidos quando o programa encerra
2. **Sem verificação de integridade robusta**: Implementação básica de hash
3. **Sem otimizações**: Transferência sequencial simples
4. **Sem interface gráfica**: Apenas linha de comando
5. **Rede local apenas**: Não funciona através da internet sem configuração

## Extensões Possíveis

Para expandir o projeto:

1. **Interface Web**: Adicionar Flask para interface HTTP
2. **Persistência**: Salvar estado em banco de dados
3. **Protocolo UDP**: Implementar comunicação UDP para melhor performance
4. **Rarity-first**: Implementar algoritmo para baixar pedaços mais raros primeiro
5. **DHT**: Implementar Distributed Hash Table para eliminar tracker central
6. **Criptografia**: Adicionar criptografia nas comunicações

## Arquivos de Log

O sistema mostra logs no console. Para salvar em arquivo:

```bash
python teste_manual.py > sistema_torrent.log 2>&1
```

## Conceitos de Sistemas Distribuídos Demonstrados

- **P2P Architecture**: Comunicação direta entre peers
- **Centralized Discovery**: Tracker como ponto central de descoberta
- **Data Fragmentation**: Divisão de arquivos em pedaços
- **Fault Tolerance**: Sistema continua funcionando com peers saindo/entrando
- **Load Distribution**: Carga distribuída entre múltiplos peers
- **Network Protocols**: TCP para comunicação confiável

Este projeto fornece uma base sólida para entender os princípios fundamentais do BitTorrent e sistemas P2P em geral.