import time
import requests

API = "https://www.fnde.gov.br/olinda-ide/servico/DADOS_ABERTOS_SIOPE/versao/v1/odata/"


def chamar(entidade: str, ano: int, uf: str, periodo: int, select: str | None = None) -> list[dict]:
    url = f"{API}{entidade}(Ano_Consulta=@Ano_Consulta,Num_Peri=@Num_Peri,Sig_UF=@Sig_UF)"
    params = {"@Ano_Consulta": ano, "@Num_Peri": periodo, "@Sig_UF": f"'{uf}'", "$format": "json"}
    if select:
        params["$select"] = select  # reduz o volume; se o servidor recusar, refazemos sem ele

    registros, proxima, p = [], url, params
    while proxima:
        r = requests.get(proxima, params=p, timeout=60)
        if r.status_code == 400 and select:
            return chamar(entidade, ano, uf, periodo, select=None)
        r.raise_for_status()
        dados = r.json()
        registros.extend(dados.get("value", []))
        proxima = dados.get("@odata.nextLink")
        p = None
    return registros


def estaduais(entidade, ano, uf, periodo, select):
    return [r for r in chamar(entidade, ano, uf, periodo, select) if r.get("TIPO") == "Estadual"]


if __name__ == "__main__":
    print("[1] MG — linhas ESTADUAIS em Despesas_Funcao_Educacao_Siope, por ano e bimestre")
    for ano in range(2017, 2026):
        cont = []
        for per in range(1, 7):
            cont.append(len(estaduais("Despesas_Funcao_Educacao_Siope", ano, "MG", per, "TIPO,NUM_ANO,SIG_UF")))
            time.sleep(0.2)
        print(f"  {ano}: " + " | ".join(f"b{i + 1}={n}" for i, n in enumerate(cont)))

    print("\n[2] RS — mesma contagem (anos com lacuna)")
    for ano in (2018, 2019):
        cont = []
        for per in range(1, 7):
            cont.append(len(estaduais("Despesas_Funcao_Educacao_Siope", ano, "RS", per, "TIPO,NUM_ANO,SIG_UF")))
            time.sleep(0.2)
        print(f"  {ano}: " + " | ".join(f"b{i + 1}={n}" for i, n in enumerate(cont)))

    print("\n[3] MG e RS — linha ESTADUAL na entidade Dados_Gerais_Siope (período 6): gasto total em educação")
    for uf in ("MG", "RS"):
        for ano in range(2017, 2026):
            linhas = estaduais("Dados_Gerais_Siope", ano, uf, 6, "TIPO,NUM_ANO,SIG_UF,VL_DESP_PAGA_EDU,VAL_DESP_PAGA")
            if linhas:
                print(f"  {uf} {ano}: {len(linhas)} linha(s) | VL_DESP_PAGA_EDU={linhas[0].get('VL_DESP_PAGA_EDU')} | VAL_DESP_PAGA={linhas[0].get('VAL_DESP_PAGA')}")
            else:
                print(f"  {uf} {ano}: sem linha estadual")
            time.sleep(0.2)