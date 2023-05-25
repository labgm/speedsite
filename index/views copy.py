#| ESSA CÓPIA ESTAVA APENAS ENVIANDO OS DADOS PRO
#| SERVIDOR REMOTO 

import subprocess, os, uuid, time, psutil
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from zipfile import ZipFile
import paramiko
from .forms import UploadFileForm
from .models import User, Project, Process

# Create your views here.
#View inicial.
def index(request):
    form = UploadFileForm() #Carrega o formulário
    os.chdir('/var/www/html/speedy/') #Defini o diretório de trabalho
    diroot = os.getcwd()
    cleanSessions(request)
    print(diroot)
    return render(request, 'index.html', {'form': form, 'dir': diroot})

def upload(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES) #Recebe o formulário preenchido
        if form.is_valid(): #Verifica se o formulário foi preenchido corretamente
            
            # Informações de conexão SSH para o servidor remoto
            host = '200.239.92.130'
            username = 'victor'
            password = '@victor'
            port = 23

            # Caminho remoto onde o arquivo será salvo
            remote_path = '/storage1/victor/FILES_SPEEDYPIPE'


            # TESTE FUNCIONANDO
            # # Salvar o arquivo em um caminho temporário no servidor Django
            # for f in request.FILES.getlist('fileFastq'):
            #     temp_file_path = os.path.join('temp', f.name)
            #     with open(temp_file_path, 'wb+') as destination:
            #         for chunk in f.chunks():
            #             destination.write(chunk)
            #             print(f'Enviando arquivo {f.name}...')

            #     # Conectar ao servidor remoto
            #     ssh_client = paramiko.SSHClient()
            #     ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            #     ssh_client.connect(hostname=host, username=username, password=password, port=port)

            #     # Enviar arquivo para o servidor remoto
            #     local_path = f'temp/{f.name}'
            #     remote_path = f'/home/victor/dir_speedypipe/{f.name}'

            #     sftp_client = ssh_client.open_sftp()
            #     sftp_client.put(local_path, remote_path)

            #     # Fechar a conexão SFTP e SSH
            #     sftp_client.close()
            #     ssh_client.close()


            # Excluir o arquivo temporário do servidor Django
            # os.remove(temp_file_path)

            # CRIAR O USER NO DB COM OS DADOS DO FORMULÁRIO
            user = User.objects.create(name=request.POST['name'], email=request.POST['email'])
            user.save()
            project = Project.objects.create(user=user)
            project.save()
            
            # CRIAR PASTA DO PROJETO USER[PK]_PROJECT[PK]
            dirproject = f'USER{user.pk}_PROJECT{project.pk}'
            os.system(f'mkdir {dirproject}')
            request.session['statusUpload'] = 'Copying essentials files...'
            # Copia o pipeline pra Pasta do Projeto
            os.system(f'git clone git@github.com:engbiopct/speedypipe4meta.git {dirproject}')
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
                # return render(request, 'upload_arquivo.html', {'mensagem': 'Arquivo enviado com sucesso.'})  
                # handle_uploaded_file(request, f, f'{dirproject}/data')
            ssh_client = paramiko.SSHClient()
            ssh_client.load_system_host_keys()
            ssh_client.connect(hostname=host, username=username, password=password, port=port)

            sftp_client = ssh_client.open_sftp()
            sftp_client.mkdir(f'{remote_path}/{dirproject}') #Cria a pasta do Projeto no Servidor Remoto
            local_folder_path = dirproject
            remote_folder_path = f'{remote_path}/{dirproject}'
            
            # sftp_client.puttree(local_folder_path, remote_folder_path)

            send_folder(sftp_client, local_folder_path, remote_folder_path)
            list_files = sftp_client.listdir(f'{remote_path}/{dirproject}/data')

            sftp_client.close()
            ssh_client.close()
            message = 'Upload OK!'
            # return JsonResponse({'message': message, 'dirproject': dirproject, 'id': user.pk})
            return JsonResponse({'message': message, 'list_files': list_files})

            # return render(request, 'index.html', {'message': message, 'dirproject': dirproject})
    else:
        form = UploadFileForm()
        message = 'Faça o upload dos arquivos'
        return render(request, 'index.html', {'form': form, 'message': message})

