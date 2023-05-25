import subprocess, os, uuid, time, psutil, zipfile, paramiko, io, pysftp, re
from io import StringIO
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse, FileResponse
from zipfile import ZipFile
from .forms import UploadFileForm
from .models import User, Project, Processament
from django.core.exceptions import ObjectDoesNotExist
from bs4 import BeautifulSoup
import pandas as pd
import altair as alt
# from vega_datasets import data
# Create your views here.

# VIEW INICIAL
def index(request):
    form = UploadFileForm() #Carrega o formulário
    os.chdir('/var/www/html/speedy/') #Defini o diretório de trabalho
    diroot = os.getcwd()
    cleanSessions(request)
    print(diroot)
    return render(request, 'index.html', {'form': form, 'dir': diroot})

# VIEW UPLOAD FILES
def upload(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES) #Recebe o formulário preenchido
        if form.is_valid(): #Verifica se o formulário foi preenchido corretamente

            # Caminho remoto onde o arquivo será salvo
            remote_path = '/storage1/victor/FILES_SPEEDYPIPE'

            # CRIAR O USER NO DB COM OS DADOS DO FORMULÁRIO
            user = User.objects.create(name=request.POST['name'], email=request.POST['email'])
            user.save()
            project = Project.objects.create(user=user)
            project.save()
            
            # CRIAR PASTA DO PROJETO USER[PK]_PROJECT[PK]
            dirproject = f'USER{user.pk}_PROJECT{project.pk}'
            os.system(f'mkdir {dirproject}')
            request.session['statusUpload'] = 'Copying essentials files...'
            os.system(f'mkdir {dirproject}/data')
            
            for f in request.FILES.getlist('fileFastq'):
                file_size = f.size
                uploaded_size = 0
                with open(f'{dirproject}/data/{f}', 'wb+') as destino:
                    for chunk in f.chunks():  # Lê o arquivo em pedaços
                        destino.write(chunk)  # Grava cada pedaço do arquivo no arquivo de destino
                        uploaded_size += len(chunk)
                        percentage = round((uploaded_size / file_size) * 100)
                        request.session['statusUpload'] = f'Saving file: {f}'
                        request.session['filePercent'] = percentage
                        request.session.save()
                        print(f'Gravando arquivo {f} {percentage}%')
            # Informações de conexão SSH para o servidor remoto
            host = '200.239.92.130'
            username = 'victor'
            password = '@victor'
            port = 23

            # PREPARA A CONEXÃO REMOTA
            ssh_client = paramiko.SSHClient()
            ssh_client.load_host_keys('/home/victor/.ssh/known_hosts')
            #ssh_client.load_system_host_keys()
            ssh_client.connect(hostname=host, username=username, password=password, port=port)
            sftp_client = ssh_client.open_sftp()
            
            #Cria a pasta do Projeto no Servidor Remoto
            sftp_client.mkdir(f'{remote_path}/{dirproject}') 
            local_folder_path = dirproject
            remote_folder_path = f'{remote_path}/{dirproject}'
            send_folder(sftp_client, local_folder_path, remote_folder_path)
            
            # LISTA OS ARQUIVOS ENVIADOS PARA A EXIBIÇÃO 
            list_files = sftp_client.listdir(f'{remote_path}/{dirproject}/data')
            
            sftp_client.close()
            ssh_client.close()

            processament = Processament.objects.create(project=project, status='Pending', priority=2)
            processament.save()

            # return render(request, 'processament.html', context)
            return JsonResponse({'message' : 'Your files have been submitted!', 
                                 'list_files': list_files,
                                 'data_processament': project.pk})
    else:
        form = UploadFileForm()
        message = 'Faça o upload dos arquivos'
        return render(request, 'index.html', {'form': form, 'message': message})

