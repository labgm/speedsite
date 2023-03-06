from django.shortcuts import render
from django.http import JsonResponse
import subprocess, os
from .forms import UploadFileForm
from .models import User, Project

# Create your views here.
def index(request):
    form = UploadFileForm()
    os.chdir('/storage1/victor/speedsite/')
    diroot = os.getcwd()
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
            os.system(f'git clone git@github.com:engbiopct/speedypipe4meta.git {dirproject}')
            os.system(f'mkdir {dirproject}/data')
            
            for f in request.FILES.getlist('fileFastq'):
                handle_uploaded_file(request, f, f'{dirproject}/data')
            message = 'Upload OK!'
            return JsonResponse({'message': message, 'dirproject': dirproject})
            # return render(request, 'index.html', {'message': message, 'dirproject': dirproject})
    else:
        form = UploadFileForm()
        message = 'Faça o upload dos arquivos'
        return render(request, 'index.html', {'form': form, 'message': message})

def processament(request):

    return render(request, 'processament.html')

def run_snakemake(request):
    dirproject = request.GET.get('dirproject')
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
    pathSnakefile = os.path.join(dirproject, 'Snakefile')
    print(pathSnakefile)

    # execute Snakemake using subprocess module
    with subprocess.Popen(['snakemake', '--cores', 'all'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT) as proc:
        # process = subprocess.Popen(['snakemake', '--cores', 'all'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        # subprocess.run(["snakemake", "-s", "/caminho/para/o/arquivo/Snakefile"], check=True)
        output, error = proc.communicate()
        print(output.decode('utf-8').rstrip('\n'))
        request.session['process_status'] = output.decode('utf-8').rstrip('\n')
        request.session.save()
        
        context = {
            'output': output.decode('utf-8').rstrip('\n'),
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
        request.session['statusProcessament'] = f'Enviando arquivo {f} {percentage}%'
        request.session['filePercent'] = percentage
        request.session.save()
        print(f'Enviando arquivo {f} {percentage}%')
    destination.close()

def get_process_status(request):
    # recupera o status do processo da sessão
    status = request.session.get('process_status', '')
    
    # retorna o status como uma resposta JSON
    return JsonResponse({'status': status})