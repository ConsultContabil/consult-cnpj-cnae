import re
import emoji
from flask import Flask, render_template, request
import psycopg2
import requests
# from bs4 import BeautifulSoup
from emoji import emojize

app = Flask(__name__)

def connect_to_database():
    # DATABASE_URL = 'postgres://cruabhpyxfijeb:f6284d7263b8aca591f16efbb54a0dc8b45e7cfb9d3d80c2a1f9d505e2d16cf4@ec2-23-22-172-65.compute-1.amazonaws.com:5432/dchehg23gti1nq'
    DATABASE_URL = "postgresql://postgres:1234@34.151.216.54:5432/table?sslmode=require"
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    return conn

def consultar_cnpj_risco(cnpj):
    url = f"https://www.receitaws.com.br/v1/cnpj/{cnpj}"
    response = requests.get(url)
    
    if response.status_code == 200:
        try:
            data = response.json()
            atividades = data.get("atividade_principal", []) + data.get("atividades_secundarias", [])
            cnaes = [atividade.get("code", "")[:10] for atividade in atividades]
            nome_empresa = data.get("nome", "")
            
            return cnaes, nome_empresa  # Retorna tanto os CNAEs quanto o nome da empresa
        except ValueError:
            return render_template('error.html'), ""
    else:
        return None, ""

def obter_cnaes_desejados_risco():
    conn = connect_to_database()
    cursor = conn.cursor()
    cursor.execute('SELECT LEFT(cnae, 7), grau_risco FROM app_controledispensacnaes')
    rows = cursor.fetchall()
    cnaes_desejados = {row[0]: row[1] for row in rows}
    # print(cnaes_desejados)
    return cnaes_desejados

def obter_cnaes_dispensados():
    conn = connect_to_database()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM app_controledispensacnaes')
    rows = cursor.fetchall()
    cnaes_desejados = []
    for row in rows:
        cnae = row[1]
        cnae = formatar_cnae(str(cnae))
        descricao = row[2]
        licenciatura_teresina = row[5]
        condicao_licenciatura = row[6]
        
        # risco_ambiental = row[2]
        # risco_sanitario = row[3]
        # baixo_risco_a = row[4]
        # cnaes_desejados.append((cnae, descricao, risco_ambiental, risco_sanitario, baixo_risco_a))
        cnaes_desejados.append((cnae, descricao, condicao_licenciatura, licenciatura_teresina))
    return cnaes_desejados

def obter_grau_risco_do_banco_de_dados(cnae):
    conn = connect_to_database()
    cursor = conn.cursor()
    cursor.execute('SELECT cnae, descricao, grau_risco FROM app_controledispensacnaes WHERE cnae = %s', (cnae,))
    rows = cursor.fetchall()
    for row in rows:
        # print(row[0], row[1], row[2])
        cnae = row[0]
        descricao = row[1]
        grau_risco = row[2]
        if not descricao:
            descricao = ''
    return descricao

def obter_cnaes_desejados_ie():
    conn = connect_to_database()
    cursor = conn.cursor()
    cursor.execute('SELECT cnae, obrigatoriedade_ie FROM app_controledispensacnaes')
    rows = cursor.fetchall()
    cnaes_desejados = []
    for row in rows:
        cnae = row[0]
        status = row[1]
        cnaes_desejados.append((cnae, status))
    return cnaes_desejados

