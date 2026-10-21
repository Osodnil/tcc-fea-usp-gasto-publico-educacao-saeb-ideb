import requests

API_BASE = "https://www.fnde.gov.br/olinda-ide/servico/DADOS_ABERTOS_SIOPE/versao/v1/odata/"
ENTIDADE = "Dados_Gerais_Siope"


def checar_df(ano: int) -> None:
    url = f"{API_BASE}{ENTIDADE}(Ano_Consulta=@Ano_Consulta,Num_Peri=@Num_Peri,Sig_UF=@Sig_UF)"
    params = {
        "@Ano_Consulta": ano,
        "@Num_Peri": 6,
        "@Sig_UF": "'DF'",
        "$format": "json",
    }
    resp = requests.get(url, params=params, timeout=30)
    dados = resp.json().get("value", []) if resp.status_code == 200 else []

    print(f"\n[{ano}] {len(dados)} registro(s) brutos para DF")
    for registro in dados:
        print(f"  TIPO={registro.get('TIPO')} | COD_MUNI={registro.get('COD_MUNI')} | NOM_MUNI={registro.get('NOM_MUNI')}")


if __name__ == "__main__":
    for ano in range(2017, 2026):
        checar_df(ano)