def outputs(request):
    # GRÁFICO DE QUALIDADE
    # scores = extract_data_from_fastqc_txt('/var/www/html/speedy/USER154_PROJECT154/results/F1/fastqc/F1_1_fastqc/fastqc_data.txt')    
    # chart = plot_quality_scores(scores)
    # chart_html = chart.to_html()
    # chart_json = chart.to_json()
    # os.listdir('/var/www/html/speedy/USER169_PROJECT169/results/F1/fastqc/F1_1_fastqc/im')
    id = request.GET.get('id')

    host = '200.239.92.130'
    username = 'victor'
    password = '@victor'
    port = 23

    # PREPARA A CONEXÃO REMOTA
    ssh_client = paramiko.SSHClient()
    ssh_client.load_host_keys('/home/victor/.ssh/known_hosts')
    #ssh_client.load_system_host_keys()
    ssh_client.connect(hostname=host, username=username, password=password, port=port)
    sftp_client = ssh_client.open_sftp()
    
    # Realiza a conexão SFTP
    transport = paramiko.Transport((host, port))
    transport.connect(username=username, password=password)
    sftp = transport.open_sftp_client()

    # LISTA AS AMOSTRAS DO PROJETO
    samples = sftp_client.listdir(f'/storage1/victor/FILES_SPEEDYPIPE/USER{id}_PROJECT{id}/results')
    if 'bin' in samples:
        samples.remove('bin')
    if 'comandos.sh' in samples:
        samples.remove('comandos.sh')
    if 'microeco' in samples:
        samples.remove('microeco')
    data = {}

    for sample in samples:
        # Caminho do arquivo HTML remoto
        remote_fastqc_foward = f'/storage1/victor/FILES_SPEEDYPIPE/USER{id}_PROJECT{id}/results/{sample}/fastqc/{sample}_1_fastqc.html'
        remote_fastqc_reverse = f'/storage1/victor/FILES_SPEEDYPIPE/USER{id}_PROJECT{id}/results/{sample}/fastqc/{sample}_2_fastqc.html'
        remote_kraken_path = f'/storage1/victor/FILES_SPEEDYPIPE/USER{id}_PROJECT{id}/results/{sample}/kraken/{sample}_report.html'
        
        # list = ['chave1', 'valor1', 'chave2', 'valor2', 'chave3', 'valor3']

        # dicionario = dict(zip(lista[::2], lista[1::2]))
        # print(dicionario)                                             
        
        # Obtém o conteúdo do arquivo HTML Foward e Reverse
        html_foward = sftp.open(remote_fastqc_foward, 'r')
        html_reverse = sftp.open(remote_fastqc_reverse, 'r')
        
        # Faz a leitura do arquivo com decodificação UTF-8
        html_foward = html_foward.read().decode('utf-8')
        html_reverse = html_reverse.read().decode('utf-8')

        html_foward = html_foward.replace('#M',f'#{sample}')
        html_foward = html_foward.replace('id="M',f'id="{sample}')
        html_reverse = html_reverse.replace('#M',f'#{sample}')
        html_reverse = html_reverse.replace('id="M',f'id="{sample}')

        # Lê o arquivo com o BeautifulSoup
        soup_foward = BeautifulSoup(html_foward, 'html.parser')
        soup_reverse = BeautifulSoup(html_reverse, 'html.parser')
        
        # Extrai as informações da classe main do html
        div_main_foward = soup_foward.find('div', class_='main')
        div_main_reverse = soup_reverse.find('div', class_='main')
        conteudo_div_main_foward = div_main_foward.prettify()
        conteudo_div_main_reverse = div_main_reverse.prettify()
        
        # Extrai as informações da classe summary do html
        div_summary_foward = soup_foward.find('div', class_='summary')
        div_summary_reverse = soup_reverse.find('div', class_='summary')
        conteudo_div_summary_foward = div_summary_foward.prettify()
        conteudo_div_summary_reverse = div_summary_reverse.prettify()

        # Obtém o conteúdo do arquivo report do Kraken
        kraken_report = sftp.open(remote_kraken_path, 'r')
        html_kraken_report = kraken_report.read().decode('utf-8')
        
        # adiciona a informação ao dicionário
        data[sample] = {
            'conteudo_div_main_foward': conteudo_div_main_foward,
            'conteudo_div_main_reverse': conteudo_div_main_reverse,
            'conteudo_div_summary_foward': conteudo_div_summary_foward,
            'conteudo_div_summary_reverse': conteudo_div_summary_reverse,
            'html_kraken_report': html_kraken_report   
        }

    # print(data)


    # Fecha a conexão SFTP
    sftp.close()
    transport.close()
    sftp_client.close()
    ssh_client.close()
    # samples = os.listdir('/storage1/victor/FILES_SPEEDYPIPE/USER169_PROJECT169/results')

    # Código para criar o gráfico de qualidade de sequenciamento usando o Altair
    # grafico_qualidade = alt.Chart(dados_fastqc).mark_line().encode(
    #     x='Posição',
    #     y='Qualidade Média',
    #     tooltip=['Posição', 'Qualidade Média']
    # ).properties(
    #     title='Gráfico de Qualidade de Sequenciamento',
    #     xlabel='Posição',
    #     ylabel='Qualidade Média'
    # ).to_json()
    
    context = {
        # 'chart_html': chart_html, 
        # 'scores':scores
        'samples': samples,
        'data': data
    }

    return render(request, 'outputs.html', context)
    # return render(request, 'outputs.html', context)