def output_snakemake(request):
    context = {
        'output': 'Teste de Página',
        'time': '00:00:00', 
        'dirproject': 'USER33_PROJECT33'
    }
    return render(request, 'snakemake_output.html', context)

def processament(request):
    
    
    return render(request, 'processament.html', {'saida':'Out'})
    # from django.shortcuts import redirect
    # id_user = request.GET.get('id')

    # # Iniciando um processo usando a função Popen
    # with subprocess.Popen(["ping", "200.239.92.130", "-c", "30"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=30, universal_newlines=True) as processo:
    #     # Obtendo o ID do processo
    #     pid = processo.pid

    #     # Gerar um UUID para o processo
    #     process_uuid = uuid.uuid4()

    #     # Salvar o UUID em algum lugar (como um banco de dados)
    #     process = Process.objects.create(id=process_uuid, user=id_user, pid = pid)
    #     process.save()
    #     output = ""

    #     for line in processo.stdout:
    #         # armazenar a saída em uma string
    #         output += line
    #         # atualizar a sessão com a saída do processo
    #         print(line)
    #         process.lastUpdate = output
    #         process.save()
    #         # Imprima o ID do processo
    #         print("ID do processo: ", pid)

    # url_acompanhamento = '/status/?id=' + str(pid) + '&id_user=90'
    # # Redireciona o usuário para a página de acompanhamento
    # return redirect(url_acompanhamento)
    
    
    

    # Espere até que o subprocesso termine
    # processo.wait()

    # Obtenha uma referência ao processo pelo PID
    # processo = psutil.Process(pid)

    # with processo.oneshot():
    #     print(processo.name())  # execute internal routine once collecting multiple info
    #     print(processo.cpu_times())  # return cached value
    #     print(processo.cpu_percent())  # return cached value
    #     print(processo.create_time())  # return cached value
    #     print(processo.ppid())  # return cached value
    #     print(processo.status())  # return cached value
    
    # request.session['pid'] = pid
    # request.session.save()
    # Obtenha a saída do processo
    # saida = processo.info #.stdout.read().decode()
    # psutil.Process().cmdline()
    
    # Imprima a saída do processo
    # print(saida)

    # Envie um sinal SIGTERM para encerrar o processo
    # os.kill(pid, signal.SIGTERM)

    # Verifique se o processo ainda está em execução
    # if processo.poll() is None:
    #     print("O processo ainda está em execução.")
    # else:
    #     print("O processo foi encerrado.")

    # return render(request, 'processament.html', {'pid': pid})

def status(request):
    # Obtém o ID do processo a partir dos parâmetros passados na URL
    pid = int(request.GET.get('id'))
    dataProcess = Process.objects.get(pid=pid)

    if psutil.pid_exists(pid):
        print("O processo está em execução.")
        # Obtenha uma referência ao processo pelo PID
        processo = psutil.Process(pid)
        name = processo.name()
        pstatus = processo.status()
        create_time = time.strftime('%H:%M:%S', time.localtime(processo.create_time()))
    else:
        print("O processo foi encerrado.")
        name = 'O processo foi encerrado.'
        pstatus = 'O processo foi encerrado.'
        create_time = ''

    context = {
        'pid': pid,
        'status': pstatus,
        'time': create_time, 
        'dataProcess': dataProcess
    }

    # with processo.oneshot():
    #     print(processo.name())  # execute internal routine once collecting multiple info
    #     print(processo.cpu_times())  # return cached value
    #     print(processo.cpu_percent())  # return cached value
    #     print(processo.create_time())  # return cached value
    #     print(processo.ppid())  # return cached value
    #     print(processo.status())  # return cached value
    
    return render(request, 'status.html', context)

