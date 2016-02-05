import os
import zipfile

from fabric.colors import green
from fabric.api import local
from fabdeployconfig import env, dev, stage  # noqa

from jinja2 import Environment, FileSystemLoader

loader = FileSystemLoader('./conf/', followlinks=True)
templateEnv = Environment(loader=loader)


def _get_commit_id():
    return local('git rev-parse HEAD', capture=True)[:20]


def _get_current_branch_name():
    return local('git branch | grep "^*" | cut -d" " -f2', capture=True)


def notify(msg):
    bar = '+' + '-' * (len(msg) + 2) + '+'
    print green('')
    print green(bar)
    print green("| %s |" % msg)
    print green(bar)
    print green('')


def createDockerrunFile(tag):
    template = templateEnv.get_template('Dockerrun.aws.json.tmpl')
    fname = "conf/Dockerrun.aws.json"
    with open(fname, 'w') as f:
        data = template.render(tag=tag)
        f.write(data)
    notify("Create Dockerrun.aws.json with tag %s" % tag)


def createNginxConfig():
    template = templateEnv.get_template('nginx.ureport.conf.tmpl')
    fname = "conf/nginx.ureport.conf"
    with open(fname, 'w') as f:
        data = template.render(hostname=env.hostname)
        f.write(data)
    notify("Create nginx.ureport.conf with hostname: %(hostname)s" % env)


def _zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file))


def createZip():
    zipf = zipfile.ZipFile('conf/deploy.zip', 'w')
    _zipdir('.ebextensions/', zipf)
    zipf.write('conf/Dockerrun.aws.json', arcname='Dockerrun.aws.json')
    zipf.close()


def prebuild():
    createNginxConfig()


def preparedeploy():
    createDockerrunFile(os.environ.get("TRAVIS_TAG", "latest"))
    createZip()
