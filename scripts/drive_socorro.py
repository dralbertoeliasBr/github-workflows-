#!/usr/bin/env python3
"""
drive_socorro.py — recupera arquivos da lixeira do Google Drive e fecha
compartilhamentos públicos, em lote.

Feito para rodar no Cloud Shell (https://shell.cloud.google.com), que abre no
navegador do celular e já vem autenticado com a sua conta Google.

    1) Autorize o acesso ao Drive, uma vez:
         gcloud auth login --enable-gdrive-access

    2) Use:
         ./scripts/drive_socorro.py listar-lixeira
         ./scripts/drive_socorro.py listar-lixeira --midia
         ./scripts/drive_socorro.py periodo 2024
         ./scripts/drive_socorro.py datar "raio"
         ./scripts/drive_socorro.py restaurar
         ./scripts/drive_socorro.py restaurar --midia --periodo 2024
         ./scripts/drive_socorro.py listar-publicos
         ./scripts/drive_socorro.py fechar-publicos --confirmar

Nada é alterado sem um subcomando explícito. Os comandos "listar-*", "datar" e
"periodo" apenas leem.

A lixeira do Drive retém 30 dias. Passado isso a exclusão é definitiva e nenhuma
ferramenta recupera — inclusive esta.

Só usa a biblioteca padrão: não precisa instalar nada.
"""

import argparse
import json
import random
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://www.googleapis.com/drive/v3"
ESCOPO = "https://www.googleapis.com/auth/drive"
CAMPOS = "id,name,mimeType,size,createdTime,modifiedTime"

TENTATIVAS = 5          # tentativas por requisição antes de desistir
PAUSA_BASE = 1.0        # segundos; dobra a cada tentativa


# --------------------------------------------------------------- infraestrutura

class ErroFatal(Exception):
    """Erro que deve encerrar o programa com mensagem legível."""


def obter_token() -> str:
    if not shutil.which("gcloud"):
        raise ErroFatal(
            "'gcloud' não encontrado.\n"
            "Rode isto no Cloud Shell: https://shell.cloud.google.com"
        )

    # Pede o escopo de Drive explicitamente; se a versão do gcloud não aceitar
    # a flag, cai para o token padrão, que pode já trazer o escopo.
    for args in (["--scopes=" + ESCOPO], []):
        r = subprocess.run(
            ["gcloud", "auth", "print-access-token", *args],
            capture_output=True, text=True,
        )
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()

    raise ErroFatal(
        "Não foi possível obter um token de acesso.\n"
        "Autorize uma vez e repita:\n"
        "  gcloud auth login --enable-gdrive-access"
    )


def _e_limite(codigo: int, corpo: dict) -> bool:
    """Distingue excesso de requisições de uma negativa definitiva."""
    if codigo in (429, 500, 502, 503, 504):
        return True
    if codigo == 403:
        erros = (corpo.get("error") or {}).get("errors") or []
        return any(
            e.get("reason") in ("rateLimitExceeded", "userRateLimitExceeded")
            for e in erros
        )
    return False