def verificar_status_cnaes_api(cnaes_api):
    conn = connect_to_database()
    cursor = conn.cursor()

    cnaes_desejados = obter_cnaes_desejados_ie() # Lista de CNAEs desejados do banco de dados
    # Convertendo os CNAEs do banco de dados para strings para comparação
    cnaes_desejados_str = [str(cnae[0]) for cnae in cnaes_desejados]

    status_cnaes = []

    idx = 0  # Variável para iterar sobre os elementos da lista cnaes_api
    while idx < len(cnaes_api):
        cnae = cnaes_api[idx]
        atividade = cnaes_api[idx + 1]  # Atividade correspondente ao cnae
        idx += 2  # Incrementa o índice para a próxima iteração

        # Verificar se o CNAE obtido está na lista de CNAEs desejados do banco de dados
        if cnae in cnaes_desejados_str:
            # Obter o status do CNAE correspondente
            status = [c[1] for c in cnaes_desejados if str(c[0]) == cnae][0]
            print(cnae, status)
            if status.lower() == 'sim':
                ctrl = 1
                resultado = "Necessita"
            elif status.lower() == 'não':
                ctrl = 0
                resultado = "Não necessita"
            elif status.lower() == 'sim/não':
                ctrl = 2
                resultado = "Depende"
            else:
                resultado = "Erro ao processar requisição"
            cnae = formatar_cnae(cnae)
            status_cnaes.append((cnae, resultado, atividade, ctrl))
        else:
            status_cnaes.append((cnae, "Não encontrado no banco de dados", atividade))

    conn.close()
    return status_cnaes

def consultar_atividade(cnae):
    url = f"https://compras.dados.gov.br/fornecedores/doc/cnae/{cnae}.json"
    response = requests.get(url)
    
    if response.status_code == 200:
        try:
            data = response.json()['descricao']
            return data
        except KeyError:
            # Se não encontrou a chave 'descricao', pode ser uma resposta vazia, então consideramos como não encontrado
            return render_template('error.html')
    elif response.status_code == 404:
        return 'erro'
    else:
        return render_template('error.html')

def formatar_cnae(cnae):
    # Remove caracteres não numéricos do CNAE
    cnae = re.sub(r'\D', '', cnae)

    # Aplica a formatação desejada
    cnae_formatado = re.sub(r'^(\d{2})(\d{2})(\d{1})(\d{2})$', r'\1.\2-\3/\4', cnae)

    return cnae_formatado

def desformata_cnae(cnae_formatado):
    # Remove caracteres não numéricos do CNAE formatado
    cnae_desformatado = re.sub(r'\D', '', cnae_formatado)
    return cnae_desformatado

def formatar_cnpj(cnpj):
    cnpj_formatado = '{}.{}.{}/{}-{}'.format(cnpj[:2], cnpj[2:5], cnpj[5:8], cnpj[8:12], cnpj[12:])
    return cnpj_formatado

def desformatar_cnpj(cnpj):
    cnpj = cnpj.replace('.', '')
    cnpj = cnpj.replace('/', '')
    cnpj = cnpj.replace('-', '')
    cnpj = cnpj[:2] + cnpj[2:5] + cnpj[5:8] + cnpj[8:12] + cnpj[12:]
    return cnpj

def consultar_cnpj_cadastur(cnpj):
    url = f"https://publica.cnpj.ws/cnpj/{cnpj}"
    #consultar a UF aqui pra realizar o passo 3
    response = requests.get(url)
    if response.status_code == 200:
        try:
            data = response.json()
            return data
        except ValueError:
            return render_template('error.html')
    elif response.status_code == 404:
        return 'erro'

def obter_cnaes_desejados_cadastur():
    conn = connect_to_database()
    cursor = conn.cursor()
    cursor.execute('SELECT cnae, descricao, atividade_turistica FROM app_controledispensacnaes')
    rows = cursor.fetchall()
    cnaes_desejados = []
    for row in rows:
        cnae = row[0]
        cnaef = desformata_cnae(cnae)
        descricao = row[1]
        atividade = row[2]
        if atividade != '':
            cnaes_desejados.append((cnaef, descricao, atividade))
    return cnaes_desejados

def consultar_cnpj(cnpj):
    url = f"https://www.receitaws.com.br/v1/cnpj/{cnpj}"
    response = requests.get(url)
    print(response.status_code)
    if response.status_code == 200:
        try:
            data = response.json()
            return data
        except ValueError:
            return render_template('error.html')
    elif response.status_code == 404:
        return 'message'

def obter_atividade_por_cnae(cnae, table):
    rows = table.find_all('tr')
    for row in rows:
        cells = row.find_all('td')
        if len(cells) >= 2:
            cnae_atual = cells[0].text.strip()
            cnae_atual = desformata_cnae(cnae_atual)
            atividade = cells[1].text.strip()

            if cnae_atual == cnae:
                return atividade

