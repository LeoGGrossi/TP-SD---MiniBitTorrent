# 🧹 Sistema BitTorrent Simplificado

Este projeto implementa uma versão didática e simplificada do protocolo **BitTorrent**, com o objetivo de demonstrar conceitos fundamentais de **sistemas distribuídos peer-to-peer**.

---

## 🏧 Arquitetura do Sistema

O sistema é composto por três componentes principais:

### 🔹 1. Tracker (`tracker.py`)

* Servidor central que coordena a comunicação entre peers.
* Mantém um registro de quais peers possuem quais arquivos.
* Fornece a lista de peers disponíveis para download.
* Funciona como um “índice” do sistema.

### 🔹 2. Peer (`peer.py`)

* Cliente que pode atuar como **seeder** (compartilha arquivos) ou **leecher** (baixa arquivos).
* Comunica-se com o tracker para anunciar presença e descobrir outros peers.
* Realiza a transferência direta de arquivos entre peers.
* Divide os arquivos em pedaços (pieces) para permitir download paralelo.

### 🔹 3. Teste Manual (`teste_manual.py`)

* Script de demonstração automatizada de todo o sistema.
* Cria arquivos de teste, inicia o tracker e os peers.
* Exibe o processo completo de compartilhamento e download.

---

## 💡 Conceitos Demonstrados

* **Descentralização**: transferência direta entre peers.
* **Tolerância a falhas**: o sistema segue funcionando mesmo com a saída de peers.
* **Eficiência**: uso de paralelismo no download via divisão de arquivos.
* **Descoberta de peers**: realizada de forma centralizada pelo tracker.

---

## ⚙️ Pré-requisitos

* Python 3.6 ou superior
* Bibliotecas padrão do Python: `socket`, `threading`, `json`, `hashlib`

---

## 📁 Estrutura de Arquivos

```
projeto_torrent/
├── tracker.py          # Servidor tracker
├── peer.py             # Cliente peer
├── teste_manual.py     # Demonstração automatizada
├── README.md           # Este arquivo
├── teste/              # Arquivos originais (gerados automaticamente)
└── resultado/          # Arquivos baixados (gerados automaticamente)
```

---

## ▶️ Como Executar

### ✅ Opção 1: Execução Automática (Recomendada)

```bash
python teste_manual.py
```

Este comando irá:

1. Criar arquivos de teste
2. Iniciar o tracker
3. Iniciar um peer seeder
4. Iniciar um peer downloader
5. Exibir logs do processo de download

---

### ⚙️ Opção 2: Execução Manual

#### 1. Iniciar o Tracker

```bash
python -c "from tracker import Tracker; Tracker().start()"
```

#### 2. Iniciar um Peer Seeder

```bash
python -c "
import threading, time
from peer import Peer

with open('arquivo_teste.txt', 'w') as f:
    f.write('Conteúdo do arquivo de teste\n' * 100)

peer = Peer('seeder1', port=9001)
threading.Thread(target=peer.start, daemon=True).start()
time.sleep(1)

hash_arquivo = peer.add_file('arquivo_teste.txt')
print(f'Arquivo disponível com hash: {hash_arquivo}')
input('Pressione Enter para sair...')
"
```

#### 3. Iniciar um Peer Downloader

```bash
python -c "
import threading, time
from peer import Peer

peer = Peer('downloader1', port=9002)
threading.Thread(target=peer.start, daemon=True).start()
time.sleep(1)

hash_arquivo = input('Digite o hash do torrent: ')
success = peer.download_file(hash_arquivo, 'arquivo_baixado.txt')

print('Download concluído!' if success else 'Falha no download.')
"
```

---

## 🧪 Testes

### Teste 1: Demonstração Básica

```bash
python teste_manual.py
ls teste/         # Arquivos originais
ls resultado/     # Arquivos baixados
diff teste/arquivo1.txt resultado/arquivo1_downloaded.txt
```

### Teste 2: Múltiplos Peers

Execute os comandos abaixo em terminais separados:

#### Tracker

```bash
python -c "from tracker import Tracker; Tracker().start()"
```

#### Seeder 1

```bash
python -c "
import threading, time
from peer import Peer
with open('arquivo1.txt', 'w') as f: f.write('Arquivo 1\n' * 50)
peer = Peer('seeder1', port=9001)
threading.Thread(target=peer.start, daemon=True).start()
time.sleep(1)
print('Hash:', peer.add_file('arquivo1.txt'))
input('Enter para sair...')
"
```

#### Seeder 2

```bash
python -c "
import threading, time
from peer import Peer
with open('arquivo2.txt', 'w') as f: f.write('Arquivo 2\n' * 30)
peer = Peer('seeder2', port=9002)
threading.Thread(target=peer.start, daemon=True).start()
time.sleep(1)
print('Hash:', peer.add_file('arquivo2.txt'))
input('Enter para sair...')
"
```

#### Downloader

```bash
python -c "
import threading, time
from peer import Peer
peer = Peer('downloader', port=9003)
threading.Thread(target=peer.start, daemon=True).start()
time.sleep(1)
peer.download_file('HASH_DO_ARQUIVO1', 'download1.txt')
peer.download_file('HASH_DO_ARQUIVO2', 'download2.txt')
"
```

---

## 💦 Solução de Problemas

### ⚠️ Address already in use

* Altere as portas no código (`port=8001`, `port=9001`, etc.)

### 🔌 Peers não se conectam

* Verifique se o tracker está ativo: `netstat -an | grep 8000`
* Verifique os peers: `netstat -an | grep 900[0-9]`

### ❌ Download falha

* Confirme que o seeder possui o arquivo
* Verifique se o hash está correto
* Certifique-se de que os peers estão acessíveis entre si

---

## 🚫 Limitações (Didáticas)

1. Sem persistência de estado
2. Verificação de integridade básica
3. Transferência sequencial simples
4. Apenas interface de linha de comando
5. Funciona apenas em rede local

---

## 🚀 Possíveis Extensões

* Interface web com Flask
* Banco de dados para persistência
* Suporte a protocolo UDP
* Estratégia "rarest piece first"
* Implementação de DHT (Distributed Hash Table)
* Criptografia ponta a ponta

---

## 📜 Logs

Para salvar os logs de execução:

```bash
python teste_manual.py > sistema_torrent.log 2>&1
```

---

## 📚 Conceitos de Sistemas Distribuídos

* **Arquitetura P2P**
* **Descoberta Centralizada**
* **Fragmentação de Dados**
* **Tolerância a Falhas**
* **Distribuição de Carga**
* **Protocolos de Rede (TCP)**

---

Este projeto é ideal para estudos acadêmicos e compreensão dos fundamentos do protocolo BitTorrent e redes P2P.