def run_snakemake(request):
    # Estabelecer conexão SSH com o servidor remoto
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect('<endereco_servidor>', username='<nome_usuario>', password='<senha>')

    dirproject = request.GET.get('dirproject')

    # Comando Snakemake para executar o pipeline
    command = f'snakemake --cores 30 --snakefile {dirproject}'

    # Executar o comando no servidor remoto
    stdin, stdout, stderr = ssh_client.exec_command(command)

    # Exibir a saída do comando
    print(stdout.read().decode())

    # Fechar a conexão SSH
    ssh_client.close()

    # dirproject = request.GET.get('dirproject')
    # id_user = request.GET.get('id')
    # project_dir = f'/storage1/victor/speedsite/{dirproject}'
    
    # # muda o diretório de trabalho para o do projeto
    # if os.path.exists(project_dir):
    #     # Mudar para o diretório do projeto
    #     os.chdir(project_dir)
    #     # Agora o diretório do projeto é o diretório de trabalho atual
    #     print("Diretório de trabalho atual:", os.getcwd())
    # else:
    #     print("Erro: o diretório do projeto não foi encontrado")
    
    # os.system('python create-config.py data --threads 16')

    # # Gerar um UUID para o processo
    # process_uuid = uuid.uuid4()
    # os.environ['SNAKEMAKE_PROCESS_ID'] = str(process_uuid)

    # # Salvar o UUID em algum lugar (como um banco de dados)
    # # process = Process.objects.create(id=process_uuid, user=id_user)
    # # process.save()
    # start_time = time.time()
    # # execute Snakemake using subprocess module
    # with subprocess.Popen(['snakemake', '--cores', '40'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=30, universal_newlines=True) as proc:
    #     # process = subprocess.Popen(['snakemake', '--cores', 'all'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    #     # subprocess.run(["snakemake", "-s", "/caminho/para/o/arquivo/Snakefile"], check=True)
    #     output = ""
    #     pid = proc.pid
    #     request.session['pid'] = pid
    #     request.session.save()
        
    #     for line in proc.stdout:
    #         # armazenar a saída em uma string
    #         output += line
    #         # atualizar a sessão com a saída do processo
    #         print(line)
    #         request.session['process_status'] = output #line.rstrip('\n')
    #         request.session.save()
    #     # output, error = proc.communicate()
    #     # print(output.decode('utf-8').rstrip('\n'))
    #     # request.session['process_status'] = output.decode('utf-8').rstrip('\n')
    #     # request.session.save()
        
    # end_time = time.time()
    # time_exec = time.strftime('%H:%M:%S', time.localtime(end_time - start_time))
    
    context = {
        # 'output': output.decode('utf-8').rstrip('\n'),
        'output': output,
        'time': time_exec, 
        'dirproject': dirproject
    }

    # render the template with the output
    return render(request, 'snakemake_output.html', context)

# FUNÇÕES ACESSÓRIAS =====================================================================================
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


def download_folder(request, project):

    folder_name = f'{project}/results'
    
    # Caminho completo para a pasta a ser compactada e baixada
    folder_path = os.path.join(folder_name)
    print(folder_path)
    # Nome do arquivo zip que será baixado
    zip_filename = f'{project}.zip'

    # Abre o arquivo zip para gravação
    with ZipFile(zip_filename, 'w') as zip_file:
        # Percorre a pasta e adiciona cada arquivo a o arquivo zip
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                zip_file.write(file_path, os.path.relpath(file_path, folder_path))

    # Abre o arquivo zip para leitura e cria uma resposta HTTP para download
    with open(zip_filename, 'rb') as zip_file:
        response = HttpResponse(zip_file.read(), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{zip_filename}"'

    # Remove o arquivo zip do disco rígido
    os.remove(zip_filename)

    # Retorna a resposta HTTP para download
    return response

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