@app.route('/verificar_risco', methods=['post'])
def verificar_risco():
    cnpj = request.form['cnpj']
    if not cnpj:
        return render_template('index_cnpj.html', resultado='Insira o cnpj antes de consultar', error_popup=True)
    cnpj = desformatar_cnpj(cnpj)
    cnaes_cnpj, nome_empresa = consultar_cnpj_risco(cnpj)

    if not cnaes_cnpj:
        return render_template('index_cnpj.html', resultado='CNPJ inválido', error_popup=True)

    cnaes_banco = obter_cnaes_desejados_risco()  # Recupere todos os CNAEs do banco de dados

    cnaes_encontrados = []
    dispensa_licenciamento = True

    ctrl_dict = {}  # Dicionário para armazenar o grau de risco para cada CNAE

    for cnae_cnpj in cnaes_cnpj:
        cnae_cnpj_inicio = cnae_cnpj # Pegue os primeiros 7 dígitos do CNAE do CNPJ
        cnae_encontrado = False
        grau_risco = 0  # Valor padrão é 0

        for cnae_banco, grau in cnaes_banco.items():
            cnae_banco_inicio = cnae_banco[:7]  # Pegue os primeiros 7 dígitos do CNAE do banco
            
            if desformata_cnae(cnae_cnpj_inicio) == cnae_banco_inicio:
                cnae_encontrado = True
                grau_risco = grau  # Obtenha o grau de risco do banco de dados
                break

        status = 'Habilitado' if cnae_encontrado else 'Não habilitado'
        ctrl_dict[cnae_cnpj_inicio] = grau_risco
        descricao = obter_grau_risco_do_banco_de_dados(desformata_cnae(cnae_cnpj_inicio))  # Passe o código correto do CNAE
        cnaes_encontrados.append((cnae_cnpj_inicio, descricao, grau_risco))
        result = 0
        if not cnae_encontrado:
            result = 1
            dispensa_licenciamento = False
    
    legis = 'Cnaes consultados segundo a Norma Regulamentadora No. 4 (NR-4) atualizada em 07/07/2023 10h24.'
    link = 'https://www.gov.br/trabalho-e-emprego/pt-br/acesso-a-informacao/participacao-social/conselhos-e-orgaos-colegiados/comissao-tripartite-partitaria-permanente/arquivos/normas-regulamentadoras/nr-04-atualizada-2022-2-1.pdf'
    coluna = 'Grau de risco'
    if dispensa_licenciamento:
        cnpj = formatar_cnpj(cnpj)
        return render_template('resultados_nr04.html', result=result, resultado=None, nome_empresa=nome_empresa, cnaes_encontrados=cnaes_encontrados, cnpj=cnpj, ctrl_dict=ctrl_dict, legislacao=legis, ctrl_cor=None, coluna=coluna, link=link)
    else:
        cnpj = formatar_cnpj(cnpj)
        return render_template('resultados_nr04.html', result=result, resultado=None, nome_empresa=nome_empresa, cnaes_encontrados=cnaes_encontrados, cnpj=cnpj, ctrl_dict=ctrl_dict, legislacao=legis, ctrl_cor=None, coluna=coluna, link=link)