def requisitar(token: str, caminho: str, metodo: str = "GET",
               corpo: dict | None = None, params: dict | None = None) -> dict:
    """Chama a API do Drive com retry exponencial nos erros transitórios."""
    url = f"{API}{caminho}"
    p = dict(params or {})
    p.setdefault("supportsAllDrives", "true")
    url += "?" + urllib.parse.urlencode(p)

    dados = json.dumps(corpo).encode() if corpo is not None else None
    pausa = PAUSA_BASE

    for tentativa in range(1, TENTATIVAS + 1):
        req = urllib.request.Request(url, data=dados, method=metodo)
        req.add_header("Authorization", f"Bearer {token}")
        if dados is not None:
            req.add_header("Content-Type", "application/json")

        try:
            with urllib.request.urlopen(req) as resp:
                bruto = resp.read()
                return json.loads(bruto) if bruto else {}

        except urllib.error.HTTPError as err:
            try:
                detalhe = json.loads(err.read() or b"{}")
            except json.JSONDecodeError:
                detalhe = {}
            msg = (detalhe.get("error") or {}).get("message", err.reason)

            if err.code in (401, 403) and not _e_limite(err.code, detalhe):
                if "insufficient" in str(msg).lower() or err.code == 401:
                    raise ErroFatal(
                        "O token não tem permissão de Drive.\n"
                        "Autorize uma vez e repita o comando:\n"
                        "  gcloud auth login --enable-gdrive-access"
                    ) from None

            if _e_limite(err.code, detalhe) and tentativa < TENTATIVAS:
                espera = pausa + random.uniform(0, 0.4)
                print(f"    (limite da API; nova tentativa em {espera:.1f}s)",
                      file=sys.stderr)
                time.sleep(espera)
                pausa *= 2
                continue

            raise ErroFatal(f"API do Drive respondeu {err.code}: {msg}") from None

        except urllib.error.URLError as err:
            if tentativa < TENTATIVAS:
                time.sleep(pausa)
                pausa *= 2
                continue
            raise ErroFatal(f"Falha de rede: {err.reason}") from None

    raise ErroFatal("Esgotadas as tentativas contra a API do Drive.")


def listar(token: str, consulta: str) -> list[dict]:
    """Percorre todas as páginas de files.list e devolve a lista completa."""
    itens: list[dict] = []
    pagina_token = None

    while True:
        params = {
            "q": consulta,
            "pageSize": "1000",
            "fields": f"nextPageToken,files({CAMPOS})",
            "includeItemsFromAllDrives": "true",
        }
        if pagina_token:
            params["pageToken"] = pagina_token

        d = requisitar(token, "/files", params=params)
        itens.extend(d.get("files", []))

        pagina_token = d.get("nextPageToken")
        if not pagina_token:
            return itens


# ------------------------------------------------------------------ consultas

def escapar(valor: str) -> str:
    """Escapa aspas simples para a sintaxe de busca do Drive."""
    return valor.replace("\\", "\\\\").replace("'", "\\'")


def montar_consulta(lixeira: bool | None = None, midia: bool = False,
                    ano: int | None = None, nome: str | None = None,
                    publico: bool = False) -> str:
    partes = []
    if lixeira is not None:
        partes.append(f"trashed = {'true' if lixeira else 'false'}")
    if midia:
        partes.append("(mimeType contains 'image/' or mimeType contains 'video/')")
    if ano is not None:
        partes.append(f"createdTime >= '{ano}-01-01T00:00:00'")
        partes.append(f"createdTime < '{ano + 1}-01-01T00:00:00'")
    if nome:
        partes.append(f"name contains '{escapar(nome)}'")
    if publico:
        partes.append("visibility = 'anyoneWithLink'")
    return " and ".join(partes) if partes else "trashed = false"


# ------------------------------------------------------------------ formatação

def humano(bytes_: str | int | None) -> str:
    try:
        n = float(bytes_)
    except (TypeError, ValueError):
        return "-"
    for u in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.0f}{u}"
        n /= 1024
    return f"{n:.1f}PB"


def marca(item: dict) -> str:
    t = item.get("mimeType", "")
    if t == "application/vnd.google-apps.folder":
        return "PA"
    if t.startswith("image/"):
        return "IM"
    if t.startswith("video/"):
        return "VD"
    if t == "application/pdf":
        return "PD"
    return "  "


def data(item: dict, campo: str = "createdTime") -> str:
    return (item.get(campo) or "")[:10] or "-"


def total_bytes(itens: list[dict]) -> int:
    soma = 0
    for i in itens:
        try:
            soma += int(i.get("size") or 0)
        except ValueError:
            pass
    return soma


# --------------------------------------------------------------------- ações

