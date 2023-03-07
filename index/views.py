from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
import subprocess, os, uuid, time, psutil
from .forms import UploadFileForm
from .models import User, Project, Process

# Create your views here.
def index(request):
    form = UploadFileForm()
    os.chdir('/storage1/victor/speedsite/')
    diroot = os.getcwd()
    cleanSessions(request)
    print(diroot)
    return render(request, 'index.html', {'form': form, 'dir': diroot})

def upload(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            # CRIAR O USER NO DB COM OS DADOS DO FORMULÁRIO
            user = User.objects.create(name=request.POST['name'], email=request.POST['email'])
            user.save()
            project = Project.objects.create(user=user)
            project.save()
            
            # CRIAR PASTA DO PROJETO USER[PK]_PROJECT[PK]
            dirproject = f'USER{user.pk}_PROJECT{project.pk}'
            os.system(f'mkdir {dirproject}')
            request.session['statusUpload'] = 'Copying essentials files...'
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
            message = 'Upload OK!'
            return JsonResponse({'message': message, 'dirproject': dirproject, 'id': user.pk})
            # return render(request, 'index.html', {'message': message, 'dirproject': dirproject})
    else:
        form = UploadFileForm()
        message = 'Faça o upload dos arquivos'
        return render(request, 'index.html', {'form': form, 'message': message})

def output_snakemake(request):
    return render(request, 'snakemake_output.html')

def processament(request):
    # Iniciando um processo usando a função Popen
    processo = subprocess.Popen(["ping", "200.239.92.130", "-c", "30"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    # Obtendo o ID do processo
    pid = processo.pid
    # pid = 44224

    # Obtenha uma referência ao processo pelo PID
    processo = psutil.Process(pid)

    with processo.oneshot():
        print(processo.name())  # execute internal routine once collecting multiple info
        print(processo.cpu_times())  # return cached value
        print(processo.cpu_percent())  # return cached value
        print(processo.create_time())  # return cached value
        print(processo.ppid())  # return cached value
        print(processo.status())  # return cached value
    
    request.session['pid'] = pid
    request.session.save()
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

    # Imprima o ID do processo
    print("ID do processo: ", pid)
    return render(request, 'processament.html', {'pid': pid})

def run_snakemake(request):
    dirproject = request.GET.get('dirproject')
    id_user = request.GET.get('id')
    project_dir = f'/storage1/victor/speedsite/{dirproject}'
    
    # muda o diretório de trabalho para o do projeto
    if os.path.exists(project_dir):
        # Mudar para o diretório do projeto
        os.chdir(project_dir)
        # Agora o diretório do projeto é o diretório de trabalho atual
        print("Diretório de trabalho atual:", os.getcwd())
    else:
        print("Erro: o diretório do projeto não foi encontrado")
    
    os.system('python create-config.py data')

     # Gerar um UUID para o processo
    process_uuid = uuid.uuid4()
    os.environ['SNAKEMAKE_PROCESS_ID'] = str(process_uuid)

    # Salvar o UUID em algum lugar (como um banco de dados)
    # process = Process.objects.create(id=process_uuid, user=id_user)
    # process.save()

    # execute Snakemake using subprocess module
    with subprocess.Popen(['snakemake', '--cores', 'all'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=30, universal_newlines=True) as proc:
        # process = subprocess.Popen(['snakemake', '--cores', 'all'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        # subprocess.run(["snakemake", "-s", "/caminho/para/o/arquivo/Snakefile"], check=True)
        output = ""
        pid = proc.pid
        request.session['pid'] = pid
        request.session.save()
        for line in proc.stdout:
            # armazenar a saída em uma string
            output += line
            # atualizar a sessão com a saída do processo
            print(line)
            request.session['process_status'] = output #line.rstrip('\n')
            request.session.save()
        # output, error = proc.communicate()
        # print(output.decode('utf-8').rstrip('\n'))
        # request.session['process_status'] = output.decode('utf-8').rstrip('\n')
        # request.session.save()
        
        context = {
            # 'output': output.decode('utf-8').rstrip('\n'),
            'output': output,
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