@app.route('/verificar_cadastur', methods=['POST'])
def verificar_cadastur():
    cnpj = request.form['cnpj']
    if not cnpj:
        error_message = 'CNPJ não foi inserido'
        return render_template('index_cnpj.html', resultado=error_message, error_popup=True)
    else:
        cnpj = desformatar_cnpj(cnpj)
        data = consultar_cnpj_cadastur(cnpj)
        if 'erro' in data:
            error_message = 'CNPJ inválido'
            return render_template('index_cnpj.html', resultado=error_message, error_popup=True)
        else:
            nome_empresa = data['razao_social']
            estabelecimento = [data['estabelecimento']]
            for cnaes in estabelecimento:

                ativ_princ = cnaes['atividade_principal'] 
                ativ_sec = cnaes['atividades_secundarias']

            cnaes_encontrados = []

            cnaes_desejados = obter_cnaes_desejados_cadastur() # Converta os CNAEs desejados em um conjunto
            # cnaes_desejados = []

            dispensa_licenciamento = True  # Comece com True e defina como False se algum CNAE não estiver na lista
            
            cnpj1 = formatar_cnpj(cnpj)
            ctrl_dict = {}  # Dicionário para armazenar o valor de ctrl para cada cnae
            ativ_princ = [ativ_princ]
            for cnae_data in ativ_princ:
                cnae = cnae_data['id']
                nome = cnae_data['descricao']
                # Adicione instruções de impressão para depuração

                # Verifique se o CNAE está na lista de CNAEs desejados
                if cnae in [c[0] for c in cnaes_desejados]:
                    status = 'Habilitado' + emoji.emojize(':check_mark:')
                    atividade = [c[2] for c in cnaes_desejados if c[0] == cnae][0]
                else:
                    status = 'Não habilitado' + emoji.emojize(':cross_mark:')
                    atividade = ''
                    dispensa_licenciamento = False  # Se um CNAE não estiver na lista, definir como False
                cnaef = formatar_cnae(cnae)
                ctrl_dict[cnaef] = 1 if status == 'Habilitado' + emoji.emojize(':check_mark:') else 2
                

                cnaes_encontrados.append((cnaef, nome, status, atividade))
            for cnae_data in ativ_sec:
                cnae = cnae_data['id']
                nome = cnae_data['descricao']
 
                # Adicione instruções de impressão para depuração

                # Verifique se o CNAE está na lista de CNAEs desejados
                if cnae in [c[0] for c in cnaes_desejados]:
                    status = 'Habilitado' + emoji.emojize(':check_mark:')
                    atividade = [c[2] for c in cnaes_desejados if c[0] == cnae][0]
                else:
                    status = 'Não habilitado' + emoji.emojize(':cross_mark:')
                    atividade = ''
                    dispensa_licenciamento = False  # Se um CNAE não estiver na lista, definir como False
                cnaef = formatar_cnae(cnae)
                ctrl_dict[cnaef] = 1 if status == 'Habilitado' + emoji.emojize(':check_mark:') else 2
                
                cnaes_encontrados.append((cnaef, nome, status, atividade))
            
            if dispensa_licenciamento:
                return render_template('resultados_cadastur.html', resultado=None, cnaes_encontrados=cnaes_encontrados, nome_empresa=nome_empresa, cnpj=cnpj1, ctrl_dict=ctrl_dict)
            else:
                return render_template('resultados_cadastur.html', resultado=None, nome_empresa=nome_empresa, cnaes_encontrados=cnaes_encontrados, cnpj=cnpj1, ctrl_dict=ctrl_dict)

@app.route('/verificar_dispensa_ie', methods=['POST'])
def verificar_dispensa_ie():
    cnpj = request.form['cnpj']
    if not cnpj:
        error_message = 'CNPJ não foi inserido'
        return render_template('index_cnpj.html', resultado=error_message, error_popup=True)
    else:
        cnpj = desformatar_cnpj(cnpj)
        data = consultar_cnpj_cadastur(cnpj)
        # print(data)
        if 'erro' in data:
            error_message = 'CNPJ incorreto ou recém-criado, dados indisponíveis'
            return render_template('index_cnpj.html', resultado=error_message, error_popup=True)
        else:
            nome_empresa = data['razao_social']
            estabelecimento = [data['estabelecimento']]
            for estabelecimento_item in estabelecimento:
                ie = None
                ie_li = estabelecimento_item['inscricoes_estaduais']
                for ies in ie_li:
                    ie = ies['inscricao_estadual']
            cnaes_desejados = obter_cnaes_desejados_ie()  # Obtém os CNAEs desejados do banco de dados
            cnaes_api = []  # Lista para armazenar os CNAEs do estabelecimento
            
            for cnaes in estabelecimento:
                ativ_princ = cnaes['atividade_principal']
                ativ_sec = cnaes['atividades_secundarias']
                cnaes_api.append(ativ_princ['id'])  # Adiciona o ID da atividade principal
                cnaes_api.append(ativ_princ['descricao'])
                for atividade in ativ_sec:
                    cnaes_api.append(atividade['id'])
                    cnaes_api.append(atividade['descricao'])
            # print(cnaes_api)
            status_cnaes = verificar_status_cnaes_api(cnaes_api)
            # print(status_cnaes)
            cnpj = formatar_cnpj(cnpj)
            return render_template('resultados_ie.html', resultado=None, nome_empresa=nome_empresa, cnpj=cnpj, ie=ie, status_cnaes=status_cnaes)