def acao_listar_lixeira(token, args):
    itens = listar(token, montar_consulta(lixeira=True, midia=args.midia,
                                          ano=args.periodo))
    print("Lixeira" + (" · apenas fotos e vídeos" if args.midia else "")
          + (f" · criados em {args.periodo}" if args.periodo else ""))
    print()

    for i in sorted(itens, key=lambda x: x.get("createdTime") or ""):
        print(f"  criado {data(i)}  {marca(i)}  {humano(i.get('size')):>9}  {i['name']}")

    print("\n" + "=" * 44)
    if not itens:
        print("A lixeira está vazia para esse filtro.")
        print("\nSe os arquivos sumiram há mais de 30 dias, a exclusão já é")
        print("definitiva e não há o que restaurar.")
        return 2

    print(f"{len(itens)} item(ns) · {humano(total_bytes(itens))} recuperáveis")
    print("\nPara trazer de volta:")
    print(f"  {sys.argv[0]} restaurar" + (" --midia" if args.midia else "")
          + (f" --periodo {args.periodo}" if args.periodo else ""))
    return 0


def acao_periodo(token, args):
    itens = listar(token, montar_consulta(ano=args.ano))
    print(f"Tudo criado em {args.ano} (inclui o que está na lixeira)\n")

    imagens = 0
    for i in sorted(itens, key=lambda x: x.get("createdTime") or ""):
        if i.get("mimeType", "").startswith("image/"):
            imagens += 1
        print(f"  {data(i)}  {marca(i)}  {humano(i.get('size')):>9}  {i['name']}")

    print("\n" + "=" * 44)
    if not itens:
        print(f"Nada criado em {args.ano} foi encontrado.")
        return 2

    print(f"{len(itens)} item(ns) de {args.ano} · {imagens} imagem(ns)"
          f" · {humano(total_bytes(itens))}")
    print("\nIM=imagem  VD=vídeo  PA=pasta  PD=pdf")
    print("\nA data à esquerda é o createdTime do próprio Google. Ela não muda")
    print("por edição posterior e sobrevive à restauração da lixeira.")
    return 0


def acao_datar(token, args):
    itens = listar(token, montar_consulta(nome=args.termo))
    print(f"Procurando por: {args.termo}")
    print("(inclui itens na lixeira)\n")

    for i in sorted(itens, key=lambda x: x.get("createdTime") or ""):
        print(f"  criado {data(i)}  modificado {data(i, 'modifiedTime')}"
              f"  {marca(i)}  {i['name']}")

    print("\n" + "=" * 44)
    if not itens:
        print("Nada encontrado com esse termo.")
        return 2

    print(f"{len(itens)} item(ns).")
    print("\nA data de criação vem dos metadados do próprio Google, não do nome")
    print("nem do conteúdo. Ela acompanha o arquivo depois de restaurado e não")
    print("muda por edição posterior.")
    return 0


def acao_restaurar(token, args):
    itens = listar(token, montar_consulta(lixeira=True, midia=args.midia,
                                          ano=args.periodo))
    if not itens:
        print("Nada na lixeira para esse filtro.")
        return 2

    print(f"Restaurando {len(itens)} item(ns)"
          + (" · apenas fotos e vídeos" if args.midia else "")
          + (f" · criados em {args.periodo}" if args.periodo else ""))
    print()

    ok = falhas = 0
    for i in itens:
        try:
            requisitar(token, f"/files/{i['id']}", metodo="PATCH",
                       corpo={"trashed": False})
            ok += 1
            print(f"  ok       {i['name']}")
        except ErroFatal as e:
            falhas += 1
            print(f"  FALHOU   {i['name']}  ({e})")

    print("\n" + "=" * 44)
    print(f"restaurados: {ok}")
    if falhas:
        print(f"falhas:      {falhas}")
    if ok:
        print("\nOs arquivos voltaram para as pastas de origem.")
    return 0 if ok else 1


def acao_listar_publicos(token, args):
    itens = listar(token, montar_consulta(publico=True))
    print("Acessível por link público\n")

    pastas = 0
    for i in sorted(itens, key=lambda x: (marca(x) != "PA", x["name"])):
        if marca(i) == "PA":
            pastas += 1
        print(f"  {marca(i)}  criado {data(i)}  {i['name']}")

    print("\n" + "=" * 44)
    if not itens:
        print("Nada está compartilhado por link público.")
        return 0

    print(f"{len(itens)} item(ns) acessível(is) a qualquer pessoa com o link"
          f" · {pastas} pasta(s)")
    print("\nFechar as PASTAS resolve o conteúdo delas junto, por herança.")
    print("\nPara fechar todos:")
    print(f"  {sys.argv[0]} fechar-publicos --confirmar")
    return 0