def processament(request):
    id = request.GET.get('id')
    if id:
        try:
            project = Processament.objects.get(project=id)
            return render(request, 'processament.html', {'id':id, 'project':project})
        except ObjectDoesNotExist:
            return render(request, 'processament.html', {'message': f'Projetc {id} not found!'})
    else:
        return render(request, 'processament.html')


# FUNÇÕES ACESSÓRIAS =====================================================================================
def extract_data_from_fastqc_html(file_path):
    with open(file_path, 'r') as file:
        soup = BeautifulSoup(file, 'html.parser')

        # Exemplo de extração de informações
        # Extraia as informações relevantes do soup aqui
        # Use métodos como find(), find_all(), etc.

        # Exemplo: Extraia as pontuações de qualidade média
        quality_scores = soup.find_all('span', class_='qc-icon-warn')
        scores = [float(score.text) for score in quality_scores]

    return scores

def extract_data_from_fastqc_txt(file_path):
    # Ler o arquivo de dados do FastQC usando o Pandas
    df = pd.read_csv(file_path, sep='\t')

    # Extrair as pontuações de qualidade média
    scores = df[df['#Base'] != '>>END_MODULE'][['#Base', 'Mean']].astype({'Mean': float})

    return scores

def plot_quality_scores(scores):
    data = pd.DataFrame({'Quality Score': scores})

    chart = alt.Chart(data).mark_bar().encode(
        x='Quality Score',
        y='count()'
    ).properties(
        title='Quality Score Distribution'
    )
    return chart