@app.route('/verificar_dispensa', methods=['POST'])
def verificar_dispensa_licenciamento():
    cnpj = request.form['cnpj']
    # print(f'cnpj:{cnpj}')
    if cnpj == '':
        return render_template('index_cnpj.html', resultado='Insira o CNPJ', error_popup=True)
    
    cnpj = desformatar_cnpj(cnpj)
    data = consultar_cnpj(cnpj)

    if 'message' in data:
        return render_template('index_cnpj.html', resultado='CNPJ inválido', error_popup=True)

    nome_empresa = data['nome']
    cnaes = [item for item in data['atividade_principal'] + data['atividades_secundarias'] if item['code'] != '00.00-0-00']

    cnaes_encontrados = []
    # print(cnaes)
    cnaes_desejados = obter_cnaes_dispensados()

    dispensa_licenciamento = True
    status = ''
    cnpj1 = formatar_cnpj(cnpj)
    ctrl_dict = {}  # Dicionário para armazenar o valor de ctrl para cada cnae
    for cnae_data in cnaes:
        cnae = cnae_data['code']
        cnae = desformata_cnae(cnae)
        # print(cnae)
        cnae = formatar_cnae(cnae)
        # print(cnae)
        nome = cnae_data['text']
        condicao = None
        condicao2 = None
        for cnae_desejado in cnaes_desejados:
            # print(cnae, cnae_desejado[0])
            if cnae == cnae_desejado[0]:
                if 'Alto risco' in cnae_desejado[2]:
                    dispensa_licenciamento = False 
                condicao = cnae_desejado[2]
                status = cnae_desejado[3]
                # print(cnae, cnae_desejado[0])
                # descricao_desejada = cnae_desejado[1]  # Aqui você acessa a descrição do CNAE desejado
                # risco_ambiental_desejado = cnae_desejado[2]  # Aqui você acessa o risco ambiental do CNAE desejado
                # risco_sanitario_desejado = cnae_desejado[3]  # Aqui você acessa o risco sanitário do CNAE desejado
                # baixo_risco_a_desejado = cnae_desejado[3]  # Aqui você acessa o baixo risco A do CNAE desejado
                # # Agora você pode comparar os valores desejados com os valores obtidos dos códigos CNAE
                # if baixo_risco_a_desejado == None:    
                #     if risco_ambiental_desejado == 'Dispensa de Licença Ambiental de Operação (LO)' and risco_sanitario_desejado == 'Dispensa de Licença Sanitária':  # Comparação dos valores
                #         status = 'Dispensado' + emoji.emojize(':check_mark:')
                #         ctrl_dict[cnae] = 1
                #     elif risco_ambiental_desejado == 'Alto Risco' and risco_sanitario_desejado == 'Alto Risco':
                #         status = 'Não dispensado' + emoji.emojize(':cross_mark:')
                #         dispensa_licenciamento = False
                #     elif risco_ambiental_desejado == 'Alto Risco' and risco_sanitario_desejado == 'Dispensa de Licença Sanitária':
                #         status = 'Não dispensado' + emoji.emojize(':cross_mark:')
                #         condicao = 'Alto risco ambiental'
                #         dispensa_licenciamento = False
                #     elif risco_ambiental_desejado == 'Dispensa de Licença Ambiental de Operação (LO)'  and risco_sanitario_desejado == 'Alto Risco':
                #         status = 'Não dispensado' + emoji.emojize(':cross_mark:')
                #         condicao = 'Alto risco sanitário'
                #         dispensa_licenciamento = False
                #     elif risco_ambiental_desejado != 'Alto Risco' and risco_sanitario_desejado == 'Alto Risco':
                #         if risco_ambiental_desejado != 'Dispensa de Licença Ambiental de Operação (LO)':
                #             status = 'Depende'
                #             condicao = risco_ambiental_desejado
                #             dispensa_licenciamento = None
                #             ctrl_dict[cnae] = 2
                #     elif risco_ambiental_desejado != 'Alto Risco' and risco_sanitario_desejado == 'Dispensa de Licença Sanitária':
                #         if risco_ambiental_desejado != 'Dispensa de Licença Ambiental de Operação (LO)':
                #             status = 'Depende'
                #             condicao = risco_ambiental_desejado
                #             dispensa_licenciamento = None
                #             ctrl_dict[cnae] = 2
                #     elif risco_ambiental_desejado == 'Dispensa de Licença Ambiental de Operação (LO)' and risco_sanitario_desejado != 'Alto Risco':
                #         if risco_sanitario_desejado != 'Dispensa de Licença Sanitária':
                #             status = 'Depende'
                #             condicao = risco_sanitario_desejado
                #             dispensa_licenciamento = None
                #             ctrl_dict[cnae] = 2
                #     elif risco_ambiental_desejado == 'Alto Risco' and risco_sanitario_desejado != 'Alto Risco':
                #         if risco_sanitario_desejado != 'Dispensa de Licença Sanitária':
                #             status = 'Depende'
                #             condicao = risco_sanitario_desejado
                #             dispensa_licenciamento = None
                #             ctrl_dict[cnae] = 2
                #     elif risco_sanitario_desejado != 'Alto Risco' and risco_ambiental_desejado != 'Alto Risco':
                #         if risco_ambiental_desejado != 'Dispensa de Licença Ambiental de Operação (LO)' and risco_sanitario_desejado != 'Dispensa de Licença Sanitária':
                #             status = 'Não dispensado' + emoji.emojize(':cross_mark:')
                #             condicao = risco_ambiental_desejado
                #             condicao2 = risco_sanitario_desejado
                #             dispensa_licenciamento = False
                #     else:
                #         status = 'Não dispensado' + emoji.emojize(':cross_mark:')
                #         dispensa_licenciamento = False
                # elif baixo_risco_a_desejado == '***':
                #     status = 'Dispensado' + emoji.emojize(':check_mark:')
                #     ctrl_dict[cnae] = 1
                # else:
                #     status = 'Depende'
                #     condicao = baixo_risco_a_desejado
                #     dispensa_licenciamento = None
                #     ctrl_dict[cnae] = 2
                # break
            # else:
            #     status = 'Não dispensado' + emoji.emojize(':cross_mark:')
            #     dispensa_licenciamento = False
    
        cnaes_encontrados.append((cnae, nome, status, condicao, condicao2))

        
    coluna = 'Status'
    legis = 'Cnaes consultados segundo o Decreto Nº 24861 DE 26/09/2023'
    link = 'https://www.legisweb.com.br/legislacao/?id=450184#:~:text=Fixa%20as%20classifica%C3%A7%C3%B5es%20de%20risco,Complementar%20Municipal%20N%C2%BA%205788%2F2022.&text=c%C3%B3digos%20da%20CNAE.&text=eventual%20Alvar%C3%A1%20de%20Funcionamento%20e,TLFF%2C%20quando%20for%20o%20caso'
    if dispensa_licenciamento:
        return render_template('resultados.html', resultado='A empresa pode ser dispensada de licenciamento', cnaes_encontrados=cnaes_encontrados, nome_empresa=nome_empresa, cnpj=cnpj1, legislacao=legis, link=link, ctrl_cor=1, coluna=coluna)
    elif dispensa_licenciamento == None:
        return render_template('resultados.html', resultado='A empresa pode ser dispensada de licenciamento caso atenda as condições impostas', cnaes_encontrados=cnaes_encontrados, nome_empresa=nome_empresa, cnpj=cnpj1, legislacao=legis, link=link, ctrl_cor=1, coluna=coluna)
    else:
        return render_template('resultados.html', resultado='A empresa não pode ser dispensada de licenciamento', nome_empresa=nome_empresa, cnaes_encontrados=cnaes_encontrados, cnpj=cnpj1, legislacao=legis, link=link, ctrl_cor=1, coluna=coluna)