def acao_fechar_publicos(token, args):
    if not args.confirmar:
        print("Este comando remove o acesso público de TODOS os itens listados em:")
        print(f"  {sys.argv[0]} listar-publicos")
        print("\nLinks que você compartilhou de propósito param de funcionar.")
        print("Revise a lista antes. Para prosseguir:")
        print(f"  {sys.argv[0]} fechar-publicos --confirmar")
        return 2

    itens = listar(token, montar_consulta(publico=True))
    if not itens:
        print("Nada está compartilhado por link público.")
        return 0

    print(f"Removendo acesso público de {len(itens)} item(ns)\n")

    ok = falhas = pulados = 0
    for i in itens:
        try:
            perms = requisitar(token, f"/files/{i['id']}/permissions",
                               params={"fields": "permissions(id,type)"})
            pid = next((p["id"] for p in perms.get("permissions", [])
                        if p.get("type") == "anyone"), None)
            if not pid:
                pulados += 1
                print(f"  pulado   {i['name']} (sem permissão pública)")
                continue

            requisitar(token, f"/files/{i['id']}/permissions/{pid}",
                       metodo="DELETE")
            ok += 1
            print(f"  fechado  {i['name']}")
        except ErroFatal as e:
            falhas += 1
            print(f"  FALHOU   {i['name']}  ({e})")

    print("\n" + "=" * 44)
    print(f"fechados: {ok}")
    if pulados:
        print(f"pulados:  {pulados}")
    if falhas:
        print(f"falhas:   {falhas}")
    print("\nAtenção: fechar o link impede acesso NOVO. Quem já baixou o")
    print("conteúdo continua com a cópia — isso nenhuma ferramenta desfaz.")
    return 0


# ---------------------------------------------------------------------- rotas

def main() -> int:
    p = argparse.ArgumentParser(
        prog="drive_socorro.py",
        description="Recupera a lixeira do Google Drive e fecha "
                    "compartilhamentos públicos, em lote.",
        epilog="Autorize uma vez: gcloud auth login --enable-gdrive-access",
    )
    sub = p.add_subparsers(dest="comando", required=True)

    def com_filtros(sp):
        sp.add_argument("--midia", action="store_true",
                        help="apenas fotos e vídeos")
        sp.add_argument("--periodo", type=int, metavar="ANO",
                        help="apenas itens criados nesse ano")
        return sp

    com_filtros(sub.add_parser("listar-lixeira", help="mostra a lixeira"))
    com_filtros(sub.add_parser("restaurar", help="tira da lixeira"))

    sp = sub.add_parser("periodo", help="tudo criado em um ano")
    sp.add_argument("ano", type=int)

    sp = sub.add_parser("datar", help="procura por nome e mostra as datas")
    sp.add_argument("termo")

    sub.add_parser("listar-publicos", help="o que está acessível por link")

    sp = sub.add_parser("fechar-publicos", help="remove o acesso por link")
    sp.add_argument("--confirmar", action="store_true")

    args = p.parse_args()

    acoes = {
        "listar-lixeira": acao_listar_lixeira,
        "restaurar": acao_restaurar,
        "periodo": acao_periodo,
        "datar": acao_datar,
        "listar-publicos": acao_listar_publicos,
        "fechar-publicos": acao_fechar_publicos,
    }

    # fechar-publicos sem --confirmar não precisa de token: só explica.
    if args.comando == "fechar-publicos" and not args.confirmar:
        return acao_fechar_publicos(None, args)

    try:
        return acoes[args.comando](obter_token(), args)
    except ErroFatal as e:
        print(f"\nERRO: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrompido.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