# DOWNLOAD DE ARQUIVOS
def download_directory(request):
    id = request.GET.get('id')
    file = f'USER{id}_PROJECT{id}'
    diretorio = f'/storage1/victor/FILES_SPEEDYPIPE'
    
    # Informações de conexão SSH para o servidor remoto
    host = '200.239.92.130'
    username = 'victor'
    password = '@victor'
    port = 23  # Porta padrão para SSH

    # Diretório remoto onde os arquivos processados estão localizados
    remote_directory = diretorio

    # Diretório local onde você deseja salvar os arquivos de volta
    local_directory = '/var/www/html/speedy/tmp'

    zip_command = f'cd {remote_directory} && zip -r {file}.zip {file}'

    # Estabelecer a conexão SSH
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(hostname=host, username=username, password=password, port=port)

    # Abrir o cliente SFTP
    sftp_client = ssh_client.open_sftp()

    # Executar o comando no servidor remoto
    stdin, stdout, stderr = ssh_client.exec_command(zip_command)
    
    remote_file_path = f'{remote_directory}/{file}.zip'
    local_file_path = f'{local_directory}/{file}.zip'

    sftp_client.get(remote_file_path, local_file_path)

    zip_filename = f'{local_directory}/{file}.zip'
    
    # Abre o arquivo zip para leitura e cria uma resposta HTTP para download
    with open(zip_filename, 'rb') as zip_file:
        response = HttpResponse(zip_file.read(), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{file}.zip"'
    
    # Fechar a conexão SFTP e SSH
    sftp_client.close()
    ssh_client.close()
    
    # Retorna a resposta HTTP para download
    return response

def handle_uploaded_file(request, f, directory):
    destination = open(f'{directory}/{f}', 'wb+')
    file_size = f.size
    uploaded_size = 0
    for chunk in f.chunks():
        destination.write(chunk)
        uploaded_size += len(chunk)
        percentage = round((uploaded_size / file_size) * 100)
        request.session['statusUpload'] = f'Enviando arquivo {f} {percentage}%'
        request.session['filePercent'] = percentage
        request.session.save()
        print(f'Gravando arquivo {f} {percentage}%')
    destination.close()

def cleanSessions(request):
    request.session['process_status'] = ''
    request.session['pid'] = 0
    request.session['statusUpload'] = ''
    request.session['filePercent'] = 0

def progress_view(request):
    # Recupera as informações de progresso da sessão
    progress = request.session.get('filePercent', None)

    if progress is None:
        # Retorna uma mensagem de erro se não houver informações de progresso na sessão
        return HttpResponse('Erro ao recuperar informações de progresso!', status=500)
    elif progress == 100:
        # Retorna uma mensagem de conclusão se o progresso for 100%
        del request.session['filePercent']
        del request.session['statusProcessament']
        request.session.save()
        return HttpResponse('Arquivo salvo com sucesso!')
    else:
        # Retorna as informações de progresso como uma resposta HTTP
        return HttpResponse(progress)

def get_process_status(request):
    # recupera o status do processo da sessão
    status = request.session.get('process_status', '')
    pid = request.session.get('pid', 0)
    statusUpload = request.session.get('statusUpload', '')
    filePercent = request.session.get('filePercent', '')
    if psutil.pid_exists(pid):
        print("O processo ainda está em execução.")
        processo = psutil.Process(pid)
        name = processo.name()
        pstatus = processo.status()
        create_time = time.strftime('%H:%M:%S', time.localtime(processo.create_time()))
    else:
        print("O processo foi encerrado.")
        name = 'O processo foi encerrado.'
        pstatus = ''
        create_time = ''
    
    # retorna o status como uma resposta JSON
    return JsonResponse({'status': status, 'statusUpload': statusUpload, 'filePercent': filePercent, 'pid': pid, 'name': name, 'pstatus': pstatus, 'create_time': create_time})

def send_folder(sftp, local_path, remote_path):
    for root, dirs, files in os.walk(local_path):
        # Itera sobre todos os arquivos na pasta local
        for file in files:
            local_file_path = os.path.join(root, file)
            relative_path = os.path.relpath(local_file_path, local_path)
            remote_file_path = os.path.join(remote_path, relative_path)

            # Envia o arquivo individual usando sftp_client.put()
            sftp.put(local_file_path, remote_file_path)

        # Itera sobre todas as pastas na pasta local
        for dir in dirs:
            local_dir_path = os.path.join(root, dir)
            relative_path = os.path.relpath(local_dir_path, local_path)
            remote_dir_path = os.path.join(remote_path, relative_path)

            # Cria a pasta remota, caso ainda não exista
            try:
                sftp.mkdir(remote_dir_path)
            except IOError:
                pass

def get_folder(sftp, remote_path, local_path):
    # Verifica se o diretório local existe, caso contrário, cria-o
    if not os.path.exists(local_path):
        os.makedirs(local_path)

    # Obtém a lista de arquivos e diretórios remotos
    file_list = sftp.listdir(remote_path)

    # Itera sobre todos os arquivos e diretórios remotos
    for file in file_list:
        remote_file_path = os.path.join(remote_path, file)
        local_file_path = os.path.join(local_path, file)

        # Verifica se é um arquivo ou diretório
        if sftp.isfile(remote_file_path):
            # Faz o download do arquivo individual usando sftp.get()
            sftp.get(remote_file_path, local_file_path)
        elif sftp.isdir(remote_file_path):
            # Cria o diretório local, caso ainda não exista
            if not os.path.exists(local_file_path):
                os.makedirs(local_file_path)
            
            # Recursivamente chama a função get_folder para o diretório remoto
            get_folder(sftp, remote_file_path, local_file_path)