@app.route('/consultar_dispensa_ie', methods=['POST'])
def consultar_dispensa_ie():
    cnae = request.form['cnae']
    cnae = desformata_cnae(cnae)
    if not cnae:
        error_message = 'CNAE não foi inserido'
        return render_template('index.html', resultado=error_message, error_popup=True)
    else:
        atividade = consultar_atividade(cnae)
        # print(atividade)
        if 'erro' in atividade:
            return render_template('index.html', resultado='CNAE não encontrado', error_popup=True)
        cnae = desformata_cnae(cnae)  # Remover formatação do CNAE
        # print(cnae)
        conn = connect_to_database()
        cursor = conn.cursor()
        legis = 'Cnaes conferidos segundo o artigo.'
        link = 'https://www.coad.com.br/imagensMat/id220754.pdf'

        # Consultar o status do CNAE no banco de dados
        cursor.execute('SELECT obrigatoriedade_ie FROM app_controledispensacnaes WHERE cnae = %s', (cnae,))
        status = cursor.fetchone()
        if status:
            if status[0].lower() == 'sim':
                ctrl = 1
                resultado = "Necessita"
            elif status[0].lower() == 'não':
                ctrl = 0
                resultado = "Não necessita"
            elif status[0].lower() == 'sim/não':
                ctrl = 2
                resultado = "Depende se realiza fato gerador do ICMS"
            else:
                resultado = "Erro ao processar requisição"

        else:
            resultado = f"Não foi possível encontrar informações para o CNAE {cnae}"

        conn.close()
        
        # Consultar a atividade relacionada ao CNAE
        atividade = consultar_atividade(cnae)
        cnae = formatar_cnae(cnae)
        return render_template('result_consulta_ie.html', cnae=cnae, resultado=resultado, atividade=atividade, ctrl = ctrl, legis=legis, link=link)

