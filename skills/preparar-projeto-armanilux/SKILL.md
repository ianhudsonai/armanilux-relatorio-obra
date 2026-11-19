---
name: preparar-projeto-armanilux
description: Prepara o computador de alguém da Armanilux para os relatórios de obra. Use na primeira vez, ou quando pedirem $preparar-projeto-armanilux, instalar ferramentas, mudar a pasta da Armanilux, o nome do responsável, a função, o PDF ou o nome das pastas de obra. Faz as perguntas, instala Python, FFmpeg e as bibliotecas neste computador e grava config.json.
license: MIT
metadata:
  author: Armanilux
  version: "1.0"
  idioma: pt-BR
---

# Preparar o projeto Armanilux

Esta skill roda uma vez por pessoa, ou de novo quando ela quiser mudar as preferências. Fale sempre em português, sem emoji. Não peça para a pessoa procurar arquivo nem dar dois cliques em nada.

A pasta desta skill é a pasta deste arquivo. O instalador é `scripts/instalar.ps1`.

## 1. Perguntar

Se já existir `%USERPROFILE%\.armanilux-relatorio\config.json`, leia e use os valores como sugestão. Faça estas perguntas, uma de cada vez, em português simples:

1. Você já tem uma pasta da Armanilux neste computador? Se sim, qual é o caminho? Se não, use `Documentos\Armanilux`.
2. Qual é o seu nome, e qual é a sua função? Isso entra no cabeçalho do relatório.
3. Além do Word, você quer um PDF? Sim ou não.
4. Como quer o nome da pasta de cada obra? O padrão é `{numero} - {cliente}`. Pode ser também `{cliente} - {numero}` ou `{numero}`.
5. Quer baixar agora o modelo de voz, para a primeira transcrição não esperar? Sim ou não. Diga que é um download único e que pode demorar.

Não invente resposta. Se a pessoa não souber o caminho, use o padrão.

## 2. Instalar as ferramentas

Diga uma frase: vai instalar o que falta neste computador; quando o aplicativo pedir permissão, aprove; se o Windows abrir Sim ou Não, clique em Sim.

Releia o PATH e execute o instalador desta pasta. Use `-BaixarModelo` só se a pessoa disse sim na pergunta 5.

```powershell
$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User') + ';' + "$env:LOCALAPPDATA\Microsoft\WinGet\Links"
powershell -ExecutionPolicy Bypass -File "<pasta-desta-skill>\scripts\instalar.ps1"
```

O instalador prefere `winget install Python.Python.3.12 --scope user` e o mesmo escopo para o FFmpeg. O pip fica em `%USERPROFILE%\.armanilux-relatorio\venv`. Pode rodar de novo. Se já estiver instalado, só confere.

Se terminar com erro, explique em português e pare. Não mande a pessoa atrás de um arquivo.

Quando terminar com código 0, releia o PATH na mesma sessão. Use o `PYTHON=` que o instalador imprimiu. Não peça para reiniciar o computador.

## 3. Gravar preferências e pastas

Com o Python do ambiente:

```powershell
& "$env:USERPROFILE\.armanilux-relatorio\venv\Scripts\python.exe" "<pasta-desta-skill>\scripts\preparar.py" --pasta-raiz "CAMINHO" --nome "NOME" --funcao "FUNCAO" --pdf sim --modelo "{numero} - {cliente}" --baixar-modelo nao
```

`--pdf` e `--baixar-modelo` são `sim` ou `nao`.

Isso grava `config.json`, cria a pasta escolhida, `Relatorios-de-Obra\_modelo` com as cinco subpastas, e um `LEIA-ME.txt` na pasta raiz. Rodar de novo só atualiza as preferências. Não apaga obras já existentes.

## 4. Encerrar

Diga onde ficou a pasta, o nome que vai no relatório e se o PDF foi pedido. Diga que, para cada obra, o próximo chat usa `$relatorio-cronologico-obra`.