@app.route('/consultar_dispensa', methods=['POST'])
def consultar_cnaes():
    legis = 'Cnaes consultados segundo o Decreto Nº 24861 DE 26/09/2023.'
    link = 'https://www.legisweb.com.br/legislacao/?id=450184#:~:text=Fixa%20as%20classifica%C3%A7%C3%B5es%20de%20risco,Complementar%20Municipal%20N%C2%BA%205788%2F2022.&text=c%C3%B3digos%20da%20CNAE.&text=eventual%20Alvar%C3%A1%20de%20Funcionamento%20e,TLFF%2C%20quando%20for%20o%20caso'

    if request.method == 'POST':
        cnae = request.form['cnae']
        if not cnae:
            error_message = 'CNAE não foi inserido'
            return render_template('index.html', resultado=error_message, error_popup=True)
        
        cnae = desformata_cnae(cnae)
        # print("CNAE desformatado:", cnae)
        cnae = formatar_cnae(cnae)
        # print("CNAE formatado:", cnae)
        cnaes_desejados = obter_cnaes_dispensados()
        condicao2 = None
        condicao = None
        for cnae_desejado in cnaes_desejados:
            # print(cnae_desejado)
            # print(cnae == cnae_desejado[0])
            if cnae == cnae_desejado[0]:
                atividade = cnae_desejado[1]
                condicao = cnae_desejado[2]
                status = cnae_desejado[3]
                
                if status == 'Dispensado':
                    status = status + emoji.emojize(':check_mark:')
                    ctrl = 1
                elif status == 'Depende':
                    ctrl = 3
                else:
                    status = status + emoji.emojize(':cross_mark:')
                    ctrl = 2
                    
                return render_template('result_consulta.html', resultado=status, cnae=cnae, atividade=atividade, ctrl=ctrl, legis=legis, link=link, condicao=condicao, condicao2=condicao2)
                
            # if cnae == cnae_desejado[0]:
            #     descricao_desejada = cnae_desejado[1]  # Descrição do CNAE desejado
            #     risco_ambiental_desejado = cnae_desejado[2]  # Risco ambiental do CNAE desejado
            #     risco_sanitario_desejado = cnae_desejado[3]  # Risco sanitário do CNAE desejado
            #     baixo_risco_a_desejado = cnae_desejado[4]  # Baixo risco A do CNAE desejado
            #     # Comparação dos valores das colunas com os valores obtidos dos CNAEs
            #     if baixo_risco_a_desejado == '***':    
            #         status = 'Dispensado' + emoji.emojize(':check_mark:')
            #     else:
            #         if risco_ambiental_desejado == 'Dispensa de Licença Ambiental de Operação (LO)' and risco_sanitario_desejado == 'Dispensa de Licença Sanitária':
            #             status = 'Dispensado' + emoji.emojize(':check_mark:')
            #         elif risco_ambiental_desejado == 'Alto Risco' and risco_sanitario_desejado == 'Alto Risco':
            #             status = 'Não dispensado' + emoji.emojize(':cross_mark:')
            #         elif risco_ambiental_desejado == 'Alto Risco' and risco_sanitario_desejado == 'Dispensa de Licença Sanitária':
            #             status = 'Não dispensado' + emoji.emojize(':cross_mark:')
            #             condicao = 'Alto risco ambiental'
            #         elif risco_ambiental_desejado == 'Dispensa de Licença Ambiental de Operação (LO)'  and risco_sanitario_desejado == 'Alto Risco':
            #             status = 'Não dispensado' + emoji.emojize(':cross_mark:')
            #             condicao = 'Alto risco sanitário'
            #         elif risco_ambiental_desejado != 'Alto Risco' and risco_sanitario_desejado == 'Alto Risco':
            #             if risco_ambiental_desejado != 'Dispensa de Licença Ambiental de Operação (LO)':
            #                 status = 'Depende'
            #                 condicao = risco_ambiental_desejado
            #         elif risco_ambiental_desejado != 'Alto Risco' and risco_sanitario_desejado == 'Dispensa de Licença Sanitária':
            #             if risco_ambiental_desejado != 'Dispensa de Licença Ambiental de Operação (LO)':
            #                 status = 'Depende'
            #                 condicao = risco_ambiental_desejado
            #         elif risco_ambiental_desejado == 'Dispensa de Licença Ambiental de Operação (LO)' and risco_sanitario_desejado != 'Alto Risco':
            #             if risco_sanitario_desejado != 'Dispensa de Licença Sanitária':
            #                 status = 'Depende'
            #                 condicao = risco_sanitario_desejado
            #         elif risco_ambiental_desejado == 'Alto Risco' and risco_sanitario_desejado != 'Alto Risco':
            #             if risco_sanitario_desejado != 'Dispensa de Licença Sanitária':
            #                 status = 'Depende'
            #                 condicao = risco_sanitario_desejado
            #         elif risco_sanitario_desejado != 'Alto Risco' and risco_ambiental_desejado != 'Alto Risco':
            #             if risco_ambiental_desejado != 'Dispensa de Licença Ambiental de Operação (LO)' and risco_sanitario_desejado != 'Dispensa de Licença Sanitária':
            #                 status = 'Não dispensado' + emoji.emojize(':cross_mark:')
            #                 condicao = risco_ambiental_desejado
            #                 condicao2 = risco_sanitario_desejado
            #         else:
            #             status = 'Não dispensado' + emoji.emojize(':cross_mark:')
            #     atividade = cnae_desejado[1]
            #     print("Atividade:", atividade)
            #     print(f'CNAE sem formatar: {cnae}')
            #     cnae = formatar_cnae(cnae)
            #     print(f'CNAE já formatado: {cnae}')
            #     if status == 'Dispensado' + emoji.emojize(':check_mark:'):
            #         ctrl = 1
            #     elif status == 'Depende':
            #         ctrl = 3
            #     else:
            #         ctrl = 2
            # return render_template('result_consulta.html', resultado=status, cnae=cnae, atividade=atividade, ctrl=ctrl, legis=legis, link=link, condicao=condicao, condicao2=condicao2)

@app.route('/index_cnae')
def index_cnae():
    return render_template('index.html', error_popup=False)

@app.route('/')
def index():
    return render_template('index_cnpj.html')

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html'), 500

if __name__ == '__main__':
    app.run(debug=True)
